from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    group_pos_credit_sale_id = fields.Many2one(
        'res.groups',
        string='Credit Sale Group',
        default=lambda self: self.env.ref('pos_credit_customer.group_pos_credit_sale', raise_if_not_found=False),
        help="Users in this group can perform credit sales in POS.",
    )
