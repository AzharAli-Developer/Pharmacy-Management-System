from odoo import api, fields, models


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
    subtotal = fields.Float(compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price