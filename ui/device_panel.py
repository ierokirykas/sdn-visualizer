from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QFormLayout, QPushButton, QGroupBox, QSpinBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QColor
from core.models import DeviceType
from ui.theme import THEME
import logging
from core.scene import DevicePositionNotifier
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
                background-color: rgba(255, 255, 255, 0.9);
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


class DevicePropertiesPanel(TransparentPanel):

    properties_changed = pyqtSignal(str)
    close_requested = pyqtSignal()  # Добавляем новый сигнал

    def __init__(self, parent=None):
        super().__init__(parent)
        self.device = None
        self.notifier = DevicePositionNotifier()
        self.setMinimumWidth(300)
        
        # Основной лейаут
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Группа общих свойств
        self.general_group = QGroupBox("Общие свойства")
        general_layout = QFormLayout()
        
        self.id_label = QLabel()
        self.type_label = QLabel()
        
        general_layout.addRow("ID:", self.id_label)
        general_layout.addRow("Тип:", self.type_label)
        self.general_group.setLayout(general_layout)
        
        # Группа сетевых свойств
        self.network_group = QGroupBox("Сетевые параметры")
        network_layout = QFormLayout()
        
        self.ip_edit = QLineEdit()
        self.mac_edit = QLineEdit()
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        
        network_layout.addRow("IP адрес:", self.ip_edit)
        network_layout.addRow("MAC адрес:", self.mac_edit)
        network_layout.addRow("Порт:", self.port_spin)
        self.network_group.setLayout(network_layout)
        
        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_properties)
        self.save_button.setEnabled(False)
        
        layout.addWidget(self.general_group)
        layout.addWidget(self.network_group)
        layout.addWidget(self.save_button)
        layout.addStretch()
        
        self.setLayout(layout)
        logger.debug("Device properties panel initialized")
    
    def set_device(self, device, notifier=None):
        """Устанавливает устройство и его нотификатор"""
        self.device = device
        self.notifier = notifier  # Сохраняем нотификатор

        if not device:
            self.clear()
            return
            
        # Общие свойства
        self.id_label.setText(device.id)
        self.type_label.setText(device.type.value)
        
        # Сетевые свойства
        self.ip_edit.setText(device.ip)
        self.mac_edit.setText(device.mac)
        self.port_spin.setValue(device.port)
        self.ip_edit.setVisible(True)
        self.mac_edit.setVisible(True)
        self.port_spin.setVisible(True)
        
        
        # Показываем/скрываем поля в зависимости от типа устройства
        if device.type == DeviceType.HOST:
            self.port_spin.setVisible(False)
            self.network_group.layout().labelForField(self.port_spin).setVisible(False)
        elif device.type == DeviceType.CONTROLLER:
            self.mac_edit.setVisible(False)
            self.network_group.layout().labelForField(self.mac_edit).setVisible(False)
        else:  # Switch
            self.ip_edit.setVisible(False)
            self.mac_edit.setVisible(False)
            self.port_spin.setVisible(False)
            self.network_group.layout().labelForField(self.ip_edit).setVisible(False)
            self.network_group.layout().labelForField(self.mac_edit).setVisible(False)
            self.network_group.layout().labelForField(self.port_spin).setVisible(False)
        
        self.save_button.setEnabled(True)
        logger.debug(f"Panel set for device: {device.id}")
    
    def clear(self):
        """Очищает панель"""
        self.device = None
        self.id_label.setText("")
        self.type_label.setText("")
        self.ip_edit.clear()
        self.mac_edit.clear()
        self.port_spin.setValue(0)
        self.save_button.setEnabled(False)
        logger.debug("Panel cleared")
    
    def save_properties(self):
        """Сохраняет изменения свойств устройства"""
        if not self.device:
            return
            
        # Применяем изменения
        if self.device.type == DeviceType.HOST:
            self.device.ip = self.ip_edit.text()
            self.device.mac = self.mac_edit.text()
        elif self.device.type == DeviceType.CONTROLLER:
            self.device.ip = self.ip_edit.text()
            self.device.port = self.port_spin.value()
        
        logger.info(f"Properties updated for {self.device.id}")
        
        # Уведомляем об изменениях через нотификатор
        if self.notifier:
            self.notifier.propertiesChanged.emit(self.device)

        # Испускаем сигнал закрытия
        self.close_requested.emit()