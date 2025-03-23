from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ChatGPTConfig(models.Model):
    _name = 'chatgpt.config'
    _description = 'ChatGPT Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên cấu hình', required=True, tracking=True)
    api_key = fields.Char(string='API Key', required=True, tracking=True)
    model = fields.Selection([
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('gpt-4', 'GPT-4'),
        ('gpt-4-turbo-preview', 'GPT-4 Turbo')
    ], string='Model', default='gpt-3.5-turbo', required=True, tracking=True)
    max_tokens = fields.Integer(string='Số token tối đa', default=1000, tracking=True)
    temperature = fields.Float(string='Temperature', default=0.7, tracking=True)
    active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, tracking=True)

    @api.constrains('api_key')
    def _check_api_key(self):
        for record in self:
            if not record.api_key:
                raise ValidationError('API Key không được để trống!') 