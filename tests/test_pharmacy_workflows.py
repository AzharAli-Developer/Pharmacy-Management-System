import re

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPharmacyWorkflows(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['pharmacy.category'].create({
            'name': 'Test Category',
        })
        self.medicine = self.env['pharmacy.medicine'].create({
            'name': 'Test Medicine',
            'category_id': self.category.id,
            'sale_price': 100.0,
            'cost_price': 60.0,
            'stock': 10,
        })
        self.supplier = self.env['pharmacy.supplier'].create({
            'name': 'Test Supplier',
        })

    def test_pos_order_reduces_stock_and_creates_customer(self):
        result = self.env['pharmacy.sale'].confirm_order(
            [{'medicine_id': self.medicine.id, 'quantity': 2, 'discount_amount': 0}],
            customer_name='Test Customer',
            discount=0,
            tax_rate=0,
            payment_method='cash',
            amount_received=200,
        )
        sale = self.env['pharmacy.sale'].browse(result['sale_id'])
        self.assertEqual(sale.state, 'confirmed')
        self.assertEqual(self.medicine.stock, 8)
        self.assertTrue(sale.customer_id)
        self.assertEqual(sale.profit_amount, 80.0)
        self.assertEqual(sale.customer_id.total_medicines_purchased, 2)
        self.assertEqual(sale.customer_id.total_spent, 200.0)

    def test_pos_order_assigns_incrementing_default_customer_name(self):
        first = self.env['pharmacy.sale'].confirm_order(
            [{'medicine_id': self.medicine.id, 'quantity': 1, 'discount_amount': 0}],
            customer_name='',
            discount=0,
            tax_rate=0,
            payment_method='cash',
            amount_received=100,
        )
        second = self.env['pharmacy.sale'].confirm_order(
            [{'medicine_id': self.medicine.id, 'quantity': 1, 'discount_amount': 0}],
            customer_name='',
            discount=0,
            tax_rate=0,
            payment_method='cash',
            amount_received=100,
        )

        first_sale = self.env['pharmacy.sale'].browse(first['sale_id'])
        second_sale = self.env['pharmacy.sale'].browse(second['sale_id'])
        first_match = re.fullmatch(r'Customer(\d+)', first_sale.customer_name)
        second_match = re.fullmatch(r'Customer(\d+)', second_sale.customer_name)

        self.assertTrue(first_match)
        self.assertTrue(second_match)
        self.assertEqual(int(second_match.group(1)), int(first_match.group(1)) + 1)
        self.assertEqual(first_sale.customer_id.name, first_sale.customer_name)
        self.assertEqual(second_sale.customer_id.name, second_sale.customer_name)

    def test_discounted_pos_order_profit_uses_sale_minus_cost(self):
        result = self.env['pharmacy.sale'].confirm_order(
            [{'medicine_id': self.medicine.id, 'quantity': 2, 'discount_amount': 20}],
            customer_name='Discount Customer',
            discount=0,
            tax_rate=0,
            payment_method='cash',
            amount_received=180,
        )

        sale = self.env['pharmacy.sale'].browse(result['sale_id'])

        self.assertEqual(sale.total_amount, 180.0)
        self.assertEqual(sale.total_cost, 120.0)
        self.assertEqual(sale.profit_amount, 60.0)

    def test_period_report_summary_uses_sales_minus_cost(self):
        today = fields.Date.context_today(self.env['pharmacy.sale'])
        self.env['pharmacy.sale'].confirm_order(
            [{'medicine_id': self.medicine.id, 'quantity': 2, 'discount_amount': 0}],
            customer_name='Report Customer',
            discount=0,
            tax_rate=0,
            payment_method='cash',
            amount_received=200,
        )
        self.env['pharmacy.expense'].create({
            'name': 'Report Expense',
            'amount': 30.0,
            'date': today,
        })

        wizard = self.env['pharmacy.period.report.wizard'].create({
            'date_from': today,
            'date_to': today,
        })

        self.assertEqual(wizard.total_sales, 200.0)
        self.assertEqual(wizard.total_cost, 120.0)
        self.assertEqual(wizard.total_profit, 80.0)

    def test_purchase_confirm_increases_stock(self):
        purchase = self.env['pharmacy.purchase'].create({
            'supplier_id': self.supplier.id,
            'medicine_ids': [(0, 0, {
                'medicine_id': self.medicine.id,
                'quantity': 5,
                'price': 50.0,
                'batch_no': 'B001',
            })],
        })
        purchase.action_confirm_purchase()
        self.assertEqual(self.medicine.stock, 15)
        self.assertAlmostEqual(self.medicine.cost_price, 850.0 / 15.0)
        self.assertEqual(purchase.state, 'confirmed')
        self.assertTrue(self.env['pharmacy.medicine.batch'].search([
            ('medicine_id', '=', self.medicine.id),
            ('batch_no', '=', 'B001'),
        ]))

    def test_stock_adjustment_sets_new_quantity(self):
        adjustment = self.env['pharmacy.stock.adjustment'].create({
            'reason': 'count',
            'line_ids': [(0, 0, {
                'medicine_id': self.medicine.id,
                'new_quantity': 7,
            })],
        })
        adjustment.action_approve()
        self.assertEqual(self.medicine.stock, 7)
        self.assertEqual(adjustment.state, 'approved')
