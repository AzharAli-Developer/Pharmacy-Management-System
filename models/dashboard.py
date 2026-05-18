from datetime import timedelta
from odoo import api, fields, models


class PharmacyDashboard(models.Model):
    _name = 'pharmacy.dashboard'
    _description = 'Pharmacy Dashboard'

    name = fields.Char(default='Pharmacy Dashboard', required=True)
    category_count = fields.Integer(compute='_compute_dashboard_counts')
    medicine_count = fields.Integer(compute='_compute_dashboard_counts')
    patient_count = fields.Integer(compute='_compute_dashboard_counts')

    @api.depends_context('uid')
    def _compute_dashboard_counts(self):
        category_count = self.env['pharmacy.category'].search_count([])
        medicine_count = self.env['pharmacy.medicine'].search_count([])
        patient_count = len(
            set(
                self.env['pharmacy.sale']
                .search([('customer_name', '!=', False)])
                .mapped('customer_name')
            )
        )

        for rec in self:
            rec.category_count = category_count
            rec.medicine_count = medicine_count
            rec.patient_count = patient_count

    @api.model
    def get_dashboard_data(self, period='today', start_date=False, end_date=False):
        date_from, date_to = self._get_period_dates(period, start_date, end_date)
        today = fields.Date.context_today(self)

        sales = self.env['pharmacy.sale'].search([
            ('sale_date', '>=', date_from),
            ('sale_date', '<=', date_to),
        ])

        expenses = self.env['pharmacy.expense'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])

        graph = self._get_sales_graph(today)

        expired = self.env['pharmacy.medicine'].search([
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today),
        ], order='expiry_date asc', limit=8)

        expiring_soon = self.env['pharmacy.medicine'].search([
            ('expiry_date', '>=', today),
            ('expiry_date', '<=', today + timedelta(days=15)),
        ], order='expiry_date asc', limit=8)

        return {
            'period': period,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'cards': {
                'categories': self.env['pharmacy.category'].search_count([]),
                'medicines': self.env['pharmacy.medicine'].search_count([]),
                'orders': self.env['pharmacy.sale'].search_count([]),
                'suppliers': self.env['pharmacy.supplier'].search_count([]),
                'expenses': sum(expenses.mapped('amount')),
                'sales': sum(sales.mapped('total_amount')),
            },
            'graph': graph,
            'expired': self._medicine_rows(expired),
            'expiring_soon': self._medicine_rows(expiring_soon),
        }

    @api.model
    def get_period_report(self, period='today', start_date=False, end_date=False):
        date_from, date_to = self._get_period_dates(period, start_date, end_date)

        wizard = self.env['pharmacy.period.report.wizard'].create({
            'date_from': date_from,
            'date_to': date_to,
        })

        return {
            'wizard_id': wizard.id,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'lines': wizard.get_report_lines(),
            'gross_bill': wizard.gross_bill,
            'total_discount': wizard.total_discount,
            'total_expense': wizard.total_expense,
            'total_amount': wizard.total_amount,
        }

    @api.model
    def get_period_report_action(self, wizard_id, report_type):
        wizard = self.env['pharmacy.period.report.wizard'].browse(wizard_id).exists()
        if not wizard:
            return False

        if report_type == 'xlsx':
            return wizard.action_download_xlsx()

        return wizard.action_download_pdf()

    def _get_period_dates(self, period='today', start_date=False, end_date=False):
        today = fields.Date.context_today(self)

        if period == '7':
            return today - timedelta(days=6), today

        if period == '30':
            return today - timedelta(days=29), today

        if period == 'custom' and start_date and end_date:
            return fields.Date.to_date(start_date), fields.Date.to_date(end_date)

        return today, today

    def _get_sales_graph(self, today):
        graph_start = today - timedelta(days=13)

        sales = self.env['pharmacy.sale'].search([
            ('sale_date', '>=', graph_start),
            ('sale_date', '<=', today),
            ('state', '=', 'confirmed'),
        ])

        grouped = {}
        for sale in sales:
            key = fields.Date.to_string(sale.sale_date)
            grouped[key] = grouped.get(key, 0) + sale.total_amount

        graph = []
        current = graph_start

        while current <= today:
            key = fields.Date.to_string(current)
            graph.append({
                'date': key,
                'amount': grouped.get(key, 0),
            })
            current += timedelta(days=1)

        return graph

    def _medicine_rows(self, medicines):
        today = fields.Date.context_today(self)

        return [
            {
                'id': medicine.id,
                'name': medicine.name,
                'category': medicine.category_id.name if medicine.category_id else '',
                'stock': medicine.stock,
                'expiry_date': fields.Date.to_string(medicine.expiry_date),
                'remaining_days': (
                    (medicine.expiry_date - today).days
                    if medicine.expiry_date else 0
                ),
            }
            for medicine in medicines
        ]