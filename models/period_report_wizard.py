from odoo import api, fields, models
from odoo.exceptions import UserError


class PharmacyPeriodReportWizard(models.TransientModel):
    _name = 'pharmacy.period.report.wizard'
    _description = 'Pharmacy Period Sales Report'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    total_sale_price = fields.Float(compute='_compute_totals')
    gross_bill = fields.Float(compute='_compute_totals')
    total_discount = fields.Float(compute='_compute_totals')
    total_tax = fields.Float(compute='_compute_totals')
    total_expense = fields.Float(compute='_compute_totals')
    total_amount = fields.Float(compute='_compute_totals')
    total_sales = fields.Float(compute='_compute_totals')
    total_cost = fields.Float(compute='_compute_totals')
    total_profit = fields.Float(compute='_compute_totals')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise UserError('Start date cannot be after end date.')

    def _get_sales(self):
        self.ensure_one()
        return self.env['pharmacy.sale'].search([
            ('sale_date', '>=', self.date_from),
            ('sale_date', '<=', self.date_to),
            ('state', '=', 'confirmed'),
        ], order='sale_date asc, id asc')

    def _get_expenses(self):
        self.ensure_one()
        return self.env['pharmacy.expense'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ], order='date asc, id asc')

    def get_report_lines(self):
        self.ensure_one()
        lines = []
        for sale in self._get_sales():
            medicines = ', '.join(
                '%s x %s' % (line.medicine_id.name, line.quantity)
                for line in sale.medicine_ids
            )
            lines.append({
                'sale_name': sale.name,
                'sale_date': fields.Date.to_string(sale.sale_date),
                'patient': sale.customer_name or 'Walk-in Customer',
                'medicines': medicines,
                'gross_amount': sale.sub_total_amount,
                'discount_amount': sale.total_discount_amount,
                'tax_amount': sale.tax_amount,
                'net_amount': sale.total_amount,
            })
        return lines

    @api.depends('date_from', 'date_to')
    def _compute_totals(self):
        for wizard in self:
            if not wizard.date_from or not wizard.date_to:
                wizard.gross_bill = 0.0
                wizard.total_discount = 0.0
                wizard.total_tax = 0.0
                wizard.total_expense = 0.0
                wizard.total_amount = 0.0
                wizard.total_sale_price = 0.0
                wizard.total_sales = 0.0
                wizard.total_cost = 0.0
                wizard.total_profit = 0.0
                continue

            sales = wizard._get_sales()
            expenses = wizard._get_expenses()
            wizard.gross_bill = sum(sales.mapped('sub_total_amount'))
            wizard.total_discount = sum(sales.mapped('total_discount_amount'))
            wizard.total_tax = sum(sales.mapped('tax_amount'))
            wizard.total_expense = sum(expenses.mapped('amount'))
            wizard.total_sales = sum(sales.mapped('total_amount'))
            wizard.total_cost = sum(sales.mapped('total_cost'))
            wizard.total_profit = wizard.total_sales - wizard.total_cost
            wizard.total_amount = wizard.total_sales - wizard.total_expense
            wizard.total_sale_price = wizard.total_amount

    def action_download_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/pharmacy_management_system.report_pharmacy_period_sales/%s?download=true' % self.id,
            'target': 'download',
        }

    def action_download_xlsx(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/pharmacy/report/%s/xlsx' % self.id,
            'target': 'download',
        }
