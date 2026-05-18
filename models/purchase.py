from odoo import api, fields, models


class Purchase(models.Model):
    _name = "pharmacy.purchase"
    _description = "Pharmacy Purchase"
    _order = "purchase_date desc, id desc"

    name = fields.Char(default='New', required=True)
    supplier_id = fields.Many2one(
        'pharmacy.supplier',
        required=True,
        ondelete='restrict'
    )
    medicine_ids = fields.One2many('pharmacy.purchase.line', 'purchase_id')
    total_amount = fields.Float(compute='_compute_total_amount', store=True)
    purchase_date = fields.Date(default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed')],
        default='draft',
        required=True,
    )

    @api.depends('medicine_ids.subtotal')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.medicine_ids.mapped('subtotal'))

    def action_confirm_purchase(self):
        for rec in self:
            if rec.state == 'confirmed':
                continue

            for line in rec.medicine_ids:
                line.medicine_id.stock += line.quantity

            rec.state = 'confirmed'