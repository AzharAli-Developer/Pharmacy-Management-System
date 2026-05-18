from odoo import api, fields, models


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
    discount_amount = fields.Float(default=0.0)
    subtotal = fields.Float(compute='_compute_subtotal', store=True)
    total_amount = fields.Float(compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price', 'discount_amount')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price
            rec.total_amount = max(rec.subtotal - rec.discount_amount, 0.0)