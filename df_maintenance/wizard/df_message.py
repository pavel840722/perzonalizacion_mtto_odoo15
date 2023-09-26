from odoo import models, fields, api

class MessageWizard(models.TransientModel):
    _name = 'df.message.wizard'
    _description = "Show Message"

    message = fields.Text('Message', required=True)


    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}