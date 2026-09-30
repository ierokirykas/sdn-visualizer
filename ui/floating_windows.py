from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QWidget, QPushButton, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
                             QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout, QMainWindow, QFrame, QGroupBox,
                             QSlider,QGridLayout)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QCursor, QColor

from ui.device_panel import DevicePropertiesPanel
from ui.link_panel import LinkPropertiesPanel
from ui.theme import THEME

class FloatingPanel(QMainWindow):
    """Базовый класс для плавающих панелей"""
    def __init__(self, panel_widget, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Создаем основной контейнер с фоном
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.75);
                border-radius: 15px;
                border: 1px solid {THEME['bg_start']};
            }}
            
        """)

        # Создаем layout для контейнера
        container_layout = QVBoxLayout(self.container)

        # Создаем центральный виджет и layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем кнопку закрытия
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 150);
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        # Добавляем панель свойств
        self.panel = panel_widget

        # Устанавливаем прозрачный фон для панели
        if hasattr(self.panel, 'setStyleSheet'):
            self.panel.setStyleSheet("""
                TransparentPanel {
                    background-color: transparent;
                    border: none;
                    padding: 5px;
                }
                QGroupBox {
                    background-color: rgba(255, 255, 255, 0.5);
                    border-radius: 10px;
                    border: 1px solid #cccccc;
                    margin-top: 5px;
                    padding-top: 5px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border-radius: 5px;
                }
                QPushButton {
                    background-color: #cccccc;
                    color: #333333;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #aaaaaa;
                }
            """)
        
        layout.addWidget(self.close_btn, alignment=Qt.AlignRight)
        layout.addWidget(self.panel)
        # Добавляем содержимое в контейнер
        container_layout.addWidget(central_widget)

        self.setCentralWidget(self.container)
        
        # Для перемещения окна
        self.oldPos = None
        self.setStyleSheet("""
            FloatingPanel {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                border: 2px solid #cccccc;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging and self.oldPos is not None:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None
            self.dragging = False

class FloatingDevicePanel(FloatingPanel):
    """Плавающее окно свойств устройства"""
    def __init__(self, parent=None):
        super().__init__(DevicePropertiesPanel(), parent)
        # Соединяем сигнал закрытия панели с закрытием окна
        self.panel.close_requested.connect(self.close)

    def set_device(self, device, notifier):
        self.panel.set_device(device, notifier)

class FloatingLinkPanel(FloatingPanel):
    """Плавающее окно свойств связи"""
    def __init__(self, parent=None):
        super().__init__(LinkPropertiesPanel(), parent)
        # Соединяем сигнал закрытия панели с закрытием окна
        self.panel.close_requested.connect(self.close)

    def set_link(self, link, notifier):
        self.panel.set_link(link, notifier)

class FloatingDialog(QDialog):
    """Базовый класс для плавающих диалогов"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Создаем основной контейнер с фоном
        self.container = QWidget()
        self.container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 15px;
                border: 2px solid {THEME['surface']};
                padding: 3px;
                margin: 2px;
            }}
            QLabel {{
                color: {THEME['text_on_light']};
                font-weight: 500;
            }}
            
            QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid {THEME['surface']};
                border-radius: 5px;
                padding: 2px;
                color: {THEME['text_on_light']};
            }}
            
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {THEME['primary']};
                background-color: rgba(255, 255, 255, 0.85);
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
            QGroupBox {{
                background-color: white;
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
                background-color: white;
                border-radius: 5px;
            }}
        """)
        
        # Создаем layout для контейнера
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(5)
        
        # Устанавливаем контейнер как основной виджет
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.container)
        
        # Для перемещения окна
        self.oldPos = None
        self.dragging = False


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging and self.oldPos is not None:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.oldPos = None


class QoSDialog(FloatingDialog):
    """Плавающий диалог параметров QoS"""
    def __init__(self, parent=None, num_switches=0):
        super().__init__(parent)
        self.setWindowTitle("QoS Routing Parameters")
        self.resize(400, 500)  # Увеличим высоту для новых полей
        self.num_switches = num_switches
        
        # Добавляем стиль для формы
        self.container.setStyleSheet(self.container.styleSheet() + f"""
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
        """)

        # Загрузка предыдущих значений
        self.settings = QSettings("YourCompany", "SDNVisualizer")
        
        self.setup_ui()
        self.load_previous_values()
        self.update_ui()  # Первоначальное обновление интерфейса
    
    def setup_ui(self):
        # Получаем layout контейнера
        layout = self.container.layout()
        
        # Заголовок
        title = QLabel("<h3 style='color: #2c3e50;'>QoS Routing Parameters</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Группа выбора алгоритма
        algorithm_group = QGroupBox("Algorithm Selection")
        algorithm_layout = QFormLayout(algorithm_group)

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["MCP", "MCOP", "CSP", "LARAC","Fuzzy Logic"])
        self.algorithm_combo.currentTextChanged.connect(self.update_ui)
        algorithm_layout.addRow("Algorithm:", self.algorithm_combo)
        layout.addWidget(algorithm_group)
        
        # Группа выбора метрик
        metrics_group = QGroupBox("Metrics Selection")
        metrics_layout = QFormLayout(metrics_group)
        
        self.metric1_combo = QComboBox()
        self.metric1_combo.addItems(["Delay", "Packet Loss Rate", "Bandwidth"])
        self.metric1_combo.currentTextChanged.connect(self.update_ui)

        self.metric2_combo = QComboBox()
        self.metric2_combo.addItems(["Delay", "Packet Loss Rate", "Bandwidth"])
        self.metric2_combo.currentTextChanged.connect(self.update_ui)
        metrics_layout.addRow("Primary Metric:", self.metric1_combo)
        metrics_layout.addRow("Secondary Metric:", self.metric2_combo)
        layout.addWidget(metrics_group)
        
        # Группа параметров
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout(params_group)
        
        self.src_spin = QSpinBox()
        self.src_spin.setRange(0, self.num_switches - 1 if self.num_switches > 0 else 0)
        
        self.dst_spin = QSpinBox()
        self.dst_spin.setRange(0, self.num_switches - 1 if self.num_switches > 0 else 0)
        
        self.k_spin = QSpinBox()
        self.k_spin.setRange(1, 20)
        
        self.metric1_limit_spin = QDoubleSpinBox()
        self.metric1_limit_spin.setRange(0, 1000)
        
        self.metric2_limit_spin = QDoubleSpinBox()
        self.metric2_limit_spin.setRange(0, 100)
        
        self.lambda_spin = QDoubleSpinBox()
        self.lambda_spin.setRange(0, 10)
        self.lambda_spin.setSingleStep(0.1)
        
        params_layout.addRow("Source Switch (0-based):", self.src_spin)
        params_layout.addRow("Destination Switch (0-based):", self.dst_spin)
        params_layout.addRow("Number of Paths (k):", self.k_spin)
        params_layout.addRow("Primary Metric Limit:", self.metric1_limit_spin)
        params_layout.addRow("Secondary Metric Limit:", self.metric2_limit_spin)
        params_layout.addRow("Lambda (λ):", self.lambda_spin)
        
        layout.addWidget(params_group)
        
        # Группа нечеткой логики
        self.fuzzy_group = QGroupBox("Fuzzy Logic Parameters")
        fuzzy_layout = QGridLayout(self.fuzzy_group)
        
        # Веса метрик
        fuzzy_layout.addWidget(QLabel("Metrics Weights:"), 0, 0)
        
        self.delay_weight_slider = QSlider(Qt.Horizontal)
        self.delay_weight_slider.setRange(0, 100)
        self.delay_weight_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_weight_label = QLabel("Delay: 0.4")
        fuzzy_layout.addWidget(QLabel("Delay:"), 1, 0)
        fuzzy_layout.addWidget(self.delay_weight_slider, 1, 1)
        fuzzy_layout.addWidget(self.delay_weight_label, 1, 2)
        
        self.loss_weight_slider = QSlider(Qt.Horizontal)
        self.loss_weight_slider.setRange(0, 100)
        self.loss_weight_slider.setTickPosition(QSlider.TicksBelow)
        self.loss_weight_label = QLabel("Loss: 0.3")
        fuzzy_layout.addWidget(QLabel("Packet Loss:"), 2, 0)
        fuzzy_layout.addWidget(self.loss_weight_slider, 2, 1)
        fuzzy_layout.addWidget(self.loss_weight_label, 2, 2)
        
        self.bandwidth_weight_slider = QSlider(Qt.Horizontal)
        self.bandwidth_weight_slider.setRange(0, 100)
        self.bandwidth_weight_slider.setTickPosition(QSlider.TicksBelow)
        self.bandwidth_weight_label = QLabel("Bandwidth: 0.3")
        fuzzy_layout.addWidget(QLabel("Bandwidth:"), 3, 0)
        fuzzy_layout.addWidget(self.bandwidth_weight_slider, 3, 1)
        fuzzy_layout.addWidget(self.bandwidth_weight_label, 3, 2)
        
        # Подключаем слайдеры к обновлению меток
        self.delay_weight_slider.valueChanged.connect(self.update_fuzzy_weights)
        self.loss_weight_slider.valueChanged.connect(self.update_fuzzy_weights)
        self.bandwidth_weight_slider.valueChanged.connect(self.update_fuzzy_weights)
        
        # Параметры функций принадлежности
        fuzzy_layout.addWidget(QLabel("Membership Functions:"), 4, 0, 1, 3)
        
        self.quality_threshold_spin = QDoubleSpinBox()
        self.quality_threshold_spin.setRange(0, 1)
        self.quality_threshold_spin.setSingleStep(0.1)
        self.quality_threshold_spin.setValue(0.7)
        fuzzy_layout.addWidget(QLabel("Quality Threshold:"), 5, 0)
        fuzzy_layout.addWidget(self.quality_threshold_spin, 5, 1, 1, 2)
        
        layout.addWidget(self.fuzzy_group)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

    def update_fuzzy_weights(self):
        """Обновляет отображение весов нечеткой логики"""
        total = (self.delay_weight_slider.value() + 
                self.loss_weight_slider.value() + 
                self.bandwidth_weight_slider.value())
        
        if total > 0:
            delay_weight = self.delay_weight_slider.value() / total
            loss_weight = self.loss_weight_slider.value() / total
            bandwidth_weight = self.bandwidth_weight_slider.value() / total
            
            self.delay_weight_label.setText(f"Delay: {delay_weight:.2f}")
            self.loss_weight_label.setText(f"Loss: {loss_weight:.2f}")
            self.bandwidth_weight_label.setText(f"Bandwidth: {bandwidth_weight:.2f}")

    def update_ui(self):
        """Обновляет интерфейс в зависимости от выбранного алгоритма"""
        algorithm = self.algorithm_combo.currentText()
        
        # Скрываем все дополнительные поля сначала
        self.metric1_limit_spin.setVisible(False)
        self.metric2_limit_spin.setVisible(False)
        self.lambda_spin.setVisible(False)
        self.fuzzy_group.setVisible(False)

        # Показываем нужные поля в зависимости от алгоритма
        if algorithm == "MCP":
            self.metric1_limit_spin.setVisible(True)
            self.metric2_limit_spin.setVisible(True)
            self.metric1_limit_spin.setSuffix(" ms" if self.metric1_combo.currentText() == "Delay" else " %" if self.metric1_combo.currentText() == "Packet Loss Rate" else " Mbps")
            self.metric2_limit_spin.setSuffix(" ms" if self.metric2_combo.currentText() == "Delay" else " %" if self.metric2_combo.currentText() == "Packet Loss Rate" else " Mbps")
        elif algorithm == "MCOP":
            # Только выбор метрик, без ограничений
            pass
        elif algorithm == "CSP":
            self.metric2_limit_spin.setVisible(True)
            self.metric2_limit_spin.setSuffix(" ms" if self.metric2_combo.currentText() == "Delay" else " %" if self.metric2_combo.currentText() == "Packet Loss Rate" else " Mbps")
        elif algorithm == "LARAC":
            self.metric1_limit_spin.setVisible(True)
            self.metric2_limit_spin.setVisible(True)
            self.lambda_spin.setVisible(True)
            self.metric1_limit_spin.setSuffix(" ms" if self.metric1_combo.currentText() == "Delay" else " %" if self.metric1_combo.currentText() == "Packet Loss Rate" else " Mbps")
            self.metric2_limit_spin.setSuffix(" ms" if self.metric2_combo.currentText() == "Delay" else " %" if self.metric2_combo.currentText() == "Packet Loss Rate" else " Mbps")
        elif algorithm == "Fuzzy Logic":
            # # Скрываем стандартные ограничения и показываем параметры нечеткой логики
            # self.metric1_limit_spin.setVisible(False)
            # self.metric2_limit_spin.setVisible(False)
            # self.lambda_spin.setVisible(False)
            # self.fuzzy_group.setVisible(True)
            pass
            
    def load_previous_values(self):
        """Загружает предыдущие значения из настроек"""
        self.algorithm_combo.setCurrentText(
            self.settings.value("qos_algorithm", "MCP"))
        self.metric1_combo.setCurrentText(
            self.settings.value("qos_metric1", "Delay"))
        self.metric2_combo.setCurrentText(
            self.settings.value("qos_metric2", "Packet Loss Rate"))
        self.src_spin.setValue(self.settings.value("qos_src", 0, type=int))
        self.dst_spin.setValue(self.settings.value("qos_dst", min(1, self.num_switches - 1), type=int))
        self.k_spin.setValue(self.settings.value("qos_k", 4, type=int))
        self.metric1_limit_spin.setValue(self.settings.value("qos_metric1_limit", 100.0, type=float))
        self.metric2_limit_spin.setValue(self.settings.value("qos_metric2_limit", 10.0, type=float))
        self.lambda_spin.setValue(self.settings.value("qos_lambda", 1.0, type=float))

        # # Загружаем параметры нечеткой логики
        # self.delay_weight_slider.setValue(self.settings.value("fuzzy_delay_weight", 40, type=int))
        # self.loss_weight_slider.setValue(self.settings.value("fuzzy_loss_weight", 30, type=int))
        # self.bandwidth_weight_slider.setValue(self.settings.value("fuzzy_bandwidth_weight", 30, type=int))
        # self.quality_threshold_spin.setValue(self.settings.value("fuzzy_quality_threshold", 0.7, type=float))
        
        self.update_fuzzy_weights()
    
    def save_current_values(self):
        """Сохраняет текущие значения в настройки"""
        self.settings.setValue("qos_algorithm", self.algorithm_combo.currentText())
        self.settings.setValue("qos_metric1", self.metric1_combo.currentText())
        self.settings.setValue("qos_metric2", self.metric2_combo.currentText())
        self.settings.setValue("qos_src", self.src_spin.value())
        self.settings.setValue("qos_dst", self.dst_spin.value())
        self.settings.setValue("qos_k", self.k_spin.value())
        self.settings.setValue("qos_metric1_limit", self.metric1_limit_spin.value())
        self.settings.setValue("qos_metric2_limit", self.metric2_limit_spin.value())
        self.settings.setValue("qos_lambda", self.lambda_spin.value())

        # Сохраняем параметры нечеткой логики
        # self.settings.setValue("fuzzy_delay_weight", self.delay_weight_slider.value())
        # self.settings.setValue("fuzzy_loss_weight", self.loss_weight_slider.value())
        # self.settings.setValue("fuzzy_bandwidth_weight", self.bandwidth_weight_slider.value())
        # self.settings.setValue("fuzzy_quality_threshold", self.quality_threshold_spin.value())
    
    def accept(self):
        """Сохраняет значения перед закрытием"""
        self.save_current_values()
        super().accept()
    
    def get_qos_parameters(self):
        # Определяем, какие метрики выбраны
        metric1_type = self.metric1_combo.currentText().lower().replace(" ", "_")
        metric2_type = self.metric2_combo.currentText().lower().replace(" ", "_")
        # Добавляем специфичные параметры для каждого алгоритма
        params = {
            "algorithm": self.algorithm_combo.currentText().lower(),
            "src": self.src_spin.value(),
            "dst": self.dst_spin.value(),
            "k": self.k_spin.value(),
        }

        algorithm = self.algorithm_combo.currentText().lower()
        if algorithm == "fuzzy logic":
            # # Вычисляем нормализованные веса
            # total = (self.delay_weight_slider.value() + 
            #         self.loss_weight_slider.value() + 
            #         self.bandwidth_weight_slider.value())
            
            # if total > 0:
            #     params.update({
            #         "delay_weight": self.delay_weight_slider.value() / total,
            #         "loss_weight": self.loss_weight_slider.value() / total,
            #         "bandwidth_weight": self.bandwidth_weight_slider.value() / total,
            #         "quality_threshold": self.quality_threshold_spin.value()
            #     })
            # else:
            #     # Значения по умолчанию
            #     print(algorithm)
            #     params.update({
            #         "delay_weight": 0.4,
            #         "loss_weight": 0.3,
            #         "bandwidth_weight": 0.3,
            #         "quality_threshold": self.quality_threshold_spin.value()
            #     })
            pass
        else:
            params.update({
                "metric1_type": metric1_type,
                "metric2_type": metric2_type,
                "metric1_limit": self.metric1_limit_spin.value(),
                "metric2_limit": self.metric2_limit_spin.value(),
                "lambda_val": self.lambda_spin.value()
            })
        
        return params
        

        
    
class QoSResultsDialog(FloatingDialog):
    """Плавающий диалог результатов QoS"""
    def __init__(self, parent=None, routes=None, metric1_matrix=None, metric2_matrix=None, metric1_type="delay", metric2_type="packet_loss_rate"):
        super().__init__(parent)
        self.setWindowTitle("QoS Routing Results")
        self.resize(700, 400)
        
        self.routes = routes or []
        self.metric1_matrix = metric1_matrix or []
        self.metric2_matrix = metric2_matrix or []
        self.metric1_type = metric1_type
        self.metric2_type = metric2_type

        # Добавляем стиль для таблицы с непрозрачными элементами
        self.container.setStyleSheet(self.container.styleSheet() + f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid {THEME['surface']};
                border-radius: 5px;
                gridline-color: {THEME['surface']};
                padding: 0px;
            }}
            
            QTableWidget::item {{
                padding: 0px;
                border-bottom: 1px solid {THEME['surface']};
                background-color: white;
            }}
            QHeaderView::HeaderSection{{
                padding: 0px;
                font-size: 10pt;
            }}
            QHeaderView::section {{
                background-color: {THEME['primary']};
                color: {THEME['text_on_dark']};
                padding-bottom: 10px;
                border: none;
                font-weight: bold;
                font-size: 10pt;
            }}
            
            QTableWidget QTableCornerButton::section {{
                background-color: {THEME['primary']};
                border: none;
            }}
        """)

        self.setup_ui()
    
    def setup_ui(self):
        # Получаем layout контейнера
        layout = self.container.layout()
        
        # Заголовок с непрозрачным фоном
        title = QLabel("<h3 style='color: #2c3e50; background-color: rgba(255,255,255,0.5); padding: 5px; border-radius: 5px;'>QoS Routing Results</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        if not self.routes:
            no_routes_label = QLabel("No routes found satisfying the constraints")
            no_routes_label.setAlignment(Qt.AlignCenter)
            no_routes_label.setStyleSheet("background-color: rgba(255,255,255,0.5); padding: 5px; border-radius: 5px;")
            layout.addWidget(no_routes_label)
        else:
            # Создаем таблицу для отображения результатов
            table = QTableWidget()
            table.setColumnCount(5)
            
            # Увеличиваем размер заголовков
            horizontal_header = table.horizontalHeader()
            horizontal_header.setDefaultSectionSize(120)  # Ширина колонок
            horizontal_header.setMinimumHeight(35)  # Высота горизонтального заголовка
            
            vertical_header = table.verticalHeader()
            vertical_header.setDefaultSectionSize(30)  # Высота строк
            vertical_header.setMinimumWidth(40)  # Ширина вертикального заголовка

           # Обновляем заголовки колонок в зависимости от выбранных метрик
            metric1_label = self.metric1_type.replace("_", " ").title()
            metric2_label = self.metric2_type.replace("_", " ").title()
            
            table.setHorizontalHeaderLabels(["Route", "Path", f"Total {metric1_label}", f"Total {metric2_label}", "Success Rate"])
            
            table.setRowCount(len(self.routes))
            
            # Заполняем таблицу данными
            for i, route in enumerate(self.routes):
                # Вычисляем метрики для маршрута
                total_delay = 0
                success_rate = 1.0  # Начальный коэффициент успешной доставки (100%)
                
                for j in range(len(route) - 1):
                    u = route[j]
                    v = route[j + 1]
                    total_delay += self.metric1_matrix[u][v]
                    # Рассчитываем коэффициент успешной доставки для каждого звена
                    loss_fraction = self.metric2_matrix[u][v] / 100.0
                    success_rate *= (1 - loss_fraction)
                
                # Общий процент потерь
                total_loss = (1 - success_rate) * 100
                
                # Заполняем строку таблицы
                table.setItem(i, 0, QTableWidgetItem(f"{i + 1}"))
                table.setItem(i, 1, QTableWidgetItem(" → ".join(str(node + 1) for node in route)))
                table.setItem(i, 2, QTableWidgetItem(f"{total_delay:.1f} ms"))
                table.setItem(i, 3, QTableWidgetItem(f"{total_loss:.2f}%"))
                table.setItem(i, 4, QTableWidgetItem(f"{success_rate*100:.2f}%"))
            
            # Настраиваем внешний вид таблицы
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.resizeColumnsToContents()
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            # Устанавливаем альтернативные цвета строк
            table.setAlternatingRowColors(True)
            
            layout.addWidget(table)
        
        # Добавляем кнопку закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        
        layout.addWidget(button_box)