from odoo import api, fields, models
from odoo.exceptions import UserError


class Sale(models.Model):
    _name = "pharmacy.sale"
    _description = "Pharmacy Sale"
    _order = "sale_date desc, id desc"

    name = fields.Char(default='New', required=True)
    customer_name = fields.Char()
    medicine_ids = fields.One2many('pharmacy.sale.line', 'sale_id')
    total_amount = fields.Float(compute='_compute_total_amount', store=True)
    sub_total_amount = fields.Float(compute='_compute_total_amount', store=True)
    sale_date = fields.Date(default=fields.Date.context_today, required=True)
    discount = fields.Float(default=0.0)
    line_discount_amount = fields.Float(compute='_compute_total_amount', store=True)
    total_discount_amount = fields.Float(compute='_compute_total_amount', store=True)
    cashier_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed')],
        default='draft',
        required=True,
    )

    @api.depends(
        'medicine_ids.subtotal',
        'medicine_ids.total_amount',
        'medicine_ids.discount_amount',
        'discount'
    )
    def _compute_total_amount(self):
        for rec in self:
            rec.sub_total_amount = sum(rec.medicine_ids.mapped('subtotal'))
            rec.line_discount_amount = sum(rec.medicine_ids.mapped('discount_amount'))
            rec.total_discount_amount = rec.line_discount_amount + rec.discount
            rec.total_amount = max(
                sum(rec.medicine_ids.mapped('total_amount')) - rec.discount,
                0.0
            )

    @api.model
    def get_order_screen_data(self):
        return {
            'categories': self.env['pharmacy.category'].search_read([], ['name'], order='name'),
            'medicines': self.env['pharmacy.medicine'].search_read(
                [],
                ['name', 'category_id', 'description', 'sale_price', 'stock', 'expiry_date'],
                order='name',
            ),
        }

    def _get_next_sale_reference(self):
        last = self.search([], limit=1, order='id desc')
        next_id = (last.id + 1) if last else 1
        return f'SAL-{next_id:05d}'

    @api.model
    def confirm_order(self, cart_lines, customer_name=False, discount=0.0):
        if not cart_lines:
            raise UserError('Please add at least one medicine.')

        medicine_ids = [line.get('medicine_id') for line in cart_lines]
        medicines = {
            med.id: med for med in self.env['pharmacy.medicine'].browse(medicine_ids)
        }

        order_lines = []

        for line in cart_lines:
            medicine = medicines.get(line.get('medicine_id'))
            quantity = int(line.get('quantity') or 0)

            if not medicine or quantity <= 0:
                continue

            if medicine.stock < quantity:
                raise UserError(
                    f'{medicine.name} has only {medicine.stock} units available.'
                )

            discount_amount = max(float(line.get('discount_amount') or 0.0), 0.0)
            line_total = quantity * medicine.sale_price

            if discount_amount > line_total:
                discount_amount = line_total

            order_lines.append((0, 0, {
                'medicine_id': medicine.id,
                'quantity': quantity,
                'price': medicine.sale_price,
                'discount_amount': discount_amount,
            }))

        if not order_lines:
            raise UserError('Invalid cart data.')

        sale = self.create({
            'name': self._get_next_sale_reference(),
            'customer_name': customer_name or 'Walk-in Customer',
            'sale_date': fields.Date.context_today(self),
            'discount': max(float(discount or 0.0), 0.0),
            'cashier_id': self.env.user.id,
            'state': 'confirmed',
            'medicine_ids': order_lines,
        })

        for line in sale.medicine_ids:
            line.medicine_id.stock -= line.quantity

        return {
            'sale_id': sale.id,
            'name': sale.name,
            'total_amount': sale.total_amount,
        }

    def action_print_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/pharmacy/sale/{self.id}/receipt/print',
            'target': 'new',
        }

    def action_download_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/pdf/pharmacy_management_system.report_pharmacy_sale_receipt/{self.id}?download=true',
            'target': 'download',
        }