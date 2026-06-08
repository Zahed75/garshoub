from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_kitchen_display = fields.Boolean(
        string='Enable Kitchen Display',
        default=True,
        help="When enabled, POS orders will automatically create kitchen orders.",
    )
