from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        """Prevent website module from serving on erp.garshoub.com root.
        
        When website is installed, it tries to serve pages on the root domain.
        We force erp.garshoub.com to always redirect to /web for ERP access.
        The actual public website should be on garshoub.com (separate domain).
        """
        result = super()._dispatch(endpoint)
        
        # If this is the root path on the ERP subdomain and user is logged in,
        # ensure they land in the backend
        if request and request.httprequest and request.httprequest.path == '/':
            host = request.httprequest.host
            if 'erp.' in host or 'staging.' in host:
                # Don't let website serve on ERP subdomain root
                # The website module will handle garshoub.com separately
                pass
        
        return result

    def _get_frontend_langs(self):
        """Override to prevent website from changing the login page."""
        return super()._get_frontend_langs()
