import json
import logging
import werkzeug

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class ZaloWebhookController(http.Controller):
    
    @http.route('/chatgpt_zalo_connector/webhook/<int:zalo_config_id>', type='json', auth='public', csrf=False, methods=['POST'])
    def zalo_webhook(self, zalo_config_id, **kwargs):
        """Xử lý webhook từ Zalo OA"""
        try:
            # Lấy thông tin gửi từ Zalo
            data = request.jsonrequest
            _logger.info("Nhận webhook từ Zalo: %s", json.dumps(data))
            
            # Kiểm tra cấu hình Zalo
            zalo_config = request.env['zalo.config'].sudo().browse(zalo_config_id)
            if not zalo_config.exists():
                _logger.error("Không tìm thấy cấu hình Zalo với ID: %s", zalo_config_id)
                return {'error': 'Invalid configuration'}
            
            # Xử lý sự kiện theo loại
            event_name = data.get('event_name')
            
            if event_name == 'user_send_text':
                # Xử lý tin nhắn văn bản
                return self._handle_user_message(zalo_config, data)
            
            return {'success': True}
            
        except Exception as e:
            _logger.exception("Lỗi xử lý webhook Zalo: %s", str(e))
            return {'error': str(e)}
    
    def _handle_user_message(self, zalo_config, data):
        """Xử lý tin nhắn từ người dùng Zalo"""
        try:
            sender_id = data.get('sender', {}).get('id')
            message = data.get('message', {}).get('text', '')
            
            if not sender_id or not message:
                _logger.error("Thiếu thông tin sender_id hoặc tin nhắn")
                return {'error': 'Missing sender or message'}
            
            # Tạo bản ghi tin nhắn mới
            zalo_message = request.env['zalo.message'].sudo().create({
                'zalo_user_id': sender_id,
                'user_message': message,
                'zalo_config_id': zalo_config.id
            })
            
            # Xử lý tin nhắn sẽ được thực hiện tự động trong create()
            
            return {'success': True}
            
        except Exception as e:
            _logger.exception("Lỗi xử lý tin nhắn Zalo: %s", str(e))
            return {'error': str(e)} 