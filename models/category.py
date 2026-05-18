from odoo import fields, models


class MedicineCategory(models.Model):
    _name = 'pharmacy.category'
    _description = 'Medicine Category'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    active = fields.Boolean(default=True)