from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        """Redirect erp.garshoub.com and staging.garshoub.com root to /web.

        Only redirects TOP-LEVEL browser navigations (Sec-Fetch-Dest: document).
        Skips iframe loads, AJAX calls, and internal Odoo redirects so the
        Website Builder and other iframe-based features keep working.
        """
        if request and request.httprequest:
            path = request.httprequest.path
            host = request.httprequest.host.lower()

            if path == '/' and ('erp.' in host or 'staging.' in host):
                # Sec-Fetch-Dest header tells us the destination:
                #   document  = top-level browser navigation → redirect
                #   iframe    = iframe load → DO NOT redirect (Website Builder)
                #   empty     = AJAX/fetch/XHR → DO NOT redirect
                #   image/script/style/etc → DO NOT redirect
                dest = request.httprequest.headers.get('Sec-Fetch-Dest')
                if dest == 'document':
                    from werkzeug.utils import redirect
                    return redirect('/web', code=302)

                # Fallback for browsers without Sec-Fetch-Dest (older browsers):
                # Only redirect if there's no Referer from our own backend
                # (which would indicate an internal Odoo request like iframe load)
                if dest is None:
                    referer = request.httprequest.headers.get('Referer', '')
                    # If referer contains /web or /odoo, it's an internal request
                    if '/web' in referer or '/odoo' in referer:
                        pass  # Don't redirect
                    else:
                        from werkzeug.utils import redirect
                        return redirect('/web', code=302)

        return super()._dispatch(endpoint)
