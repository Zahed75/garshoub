from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _pre_dispatch(cls, rule, args):
        """Redirect erp.garshoub.com root to /web before website module serves it.
        
        The website module serves its home page on the root '/' path.
        We intercept requests to erp.garshoub.com and redirect to /web
        so the ERP backend is always accessible on the ERP subdomain.
        """
        if request and request.httprequest:
            path = request.httprequest.path
            host = request.httprequest.host.lower()
            
            # If accessing erp.garshoub.com or staging.garshoub.com root
            if path == '/' and ('erp.' in host or 'staging.' in host):
                from werkzeug.utils import redirect
                return redirect('/web', code=302)
        
        return super()._pre_dispatch(rule, args)
