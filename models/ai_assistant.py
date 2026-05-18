import json
import logging
import re
import urllib.error
import urllib.request

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PharmacyAiAssistant(models.AbstractModel):
    _name = 'pharmacy.ai.assistant'
    _description = 'Pharmacy AI Assistant'

    HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

    @api.model
    def chat(self, message, history=None):
        message = (message or '').strip()
        history = history or []

        if not message:
            raise UserError('Please enter a message.')

        token = self.env['ir.config_parameter'].sudo().get_param(
            'pharmacy_management_system.hf_api_token'
        )

        model = self.env['ir.config_parameter'].sudo().get_param(
            'pharmacy_management_system.hf_model',
            'meta-llama/Meta-Llama-3-8B-Instruct:novita'
        )

        if not token:
            raise UserError('HuggingFace API token is not configured.')

        db_context = self._build_database_context(message)

        system_prompt = f"""
You are an AI assistant for an Odoo Pharmacy Management System.

Rules:
1. Use pharmacy database data if available.
2. If medicine exists in DB, use exact DB data.
3. If medicine not found, provide general medicine knowledge.
4. Help users with pharmacy workflow.
5. Answer general questions normally.
6. Never invent fake stock or sales data.

Workflow Knowledge:
- Medicines are managed from Medicines menu.
- Sales are created from Orders screen.
- Purchases are managed from Purchases menu.
- Suppliers are managed from Suppliers menu.
- Expenses are managed from Expenses menu.
- Reports are generated from Dashboard previous report section.

Database Context:
{db_context}
"""

        messages = [{
            "role": "system",
            "content": system_prompt,
        }]

        for item in history[-8:]:
            if item.get("role") and item.get("content"):
                messages.append({
                    "role": item["role"],
                    "content": item["content"],
                })

        messages.append({
            "role": "user",
            "content": message,
        })

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 700,
        }

        try:
            req = urllib.request.Request(
                self.HF_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))

            choices = result.get("choices", [])

            if not choices:
                raise UserError("AI returned empty response.")

            return {
                "answer": choices[0]["message"]["content"]
            }

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="ignore")
            _logger.exception(details)
            raise UserError("HuggingFace API request failed.")

        except urllib.error.URLError:
            raise UserError("Could not connect to HuggingFace API.")

        except Exception as error:
            _logger.exception(error)
            raise UserError("AI assistant failed.")

    def _extract_keywords(self, message):
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', message)
        words = cleaned.split()
        return [word for word in words if len(word) > 2]

    def _build_database_context(self, message):
        context = []
        msg = message.lower()

        medicines = self.env['pharmacy.medicine'].search([], limit=200)

        matched_medicines = medicines.filtered(
            lambda med: med.name and msg in med.name.lower()
        )

        if matched_medicines:
            context.append("Medicine Database Records:")
            for med in matched_medicines[:5]:
                context.append(
                    f"""
    Medicine Name: {med.name}
    Category: {med.category_id.name if med.category_id else ''}
    Price: {med.sale_price}
    Current Stock: {med.stock}
    Expiry Date: {med.expiry_date}
    Description: {med.description or 'No description available'}
    """
                )

        if "sale" in msg or "order" in msg:
            sales = self.env['pharmacy.sale'].search([], limit=5)
            for sale in sales:
                context.append(
                    f"""
    Sale Record:
    Sale No: {sale.name}
    Customer: {sale.customer_name}
    Total Amount: {sale.total_amount}
    """
                )

        if "supplier" in msg:
            suppliers = self.env['pharmacy.supplier'].search([], limit=5)
            for supplier in suppliers:
                context.append(
                    f"""
    Supplier:
    Name: {supplier.name}
    Phone: {supplier.phone or ''}
    Email: {supplier.email or ''}
    """
                )

        if "expense" in msg:
            expenses = self.env['pharmacy.expense'].search([], limit=5)
            for expense in expenses:
                context.append(
                    f"""
    Expense:
    Name: {expense.name}
    Amount: {expense.amount}
    """
                )

        return "\n".join(context) if context else "No matching pharmacy database record found."