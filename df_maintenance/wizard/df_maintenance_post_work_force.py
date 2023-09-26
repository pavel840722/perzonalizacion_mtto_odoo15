from odoo import models, fields, _, api
from datetime import datetime
from odoo.exceptions import ValidationError

class PostWorkForce(models.TransientModel):
    _name = 'df.post.work.force'

    closing_date = fields.Datetime('Closing date', required=True)

    # @api.onchange('closing_date')
    # def _onchange_closing_date(self):
    #     if self.closing_date and self.closing_date > datetime.now():
    #         raise ValidationError(_('The date cannot be greater than the current date'))

    def post_work_force(self):
        if self.closing_date > datetime.now():
            raise ValidationError(_('The date cannot be greater than the current date'))
        self.env['df.maintenance.work.order'].post_work_force(self.closing_date)
        if self.env.context['lang'] == 'es_ES':
            message_id = self.env['df.message.wizard'].create({'message': 'La acción fue completada.'})
        else:
            message_id = self.env['df.message.wizard'].create({'message': 'The action was completed.'})
        return {
            'name': _('Message'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'df.message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }