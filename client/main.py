import sys
import os
import ctypes
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QSystemTrayIcon, QMenu)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
import logging
from client.config import Config
from client.connection import ClientConnection
from client.utils import is_admin, run_as_admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConnectionThread(QThread):
    """Поток для управления подключением"""
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url
        self.client = None
        self.running = True
    
    def run(self):
        try:
            self.status_update.emit("Connecting to server...")
            self.client = ClientConnection(self.server_url, self.status_update)
            self.client.connect()
            
            # Держим соединение активным
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self.running = False
        if self.client:
            self.client.disconnect()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.connection_thread = None
        self.config = Config()
        self.init_ui()
        
        # Системный трей
        self.tray_icon = None
        self.setup_tray_icon()
    
    def init_ui(self):
        self.setWindowTitle("Remote Access Client")
        self.setGeometry(300, 300, 600, 400)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Remote Access Client")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Поле ввода URL сервера
        layout.addWidget(QLabel("Server URL:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("https://your-server.onrender.com")
        self.server_input.setText(self.config.get('server_url', ''))
        layout.addWidget(self.server_input)
        
        # Кнопка подключения
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)
        
        # Статус
        layout.addWidget(QLabel("Status:"))
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(200)
        layout.addWidget(self.status_text)
        
        # Кнопка сворачивания в трей
        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.clicked.connect(self.hide)
        layout.addWidget(minimize_btn)
        
        central_widget.setLayout(layout)
        
        # Начальный статус
        self.update_status("Ready. Enter server URL and click Connect.")
    
    def setup_tray_icon(self):
        """Настройка иконки в системном трее"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Иконка (используем стандартную если нет custom)
            icon = QIcon()
            if os.path.exists('resources/icon.ico'):
                icon = QIcon('resources/icon.ico')
            
            self.tray_icon.setIcon(icon)
            
            # Контекстное меню
            tray_menu = QMenu()
            show_action = tray_menu.addAction("Show")
            show_action.triggered.connect(self.show)
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.quit_application)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Двойной клик для показа окна
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def toggle_connection(self):
        if self.connection_thread and self.connection_thread.isRunning():
            # Отключение
            self.update_status("Disconnecting...")
            self.connection_thread.stop()
            self.connection_thread.wait()
            self.connect_btn.setText("Connect")
            self.update_status("Disconnected")
        else:
            # Подключение
            server_url = self.server_input.text().strip()
            
            if not server_url:
                self.update_status("Error: Please enter server URL")
                return
            
            # Сохраняем URL
            self.config.set('server_url', server_url)
            self.config.save()
            
            # Запускаем подключение
            self.connection_thread = ConnectionThread(server_url)
            self.connection_thread.status_update.connect(self.update_status)
            self.connection_thread.error_occurred.connect(self.on_connection_error)
            self.connection_thread.start()
            
            self.connect_btn.setText("Disconnect")
    
    def update_status(self, message):
        """Обновление статуса"""
        self.status_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        logger.info(message)
    
    def on_connection_error(self, error):
        """Обработка ошибок подключения"""
        self.update_status(f"Error: {error}")
        self.connect_btn.setText("Connect")
        if self.connection_thread:
            self.connection_thread.stop()
    
    def quit_application(self):
        """Завершение приложения"""
        if self.connection_thread and self.connection_thread.isRunning():
            self.connection_thread.stop()
            self.connection_thread.wait()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.quit()
    
    def closeEvent(self, event):
        """Перехват закрытия окна"""
        event.ignore()
        self.hide()
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Remote Access Client",
                "Application minimized to tray",
                QSystemTrayIcon.Information,
                2000
            )


def main():
    # Проверка прав администратора
    if not is_admin():
        logger.warning("Not running as administrator. Requesting elevation...")
        run_as_admin()
        sys.exit(0)
    
    logger.info("Starting Remote Access Client as administrator")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Не закрываем при закрытии окна
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
