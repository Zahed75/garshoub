from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    source_from = fields.Selection([
        ('purchase', 'Purchase'),
        ('transfer', 'Internal Transfer'),
        ('return', 'Return'),
        ('other', 'Other'),
    ], string='Source from Others', default='other', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            picking_type_id = vals.get('picking_type_id')
            if picking_type_id and not vals.get('source_from'):
                picking_type = self.env['stock.picking.type'].browse(picking_type_id)
                if picking_type.code == 'incoming':
                    vals['source_from'] = 'purchase'
                else:
                    vals['source_from'] = 'other'
        return super().create(vals_list)
