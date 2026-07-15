from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PharmacyStockAdjustment(models.Model):
    _name = 'pharmacy.stock.adjustment'
    _description = 'Pharmacy Stock Adjustment'
    _order = 'date desc, id desc'

    name = fields.Char(default='New', required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    reason = fields.Selection(
        [
            ('count', 'Stock Count'),
            ('damage', 'Damaged Medicine'),
            ('correction', 'Data Correction'),
            ('other', 'Other'),
        ],
        default='count',
        required=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many('pharmacy.stock.adjustment.line', 'adjustment_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved')],
        default='draft',
        required=True,
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharmacy.stock.adjustment'
                ) or 'New'
        return super().create(vals_list)

    def action_approve(self):
        for adjustment in self:
            if adjustment.state == 'approved':
                continue
            if not adjustment.line_ids:
                raise UserError('Please add at least one adjustment line.')
            for line in adjustment.line_ids:
                medicine = line.medicine_id.sudo()
                previous_stock = medicine.stock
                new_stock = line.new_quantity
                medicine.write({'stock': new_stock})
                self.env['pharmacy.stock.move'].sudo().create({
                    'name': adjustment.name,
                    'medicine_id': medicine.id,
                    'move_type': 'adjustment',
                    'quantity': new_stock - previous_stock,
                    'previous_stock': previous_stock,
                    'new_stock': new_stock,
                    'notes': adjustment.notes or dict(adjustment._fields['reason'].selection).get(adjustment.reason),
                })
            adjustment.state = 'approved'


class PharmacyStockAdjustmentLine(models.Model):
    _name = 'pharmacy.stock.adjustment.line'
    _description = 'Pharmacy Stock Adjustment Line'

    adjustment_id = fields.Many2one(
        'pharmacy.stock.adjustment',
        required=True,
        ondelete='cascade',
    )
    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        required=True,
        ondelete='restrict',
    )
    current_quantity = fields.Integer(related='medicine_id.stock', readonly=True)
    new_quantity = fields.Integer(required=True)

    @api.constrains('new_quantity')
    def _check_new_quantity(self):
        for line in self:
            if line.new_quantity < 0:
                raise ValidationError('Adjusted stock cannot be negative.')
