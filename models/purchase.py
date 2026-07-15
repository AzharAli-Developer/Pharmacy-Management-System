from odoo import api, fields, models
from odoo.exceptions import UserError


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
    amount_paid = fields.Float(default=0.0)
    balance_due = fields.Float(compute='_compute_balance_due', store=True)
    payment_status = fields.Selection(
        [
            ('unpaid', 'Unpaid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        compute='_compute_balance_due',
        store=True,
    )
    purchase_date = fields.Date(default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed')],
        default='draft',
        required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharmacy.purchase'
                ) or 'New'
        return super().create(vals_list)

    @api.depends('medicine_ids.subtotal')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.medicine_ids.mapped('subtotal'))

    @api.depends('total_amount', 'amount_paid')
    def _compute_balance_due(self):
        for rec in self:
            rec.balance_due = max(rec.total_amount - rec.amount_paid, 0.0)
            if rec.balance_due <= 0 and rec.total_amount:
                rec.payment_status = 'paid'
            elif rec.amount_paid > 0:
                rec.payment_status = 'partial'
            else:
                rec.payment_status = 'unpaid'

    def action_confirm_purchase(self):
        for rec in self:
            if rec.state == 'confirmed':
                continue

            if not rec.medicine_ids:
                raise UserError('Please add at least one medicine before confirming.')

            for line in rec.medicine_ids:
                medicine = line.medicine_id.sudo()
                previous_stock = medicine.stock
                new_stock = previous_stock + line.quantity
                current_value = previous_stock * medicine.cost_price
                incoming_value = line.quantity * line.price
                medicine.write({
                    'stock': new_stock,
                    'cost_price': (
                        (current_value + incoming_value) / new_stock
                        if new_stock else medicine.cost_price
                    ),
                })
                self.env['pharmacy.stock.move'].sudo().create({
                    'name': rec.name,
                    'medicine_id': medicine.id,
                    'move_type': 'purchase',
                    'quantity': line.quantity,
                    'previous_stock': previous_stock,
                    'new_stock': new_stock,
                    'purchase_id': rec.id,
                    'notes': 'Purchase confirmed',
                })
                batch = self.env['pharmacy.medicine.batch'].sudo().create_or_update_batch(
                    medicine=medicine,
                    quantity=line.quantity,
                    purchase_price=line.price,
                    supplier=rec.supplier_id,
                    batch_no=line.batch_no,
                    expiry_date=line.expiry_date or medicine.expiry_date,
                )
                if batch:
                    self.env['pharmacy.stock.move'].sudo().search([
                        ('purchase_id', '=', rec.id),
                        ('medicine_id', '=', medicine.id),
                    ], order='id desc', limit=1).write({'batch_id': batch.id})

            rec.state = 'confirmed'
