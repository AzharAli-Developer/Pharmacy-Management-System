from odoo import fields, models


class PharmacyStockMove(models.Model):
    _name = 'pharmacy.stock.move'
    _description = 'Pharmacy Stock Movement'
    _order = 'date desc, id desc'

    name = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        required=True,
        ondelete='restrict',
        index=True,
    )
    move_type = fields.Selection(
        [
            ('purchase', 'Purchase'),
            ('sale', 'Sale'),
            ('return', 'Return'),
            ('adjustment', 'Adjustment'),
        ],
        required=True,
        index=True,
    )
    quantity = fields.Integer(required=True)
    previous_stock = fields.Integer(readonly=True)
    new_stock = fields.Integer(readonly=True)
    batch_id = fields.Many2one('pharmacy.medicine.batch', ondelete='set null')
    sale_id = fields.Many2one('pharmacy.sale', ondelete='set null')
    purchase_id = fields.Many2one('pharmacy.purchase', ondelete='set null')
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
    )
    notes = fields.Char()
