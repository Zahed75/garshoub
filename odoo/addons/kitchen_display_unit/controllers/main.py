from odoo import http
from odoo.http import request


class KitchenDisplayController(http.Controller):

    @http.route('/kitchen/display', type='http', auth='public', website=False)
    def kitchen_display(self, **kw):
        return request.render('kitchen_display_unit.kitchen_display_page')

    @http.route('/kitchen/orders', type='jsonrpc', auth='public', methods=['POST'])
    def get_orders(self, **kw):
        orders = request.env['kitchen.order'].sudo().search([
            ('status', 'in', ['new', 'in_progress', 'ready']),
        ], order='create_date desc')
        return {
            'orders': [{
                'id': o.id,
                'name': o.name,
                'partner_name': o.partner_name,
                'partner_phone': o.partner_phone,
                'delivery_address': o.delivery_address,
                'order_date': o.order_date.strftime('%Y-%m-%d %H:%M') if o.order_date else '',
                'total_amount': o.total_amount,
                'status': o.status,
                'notes': o.notes,
                'lines': [{
                    'product_name': l.product_name,
                    'quantity': l.quantity,
                    'subtotal': l.subtotal,
                } for l in o.order_lines],
            } for o in orders]
        }

    @http.route('/kitchen/order/update', type='jsonrpc', auth='public', methods=['POST'])
    def update_order_status(self, order_id, status, **kw):
        order = request.env['kitchen.order'].sudo().browse(int(order_id))
        if order.exists():
            order.write({'status': status})
            return {'success': True}
        return {'success': False, 'error': 'Order not found'}
