from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_status = fields.Char(
        string='Paid Status',
        compute='_compute_payment_status',
        store=False,
    )

    @api.depends('payment_state')
    def _compute_payment_status(self):
        for move in self:
            if move.payment_state == 'paid':
                move.payment_status = 'Paid'
            elif move.payment_state == 'partial':
                move.payment_status = 'Partial'
            elif move.payment_state == 'not_paid':
                move.payment_status = 'Unpaid'
            else:
                move.payment_status = move.payment_state or 'Unpaid'
