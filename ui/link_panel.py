# ui/link_panel.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QFormLayout, QPushButton, QGroupBox, QDoubleSpinBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QColor
from ui.theme import THEME
import logging

logger = logging.getLogger(__name__)

class TransparentPanel(QFrame):     
    """Полупрозрачная панель с закруглёнными углами"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Устанавливаем стиль с полупрозрачным фоном и закруглёнными углами
        self.setStyleSheet(f"""
            TransparentPanel {{
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 15px;
                border: 2px solid {THEME['surface']};
                padding: 15px;
            }}
            
            QGroupBox {{
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 10px;
                border: 1px solid {THEME['surface']};
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: {THEME['text_on_light']};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 5px;
            }}
            
            QLabel {{
                color: {THEME['text_on_light']};
                font-weight: 500;
            }}
            
            QLineEdit, QDoubleSpinBox {{
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid {THEME['surface']};
                border-radius: 5px;
                padding: 5px;
                color: {THEME['text_on_light']};
            }}
            
            QLineEdit:focus, QDoubleSpinBox:focus {{
                border: 2px solid {THEME['primary']};
                background-color: rgba(255, 255, 255, 0.95);
            }}
            
            QPushButton {{
                background-color: {THEME['surface']};
                color: {THEME['text_on_dark']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {THEME['primary']};
            }}
            
            QPushButton:disabled {{
                background-color: rgba(128, 128, 128, 0.5);
                color: rgba(128, 128, 128, 0.8);
            }}
        """)

class LinkPropertiesPanel(TransparentPanel):

    properties_changed = pyqtSignal(str)  # Сигнал при изменении свойств
    close_requested = pyqtSignal()  # Добавляем новый сигнал

    def __init__(self, parent=None):
        super().__init__(parent)
        self.link = None
        self.link_item = None  # Добавим ссылку на графический элемент
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Группа параметров связи
        self.properties_group = QGroupBox("Параметры связи")
        form_layout = QFormLayout()
        
        self.source_label = QLabel()
        self.target_label = QLabel()
        
        self.bandwidth_spin = QDoubleSpinBox()
        self.bandwidth_spin.setRange(0.1, 1000.0)
        self.bandwidth_spin.setSuffix(" Mbps")
        
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 1000.0)
        self.delay_spin.setSuffix(" ms")
        
        self.loss_spin = QDoubleSpinBox()
        self.loss_spin.setRange(0.0, 100.0)
        self.loss_spin.setSuffix(" %")
        
        form_layout.addRow("Источник:", self.source_label)
        form_layout.addRow("Назначение:", self.target_label)
        form_layout.addRow("Пропускная способность:", self.bandwidth_spin)
        form_layout.addRow("Задержка:", self.delay_spin)
        form_layout.addRow("Потери:", self.loss_spin)
        
        self.properties_group.setLayout(form_layout)
        
        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_properties)
        self.save_button.setEnabled(False)


        layout.addWidget(self.properties_group)
        layout.addWidget(self.save_button)
        layout.addStretch()
        
        self.setLayout(layout)
        logger.debug("Link properties panel initialized")
    
    def set_link(self, link,notifier=None):
        """Устанавливает связь и графический элемент для редактирования"""
        self.link = link
        if not link:
            self.clear()
            return
        self.source_label.setText(link.source)
        self.target_label.setText(link.target)
        self.bandwidth_spin.setValue(link.bandwidth)
        self.delay_spin.setValue(link.delay)
        self.loss_spin.setValue(link.loss)
        self.save_button.setEnabled(True)
        self.notifier = notifier  # Сохраняем нотификатор
        logger.debug(f"Panel set for link: {link.source}->{link.target}")
    
    def clear(self):
        """Очищает панель"""
        self.link = None
        self.source_label.setText("")
        self.target_label.setText("")
        self.bandwidth_spin.setValue(1.0)
        self.delay_spin.setValue(1.0)
        self.loss_spin.setValue(0.0)
        self.save_button.setEnabled(False)
        logger.debug("Link panel cleared")
    
    def save_properties(self):
        """Сохраняет изменения свойств связи"""
        if not self.link:
            return
            
        # Применяем изменения
        self.link.bandwidth = self.bandwidth_spin.value()
        self.link.delay = self.delay_spin.value()
        self.link.loss = self.loss_spin.value()
        
        logger.info(f"Properties updated for link {self.link.source}→{self.link.target}")

        # Уведомляем об изменениях через нотификатор
        if self.notifier:
            self.notifier.propertiesChanged.emit()

        # Уведомляем об изменениях
        self.properties_changed.emit(f"{self.link.source}-{self.link.target}")

        # Испускаем сигнал закрытия
        self.close_requested.emit()