import io

from odoo import fields, http
from odoo.http import content_disposition, request
from odoo.tools.misc import xlsxwriter


class PharmacyReportController(http.Controller):

    @http.route('/pharmacy/sale/<int:sale_id>/receipt/print', type='http', auth='user')
    def print_sale_receipt(self, sale_id, **kwargs):
        sale = request.env['pharmacy.sale'].browse(sale_id).exists()
        if not sale:
            return request.not_found()
        html = request.env['ir.qweb']._render(
            'pharmacy_management_system.pharmacy_sale_receipt_print_page',
            {'sale': sale},
        )
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route('/pharmacy/report/<int:wizard_id>/xlsx', type='http', auth='user')
    def download_period_report_xlsx(self, wizard_id, **kwargs):
        wizard = request.env['pharmacy.period.report.wizard'].browse(wizard_id).exists()
        if not wizard:
            return request.not_found()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sales Report')

        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#E8EEF7', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        text_format = workbook.add_format({'border': 1})

        worksheet.write(0, 0, 'Pharmacy Sales Report', title_format)
        worksheet.write(1, 0, 'From')
        worksheet.write(1, 1, fields.Date.to_string(wizard.date_from))
        worksheet.write(1, 2, 'To')
        worksheet.write(1, 3, fields.Date.to_string(wizard.date_to))

        headers = ['Customer Name', 'Medicine Record', 'Total Bill', 'Discount']
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)

        row = 4
        for line in wizard.get_report_lines():
            worksheet.write(row, 0, line['patient'], text_format)
            worksheet.write(row, 1, line['medicines'], text_format)
            worksheet.write(row, 2, line['gross_amount'], money_format)
            worksheet.write(row, 3, line['discount_amount'], money_format)
            row += 1

        worksheet.write(row, 2, 'Gross Bill', header_format)
        worksheet.write(row, 3, wizard.gross_bill, money_format)
        row += 1
        worksheet.write(row, 2, 'Discount', header_format)
        worksheet.write(row, 3, wizard.total_discount, money_format)
        row += 1
        worksheet.write(row, 2, 'Expense', header_format)
        worksheet.write(row, 3, wizard.total_expense, money_format)
        row += 1
        worksheet.write(row, 2, 'Total Amount', header_format)
        worksheet.write(row, 3, wizard.total_amount, money_format)
        worksheet.set_column(0, 0, 22)
        worksheet.set_column(1, 1, 45)
        worksheet.set_column(2, 3, 16)
        workbook.close()
        output.seek(0)

        filename = 'pharmacy_sales_report_%s_%s.xlsx' % (
            fields.Date.to_string(wizard.date_from),
            fields.Date.to_string(wizard.date_to),
        )
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
