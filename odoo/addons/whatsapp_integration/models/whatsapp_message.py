from odoo import models, fields, api


class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message Log'
    _order = 'create_date desc'

    name = fields.Char(string='Message ID', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    message_type = fields.Selection([
        ('invoice_notification', 'Invoice Notification'),
        ('payment_reminder', 'Payment Reminder'),
    ], string='Message Type', required=True)
    phone = fields.Char(string='Phone Number')
    body = fields.Text(string='Message Body')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ], string='Status', default='draft')
    error_message = fields.Text(string='Error')
    reminder_level = fields.Integer(string='Reminder Level', default=0)
