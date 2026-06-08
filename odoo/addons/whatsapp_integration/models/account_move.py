from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    whatsapp_message_ids = fields.One2many(
        'garshoub.whatsapp.log', 'invoice_id',
        string='WhatsApp Messages',
    )
    whatsapp_sent = fields.Boolean(string='WhatsApp Sent', default=False)

    def action_send_whatsapp(self):
        """Send invoice via WhatsApp."""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return

        partner = self.partner_id
        if not partner.mobile and not partner.phone:
            self.env['garshoub.whatsapp.log'].create({
                'partner_id': partner.id,
                'invoice_id': self.id,
                'message_type': 'invoice_notification',
                'status': 'failed',
                'error_message': 'Customer has no phone number.',
            })
            return

        phone = partner.mobile or partner.phone
        # Clean phone number
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if not phone.startswith('971') and not phone.startswith('0'):
            phone = '971' + phone.lstrip('0')
        elif phone.startswith('0'):
            phone = '971' + phone[1:]

        message_body = self._prepare_whatsapp_invoice_message()
        result = self._send_whatsapp_message(phone, message_body)

        self.env['garshoub.whatsapp.log'].create({
            'name': result.get('message_id', ''),
            'partner_id': partner.id,
            'invoice_id': self.id,
            'message_type': 'invoice_notification',
            'phone': phone,
            'body': message_body,
            'status': 'sent' if result.get('success') else 'failed',
            'error_message': result.get('error', ''),
        })

        if result.get('success'):
            self.whatsapp_sent = True

        return result

    def _prepare_whatsapp_invoice_message(self):
        self.ensure_one()
        return (
            f"Dear {self.partner_id.name},\n\n"
            f"Your invoice {self.name} for AED {self.amount_total:.2f} is ready.\n"
            f"Due date: {self.invoice_date_due or 'N/A'}.\n\n"
            f"Thank you,\nAl Garshoub Foodstuff TRD"
        )

    def _send_whatsapp_message(self, phone, body):
        """Send message via WhatsApp Cloud API."""
        params = self.env['ir.config_parameter'].sudo()
        token = params.get_param('whatsapp.api_token')
        phone_id = params.get_param('whatsapp.phone_number_id')
        api_version = params.get_param('whatsapp.api_version', 'v18.0')

        if not token or not phone_id:
            return {'success': False, 'error': 'WhatsApp API not configured. Go to Settings > WhatsApp Integration.'}

        url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': phone,
            'type': 'text',
            'text': {'body': body},
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if response.status_code == 200 and 'messages' in data:
                return {'success': True, 'message_id': data['messages'][0]['id']}
            else:
                error = data.get('error', {}).get('message', 'Unknown error')
                _logger.error('WhatsApp API error: %s', error)
                return {'success': False, 'error': error}
        except Exception as e:
            _logger.error('WhatsApp send failed: %s', str(e))
            return {'success': False, 'error': str(e)}

    @api.model
    def _cron_whatsapp_payment_reminders(self):
        """Send automated payment reminders for overdue invoices."""
        today = fields.Date.context_today(self)

        # Reminder levels:
        # Level 1: 3 days after due date
        # Level 2: 7 days after due date
        # Level 3: 15 days after due date
        levels = [
            {'days': 3, 'level': 1},
            {'days': 7, 'level': 2},
            {'days': 15, 'level': 3},
        ]

        for level_info in levels:
            days = level_info['days']
            level = level_info['level']

            invoices = self.search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '!=', False),
            ])

            for invoice in invoices:
                overdue_days = (today - invoice.invoice_date_due).days
                if overdue_days < days:
                    continue

                # Check if this reminder level was already sent
                existing = self.env['garshoub.whatsapp.log'].search([
                    ('invoice_id', '=', invoice.id),
                    ('message_type', '=', 'payment_reminder'),
                    ('reminder_level', '=', level),
                ], limit=1)
                if existing:
                    continue

                partner = invoice.partner_id
                phone = partner.mobile or partner.phone
                if not phone:
                    continue

                # Clean phone
                phone = phone.replace(' ', '').replace('-', '').replace('+', '')
                if not phone.startswith('971') and not phone.startswith('0'):
                    phone = '971' + phone.lstrip('0')
                elif phone.startswith('0'):
                    phone = '971' + phone[1:]

                body = (
                    f"Dear {partner.name},\n\n"
                    f"This is a friendly reminder that invoice {invoice.name} "
                    f"for AED {invoice.amount_residual:.2f} is overdue by {overdue_days} days.\n\n"
                    f"Please arrange payment at your earliest convenience.\n\n"
                    f"Thank you,\nAl Garshoub Foodstuff TRD"
                )

                result = invoice._send_whatsapp_message(phone, body)
                self.env['garshoub.whatsapp.log'].create({
                    'name': result.get('message_id', ''),
                    'partner_id': partner.id,
                    'invoice_id': invoice.id,
                    'message_type': 'payment_reminder',
                    'phone': phone,
                    'body': body,
                    'status': 'sent' if result.get('success') else 'failed',
                    'error_message': result.get('error', ''),
                    'reminder_level': level,
                })
