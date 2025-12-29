import socketio
import platform
import socket
import json
import logging
from client.ui_capture import UITreeCapture
from client.command_executor import CommandExecutor
from client.ui_interaction import UIInteraction

logger = logging.getLogger(__name__)


class ClientConnection:
    def __init__(self, server_url, status_callback=None):
        self.server_url = server_url
        self.status_callback = status_callback
        self.client_id = None
        
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=10,  # Увеличено
            reconnection_delay_max=30,
            request_timeout=120  # Добавлено - ждем 2 минуты
        )

        
        self.ui_capture = UITreeCapture()
        self.command_executor = CommandExecutor()
        self.ui_interaction = UIInteraction()
        
        self.setup_handlers()
    
    def update_status(self, message):
        """Обновление статуса"""
        logger.info(message)
        if self.status_callback:
            self.status_callback.emit(message)
    
    def setup_handlers(self):
        """Настройка обработчиков событий"""
        
        @self.sio.event
        def connect():
            self.update_status("Connected to server!")
            
            # Регистрация клиента
            info = {
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'capabilities': ['commands', 'ui_tree', 'ui_interaction']
            }
            
            self.sio.emit('register_client', {
                'client_id': None,
                'info': info
            })
        
        @self.sio.event
        def registered(data):
            self.client_id = data.get('client_id')
            self.update_status(f"Registered as: {self.client_id}")
        
        @self.sio.event
        def execute_command(data):
            """Выполнение команды"""
            command = data.get('command')
            controller_sid = data.get('controller_sid')
            
            self.update_status(f"Executing: {command[:50]}...")
            
            result = self.command_executor.execute(command)
            
            self.sio.emit('command_result', {
                'client_id': self.client_id,
                'controller_sid': controller_sid,
                'output': result['output'],
                'error': result['error'],
                'success': result['success']
            })
            
            self.update_status(f"Command completed: {'SUCCESS' if result['success'] else 'FAILED'}")
        
        @self.sio.event
        def capture_ui_tree(data):
            """Захват UI-дерева"""
            controller_sid = data.get('controller_sid')
            full = data.get('full', True)
            element_path = data.get('element_path')
            
            self.update_status("Capturing UI tree...")
            
            try:
                ui_tree = self.ui_capture.capture(
                    full=full,
                    element_path=element_path
                )
                
                compressed_data = self.ui_capture.compress(ui_tree)
                
                self.sio.emit('ui_tree_update', {
                    'client_id': self.client_id,
                    'ui_tree': compressed_data,
                    'compressed': True,
                    'delta': not full,
                    'timestamp': time.time()
                })
                
                self.update_status(f"UI tree sent ({len(compressed_data)} bytes compressed)")
                
            except Exception as e:
                logger.error(f"UI capture error: {e}")
                self.update_status(f"UI capture failed: {e}")
        
        @self.sio.event
        def ui_interact(data):
            """Взаимодействие с UI элементом"""
            controller_sid = data.get('controller_sid')
            element_path = data.get('element_path')
            action = data.get('action')
            params = data.get('params', {})
            
            self.update_status(f"UI interaction: {action} on {element_path}")
            
            try:
                result = self.ui_interaction.interact(element_path, action, params)
                
                self.sio.emit('command_result', {
                    'client_id': self.client_id,
                    'controller_sid': controller_sid,
                    'output': json.dumps(result),
                    'error': None,
                    'success': True
                })
                
                self.update_status("UI interaction completed")
                
            except Exception as e:
                logger.error(f"UI interaction error: {e}")
                self.sio.emit('command_result', {
                    'client_id': self.client_id,
                    'controller_sid': controller_sid,
                    'output': '',
                    'error': str(e),
                    'success': False
                })
        
        @self.sio.event
        def disconnect():
            self.update_status("Disconnected from server")
        
        @self.sio.event
        def connect_error(data):
            self.update_status(f"Connection error: {data}")
    
    def connect(self):
        """Подключение к серверу"""
        try:
            self.sio.connect(self.server_url)
            self.update_status("Connection established")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Отключение от сервера"""
        if self.sio.connected:
            self.sio.disconnect()
        self.update_status("Disconnected")

