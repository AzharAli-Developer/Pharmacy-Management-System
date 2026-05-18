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
        this.chartRef = useRef("salesChart");
        this.aiChatRef = useRef("aiChatHistory");
        this.salesChart = null;

        this.state = useState({
            data: null,
            period: "today",
            startDate: "",
            endDate: "",
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
                    text: "Hello! I am your AI Pharmacy Assistant. I can help you with medicine usage, stock details, pharmacy records, and general questions. Please ask your question.",
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
        this.state.data = await this.orm.call(
            "pharmacy.dashboard",
            "get_dashboard_data",
            [
                this.state.period,
                this.state.startDate,
                this.state.endDate,
            ]
        );
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
            const cleanHistory = this.state.aiMessages
                .slice(-10)
                .map((msg) => ({
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
                text: response.error
                    ? response.message
                    : response.answer,
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
                        label: "Daily Sales",
                        data: amounts,
                        borderColor: "#059669",
                        backgroundColor: "rgba(5,150,105,0.14)",
                        borderWidth: 3,
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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

openAction(key) {
    const actions = {
        categories: "pharmacy_management_system.action_pharmacy_category",
        medicines: "pharmacy_management_system.action_pharmacy_medicine",
        suppliers: "pharmacy_management_system.action_pharmacy_supplier",
        purchases: "pharmacy_management_system.action_pharmacy_purchase",
        expenses: "pharmacy_management_system.action_pharmacy_expense",
        sales: "pharmacy_management_system.action_pharmacy_sale",
    };

    const actionXmlId = actions[key];

    if (!actionXmlId) {
        return;
    }

    this.action.doAction(actionXmlId);
}
}

registry.category("actions").add("pharmacy_dashboard", PharmacyDashboardAction);