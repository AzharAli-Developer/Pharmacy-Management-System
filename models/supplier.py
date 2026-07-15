from odoo import fields, models


class Supplier(models.Model):
    _name = 'pharmacy.supplier'
    _description = 'Pharmacy Supplier'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    phone = fields.Char()
    email = fields.Char()
    address = fields.Text()
    contact_person = fields.Char()
