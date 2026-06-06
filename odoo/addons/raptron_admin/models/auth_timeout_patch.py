from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_lock_timeout_inactivity(self):
        """Disable inactivity timeout to prevent CSRF/session errors during work.

        The auth_timeout module's inactivity tracking causes users to be kicked out
        with 'invalid CSRF token' errors. Disabling inactivity timeout keeps users
        logged in while they work, only logging them out after actual session expiry.
        """
        return None
