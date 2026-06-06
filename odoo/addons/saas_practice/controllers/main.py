import odoo
from odoo import http, tools
from odoo.http import request
from odoo.addons.web.controllers.home import Home
import logging

_logger = logging.getLogger(__name__)

MASTER_DB = 'odooZayanori'
ADMIN_EMAIL = 'zayanori.business@gmail.com'

class SaaSAdminController(Home):

    def _check_admin_access(self):
        # Only allow the specified admin email
        if request.env.user.login != ADMIN_EMAIL:
            return False
        return True

    @http.route('/saas_practice/logo/<string:filename>', type='http', auth='public')
    def serve_logo(self, filename, **kwargs):
        import os
        from odoo.modules import get_module_path
        
        module_path = get_module_path('saas_practice')
        if module_path:
            file_path = os.path.join(module_path, 'logo', filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                return request.make_response(content, [('Content-Type', 'image/png')])
        return request.not_found()

    @http.route('/admin_practice', type='http', auth='user', website=True, sitemap=False)
    def render_admin_portal(self, **kw):
        # Force master database context
        if request.session.db != MASTER_DB:
            request.session.db = MASTER_DB
            return request.redirect('/admin')

        if not self._check_admin_access():
            return request.render('http_routing.403')
            
        return request.render('saas_practice.admin_portal_template', {})

    @http.route('/admin/create_db', type='http', auth='user', methods=['POST'], csrf=False)
    def create_database(self, **post):
        if not self._check_admin_access():
            return request.render('http_routing.403')

        db_name = post.get('company_name')
        admin_email = post.get('email')
        admin_password = post.get('password')
        
        # Automatically fetch the master password from Odoo config
        master_password = tools.config.get('admin_passwd', 'admin')

        if not all([db_name, admin_email, admin_password]):
            return "Missing required fields."

        try:
            _logger.info(f"Attempting to create database {db_name}...")
            odoo.service.db.exp_create_database(
                db_name, False, 'en_US', admin_password, master_password
            )
            
            # Save mapping in the master database
            from odoo.orm.registry import Registry
            registry = Registry(MASTER_DB)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                env['saas.client'].create({
                    'name': db_name,
                    'db_name': db_name,
                    'admin_email': admin_email,
                })
                cr.commit()
            
            # Update the admin user login in the newly created database
            new_db_registry = Registry(db_name)
            with new_db_registry.cursor() as new_cr:
                new_env = odoo.api.Environment(new_cr, odoo.SUPERUSER_ID, {})
                admin_user = new_env.ref('base.user_admin', raise_if_not_found=False)
                if admin_user:
                    admin_user.write({
                        'login': admin_email,
                        'name': db_name + " Admin"
                    })
                    
                    # 1. Set expiration date to 10 years in the future for practice
                    from datetime import datetime, timedelta
                    future_date = (datetime.now() + timedelta(days=3650)).strftime('%Y-%m-%d %H:%M:%S')
                    env = odoo.api.Environment(new_cr, odoo.SUPERUSER_ID, {})
                    env['ir.config_parameter'].sudo().set_param('database.expiration_date', future_date)
                    env['ir.config_parameter'].sudo().set_param('database.expiration_reason', 'none')
                    
                    # 2. Disable publisher warranty (removes "odoo cloud" communication)
                    cron = env.ref('base.ir_cron_publisher_warranty_contract', raise_if_not_found=False)
                    if cron:
                        cron.active = False
                new_cr.commit()
            
            # Send Onboarding Email
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = 'tech.syscomatic@gmail.com'
            msg['To'] = admin_email
            msg['Subject'] = f"Welcome to Syscomatic SaaS - {db_name}"
            
            body = f"""Hello,
            
Your company workspace has been successfully created!

Here are your login credentials:
URL: http://localhost:8069/web/login
Email: {admin_email}
Password: {admin_password}

Best regards,
Syscomatic Team
"""
            msg.attach(MIMEText(body, 'plain'))
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login('tech.syscomatic@gmail.com', 'boqs tsjb jppz gknm')
                server.send_message(msg)
                server.quit()
                _logger.info(f"Onboarding email sent to {admin_email}")
            except Exception as e:
                _logger.error(f"Failed to send email: {e}")
            
            success_msg = f"Database <b>{db_name}</b> successfully created! Onboarding email sent to <b>{admin_email}</b>."
            return request.render('saas_practice.admin_portal_template', {'success_msg': success_msg})
            
        except Exception as e:
            _logger.error("Failed to create database", exc_info=True)
            error_msg = f"Could not create database. Check the server logs. Error: {str(e)}"
            return request.render('saas_practice.admin_portal_template', {'error_msg': error_msg})

    # Override standard login to auto-select DB based on email
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST' and kw.get('login'):
            login_email = kw.get('login')
            password = kw.get('password')
            
            try:
                # Query master DB to find if this email belongs to a specific client DB
                from odoo.orm.registry import Registry
                registry = Registry(MASTER_DB)
                with registry.cursor() as cr:
                    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                    client = env['saas.client'].search([('admin_email', '=', login_email)], limit=1)
                    if client:
                        target_db = client.db_name
                        
                        # If switching from another DB, perform a fresh authentication
                        if request.session.db != target_db:
                            _logger.info(f"Switching session DB to {target_db} for {login_email}")
                            
                            # In Odoo 19, authenticate expects (env, credentials_dict)
                            if password:
                                try:
                                    target_registry = Registry(target_db)
                                    with target_registry.cursor() as target_cr:
                                        target_env = odoo.api.Environment(target_cr, odoo.SUPERUSER_ID, {})
                                        credentials = {
                                            'type': 'password',
                                            'login': login_email,
                                            'password': password
                                        }
                                        auth_info = request.session.authenticate(target_env, credentials)
                                        if auth_info.get('uid'):
                                            return request.redirect(redirect or '/web')
                                except Exception as e:
                                    _logger.error(f"Direct auth failed: {e}")
            except Exception as e:
                _logger.error(f"Error during DB auto-selection: {e}")
                
        return super(SaaSAdminController, self).web_login(redirect=redirect, **kw)
