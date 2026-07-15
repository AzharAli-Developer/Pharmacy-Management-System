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
        week_start = today - timedelta(days=6)
        month_start = today.replace(day=1)

        sales = self.env['pharmacy.sale'].search([
            ('sale_date', '>=', date_from),
            ('sale_date', '<=', date_to),
            ('state', '=', 'confirmed'),
        ])

        expenses = self.env['pharmacy.expense'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        today_expenses = self.env['pharmacy.expense'].read_group(
            [('date', '=', today)],
            ['amount:sum'],
            [],
        )

        graph = self._get_sales_graph(today)

        expired = self.env['pharmacy.medicine'].search([
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today),
        ], order='expiry_date asc', limit=8)

        expiring_soon = self.env['pharmacy.medicine'].search([
            ('expiry_date', '>=', today),
            ('expiry_date', '<=', today + timedelta(days=15)),
            ('stock', '>', 0),
        ], order='expiry_date asc', limit=8)

        low_stock = self.env['pharmacy.medicine'].search([
            ('stock', '<=', 10),
        ], order='stock asc, name asc', limit=8)

        recent_orders = self.env['pharmacy.sale'].search([
            ('state', '=', 'confirmed'),
        ], order='sale_date desc, id desc', limit=8)

        return {
            'period': period,
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'cards': {
                'categories': self.env['pharmacy.category'].search_count([]),
                'medicines': self.env['pharmacy.medicine'].search_count([]),
                'orders': self.env['pharmacy.sale'].search_count([('state', '=', 'confirmed')]),
                'suppliers': self.env['pharmacy.supplier'].search_count([]),
                'expenses': sum(expenses.mapped('amount')),
                'sales': sum(sales.mapped('total_amount')),
                'cost': sum(sales.mapped('total_cost')),
                'today_sales': self._sum_sales(today, today),
                'today_expenses': today_expenses[0].get('amount', 0.0) if today_expenses else 0.0,
                'today_orders': self.env['pharmacy.sale'].search_count([
                    ('sale_date', '=', today),
                    ('state', '=', 'confirmed'),
                ]),
                'week_sales': self._sum_sales(week_start, today),
                'month_sales': self._sum_sales(month_start, today),
                'net_revenue': sum(sales.mapped('total_amount')) - sum(expenses.mapped('amount')),
                'low_stock': self.env['pharmacy.medicine'].search_count([('stock', '<=', 10)]),
                'expiring_soon': self.env['pharmacy.medicine'].search_count([
                    ('expiry_date', '>=', today),
                    ('expiry_date', '<=', today + timedelta(days=15)),
                    ('stock', '>', 0),
                ]),
                'purchases': self._sum_purchases(date_from, date_to),
                'customers': self._customer_count(),
            },
            'graph': graph,
            'expired': self._medicine_rows(expired),
            'expiring_soon': self._medicine_rows(expiring_soon),
            'low_stock': self._medicine_rows(low_stock),
            'recent_orders': self._sale_rows(recent_orders),
            'best_sellers': self._best_sellers(date_from, date_to),
            'purchase_summary': self._purchase_summary(date_from, date_to),
            'customer_summary': self._customer_summary(date_from, date_to),
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
            'total_tax': wizard.total_tax,
            'total_expense': wizard.total_expense,
            'total_amount': wizard.total_amount,
            'total_sales': wizard.total_sales,
            'total_cost': wizard.total_cost,
            'total_profit': wizard.total_profit,
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

    def _sum_sales(self, date_from, date_to):
        data = self.env['pharmacy.sale'].read_group(
            [
                ('sale_date', '>=', date_from),
                ('sale_date', '<=', date_to),
                ('state', '=', 'confirmed'),
            ],
            ['total_amount:sum'],
            [],
        )
        return data[0].get('total_amount', 0.0) if data else 0.0

    def _sum_purchases(self, date_from, date_to):
        data = self.env['pharmacy.purchase'].read_group(
            [
                ('purchase_date', '>=', date_from),
                ('purchase_date', '<=', date_to),
                ('state', '=', 'confirmed'),
            ],
            ['total_amount:sum'],
            [],
        )
        return data[0].get('total_amount', 0.0) if data else 0.0

    def _customer_count(self):
        return self.env['pharmacy.customer'].search_count([])

    def _sale_rows(self, sales):
        return [
            {
                'id': sale.id,
                'name': sale.name,
                'customer': sale.customer_name or 'Walk-in Customer',
                'sale_date': fields.Date.to_string(sale.sale_date),
                'total_amount': sale.total_amount,
                'items': sum(sale.medicine_ids.mapped('quantity')),
            }
            for sale in sales
        ]

    def _best_sellers(self, date_from, date_to):
        rows = self.env['pharmacy.sale.line'].read_group(
            [
                ('sale_id.sale_date', '>=', date_from),
                ('sale_id.sale_date', '<=', date_to),
                ('sale_id.state', '=', 'confirmed'),
            ],
            ['quantity:sum', 'total_amount:sum'],
            ['medicine_id'],
            orderby='quantity desc',
            limit=8,
        )
        return [
            {
                'medicine_id': row['medicine_id'][0] if row.get('medicine_id') else False,
                'name': row['medicine_id'][1] if row.get('medicine_id') else 'Unknown',
                'quantity': row.get('quantity', 0),
                'amount': row.get('total_amount', 0.0),
            }
            for row in rows
        ]

    def _purchase_summary(self, date_from, date_to):
        purchases = self.env['pharmacy.purchase'].search([
            ('purchase_date', '>=', date_from),
            ('purchase_date', '<=', date_to),
            ('state', '=', 'confirmed'),
        ])
        return {
            'count': len(purchases),
            'amount': sum(purchases.mapped('total_amount')),
        }

    def _customer_summary(self, date_from, date_to):
        sales = self.env['pharmacy.sale'].search([
            ('sale_date', '>=', date_from),
            ('sale_date', '<=', date_to),
            ('state', '=', 'confirmed'),
        ])
        names = {
            (sale.customer_name or '').strip().lower()
            for sale in sales
            if (sale.customer_name or '').strip()
        }
        return {
            'customers': len(names),
            'average_bill': (
                sum(sales.mapped('total_amount')) / len(sales)
                if sales else 0.0
            ),
        }

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
