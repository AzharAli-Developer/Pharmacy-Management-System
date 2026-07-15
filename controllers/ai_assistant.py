from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class PharmacyAiAssistantController(http.Controller):
    """Add Pharmacy Assistant."""

    @http.route(
        '/pharmacy/ai/chat',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False
    )
    def pharmacy_ai_chat(self, message=None, history=None, **kwargs):
        try:
            return request.env['pharmacy.ai.assistant'].chat(
                message=message,
                history=history or [],
            )

        except UserError as error:
            return {
                'error': True,
                'message': str(error),
            }

        except Exception:
            return {
                'error': True,
                'message': 'Unexpected server error.',
            }
