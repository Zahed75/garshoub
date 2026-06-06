from odoo import models, fields, api
from datetime import datetime

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def _register_hook(self):
        """Force database expiration to 2099 on every registry load."""
        res = super()._register_hook()
        self.set_param('database.expiration_date', '2099-12-31 23:59:59')
        # Also remove any enterprise registration warning
        self.set_param('database.enterprise_code', 'SURRENDER-TO-SYCO')
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('key') == 'database.expiration_date':
                vals['value'] = '2099-12-31 23:59:59'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('key') == 'database.expiration_date':
            vals['value'] = '2099-12-31 23:59:59'
        return super().write(vals)

class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'

    @api.model
    def _get_message(self):
        """Disable phone-home to Odoo servers for subscription checks."""
        return {}

    @api.model
    def _update_notification(self, cron_mode=True):
        """Silence subscription notifications."""
        return True
