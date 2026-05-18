/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class PharmacyOrders extends Component {
    static template = "pharmacy_management_system.PharmacyOrders";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.state = useState({
            medicines: [],
            categories: [],
            cart: [],
            search: "",
            categoryId: false,
            customerName: "",
            loading: true,
            fdiscount: "",
            pdiscount: "",
            discount: 0,
            showDiscountModal: false,
            discountMode: false,
            showCancelConfirm: false,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const data = await this.orm.call(
            "pharmacy.sale",
            "get_order_screen_data",
            [],
        );
        this.state.categories = data.categories;
        this.state.medicines = data.medicines;
        this.state.loading = false;
    }

    get filteredMedicines() {
        const search = this.state.search.trim().toLowerCase();
        return this.state.medicines.filter((medicine) => {
            const matchesSearch =
                !search || medicine.name.toLowerCase().includes(search);
            const matchesCategory =
                !this.state.categoryId ||
                medicine.category_id[0] === this.state.categoryId;
            return matchesSearch && matchesCategory;
        });
    }

    get subTotal() {
        return this.state.cart.reduce(
            (total, line) => total + line.quantity * line.price,
            0,
        );
    }

    get lineDiscountTotal() {
        return this.state.cart.reduce(
            (total, line) => total + this.getLineDiscount(line),
            0,
        );
    }

    get grossAfterLineDiscount() {
        return Math.max(this.subTotal - this.lineDiscountTotal, 0);
    }

    get getDiscount() {
        const { fdiscount, pdiscount } = this.state;

        const fixedDiscount = Number(fdiscount) || 0;
        const percentDiscount = Number(pdiscount) || 0;
        const orderDiscount =
            fixedDiscount > 0
                ? fixedDiscount
                : percentDiscount > 0
                    ? (this.grossAfterLineDiscount * percentDiscount) / 100
                    : 0;

        this.state.discount = Math.min(Math.max(orderDiscount, 0), this.grossAfterLineDiscount);

        return this.state.discount;
    }

    get totalDiscount() {
        return this.lineDiscountTotal + this.getDiscount;
    }

    get getTotal() {
        return Math.max(this.grossAfterLineDiscount - this.getDiscount, 0);
    }

    onSearch(ev) {
        this.state.search = ev.target.value;
    }

    setCategory(categoryId) {
        this.state.categoryId = categoryId;
    }

    addToCart(medicine) {
        if (medicine.stock <= 0) {
            this.notification.add(`${medicine.name} is out of stock.`, {
                type: "warning",
            });
            return;
        }
        const line = this.state.cart.find(
            (item) => item.medicine_id === medicine.id,
        );
        if (line) {
            this.increaseQty(line);
            return;
        }
        this.state.cart.push({
            medicine_id: medicine.id,
            name: medicine.name,
            price: medicine.sale_price,
            quantity: 1,
            stock: medicine.stock,
            discount_amount: 0,
        });
    }

    increaseQty(line) {
        if (line.quantity >= line.stock) {
            this.notification.add(
                `Only ${line.stock} units available for ${line.name}.`,
                { type: "warning" },
            );
            return;
        }
        line.quantity += 1;
    }

    decreaseQty(line) {
        if (line.quantity <= 1) {
            this.removeLine(line);
            return;
        }
        line.quantity -= 1;
    }

    removeLine(line) {
        const index = this.state.cart.indexOf(line);
        if (index >= 0) {
            this.state.cart.splice(index, 1);
        }
    }

    cancelOrder() {
        this.state.showCancelConfirm = true;
    }

    clearOrder() {
        this.state.cart.splice(0, this.state.cart.length);
        this.state.customerName = "";
        this.state.fdiscount = "";
        this.state.pdiscount = "";
        this.state.discount = 0;
        this.state.discountMode = false;
        this.state.showCancelConfirm = false;
    }

    closeCancelConfirm() {
        this.state.showCancelConfirm = false;
    }

    openDiscountModal() {
        this.state.showDiscountModal = true;
        this.state.discountMode = false;
    }

    closeDiscountModal() {
        this.state.showDiscountModal = false;
        this.state.discountMode = false;
    }

    selectFixedDiscount() {
        this.state.discountMode = "fixed";
        this.state.pdiscount = "";
    }

    selectPercentDiscount() {
        this.state.discountMode = "percent";
        this.state.fdiscount = "";
    }

    applyDiscount() {
        this.closeDiscountModal();
    }

    updateLineDiscount(line, ev) {
        const value = Math.max(Number(ev.target.value) || 0, 0);
        line.discount_amount = Math.min(value, line.quantity * line.price);
    }

    getLineDiscount(line) {
        return Math.min(Math.max(Number(line.discount_amount) || 0, 0), line.quantity * line.price);
    }

    getLineTotal(line) {
        return Math.max((line.quantity * line.price) - this.getLineDiscount(line), 0);
    }

    async confirmOrder() {
        if (!this.state.cart.length) {
            this.notification.add("Add medicines to the cart first.", {
                type: "warning",
            });
            return;
        }
        const result = await this.orm.call("pharmacy.sale", "confirm_order", [
            this.state.cart.map((line) => ({
                medicine_id: line.medicine_id,
                quantity: line.quantity,
                discount_amount: this.getLineDiscount(line),
            })),
            this.state.customerName,
            this.state.discount,
        ]);
        this.notification.add(
            `Order ${result.name} confirmed. Total: ${result.total_amount}`,
            {
                type: "success",
            },
        );
        this.clearOrder();
        await this.loadData();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pharmacy.sale",
            res_id: result.sale_id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("pharmacy_orders", PharmacyOrders);
