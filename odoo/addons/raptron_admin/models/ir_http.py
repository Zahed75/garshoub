from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _match(cls, endpoint):
        """Intercept root requests on erp.garshoub.com and redirect to /web.
        
        When website module is installed, it takes over the root '/' route.
        We need to force erp.garshoub.com to always serve the ERP backend,
        while garshoub.com serves the public website.
        """
        result = super()._match(endpoint)
        
        # Check if this is the root path on ERP subdomain
        if request and request.httprequest:
            path = request.httprequest.path
            host = request.httprequest.host.lower()
            
            # If accessing erp.garshoub.com or staging.garshoub.com root
            if path == '/' and ('erp.' in host or 'staging.' in host):
                # Redirect to /web so website doesn't serve here
                from werkzeug.utils import redirect
                return redirect('/web', code=302)
        
        return result
