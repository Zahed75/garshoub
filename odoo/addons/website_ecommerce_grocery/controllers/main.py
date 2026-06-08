from odoo import http
from odoo.http import request


class GroceryEcommerceController(http.Controller):

    @http.route('/shop/grocery', type='http', auth='public', website=True)
    def grocery_home(self, **kw):
        categories = request.env['product.public.category'].search([
            ('website_published', '=', True),
        ], order='sequence, name')

        featured = request.env['product.template'].search([
            ('website_published', '=', True),
            ('is_published', '=', True),
        ], limit=12, order='website_sequence')

        values = {
            'categories': categories,
            'featured_products': featured,
        }
        return request.render('website_ecommerce_grocery.grocery_homepage', values)
