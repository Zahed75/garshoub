from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit'),
    ], string='Payment Mode', default='cash', required=True)

    @api.model
    def _order_fields(self, ui_order):
        fields = super()._order_fields(ui_order)
        fields['payment_mode'] = ui_order.get('payment_mode', 'cash')
        return fields

    def action_pos_order_invoice(self):
        """Override to handle credit sales: create invoice without payment."""
        res = super().action_pos_order_invoice()
        for order in self:
            if order.payment_mode == 'credit' and order.account_move:
                # For credit sales, invoice is created but no payment is registered
                # The invoice remains open in AR with customer's payment term
                pass
        return res
