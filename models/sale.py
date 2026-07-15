from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class Sale(models.Model):
    _name = "pharmacy.sale"
    _description = "Pharmacy Sale"
    _order = "sale_date desc, id desc"

    name = fields.Char(default='New', required=True)
    customer_id = fields.Many2one('pharmacy.customer', ondelete='set null')
    customer_name = fields.Char()
    medicine_ids = fields.One2many('pharmacy.sale.line', 'sale_id')
    total_amount = fields.Float(compute='_compute_total_amount', store=True)
    sub_total_amount = fields.Float(compute='_compute_total_amount', store=True)
    total_cost = fields.Float(compute='_compute_total_amount', store=True)
    profit_amount = fields.Float(compute='_compute_total_amount', store=True)
    sale_date = fields.Date(default=fields.Date.context_today, required=True)
    discount = fields.Float(default=0.0)
    tax_rate = fields.Float(default=0.0)
    tax_amount = fields.Float(compute='_compute_total_amount', store=True)
    payment_method = fields.Selection(
        [
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('mobile', 'Mobile Wallet'),
        ],
        default='cash',
        required=True,
    )
    amount_received = fields.Float(default=0.0)
    change_amount = fields.Float(compute='_compute_change_amount', store=True)
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
        'medicine_ids.profit_amount',
        'medicine_ids.cost_price',
        'medicine_ids.discount_amount',
        'discount',
        'tax_rate',
    )
    def _compute_total_amount(self):
        for rec in self:
            rec.sub_total_amount = sum(rec.medicine_ids.mapped('subtotal'))
            rec.line_discount_amount = sum(rec.medicine_ids.mapped('discount_amount'))
            gross_after_line_discount = sum(rec.medicine_ids.mapped('total_amount'))
            order_discount = min(max(rec.discount, 0.0), gross_after_line_discount)
            taxable_amount = max(gross_after_line_discount - order_discount, 0.0)
            rec.tax_amount = (taxable_amount * max(rec.tax_rate, 0.0)) / 100
            rec.total_discount_amount = rec.line_discount_amount + order_discount
            rec.total_amount = taxable_amount + rec.tax_amount
            rec.total_cost = sum(
                line.quantity * line.cost_price
                for line in rec.medicine_ids
            )
            rec.profit_amount = rec.total_amount - rec.total_cost

    @api.depends('amount_received', 'total_amount')
    def _compute_change_amount(self):
        for sale in self:
            sale.change_amount = max(sale.amount_received - sale.total_amount, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self._get_next_sale_reference()
            if vals.get('customer_id') and not vals.get('customer_name'):
                vals['customer_name'] = self.env['pharmacy.customer'].browse(
                    vals['customer_id']
                ).name
            elif vals.get('customer_name') and not vals.get('customer_id'):
                customer = self.env['pharmacy.customer'].find_or_create_from_name(
                    vals.get('customer_name')
                )
                if customer:
                    vals['customer_id'] = customer.id
        return super().create(vals_list)

    @api.constrains('discount', 'tax_rate')
    def _check_sale_values(self):
        for sale in self:
            if sale.discount < 0:
                raise ValidationError('Order discount cannot be negative.')
            if sale.tax_rate < 0 or sale.tax_rate > 100:
                raise ValidationError('Tax rate must be between 0 and 100.')

    @api.model
    def get_order_screen_data(self):
        return {
            'categories': self.env['pharmacy.category'].search_read([], ['name'], order='name'),
            'medicines': self.env['pharmacy.medicine'].search_read(
                [],
                [
                    'name',
                    'generic_name',
                    'manufacturer',
                    'medicine_code',
                    'category_id',
                    'description',
                    'sale_price',
                    'stock',
                    'reorder_level',
                    'expiry_date',
                ],
                order='name',
            ),
            'recent_customers': self._get_recent_customers(),
            'tax_rate': float(
                self.env['ir.config_parameter'].sudo().get_param(
                    'pharmacy_management_system.default_tax_rate',
                    '0',
                ) or 0
            ),
        }

    def _get_next_sale_reference(self):
        return self.env['ir.sequence'].next_by_code('pharmacy.sale') or 'New'

    @api.model
    def _get_default_customer_name(self):
        Customer = self.env['pharmacy.customer']
        for _counter in range(20):
            name = self.env['ir.sequence'].next_by_code(
                'pharmacy.customer.default'
            )
            if name and not Customer.search([('name', '=ilike', name)], limit=1):
                return name

        index = 1
        while True:
            name = f'Customer{index}'
            if not Customer.search([('name', '=ilike', name)], limit=1):
                return name
            index += 1

    @api.model
    def _resolve_customer_name(self, customer_name=False):
        clean_name = (customer_name or '').strip()
        return clean_name or self._get_default_customer_name()

    def _ensure_confirmed_customer(self):
        Customer = self.env['pharmacy.customer']
        for sale in self:
            if sale.customer_id:
                if not sale.customer_name:
                    sale.customer_name = sale.customer_id.name
                continue

            customer_name = self._resolve_customer_name(sale.customer_name)
            customer = Customer.find_or_create_from_name(customer_name)
            sale.customer_name = customer_name
            sale.customer_id = customer.id if customer else False

    def _get_recent_customers(self, limit=12):
        sales = self.search([
            ('customer_name', '!=', False),
            ('state', '=', 'confirmed'),
        ], order='sale_date desc, id desc', limit=80)
        customers = []
        seen = set()
        for sale in sales:
            name = (sale.customer_name or '').strip()
            key = name.lower()
            if name and key not in seen and name != 'Walk-in Customer':
                customers.append(name)
                seen.add(key)
            if len(customers) >= limit:
                break
        return customers

    @api.model
    def confirm_order(
        self,
        cart_lines,
        customer_name=False,
        discount=0.0,
        tax_rate=0.0,
        payment_method='cash',
        amount_received=0.0,
    ):
        if not cart_lines:
            raise UserError('Please add at least one medicine.')

        medicine_ids = [
            line.get('medicine_id')
            for line in cart_lines
            if line.get('medicine_id')
        ]
        if not medicine_ids:
            raise UserError('Invalid cart data.')

        self.env.cr.execute(
            'SELECT id FROM pharmacy_medicine WHERE id IN %s FOR UPDATE',
            [tuple(set(medicine_ids))],
        )
        medicines = {
            med.id: med
            for med in self.env['pharmacy.medicine'].browse(medicine_ids).exists()
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
                'cost_price': medicine.cost_price,
                'discount_amount': discount_amount,
            }))

        if not order_lines:
            raise UserError('Invalid cart data.')

        resolved_customer_name = self._resolve_customer_name(customer_name)
        customer = self.env['pharmacy.customer'].find_or_create_from_name(
            resolved_customer_name
        )
        sale = self.create({
            'customer_id': customer.id if customer else False,
            'customer_name': resolved_customer_name,
            'sale_date': fields.Date.context_today(self),
            'discount': max(float(discount or 0.0), 0.0),
            'tax_rate': min(max(float(tax_rate or 0.0), 0.0), 100.0),
            'payment_method': payment_method if payment_method in ['cash', 'card', 'mobile'] else 'cash',
            'amount_received': max(float(amount_received or 0.0), 0.0),
            'cashier_id': self.env.user.id,
            'state': 'confirmed',
            'medicine_ids': order_lines,
        })

        for line in sale.medicine_ids:
            sale._decrease_stock_for_line(line, 'POS order confirmed')

        return {
            'sale_id': sale.id,
            'name': sale.name,
            'total_amount': sale.total_amount,
        }

    def action_confirm_sale(self):
        for sale in self:
            if sale.state == 'confirmed':
                continue
            if not sale.medicine_ids:
                raise UserError('Please add at least one medicine.')

            sale._ensure_confirmed_customer()

            medicine_ids = sale.medicine_ids.mapped('medicine_id').ids
            self.env.cr.execute(
                'SELECT id FROM pharmacy_medicine WHERE id IN %s FOR UPDATE',
                [tuple(set(medicine_ids))],
            )
            for line in sale.medicine_ids:
                if line.medicine_id.stock < line.quantity:
                    raise UserError(
                        f'{line.medicine_id.name} has only {line.medicine_id.stock} units available.'
                    )

            sale.state = 'confirmed'
            for line in sale.medicine_ids:
                sale._decrease_stock_for_line(line, 'Sale confirmed')

    def _decrease_stock_for_line(self, line, note):
        self.ensure_one()
        medicine = line.medicine_id.sudo()
        remaining = line.quantity
        batches = self.env['pharmacy.medicine.batch'].sudo().search([
            ('medicine_id', '=', medicine.id),
            ('quantity', '>', 0),
        ], order='expiry_date asc, id asc')

        for batch in batches:
            if remaining <= 0:
                break
            consumed = min(batch.quantity, remaining)
            batch.write({'quantity': batch.quantity - consumed})
            remaining -= consumed

        previous_stock = medicine.stock
        new_stock = previous_stock - line.quantity
        medicine.write({'stock': new_stock})
        self.env['pharmacy.stock.move'].sudo().create({
            'name': self.name,
            'medicine_id': medicine.id,
            'move_type': 'sale',
            'quantity': -line.quantity,
            'previous_stock': previous_stock,
            'new_stock': new_stock,
            'sale_id': self.id,
            'notes': note,
        })

    def action_print_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/pharmacy/sale/{self.id}/receipt/print',
            'target': 'new',
        }

    def action_create_return(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Return',
            'res_model': 'pharmacy.sale.return',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_sale_id': self.id,
            },
        }

    def action_download_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/pdf/pharmacy_management_system.report_pharmacy_sale_receipt/{self.id}?download=true',
            'target': 'download',
        }
