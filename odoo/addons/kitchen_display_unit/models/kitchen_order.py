from odoo import models, fields, api


class KitchenOrder(models.Model):
    _name = 'kitchen.order'
    _description = 'Kitchen Display Order'
    _order = 'create_date desc'

    name = fields.Char(string='Order Ref', required=True, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('kitchen.order') or 'New')
    pos_order_id = fields.Many2one('pos.order', string='POS Order', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    partner_name = fields.Char(string='Customer Name')
    partner_phone = fields.Char(string='Phone')
    delivery_address = fields.Text(string='Delivery Address')
    order_date = fields.Datetime(string='Order Date', default=fields.Datetime.now)
    order_lines = fields.One2many('kitchen.order.line', 'kitchen_order_id', string='Order Lines')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
    ], string='Status', default='new', required=True)
    notes = fields.Text(string='Notes')

    @api.depends('order_lines.subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.subtotal for line in order.order_lines)

    def action_in_progress(self):
        self.write({'status': 'in_progress'})

    def action_ready(self):
        self.write({'status': 'ready'})

    def action_delivered(self):
        self.write({'status': 'delivered'})


class KitchenOrderLine(models.Model):
    _name = 'kitchen.order.line'
    _description = 'Kitchen Order Line'

    kitchen_order_id = fields.Many2one('kitchen.order', string='Kitchen Order', required=True, ondelete='cascade')
    product_name = fields.Char(string='Product', required=True)
    quantity = fields.Float(string='Qty', default=1.0)
    subtotal = fields.Float(string='Subtotal')
