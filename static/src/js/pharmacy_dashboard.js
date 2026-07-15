/** @odoo-module **/

import { Component, onMounted, onPatched, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class PharmacyDashboardAction extends Component {
    static template = "pharmacy_management_system.PharmacyDashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.chartRef = useRef("salesChart");
        this.aiChatRef = useRef("aiChatHistory");
        this.salesChart = null;

        this.state = useState({
            data: null,
            period: "today",
            startDate: "",
            endDate: "",
            loading: true,
            error: "",
            showReportPicker: false,
            showCustomReport: false,
            report: null,
            showAiAssistant: false,
            aiQuestion: "",
            aiLoading: false,
            aiMessages: [
                {
                    id: 1,
                    role: "assistant",
                    text: "Hello! I can help with pharmacy workflow and available pharmacy records.",
                },
            ],
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });

        onMounted(() => this.renderSalesChart());

        onPatched(() => {
            this.renderSalesChart();
            this.scrollAiChatToBottom();
        });

        onWillUnmount(() => {
            if (this.salesChart) {
                this.salesChart.destroy();
            }
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.error = "";
        try {
            this.state.data = await this.orm.call(
                "pharmacy.dashboard",
                "get_dashboard_data",
                [this.state.period, this.state.startDate, this.state.endDate],
            );
        } catch (error) {
            this.state.error = "Dashboard data could not be loaded.";
            this.notification.add(this.state.error, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async changePeriod(period) {
        this.state.period = period;
        if (period !== "custom") {
            this.state.startDate = "";
            this.state.endDate = "";
        }
        await this.loadDashboard();
    }

    formatMoney(value) {
        return `Rs. ${Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
        })}`;
    }

    openReportPicker() {
        this.state.showReportPicker = true;
        this.state.showCustomReport = false;
        this.state.report = null;
    }

    closeReportModal() {
        this.state.showReportPicker = false;
        this.state.showCustomReport = false;
        this.state.report = null;
    }

    async setPeriod(period) {
        this.state.period = period;
        this.state.showCustomReport = false;
        this.state.report = await this.orm.call(
            "pharmacy.dashboard",
            "get_period_report",
            [period, false, false],
        );
    }

    chooseCustom() {
        this.state.period = "custom";
        this.state.showCustomReport = true;
        this.state.report = null;
    }

    async applyCustom() {
        if (!this.state.startDate || !this.state.endDate) {
            this.notification.add("Select both start and end dates.", { type: "warning" });
            return;
        }
        this.state.report = await this.orm.call(
            "pharmacy.dashboard",
            "get_period_report",
            ["custom", this.state.startDate, this.state.endDate],
        );
        this.state.showCustomReport = false;
    }

    async downloadReport(reportType) {
        if (!this.state.report?.wizard_id) {
            return;
        }
        const reportAction = await this.orm.call(
            "pharmacy.dashboard",
            "get_period_report_action",
            [this.state.report.wizard_id, reportType],
        );
        if (reportAction) {
            this.action.doAction(reportAction);
        }
    }

    openAiAssistant() {
        this.state.showAiAssistant = true;
    }

    closeAiAssistant() {
        this.state.showAiAssistant = false;
        this.state.aiQuestion = "";
    }

    scrollAiChatToBottom() {
        if (this.aiChatRef.el) {
            this.aiChatRef.el.scrollTop = this.aiChatRef.el.scrollHeight;
        }
    }

    async sendAiQuestion() {
        const question = this.state.aiQuestion.trim();
        if (!question || this.state.aiLoading) {
            return;
        }

        this.state.aiMessages.push({
            id: Date.now(),
            role: "user",
            text: question,
        });
        this.state.aiQuestion = "";
        this.state.aiLoading = true;

        try {
            const cleanHistory = this.state.aiMessages.slice(-10).map((msg) => ({
                role: msg.role,
                content: msg.text,
            }));
            const response = await rpc("/pharmacy/ai/chat", {
                message: question,
                history: cleanHistory,
            });
            this.state.aiMessages.push({
                id: Date.now() + 1,
                role: "assistant",
                text: response.error ? response.message : response.answer,
            });
        } catch (error) {
            this.state.aiMessages.push({
                id: Date.now() + 1,
                role: "assistant",
                text: "AI assistant is currently unavailable.",
            });
        } finally {
            this.state.aiLoading = false;
        }
    }

    onAiQuestionKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendAiQuestion();
        }
    }

    renderSalesChart() {
        if (!this.chartRef.el || !this.state.data?.graph || !window.Chart) {
            return;
        }

        const labels = this.state.data.graph.map((item) => item.date);
        const amounts = this.state.data.graph.map((item) => Number(item.amount) || 0);

        if (this.salesChart) {
            this.salesChart.data.labels = labels;
            this.salesChart.data.datasets[0].data = amounts;
            this.salesChart.update();
            return;
        }

        this.salesChart = new window.Chart(this.chartRef.el, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Sales",
                        data: amounts,
                        borderColor: "#0f766e",
                        backgroundColor: "rgba(15, 118, 110, 0.12)",
                        borderWidth: 3,
                        pointRadius: 3,
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }

    openMedicine(medicineId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pharmacy.medicine",
            res_id: medicineId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openSale(saleId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pharmacy.sale",
            res_id: saleId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openAction(key) {
        const actions = {
            categories: "pharmacy_management_system.action_pharmacy_category",
            medicines: "pharmacy_management_system.action_pharmacy_medicine",
            orders: "pharmacy_management_system.action_pharmacy_orders_client",
            suppliers: "pharmacy_management_system.action_pharmacy_supplier",
            customers: "pharmacy_management_system.action_pharmacy_customer",
            purchases: "pharmacy_management_system.action_pharmacy_purchase",
            expenses: "pharmacy_management_system.action_pharmacy_expense",
            sales: "pharmacy_management_system.action_pharmacy_sale",
            stock_moves: "pharmacy_management_system.action_pharmacy_stock_move",
        };
        if (actions[key]) {
            this.action.doAction(actions[key]);
        }
    }
}

registry.category("actions").add("pharmacy_dashboard", PharmacyDashboardAction);
