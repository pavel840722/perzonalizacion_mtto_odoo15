from odoo import models, fields, api, _
import datetime
# import date
from datetime import datetime, date
from odoo.exceptions import ValidationError

class SuperviseWorkOrder(models.TransientModel):
    _name = 'df.supervise.work.order'

    work_order_id = fields.Many2one('df.maintenance.work.order', 'Orden de trabajo')
    verified_employee_id = fields.Many2one('hr.employee', 'Verified By')
    date_supervised = fields.Datetime('Supervised Date')
    completion = fields.Selection([('finished','Finished'),
                                   ('unfinished','Unfinished'),
                                   ('insolvable','Insolvable')],
                                   'Completion')
    observation = fields.Text('Observations')
    causes_not_finished = fields.Selection([('more_time', 'Ejecution for more time'),
                                   ('missing_parts', 'Lack of Spare Parts'),
                                    ('work_error', 'Work Incorrect')],
                                  'Causes Not Finished')

    def supervise(self):
        if self.completion and self.completion == 'unfinished':
            if self.date_supervised:
                if self.date_supervised > datetime.now():
                    raise ValidationError(_('The end date cannot be greater than the current date.'))
                elif self.date_supervised < self.work_order_id.date_start:
                    raise ValidationError(_('The end date cannot be minor than the start date.'))
            if self.causes_not_finished and self.causes_not_finished != 'missing_parts':
                    lines = []
                    vals_aux = (0, 0, {'verified_employee_id': self.verified_employee_id.id, 'completion':  self.completion,
                                       'date_supervised': self.date_supervised, 'observation': self.observation,
                                       'causes_not_finished': self.causes_not_finished})
                    lines.append(vals_aux)
                    self.work_order_id.sudo().write({'supervised_ids': lines})
            else:
                   date_str = self.date_supervised.strftime('%Y-%m-%d')
                   self.work_order_id.observation_final = "LA ORDEN SE CIERRA POR FALTA DE PIEZAS DE REPUESTO" \
                                                          "FECHA DE CIERRE:" + date_str + "."
                   self.work_order_id.state = 'finished'
                   self.work_order_id.completion = 'unfinished'
                   self.work_order_id.date_end = self.date_supervised
                   self.work_order_id.date_supervised = self.date_supervised

                   lines = []
                   vals_aux = (
                   0, 0, {'verified_employee_id': self.verified_employee_id.id, 'completion': self.completion,
                          'date_supervised': self.date_supervised, 'observation': self.observation,
                          'causes_not_finished': self.causes_not_finished})
                   lines.append(vals_aux)
                   self.work_order_id.sudo().write({'supervised_ids': lines})
                   # self.work_order_id.supervised_ids = lines

                   self.work_order_id.state = 'finished'




        else:
            for activity in self.work_order_id.activity_ids:
                if not activity.done and self.completion == 'finished':
                    raise ValidationError(_('All activities must be marked as done before supervising as completed.'))
            if self.completion == 'finished':
                for employee in self.work_order_id.employee_ids:
                    if employee.employee_id.id == False:
                        raise ValidationError(
                            _('All charge must be a employee asociated'))
            dic = {}
            if self.verified_employee_id:
                dic['verified_employee_id'] = self.verified_employee_id
            if self.date_supervised:
                if self.date_supervised > datetime.now():
                    raise ValidationError(_('The end date cannot be greater than the current date.'))
                elif self.date_supervised < self.work_order_id.date_start:
                    raise ValidationError(_('The end date cannot be minor than the start date.'))
                dic['date_supervised'] = self.date_supervised
            if self.completion:
                dic['completion'] = self.completion
            # if self.observation:
            #     dic['observation'] = self.observation

            lines = []
            vals_aux = (
                0, 0, {'verified_employee_id': self.verified_employee_id.id, 'completion': self.completion,
                       'date_supervised': self.date_supervised, 'observation': self.observation,
                       'causes_not_finished': self.causes_not_finished})
            lines.append(vals_aux)
            self.work_order_id.sudo().write({'supervised_ids': lines})


            self.work_order_id.sudo().write(dic)
            for product in self.work_order_id.product_ids:
                product.complete_order = True


    @api.onchange('completion')
    def _onchange_completion(self):
        if self.completion == 'finished' or self.completion == 'insolvable':
            self.causes_not_finished = False




