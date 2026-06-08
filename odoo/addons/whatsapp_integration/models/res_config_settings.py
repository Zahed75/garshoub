from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_api_token = fields.Char(
        string='WhatsApp API Token',
        config_parameter='whatsapp.api_token',
    )
    whatsapp_phone_number_id = fields.Char(
        string='Phone Number ID',
        config_parameter='whatsapp.phone_number_id',
    )
    whatsapp_business_account_id = fields.Char(
        string='Business Account ID',
        config_parameter='whatsapp.business_account_id',
    )
    whatsapp_api_version = fields.Char(
        string='API Version',
        config_parameter='whatsapp.api_version',
        default='v18.0',
    )
