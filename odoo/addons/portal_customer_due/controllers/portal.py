from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalDue(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'due_amount' in counters:
            invoices = request.env['account.move'].sudo().search([
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
            ])
            values['due_amount'] = sum(invoices.mapped('amount_residual'))

        if 'overdue_amount' in counters:
            overdue_invoices = request.env['account.move'].sudo().search([
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', request.env.cr.now().date()),
            ])
            values['overdue_amount'] = sum(overdue_invoices.mapped('amount_residual'))

        return values

    @http.route(['/my/dues'], type='http', auth='user', website=True)
    def portal_my_dues(self, **kw):
        partner = request.env.user.partner_id
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ], order='invoice_date_due asc')

        values = self._prepare_portal_layout_values()
        values.update({
            'invoices': invoices,
            'total_due': sum(invoices.mapped('amount_residual')),
            'total_overdue': sum(inv.amount_residual for inv in invoices if inv.invoice_date_due and inv.invoice_date_due < request.env.cr.now().date()),
            'page_name': 'dues',
        })
        return request.render('portal_customer_due.portal_my_dues', values)
