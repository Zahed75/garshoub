from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _pre_dispatch(cls, rule, args):
        """Redirect erp.garshoub.com root to /web before website module serves it."""
        result = super()._pre_dispatch(rule, args)
        
        if request and request.httprequest:
            path = request.httprequest.path
            host = request.httprequest.host.lower()
            
            # If accessing erp.garshoub.com or staging.garshoub.com root
            if path == '/' and ('erp.' in host or 'staging.' in host):
                # Redirect to /web so website doesn't serve here
                from werkzeug.utils import redirect
                return redirect('/web', code=302)
        
        return result
