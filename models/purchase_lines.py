from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseLine(models.Model):
    _name = 'pharmacy.purchase.line'
    _description = 'Pharmacy Purchase Line'

    purchase_id = fields.Many2one(
        'pharmacy.purchase',
        required=True,
        ondelete='cascade'
    )
    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        required=True,
        ondelete='restrict'
    )
    quantity = fields.Integer(default=1, required=True)
    price = fields.Float(required=True)
    batch_no = fields.Char()
    expiry_date = fields.Date()
    subtotal = fields.Float(compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price

    @api.constrains('quantity', 'price')
    def _check_line_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Purchase quantity must be greater than zero.')
            if line.price < 0:
                raise ValidationError('Purchase price cannot be negative.')
