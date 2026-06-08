/** @odoo-module **/

import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list_screen";
import { patch } from "@web/core/utils/patch";

patch(PartnerListScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async getCustomerHistory(partnerId) {
        const result = await this.orm.call(
            'res.partner',
            'get_pos_customer_info',
            [partnerId],
            {}
        );
        return result;
    },
});
