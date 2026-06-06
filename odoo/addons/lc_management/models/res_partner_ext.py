from odoo import models, fields


class ResPartner(models.Model):
    """
    Extend res.partner with Bangladesh trade finance flags.
    Allows tagging partners as AD Banks or NBR (National Board of Revenue).
    CRITICAL: Customs duty bills must be routed to NBR partner, NOT the foreign vendor.
    """
    _inherit = 'res.partner'

    is_ad_bank = fields.Boolean(
        string='Authorized Dealer (AD) Bank',
        default=False,
        help='Tag this partner as an Authorized Dealer bank for LC management.',
    )
    is_nbr = fields.Boolean(
        string='NBR / Customs Authority',
        default=False,
        help='Tag this partner as NBR (National Board of Revenue). '
             'All customs duty vendor bills MUST use this partner as payee.',
    )
    bd_bank_branch = fields.Char(string='Bank Branch / SWIFT Code')
