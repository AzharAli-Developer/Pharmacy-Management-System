from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Medicine(models.Model):
    _name = 'pharmacy.medicine'
    _description = 'Pharmacy Medicine'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    generic_name = fields.Char(index=True)
    manufacturer = fields.Char()
    medicine_code = fields.Char(
        string='Medicine Code',
        copy=False,
        index=True,
        help='Internal SKU or shelf code used for quick POS search.',
    )
    category_id = fields.Many2one(
        'pharmacy.category',
        required=True,
        ondelete='restrict',
    )
    description = fields.Text()
    cost_price = fields.Float(string='Cost Price', default=0.0)
    sale_price = fields.Float(string='Sale Price', required=True)
    stock = fields.Integer(default=0)
    reorder_level = fields.Integer(default=10)
    expiry_date = fields.Date()
    batch_ids = fields.One2many('pharmacy.medicine.batch', 'medicine_id')

    @api.constrains('cost_price', 'sale_price', 'stock', 'reorder_level')
    def _check_positive_values(self):
        for medicine in self:
            if medicine.cost_price < 0:
                raise ValidationError('Cost price cannot be negative.')
            if medicine.sale_price < 0:
                raise ValidationError('Sale price cannot be negative.')
            if medicine.stock < 0:
                raise ValidationError('Stock cannot be negative.')
            if medicine.reorder_level < 0:
                raise ValidationError('Reorder level cannot be negative.')
