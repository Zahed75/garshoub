import re
import secrets
import logging
import unicodedata
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


def _slugify(text):
    """Convert company name to a safe DB name slug."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[\s_-]+', '_', text)
    return re.sub(r'^-+|-+$', '', text)


class SaasRegistration(models.Model):
    _name = 'saas.registration'
    _description = 'SaaS Client Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ── Basic Info ───────────────────────────────────────────────────────────
    name = fields.Char(string='Company Name', required=True, tracking=True)
    contact_name = fields.Char(string='Contact Full Name', required=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', default='+880')
    country_id = fields.Many2one('res.country', string='Country')
    language = fields.Selection(
        [('en_US', 'English'), ('bn_BD', 'Bengali')],
        string='Language', default='en_US',
    )
    company_size = fields.Selection(
        [('1-5', '1–5'), ('6-20', '6–20'), ('21-100', '21–100'), ('100+', '100+')],
        string='Company Size',
    )
    primary_interest = fields.Char(string='Primary Interest / Module')

    # ── Provisioning ─────────────────────────────────────────────────────────
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('suspended', 'Suspended'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='pending', tracking=True,
    )
    db_name = fields.Char(string='Database Name', tracking=True,
                          help='Auto-generated from company name.')
    subdomain = fields.Char(string='Subdomain URL', readonly=True)
    approved_date = fields.Datetime(string='Approved On', readonly=True)
    admin_password = fields.Char(string='Initial Admin Password', readonly=True)

    # ── CRM lead reference ────────────────────────────────────────────────────
    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead', readonly=True)

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains('email')
    def _check_email_unique(self):
        for rec in self:
            if self.search_count([('email', '=', rec.email), ('id', '!=', rec.id)]) > 0:
                raise ValidationError(_('A registration with this email already exists.'))

    @api.constrains('db_name')
    def _check_db_name_unique(self):
        for rec in self:
            if rec.db_name and self.search_count([('db_name', '=', rec.db_name), ('id', '!=', rec.id)]) > 0:
                raise ValidationError(_('A client database with this name already exists.'))

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not self.db_name:
            self.db_name = _slugify(self.name)

    # ── Lifecycle hooks ───────────────────────────────────────────────────────
    def create(self, vals):
        rec = super().create(vals)
        rec._create_crm_lead()
        return rec

    def _create_crm_lead(self):
        """Create a CRM lead for every new registration."""
        self.ensure_one()
        CrmLead = self.env['crm.lead']
        if not CrmLead:
            return
        try:
            lead = CrmLead.sudo().create({
                'name': f"[SaaS] {self.name}",
                'contact_name': self.contact_name,
                'email_from': self.email,
                'phone': self.phone,
                'description': (
                    f"Company: {self.name}\n"
                    f"Contact: {self.contact_name}\n"
                    f"Size: {self.company_size or '-'}\n"
                    f"Interest: {self.primary_interest or '-'}\n"
                    f"Source: Raptron ERP Self-Registration"
                ),
                'type': 'lead',
            })
            self.crm_lead_id = lead.id
            _logger.info('CRM lead %s created for registration %s', lead.id, self.id)
        except Exception as e:
            _logger.warning('Could not create CRM lead: %s', str(e))

    # ── State Transitions ─────────────────────────────────────────────────────
    def action_submit(self):
        for rec in self:
            rec.state = 'pending'

    def action_approve(self):
        """Approve registration, provision database, send credentials email."""
        for rec in self:
            if rec.state != 'pending':
                raise UserError(_('Only pending registrations can be approved.'))
            rec._ensure_db_name()
            rec._provision_database()
            rec.write({
                'state': 'approved',
                'approved_date': datetime.now(),
                'subdomain': f"{rec.db_name}.raptron.com",
            })
            rec._send_onboarding_email()
            # Update CRM lead to Won
            if rec.crm_lead_id:
                try:
                    rec.crm_lead_id.sudo().write({'stage_id': rec._get_won_stage_id()})
                except Exception:
                    pass
            rec.message_post(
                body=_('✅ Database <b>%s</b> provisioned. Credentials emailed to <b>%s</b>.') % (
                    rec.db_name, rec.email,
                )
            )

    def _get_won_stage_id(self):
        stage = self.env['crm.stage'].sudo().search([('is_won', '=', True)], limit=1)
        return stage.id if stage else False

    def action_suspend(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Only approved clients can be suspended.'))
            rec.state = 'suspended'
            rec.message_post(body=_('⚠️ Client suspended. Database retained.'))

    def action_reactivate(self):
        for rec in self:
            if rec.state != 'suspended':
                raise UserError(_('Only suspended clients can be reactivated.'))
            rec.state = 'approved'
            rec.message_post(body=_('✅ Client reactivated.'))

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    # ── Core Provisioning ─────────────────────────────────────────────────────
    def _ensure_db_name(self):
        self.ensure_one()
        if not self.db_name:
            self.db_name = _slugify(self.name)

    def _provision_database(self):
        """Create a new Odoo database for the client."""
        self.ensure_one()
        db_name = self.db_name
        _logger.info('Provisioning new SaaS database: %s', db_name)
        try:
            from odoo.service.db import exp_create_database
            password = self.admin_password or secrets.token_urlsafe(12)
            exp_create_database(
                db_name,
                demo=False,
                lang='en_US',
                user_password=password,
                login='admin',
                country_code=None,
                phone=self.phone or '',
            )
            self.admin_password = password
            _logger.info('Database %s created successfully.', db_name)
        except Exception as e:
            _logger.error('Failed to create database %s: %s', db_name, str(e))
            raise UserError(
                _('Database provisioning failed for "%s".\nError: %s') % (db_name, str(e))
            )

    def _send_onboarding_email(self):
        """Send onboarding credentials email to client."""
        self.ensure_one()
        template = self.env.ref(
            'raptron_admin.email_template_saas_onboarding',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
        else:
            _logger.warning('Onboarding email template not found.')

    def action_delete_database(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm Database Deletion'),
            'res_model': 'saas.registration.delete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_registration_id': self.id},
        }

    @staticmethod
    def provision_manual(env, vals):
        """Called from admin portal to manually create a client with a custom password."""
        password = vals.pop('admin_password', None) or secrets.token_urlsafe(12)
        vals['admin_password'] = password
        vals['state'] = 'pending'
        rec = env['saas.registration'].sudo().create(vals)
        return rec
