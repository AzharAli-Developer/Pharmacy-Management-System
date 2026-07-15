from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleLine(models.Model):
    _name = 'pharmacy.sale.line'
    _description = 'Pharmacy Sale Line'

    sale_id = fields.Many2one(
        'pharmacy.sale',
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
    cost_price = fields.Float(default=0.0)
    discount_amount = fields.Float(default=0.0)
    subtotal = fields.Float(compute='_compute_subtotal', store=True)
    total_amount = fields.Float(compute='_compute_subtotal', store=True)
    profit_amount = fields.Float(compute='_compute_subtotal', store=True)

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        for line in self:
            if line.medicine_id:
                line.price = line.medicine_id.sale_price
                line.cost_price = line.medicine_id.cost_price

    @api.depends('quantity', 'price', 'cost_price', 'discount_amount')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price
            rec.total_amount = max(rec.subtotal - rec.discount_amount, 0.0)
            rec.profit_amount = rec.total_amount - (rec.quantity * rec.cost_price)

    @api.constrains('quantity', 'price', 'discount_amount')
    def _check_line_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError('Sale quantity must be greater than zero.')
            if line.price < 0:
                raise ValidationError('Sale price cannot be negative.')
            if line.discount_amount < 0:
                raise ValidationError('Line discount cannot be negative.')
            if line.discount_amount > (line.quantity * line.price):
                raise ValidationError('Line discount cannot exceed line subtotal.')
