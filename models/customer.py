from odoo import api, fields, models


class PharmacyCustomer(models.Model):
    _name = 'pharmacy.customer'
    _description = 'Pharmacy Customer'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    phone = fields.Char(index=True)
    email = fields.Char()
    address = fields.Text()
    notes = fields.Text()
    sale_ids = fields.One2many('pharmacy.sale', 'customer_id')
    sale_count = fields.Integer(string='Total Orders', compute='_compute_sale_stats')
    total_medicines_purchased = fields.Integer(
        string='Total Medicines Purchased',
        compute='_compute_sale_stats',
    )
    total_spent = fields.Float(string='Total Bill Amount', compute='_compute_sale_stats')
    last_purchase_date = fields.Date(string='Last Purchase Date', compute='_compute_sale_stats')

    @api.depends(
        'sale_ids.total_amount',
        'sale_ids.sale_date',
        'sale_ids.state',
        'sale_ids.medicine_ids.quantity',
    )
    def _compute_sale_stats(self):
        for customer in self:
            confirmed_sales = customer.sale_ids.filtered(lambda sale: sale.state == 'confirmed')
            customer.sale_count = len(confirmed_sales)
            customer.total_medicines_purchased = sum(
                confirmed_sales.mapped('medicine_ids.quantity')
            )
            customer.total_spent = sum(confirmed_sales.mapped('total_amount'))
            customer.last_purchase_date = (
                max(confirmed_sales.mapped('sale_date'))
                if confirmed_sales else False
            )

    @api.model
    def find_or_create_from_name(self, name):
        clean_name = (name or '').strip()
        if not clean_name or clean_name == 'Walk-in Customer':
            return False
        customer = self.search([('name', '=ilike', clean_name)], limit=1)
        if customer:
            return customer
        return self.create({'name': clean_name})
