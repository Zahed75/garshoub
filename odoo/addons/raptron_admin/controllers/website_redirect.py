from odoo import http
from odoo.http import request


class WebsiteRedirectController(http.Controller):
    """Force erp.garshoub.com to always redirect to /web backend.
    
    When the website module is installed, it serves pages on the root domain.
    We need to intercept requests to erp.garshoub.com and redirect to /web
    so the ERP backend is always accessible on the ERP subdomain.
    """

    @http.route('/', type='http', auth='public', website=True)
    def index_redirect(self, **kw):
        host = request.httprequest.host.lower()
        
        # If this is the ERP subdomain, redirect to /web
        if 'erp.' in host or 'staging.' in host:
            return request.redirect('/web', code=302)
        
        # Otherwise (garshoub.com), let the website module handle it
        return request.redirect('/web', code=302)
