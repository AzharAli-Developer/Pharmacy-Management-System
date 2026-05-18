from odoo import fields, models


class Medicine(models.Model):
    _name = 'pharmacy.medicine'
    _description = 'Pharmacy Medicine'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    category_id = fields.Many2one(
        'pharmacy.category',
        required=True,
        ondelete='restrict',
    )
    description = fields.Text()
    sale_price = fields.Float(required=True)
    stock = fields.Integer(default=0)
    expiry_date = fields.Date()