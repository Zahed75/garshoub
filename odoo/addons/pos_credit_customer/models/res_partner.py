from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Float(string='Credit Limit', default=0.0)
    current_balance = fields.Float(
        string='Current Balance',
        compute='_compute_current_balance',
        store=False,
    )
    available_credit = fields.Float(
        string='Available Credit',
        compute='_compute_current_balance',
        store=False,
    )

    @api.depends('credit_limit', 'total_due')
    def _compute_current_balance(self):
        for partner in self:
            partner.current_balance = partner.total_due
            partner.available_credit = partner.credit_limit - partner.total_due

    def get_pos_customer_info(self):
        """API called from POS to get customer history and balance."""
        self.ensure_one()
        orders = self.env['pos.order'].search([
            ('partner_id', '=', self.id),
        ], order='date_order desc', limit=10)
        return {
            'credit_limit': self.credit_limit,
            'current_balance': self.current_balance,
            'available_credit': self.available_credit,
            'payment_terms': self.property_payment_term_id.name if self.property_payment_term_id else '',
            'orders': [{
                'id': o.id,
                'name': o.pos_reference or o.name,
                'date_order': o.date_order.strftime('%Y-%m-%d %H:%M') if o.date_order else '',
                'amount_total': o.amount_total,
                'payment_mode': o.payment_mode,
            } for o in orders],
        }
