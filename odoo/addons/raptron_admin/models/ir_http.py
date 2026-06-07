from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        """Redirect erp.garshoub.com and staging.garshoub.com root to /web.

        This runs AFTER routing and auth but BEFORE the controller endpoint
        is called. Returning a Response here short-circuits dispatch.
        """
        if request and request.httprequest:
            path = request.httprequest.path
            host = request.httprequest.host.lower()
            # Redirect root '/' on erp/staging subdomains to backend
            if path == '/' and ('erp.' in host or 'staging.' in host):
                from werkzeug.utils import redirect
                return redirect('/web', code=302)
        return super()._dispatch(endpoint)
