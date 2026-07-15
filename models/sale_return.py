from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PharmacySaleReturn(models.Model):
    _name = 'pharmacy.sale.return'
    _description = 'Pharmacy Sale Return'
    _order = 'date desc, id desc'

    name = fields.Char(default='New', required=True)
    sale_id = fields.Many2one(
        'pharmacy.sale',
        required=True,
        ondelete='restrict',
        domain=[('state', '=', 'confirmed')],
    )
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    reason = fields.Text()
    line_ids = fields.One2many('pharmacy.sale.return.line', 'return_id')
    refund_amount = fields.Float(compute='_compute_refund_amount', store=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed')],
        default='draft',
        required=True,
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharmacy.sale.return'
                ) or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.refund_amount')
    def _compute_refund_amount(self):
        for sale_return in self:
            sale_return.refund_amount = sum(sale_return.line_ids.mapped('refund_amount'))

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        sale_id = values.get('sale_id') or self.env.context.get('default_sale_id')
        if sale_id and 'line_ids' in fields_list:
            sale = self.env['pharmacy.sale'].browse(sale_id).exists()
            if sale:
                values['line_ids'] = [
                    (0, 0, {
                        'sale_line_id': line.id,
                        'medicine_id': line.medicine_id.id,
                        'sold_quantity': line.quantity,
                        'return_quantity': 0,
                        'unit_price': line.price,
                    })
                    for line in sale.medicine_ids
                ]
        return values

    @api.onchange('sale_id')
    def _onchange_sale_id(self):
        if not self.sale_id:
            return
        self.line_ids = [(5, 0, 0)] + [
            (0, 0, {
                'sale_line_id': line.id,
                'medicine_id': line.medicine_id.id,
                'sold_quantity': line.quantity,
                'return_quantity': 0,
                'unit_price': line.price,
            })
            for line in self.sale_id.medicine_ids
        ]

    def action_confirm_return(self):
        for sale_return in self:
            if sale_return.state == 'confirmed':
                continue
            lines = sale_return.line_ids.filtered(lambda line: line.return_quantity > 0)
            if not lines:
                raise UserError('Please enter at least one return quantity.')
            for line in lines:
                medicine = line.medicine_id.sudo()
                previous_stock = medicine.stock
                new_stock = previous_stock + line.return_quantity
                medicine.write({'stock': new_stock})
                self.env['pharmacy.stock.move'].sudo().create({
                    'name': sale_return.name,
                    'medicine_id': medicine.id,
                    'move_type': 'return',
                    'quantity': line.return_quantity,
                    'previous_stock': previous_stock,
                    'new_stock': new_stock,
                    'sale_id': sale_return.sale_id.id,
                    'notes': 'Sale return',
                })
            sale_return.state = 'confirmed'


class PharmacySaleReturnLine(models.Model):
    _name = 'pharmacy.sale.return.line'
    _description = 'Pharmacy Sale Return Line'

    return_id = fields.Many2one(
        'pharmacy.sale.return',
        required=True,
        ondelete='cascade',
    )
    sale_line_id = fields.Many2one('pharmacy.sale.line', ondelete='restrict')
    medicine_id = fields.Many2one('pharmacy.medicine', required=True, ondelete='restrict')
    sold_quantity = fields.Integer(readonly=True)
    return_quantity = fields.Integer(default=0)
    unit_price = fields.Float(readonly=True)
    refund_amount = fields.Float(compute='_compute_refund_amount', store=True)

    @api.depends('return_quantity', 'unit_price')
    def _compute_refund_amount(self):
        for line in self:
            line.refund_amount = line.return_quantity * line.unit_price

    @api.constrains('return_quantity', 'sold_quantity')
    def _check_return_quantity(self):
        for line in self:
            if line.return_quantity < 0:
                raise ValidationError('Return quantity cannot be negative.')
            if line.return_quantity > line.sold_quantity:
                raise ValidationError('Return quantity cannot exceed sold quantity.')
