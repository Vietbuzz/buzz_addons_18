import json
import logging
import requests
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ZaloMessage(models.Model):
    _name = 'zalo.message'
    _description = 'Zalo Message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(string='ID', readonly=True)
    zalo_user_id = fields.Char(string='Zalo User ID', required=True, tracking=True)
    user_message = fields.Text(string='Tin nhắn người dùng', required=True, tracking=True)
    chatgpt_response = fields.Text(string='Phản hồi từ ChatGPT', tracking=True)
    zalo_config_id = fields.Many2one('zalo.config', string='Cấu hình Zalo', required=True, tracking=True)
    state = fields.Selection([
        ('received', 'Đã nhận tin nhắn'),
        ('processed', 'Đã xử lý với ChatGPT'),
        ('sent', 'Đã gửi phản hồi cho Zalo'),
        ('failed', 'Gửi thất bại')
    ], string='Trạng thái', default='received', tracking=True)
    error_message = fields.Text(string='Thông báo lỗi', tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('zalo.message.sequence') or 'New'
        records = super(ZaloMessage, self).create(vals_list)
        # Tự động xử lý tin nhắn với ChatGPT khi tạo mới
        for record in records:
            record.process_with_chatgpt()
        return records
    
    def process_with_chatgpt(self):
        """Xử lý tin nhắn với ChatGPT và gửi phản hồi đến Zalo"""
        self.ensure_one()
        if not self.user_message:
            self.write({
                'state': 'failed',
                'error_message': 'Không có tin nhắn để xử lý'
            })
            return False
            
        try:
            # Lấy cấu hình ChatGPT
            chatgpt_config = self.zalo_config_id.chatgpt_config_id
            if not chatgpt_config:
                raise UserError(_('Không tìm thấy cấu hình ChatGPT cho Zalo OA này'))
                
            # Gọi API ChatGPT
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {chatgpt_config.api_key}'
            }
            
            data = {
                'model': chatgpt_config.model,
                'messages': [
                    {'role': 'user', 'content': self.user_message}
                ],
                'max_tokens': chatgpt_config.max_tokens,
                'temperature': chatgpt_config.temperature
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Lỗi API ChatGPT: {response.status_code} - {response.text}"
                self.write({
                    'state': 'failed',
                    'error_message': error_msg
                })
                _logger.error(error_msg)
                return False
                
            # Xử lý phản hồi từ ChatGPT
            result = response.json()
            chatgpt_reply = result['choices'][0]['message']['content']
            
            # Lưu phản hồi
            self.write({
                'chatgpt_response': chatgpt_reply,
                'state': 'processed'
            })
            
            # Gửi phản hồi đến Zalo
            self.send_to_zalo(chatgpt_reply)
            return True
            
        except Exception as e:
            error_msg = f"Lỗi xử lý ChatGPT: {str(e)}"
            self.write({
                'state': 'failed',
                'error_message': error_msg
            })
            _logger.exception(error_msg)
            return False
    
    def send_to_zalo(self, message):
        """Gửi tin nhắn đến người dùng Zalo"""
        self.ensure_one()
        try:
            zalo_config = self.zalo_config_id
            
            # Kiểm tra access token
            if not zalo_config.access_token or (zalo_config.token_expires_at and zalo_config.token_expires_at < datetime.now()):
                self._refresh_zalo_token()
            
            # Gọi API Zalo để gửi tin nhắn
            headers = {
                'Content-Type': 'application/json',
                'access_token': zalo_config.access_token
            }
            
            data = {
                'recipient': {
                    'user_id': self.zalo_user_id
                },
                'message': {
                    'text': message
                }
            }
            
            response = requests.post(
                f'https://openapi.zalo.me/v2.0/oa/message',
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = f"Lỗi API Zalo: {response.status_code} - {response.text}"
                self.write({
                    'state': 'failed',
                    'error_message': error_msg
                })
                _logger.error(error_msg)
                return False
            
            # Cập nhật trạng thái
            self.write({
                'state': 'sent'
            })
            return True
            
        except Exception as e:
            error_msg = f"Lỗi gửi tin nhắn Zalo: {str(e)}"
            self.write({
                'state': 'failed',
                'error_message': error_msg
            })
            _logger.exception(error_msg)
            return False
    
    def _refresh_zalo_token(self):
        """Làm mới access token Zalo"""
        self.ensure_one()
        zalo_config = self.zalo_config_id
        
        try:
            # Gọi API để lấy access token mới
            params = {
                'app_id': zalo_config.app_id,
                'app_secret': zalo_config.app_secret,
                'refresh_token': zalo_config.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.get(
                'https://oauth.zaloapp.com/v4/oa/access_token',
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                error_msg = f"Lỗi làm mới token Zalo: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise UserError(error_msg)
                
            result = response.json()
            access_token = result.get('access_token')
            refresh_token = result.get('refresh_token')
            expires_in = result.get('expires_in', 0)
            
            # Cập nhật token vào config
            expires_at = datetime.now().replace(second=0, microsecond=0)
            expires_at = expires_at.replace(second=expires_at.second + int(expires_in))
            
            zalo_config.write({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': expires_at
            })
            
            return True
            
        except Exception as e:
            error_msg = f"Lỗi làm mới token Zalo: {str(e)}"
            _logger.exception(error_msg)
            raise UserError(error_msg) 