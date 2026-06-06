from odoo import models, fields

class SaasClient(models.Model):
    _name = 'saas.client'
    _description = 'SaaS Client Database Mapping'

    name = fields.Char(string='Client Name', required=True)
    database_name = fields.Char(string='Database Name', required=True, index=True)
    admin_email = fields.Char(string='Admin Email', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', default='draft')

    def create_database(self):
        # Placeholder for database creation logic
        self.state = 'done'
