import logging
from odoo import http, _
from odoo.http import request

try:
    from odoo.addons.mail.controllers.im_status import ImStatusController
except ImportError:
    # Fallback for Odoo 19 where the controller may be in a different location
    ImStatusController = http.Controller

_logger = logging.getLogger(__name__)


class ImStatusControllerPatch(ImStatusController):
    """Patch to fix online status when websocket presence is delayed or broken."""

    @http.route("/mail/set_manual_im_status", methods=["POST"], type="json", auth="user")
    def set_manual_im_status(self, status):
        if status not in ["online", "away", "busy", "offline"]:
            raise ValueError(_("Unexpected IM status %(status)s", status=status))
        user = request.env.user

        # Store manual status so _compute_im_status respects it
        user.manual_im_status = status
        user.flush_recordset(["manual_im_status"])
        user.invalidate_recordset(["im_status"])

        # Notify bus (best effort — don't fail if bus is down)
        try:
            user._bus_send(
                "bus.bus/im_status_updated",
                {
                    "debounce": False,
                    "im_status": status,
                    "partner_id": user.partner_id.id,
                },
                subchannel="presence",
            )
        except Exception as e:
            _logger.debug("Bus notification failed for IM status: %s", e)

        return {"im_status": status}
