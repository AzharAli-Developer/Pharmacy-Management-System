/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
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
        this.searchRef = useRef("medicineSearch");
        this.onGlobalKeydown = this.onGlobalKeydown.bind(this);
        this.state = useState({
            medicines: [],
            categories: [],
            recentCustomers: [],
            cart: [],
            search: "",
            categoryId: false,
            customerName: "",
            paymentMethod: "cash",
            amountReceived: "",
            loading: true,
            confirming: false,
            error: "",
            page: 1,
            pageSize: 12,
            fdiscount: "",
            pdiscount: "",
            discount: 0,
            taxRate: 0,
            showDiscountModal: false,
            discountMode: false,
            showCancelConfirm: false,
        });

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            window.addEventListener("keydown", this.onGlobalKeydown);
        });

        onWillUnmount(() => {
            window.removeEventListener("keydown", this.onGlobalKeydown);
        });
    }

    async loadData() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call(
                "pharmacy.sale",
                "get_order_screen_data",
                [],
            );
            this.state.categories = data.categories;
            this.state.medicines = data.medicines;
            this.state.recentCustomers = data.recent_customers || [];
            this.state.taxRate = Number(data.tax_rate || 0);
        } catch (error) {
            this.state.error = "Order screen data could not be loaded.";
            this.notification.add(this.state.error, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    onGlobalKeydown(ev) {
        const tag = (ev.target?.tagName || "").toLowerCase();
        const isTyping = ["input", "textarea", "select"].includes(tag);

        if (ev.key === "/" && !isTyping) {
            ev.preventDefault();
            this.searchRef.el?.focus();
            return;
        }

        if (ev.key === "F8") {
            ev.preventDefault();
            this.confirmOrder();
            return;
        }

        if (ev.key === "Escape") {
            this.closeDiscountModal();
            this.closeCancelConfirm();
        }
    }

    get filteredMedicines() {
        const search = this.state.search.trim().toLowerCase();
        return this.state.medicines.filter((medicine) => {
            const categoryName = medicine.category_id?.[1] || "";
            const searchable = [
                medicine.name,
                medicine.generic_name,
                medicine.manufacturer,
                medicine.medicine_code,
                categoryName,
            ].filter(Boolean).join(" ").toLowerCase();
            const matchesSearch = !search || searchable.includes(search);
            const matchesCategory =
                !this.state.categoryId ||
                medicine.category_id[0] === this.state.categoryId;
            return matchesSearch && matchesCategory;
        }).sort((a, b) => {
            if (a.stock <= 0 && b.stock > 0) {
                return 1;
            }
            if (a.stock > 0 && b.stock <= 0) {
                return -1;
            }
            return a.name.localeCompare(b.name);
        });
    }

    get pagedMedicines() {
        const start = (this.state.page - 1) * this.state.pageSize;
        return this.filteredMedicines.slice(start, start + this.state.pageSize);
    }

    get totalPages() {
        return Math.max(Math.ceil(this.filteredMedicines.length / this.state.pageSize), 1);
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
        const fixedDiscount = Number(this.state.fdiscount) || 0;
        const percentDiscount = Math.min(Number(this.state.pdiscount) || 0, 100);
        const orderDiscount =
            fixedDiscount > 0
                ? fixedDiscount
                : percentDiscount > 0
                    ? (this.grossAfterLineDiscount * percentDiscount) / 100
                    : 0;
        this.state.discount = Math.min(Math.max(orderDiscount, 0), this.grossAfterLineDiscount);
        return this.state.discount;
    }

    get taxAmount() {
        const taxable = Math.max(this.grossAfterLineDiscount - this.getDiscount, 0);
        return (taxable * Math.max(Number(this.state.taxRate) || 0, 0)) / 100;
    }

    get totalDiscount() {
        return this.lineDiscountTotal + this.getDiscount;
    }

    get getTotal() {
        return Math.max(this.grossAfterLineDiscount - this.getDiscount + this.taxAmount, 0);
    }

    get changeAmount() {
        return Math.max((Number(this.state.amountReceived) || 0) - this.getTotal, 0);
    }

    formatMoney(value) {
        return `Rs. ${Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
        })}`;
    }

    onSearch(ev) {
        this.state.search = ev.target.value;
        this.state.page = 1;
    }

    setCategory(categoryId) {
        this.state.categoryId = categoryId;
        this.state.page = 1;
    }

    nextPage() {
        this.state.page = Math.min(this.state.page + 1, this.totalPages);
    }

    previousPage() {
        this.state.page = Math.max(this.state.page - 1, 1);
    }

    selectCustomer(name) {
        this.state.customerName = name;
    }

    stockTone(medicine) {
        if (medicine.stock <= 0) {
            return "danger";
        }
        if (medicine.stock <= (medicine.reorder_level || 10)) {
            return "warning";
        }
        return "ok";
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
            generic_name: medicine.generic_name || "",
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
        if (!this.state.cart.length && !this.state.customerName) {
            return;
        }
        this.state.showCancelConfirm = true;
    }

    clearOrder() {
        this.state.cart.splice(0, this.state.cart.length);
        this.state.customerName = "";
        this.state.paymentMethod = "cash";
        this.state.amountReceived = "";
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
        if (this.state.confirming) {
            return;
        }
        if (!this.state.cart.length) {
            this.notification.add("Add medicines to the cart first.", {
                type: "warning",
            });
            return;
        }
        if (this.state.paymentMethod === "cash" && Number(this.state.amountReceived || 0) < this.getTotal) {
            this.notification.add("Cash received is less than the order total.", {
                type: "warning",
            });
            return;
        }
        this.state.confirming = true;
        try {
            const result = await this.orm.call("pharmacy.sale", "confirm_order", [
                this.state.cart.map((line) => ({
                    medicine_id: line.medicine_id,
                    quantity: line.quantity,
                    discount_amount: this.getLineDiscount(line),
                })),
                this.state.customerName,
                this.state.discount,
                Number(this.state.taxRate || 0),
                this.state.paymentMethod,
                Number(this.state.amountReceived || 0),
            ]);
            this.notification.add(
                `Order ${result.name} confirmed. Total: ${this.formatMoney(result.total_amount)}`,
                { type: "success" },
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
        } finally {
            this.state.confirming = false;
        }
    }
}

registry.category("actions").add("pharmacy_orders", PharmacyOrders);
