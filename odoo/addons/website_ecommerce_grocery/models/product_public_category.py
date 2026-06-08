from odoo import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    category_image = fields.Image(string='Category Image', max_width=512, max_height=512)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    is_featured = fields.Boolean(string='Featured on Homepage', default=False)
