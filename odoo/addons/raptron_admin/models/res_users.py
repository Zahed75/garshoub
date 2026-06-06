from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # Add 'online' as a valid manual IM status option
    manual_im_status = fields.Selection(
        selection_add=[("online", "Online")],
    )

    @api.depends("manual_im_status", "presence_ids.status")
    def _compute_im_status(self):
        for user in self:
            # If user manually set themselves online, respect that choice
            # even if websocket presence tracking reports offline.
            # This fixes issues with reverse proxies or network delays
            # that prevent proper websocket presence updates.
            if user.manual_im_status == "online":
                user.im_status = "online"
            elif user.presence_ids.status in ["offline", False]:
                user.im_status = "offline"
            else:
                user.im_status = user.manual_im_status or user.presence_ids.status
