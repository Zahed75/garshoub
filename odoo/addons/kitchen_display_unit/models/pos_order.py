from odoo import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.config_id.is_kitchen_display:
                order._create_kitchen_order()
        return orders

    def _create_kitchen_order(self):
        self.ensure_one()
        lines = []
        for line in self.lines:
            lines.append((0, 0, {
                'product_name': line.product_id.name,
                'quantity': line.qty,
                'subtotal': line.price_subtotal_incl,
            }))

        partner = self.partner_id
        self.env['kitchen.order'].create({
            'pos_order_id': self.id,
            'partner_name': partner.name if partner else 'Walk-in Customer',
            'partner_phone': partner.phone or partner.mobile or '',
            'delivery_address': partner.contact_address or '',
            'order_lines': lines,
            'notes': self.note or '',
        })
