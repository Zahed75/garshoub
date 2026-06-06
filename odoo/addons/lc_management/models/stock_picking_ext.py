from odoo import models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """
    Override stock.picking to enforce the EXP Form Gate on Export LCs.
    CRITICAL PRD REQUIREMENT: Outbound delivery MUST be blocked if no
    EXP form number is recorded on the linked Letter of Credit.
    """
    _inherit = 'stock.picking'

    letter_of_credit_id = fields.Many2one(
        'letter.of.credit',
        string='Letter of Credit',
        help='Link this delivery/receipt to an LC for compliance tracking.',
    )

    def button_validate(self):
        """
        Override: Block validation of outbound (export) deliveries
        unless EXP form is recorded on the linked LC.
        """
        for picking in self:
            if (
                picking.letter_of_credit_id
                and picking.letter_of_credit_id.lc_type == 'export'
                and picking.picking_type_code == 'outgoing'
            ):
                lc = picking.letter_of_credit_id
                if not lc.exp_form_number:
                    raise UserError(_(
                        '🚫 EXPORT LC COMPLIANCE GATE\n\n'
                        'Delivery "%s" is linked to Export LC "%s".\n'
                        'You CANNOT validate this delivery until an EXP Form Number '
                        'is recorded on the LC.\n\n'
                        'This is mandatory per Bangladesh Bank foreign exchange regulations.'
                    ) % (picking.name, lc.name))
                if lc.state not in ('opened', 'docs_received'):
                    raise UserError(_(
                        '🚫 LC must be in "Opened" or "Documents Received" state '
                        'before validating export delivery.\n'
                        'Current LC state: %s'
                    ) % dict(lc._fields['state'].selection).get(lc.state))
        return super().button_validate()
