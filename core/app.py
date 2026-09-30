from PyQt5.QtWidgets import QGraphicsView, QMessageBox
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from ui.theme import apply_theme
import sys
import logging

logger = logging.getLogger(__name__)

class SDNVisualizerApp(MainWindow):
    def __init__(self):
        try:
            logger.info("Initializing SDNVisualizerApp")
            super().__init__()
            
            # Настройка вида
            self.view.setRenderHint(QPainter.Antialiasing)
            self.view.setDragMode(QGraphicsView.RubberBandDrag)
            
            # Устанавливаем минимальный размер сцены, который будет расширяться по мере добавления элементов
            self.view.setSceneRect(0, 0, 1000, 600)
            
            # Настройка поведения прокрутки
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Автоматическое масштабирование при изменении размера окна
            self.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
            
            # Связываем тулбар со сценой
            self.toolbar.active_tool_changed.connect(self.scene.set_current_action)
            
            # Добавляем лог для проверки
            logger.debug("Application view setup complete")

            # Применяем тему
            apply_theme(self)
            
        except Exception as e:
            logger.critical(f"Initialization failed: {e}", exc_info=True)
            self.show_error("Fatal Error", f"Application initialization failed: {e}")
            sys.exit(1)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)