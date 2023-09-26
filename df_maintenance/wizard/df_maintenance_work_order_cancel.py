from odoo import models, fields, api
from datetime import datetime

class MaintenanceWorkOrderCancel(models.TransientModel):
    _name = 'df.maintenance.work.order.cancel'
    _description = "Cancel Work Order"

    work_order_id = fields.Many2one('df.maintenance.work.order', 'Orden de trabajo')
    cancellation_reasons = fields.Text(string="Motivos de la cancelación",required=True, default="")
    date_cancellation = fields.Date(string="Date of cancellation",required=True, default=datetime.now())


    def action_cancel_wizard(self):
        self.work_order_id.cancellation_reasons = self.cancellation_reasons
        self.work_order_id.date_cancellation = self.date_cancellation
        self.work_order_id.state = 'cancelled'
        self.work_order_id.request_id.check_orders('cancelled')
        #     self.work_order_id.request_id.stage_id = 4
        free = 0
        in_progress = 0
        finished = 0
        posted = 0
        history = 0
        for order in self.work_order_id.request_id.work_order_ids:
            if order.state == 'free':
                in_progress = 1
            if order.state == 'in_progress':
                in_progress = 1
            elif order.state == 'finished':
                finished = 1
            elif order.state == 'posted':
                posted = 1
            elif order.state == 'history':
                history = 1
        if free == 0 and in_progress == 0 and finished == 0 and posted == 0 and history == 0:
            self.work_order_id.request_id.stage_id = 4
        elif finished == 1 and in_progress == 0 and free == 0:
            self.work_order_id.request_id.stage_id = 3

