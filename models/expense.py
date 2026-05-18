from odoo import fields, models


class Expense(models.Model):
    _name = 'pharmacy.expense'
    _description = 'Pharmacy Expense'
    _order = 'date desc, id desc'

    name = fields.Char(required=True)
    expense_type = fields.Selection(
        [
            ('tea', 'Tea'),
            ('lunch', 'Lunch'),
            ('electricity', 'Electricity'),
            ('rent', 'Rent'),
            ('salary', 'Salary'),
            ('other', 'Other'),
        ],
        default='other',
        required=True,
    )
    amount = fields.Float(required=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    notes = fields.Text()