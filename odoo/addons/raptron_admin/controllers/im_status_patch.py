import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.mail.controllers.im_status import ImStatusController

_logger = logging.getLogger(__name__)


class ImStatusControllerPatch(ImStatusController):
    """Patch to fix online status when websocket presence is delayed or broken."""

    @http.route("/mail/set_manual_im_status", methods=["POST"], type="jsonrpc", auth="user")
    def set_manual_im_status(self, status):
        if status not in ["online", "away", "busy", "offline"]:
            raise ValueError(_("Unexpected IM status %(status)s", status=status))
        user = request.env.user

        # Store "online" as a real manual status so _compute_im_status respects it
        # even when websocket presence tracking reports offline.
        user.manual_im_status = status

        # Compute the im_status using our patched logic
        user._compute_im_status()

        user._bus_send(
            "bus.bus/im_status_updated",
            {
                "debounce": False,
                "im_status": user.im_status,
                "partner_id": user.partner_id.id,
            },
            subchannel="presence",
        )
