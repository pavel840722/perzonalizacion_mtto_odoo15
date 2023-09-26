from odoo import api, fields, models, _, tools


class MaintenanceAccounts(models.Model):
    _name = 'df.maintenance.accounts'
    _description = 'Maintenance Accounts'

    name = fields.Char('Name')
    project = fields.Many2one('account.account', 'Project', require=True)
    service_transfer = fields.Many2one('account.account', 'Service transfer', require=True)
    workforce = fields.Many2one('account.account', 'Workforce', require = True)
    workforce_recovery = fields.Many2one('account.account', 'Workforce recovery', require=True)


