{
    'name': 'ChatGPT Zalo Connector',
    'version': '1.0',
    'category': 'Communication',
    'summary': 'Kết nối ChatGPT với Zalo OA',
    'description': """
        Module kết nối ChatGPT với Zalo OA
        =================================
        - Quản lý API key ChatGPT
        - Quản lý thông tin kết nối Zalo OA
        - Tự động trả lời tin nhắn Zalo bằng ChatGPT
    """,
    'author': 'Buzz',
    'website': 'https://buzz.com',
    'depends': ['base', 'mail'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/chatgpt_config_views.xml',
        'views/zalo_config_views.xml',
        'views/zalo_message_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 