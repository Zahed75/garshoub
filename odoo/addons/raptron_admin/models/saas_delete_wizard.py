from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaasRegistrationDeleteWizard(models.TransientModel):
    _name = 'saas.registration.delete.wizard'
    _description = 'Confirm Client Database Deletion'

    registration_id = fields.Many2one('saas.registration', string='Registration', required=True)
    confirm_name = fields.Char(string='Type Database Name to Confirm')

    def action_confirm_delete(self):
        self.ensure_one()
        reg = self.registration_id
        if self.confirm_name != reg.db_name:
            raise UserError(_('Database name does not match. Deletion cancelled.'))
        try:
            from odoo.service.db import exp_drop
            exp_drop(reg.db_name)
        except Exception as e:
            raise UserError(_('Failed to drop database: %s') % str(e))
        reg.message_post(body=_('🗑️ Database %s has been permanently deleted.') % reg.db_name)
        reg.write({'state': 'cancelled', 'db_name': False, 'subdomain': False})
        return {'type': 'ir.actions.act_window_close'}
