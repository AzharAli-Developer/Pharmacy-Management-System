from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PharmacyMedicineBatch(models.Model):
    _name = 'pharmacy.medicine.batch'
    _description = 'Medicine Batch'
    _order = 'expiry_date asc, id desc'

    name = fields.Char(required=True)
    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        required=True,
        ondelete='cascade',
        index=True,
    )
    batch_no = fields.Char(index=True)
    supplier_id = fields.Many2one('pharmacy.supplier', ondelete='set null')
    expiry_date = fields.Date(index=True)
    quantity = fields.Integer(default=0)
    purchase_price = fields.Float(default=0.0)
    stock_value = fields.Float(compute='_compute_stock_value')
    active = fields.Boolean(default=True)

    @api.depends('quantity', 'purchase_price')
    def _compute_stock_value(self):
        for batch in self:
            batch.stock_value = batch.quantity * batch.purchase_price

    @api.constrains('quantity', 'purchase_price')
    def _check_values(self):
        for batch in self:
            if batch.quantity < 0:
                raise ValidationError('Batch quantity cannot be negative.')
            if batch.purchase_price < 0:
                raise ValidationError('Purchase price cannot be negative.')

    @api.model
    def create_or_update_batch(self, medicine, quantity, purchase_price=0.0, supplier=False, batch_no=False, expiry_date=False):
        batch_no = (batch_no or '').strip()
        domain = [
            ('medicine_id', '=', medicine.id),
            ('batch_no', '=', batch_no),
            ('expiry_date', '=', expiry_date or False),
            ('supplier_id', '=', supplier.id if supplier else False),
        ]
        batch = self.search(domain, limit=1)
        values = {
            'name': batch_no or f'{medicine.name} Batch',
            'medicine_id': medicine.id,
            'batch_no': batch_no,
            'supplier_id': supplier.id if supplier else False,
            'expiry_date': expiry_date,
            'purchase_price': purchase_price,
        }
        if batch:
            batch.write({
                'quantity': batch.quantity + quantity,
                'purchase_price': purchase_price,
            })
            return batch
        values['quantity'] = quantity
        return self.create(values)
