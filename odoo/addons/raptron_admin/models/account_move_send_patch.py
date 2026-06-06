from odoo import models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    def _generate_and_send_invoices(self, moves, from_cron=False, allow_raising=True, allow_fallback_pdf=False, **custom_settings):
        """Override to fix KeyError: 'proforma_pdf_attachment' when PDF generation fails."""
        self._check_sending_data(moves, **custom_settings)
        moves_data = {
            move.sudo(): {
                **self._get_default_sending_settings(move, from_cron=from_cron, **custom_settings),
            }
            for move in moves
        }

        # Generate all invoice documents (PDF and electronic documents if relevant).
        self._generate_invoice_documents(moves_data, allow_fallback_pdf=allow_fallback_pdf)

        # Manage errors.
        errors = {move: move_data for move, move_data in moves_data.items() if move_data.get('error')}
        if errors:
            self._generate_invoice_fallback_documents(errors)

        # Successfully generated a PDF - Process sending.
        success = {move: move_data for move, move_data in moves_data.items() if not move_data.get('error')}
        if success:
            self._hook_if_success(success, from_cron=from_cron)

        # Update sending data of moves
        for move, move_data in moves_data.items():
            if from_cron and move_data.get('error', {}).get('retry'):
                continue
            move.sending_data = False

        # Return generated attachments.
        # FIX: Use .get() to avoid KeyError when proforma_pdf_attachment is missing
        attachments = self.env['ir.attachment']
        for move, move_data in success.items():
            attachments += self._get_invoice_extra_attachments(move) or move_data.get('proforma_pdf_attachment', self.env['ir.attachment'])

        return attachments
