from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pharmacy_hf_api_token = fields.Char(
        string='HuggingFace API Token',
        config_parameter='pharmacy_management_system.hf_api_token',
    )

    pharmacy_hf_model = fields.Char(
        string='HuggingFace Model',
        default='meta-llama/Llama-3.1-8B-Instruct:novita',
        config_parameter='pharmacy_management_system.hf_model',
    )

    pharmacy_default_tax_rate = fields.Float(
        string='Default POS Tax Rate (%)',
        config_parameter='pharmacy_management_system.default_tax_rate',
    )
