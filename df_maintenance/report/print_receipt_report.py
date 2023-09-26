# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_receipt_document'
    _description = 'Print Receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        print (self.env.context)

        docs = self.env['df.maintenance.work.order'].search([('id','=',data['order_id'])])
        stock_req_ids = []
        stock_ids = data['stock_req_ids']
        for record in stock_ids:
            stock_req_id = self.env['stock.request.order'].search([('id','=',record)])
            stock_req_ids.append(stock_req_id)

        return {
                'stock_req_ids': stock_req_ids,
                'order': docs,
        }

