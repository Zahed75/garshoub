/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.paymentMode = this.currentOrder.payment_mode || 'cash';
    },

    get paymentMode() {
        return this.state.paymentMode || 'cash';
    },

    togglePaymentMode() {
        const newMode = this.paymentMode === 'cash' ? 'credit' : 'cash';
        this.state.paymentMode = newMode;
        this.currentOrder.payment_mode = newMode;

        if (newMode === 'credit') {
            // Check if user has credit sale permission
            if (!this.pos.user.groups_id.includes(this.pos.config.group_pos_credit_sale_id?.[0])) {
                this.notification.add(_t("You don't have permission for credit sales."), { type: 'danger' });
                this.state.paymentMode = 'cash';
                this.currentOrder.payment_mode = 'cash';
                return;
            }

            // Check customer credit limit
            const partner = this.currentOrder.get_partner();
            if (partner) {
                const total = this.currentOrder.get_total_with_tax();
                if (partner.credit_limit > 0 && partner.available_credit < total) {
                    this.notification.add(
                        _t("Customer credit limit exceeded. Available: %s", this.env.utils.formatCurrency(partner.available_credit)),
                        { type: 'warning' }
                    );
                }
            }

            // Remove all paymentlines for credit sale
            const paymentlines = this.currentOrder.paymentlines;
            while (paymentlines.length > 0) {
                this.currentOrder.remove_paymentline(paymentlines[0]);
            }
            this.notification.add(_t("Credit Sale mode activated. Invoice will be created without payment."), { type: 'info' });
        } else {
            this.notification.add(_t("Cash Sale mode activated."), { type: 'success' });
        }
    },

    async validateOrder(isForceValidate) {
        if (this.paymentMode === 'credit') {
            const partner = this.currentOrder.get_partner();
            if (!partner) {
                this.notification.add(_t("Please select a customer for credit sale."), { type: 'danger' });
                return;
            }
            // For credit sale, we don't need payment lines
            // The invoice will be created and left open
            await this.currentOrder.set_to_invoice(true);
        }
        return super.validateOrder(...arguments);
    },
});
