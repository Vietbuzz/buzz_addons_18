from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ZaloConfig(models.Model):
    _name = 'zalo.config'
    _description = 'Zalo Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên cấu hình', required=True, tracking=True)
    app_id = fields.Char(string='App ID', required=True, tracking=True)
    app_secret = fields.Char(string='App Secret', required=True, tracking=True)
    oa_id = fields.Char(string='OA ID', required=True, tracking=True)
    access_token = fields.Char(string='Access Token', readonly=True, tracking=True)
    token_expires_at = fields.Datetime(string='Token hết hạn', readonly=True, tracking=True)
    active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, tracking=True)
    chatgpt_config_id = fields.Many2one('chatgpt.config', string='Cấu hình ChatGPT', required=True, tracking=True)
    webhook_url = fields.Char(string='Webhook URL', compute='_compute_webhook_url', readonly=True)

    @api.constrains('app_id', 'app_secret', 'oa_id')
    def _check_required_fields(self):
        for record in self:
            if not record.app_id:
                raise ValidationError('App ID không được để trống!')
            if not record.app_secret:
                raise ValidationError('App Secret không được để trống!')
            if not record.oa_id:
                raise ValidationError('OA ID không được để trống!')
    
    def _compute_webhook_url(self):
        """Tính toán URL webhook"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record._origin.id:
                record.webhook_url = f"{base_url}/chatgpt_zalo_connector/webhook/{record._origin.id}"
            else:
                record.webhook_url = "Lưu cấu hình để tạo webhook URL" 