import logging
import secrets
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RaptronAdminPortal(http.Controller):

    # ─── PUBLIC REGISTRATION FORM ────────────────────────────────────────────

    @http.route('/register', type='http', auth='public', methods=['POST'], csrf=False)
    def register_submit(self, **post):
        required = ['contact_name', 'name', 'email', 'phone']
        for field in required:
            if not post.get(field):
                return request.redirect('/?error=missing_fields')

        existing = request.env['saas.registration'].sudo().search(
            [('email', '=', post['email'])], limit=1
        )
        if existing:
            return request.redirect('/?error=email_exists')

        try:
            request.env['saas.registration'].sudo().create({
                'name': post.get('name'),
                'contact_name': post.get('contact_name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'country_id': int(post['country_id']) if post.get('country_id') else False,
                'language': post.get('language', 'en_US'),
                'company_size': post.get('company_size'),
                'primary_interest': post.get('primary_interest'),
                'state': 'pending',
            })
        except Exception as e:
            _logger.error('Registration failed: %s', str(e))
            return request.redirect('/?error=server_error')

        return request.redirect('/thank-you')

    @http.route('/thank-you', type='http', auth='public', website=False, csrf=False)
    def thank_you(self, **kw):
        return request.render('raptron_admin.portal_thank_you')

    # ─── STANDALONE ADMIN DASHBOARD ──────────────────────────────────────────

    @http.route('/admin', type='http', auth='user', website=False, csrf=False)
    def admin_dashboard(self, **kw):
        SaasReg = request.env['saas.registration'].sudo()
        stats = {
            'total': SaasReg.search_count([]),
            'pending': SaasReg.search_count([('state', '=', 'pending')]),
            'approved': SaasReg.search_count([('state', '=', 'approved')]),
            'suspended': SaasReg.search_count([('state', '=', 'suspended')]),
        }
        pending_list = SaasReg.search([('state', '=', 'pending')], limit=20, order='create_date desc')
        active_list = SaasReg.search([('state', '=', 'approved')], limit=20, order='approved_date desc')
        countries = request.env['res.country'].sudo().search([])
        msg = kw.get('msg')
        return request.render('raptron_admin.admin_dashboard_template', {
            'stats': stats,
            'pending_list': pending_list,
            'active_list': active_list,
            'countries': countries,
            'msg': msg,
        })

    @http.route('/admin/approve/<int:reg_id>', type='http', auth='user', csrf=False)
    def admin_approve(self, reg_id, **kw):
        reg = request.env['saas.registration'].sudo().browse(reg_id)
        if reg.exists() and reg.state == 'pending':
            try:
                reg.action_approve()
            except Exception as e:
                _logger.error('Approval failed: %s', str(e))
                return request.redirect('/admin?msg=error')
        return request.redirect('/admin')

    @http.route('/admin/suspend/<int:reg_id>', type='http', auth='user', csrf=False)
    def admin_suspend(self, reg_id, **kw):
        reg = request.env['saas.registration'].sudo().browse(reg_id)
        if reg.exists() and reg.state == 'approved':
            reg.action_suspend()
        return request.redirect('/admin')

    @http.route('/admin/create', type='http', auth='user', methods=['POST'], csrf=False)
    def admin_create_client(self, **post):
        """Manually create a client database from admin dashboard."""
        required = ['name', 'contact_name', 'email', 'phone']
        for f in required:
            if not post.get(f):
                return request.redirect('/admin?msg=missing_fields')

        existing = request.env['saas.registration'].sudo().search(
            [('email', '=', post['email'])], limit=1
        )
        if existing:
            return request.redirect('/admin?msg=email_exists')

        try:
            password = post.get('admin_password') or secrets.token_urlsafe(12)
            reg = request.env['saas.registration'].sudo().create({
                'name': post.get('name'),
                'contact_name': post.get('contact_name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'country_id': int(post['country_id']) if post.get('country_id') else False,
                'company_size': post.get('company_size'),
                'primary_interest': post.get('primary_interest'),
                'admin_password': password,
                'state': 'pending',
            })
            # Auto-approve if admin chose to provision immediately
            if post.get('auto_approve') == '1':
                reg.action_approve()
            return request.redirect('/admin?msg=created')
        except Exception as e:
            _logger.error('Manual client creation failed: %s', str(e))
            return request.redirect('/admin?msg=error')
