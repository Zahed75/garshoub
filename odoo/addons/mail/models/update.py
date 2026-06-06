# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import logging
from ast import literal_eval

import requests

from odoo import api, fields, release, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.models import AbstractModel
from odoo.tools.translate import _
from odoo.tools import config

_logger = logging.getLogger(__name__)


class Publisher_WarrantyContract(AbstractModel):
    _name = 'publisher_warranty.contract'
    _description = 'Publisher Warranty Contract'

    @api.model
    def _get_message(self):
        Users = self.env['res.users']
        IrParamSudo = self.env['ir.config_parameter'].sudo()

        dbuuid = IrParamSudo.get_param('database.uuid')
        db_create_date = IrParamSudo.get_param('database.create_date')
        limit_date = fields.Datetime.now() - datetime.timedelta(15)
        nbr_users = Users.search_count([('active', '=', True)])
        nbr_active_users = Users.search_count([("login_date", ">=", limit_date), ('active', '=', True)])
        nbr_share_users = 0
        nbr_active_share_users = 0
        if "share" in Users._fields:
            nbr_share_users = Users.search_count([("share", "=", True), ('active', '=', True)])
            nbr_active_share_users = Users.search_count([("share", "=", True), ("login_date", ">=", limit_date), ('active', '=', True)])
        user = self.env.user
        domain = [('application', '=', True), ('state', 'in', ['installed', 'to upgrade', 'to remove'])]
        apps = self.env['ir.module.module'].sudo().search_read(domain, ['name'])

        enterprise_code = IrParamSudo.get_param('database.enterprise_code')

        web_base_url = IrParamSudo.get_param('web.base.url')
        msg = {
            "dbuuid": dbuuid,
            "nbr_users": nbr_users,
            "nbr_active_users": nbr_active_users,
            "nbr_share_users": nbr_share_users,
            "nbr_active_share_users": nbr_active_share_users,
            "dbname": self.env.cr.dbname,
            "db_create_date": db_create_date,
            "version": release.version,
            "language": user.lang,
            "web_base_url": web_base_url,
            "apps": [app['name'] for app in apps],
            "enterprise_code": enterprise_code,
        }
        if user.partner_id.company_id:
            company_id = user.partner_id.company_id
            msg.update(company_id.read(["name", "email", "phone"])[0])
        return msg

    @api.model
    def _get_sys_logs(self):
        """
        [DEV MODE] Publisher warranty ping to odoo.com is DISABLED for local development.
        Original code would POST to publisher_warranty_url — suppressed permanently.
        """
        # DISABLED: no outbound ping to odoo.com
        return {"messages": [], "enterprise_info": {}}

    def update_notification(self, cron_mode=True):
        """
        [DEV MODE] Subscription notification to odoo.com is DISABLED permanently.
        This method previously sent system info to Odoo's publisher warranty server.
        Suppressed for local development — no data is sent to odoo.com.
        """
        # DISABLED: no outbound notification to odoo.com
        _logger.info("[DEV] update_notification suppressed — no ping to odoo.com")
        return True
