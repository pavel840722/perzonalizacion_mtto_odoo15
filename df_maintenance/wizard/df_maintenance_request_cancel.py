from odoo import models, fields, api
from datetime import datetime

class MaintenanceRequestCancel(models.TransientModel):
    _name = 'df.maintenance.request.cancel'
    _description = "Cancel Request"

    request_id = fields.Many2one('maintenance.request', 'Maintenance Request')
    cancellation_reasons = fields.Text(string="Reasons for cancellation")
    date_cancellation =fields.Date(string="Date of cancellation", required=True, default=datetime.now())

    def action_cancel_wizard(self):
        self.request_id.cancellation_reasons = self.cancellation_reasons
        self.request_id.date_cancellation = self.date_cancellation
        self.request_id.stage_id = 5
        for order in self.request_id.work_order_ids:
            order.state = 'cancelled'