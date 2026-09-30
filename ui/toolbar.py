from PyQt5.QtWidgets import QToolBar, QAction
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon
from core.models import DeviceType
import logging,os

logger = logging.getLogger(__name__)

class MainToolBar(QToolBar):
    # Сигнал об изменении активного инструмента
    active_tool_changed = pyqtSignal(str)
    link_display_mode_changed = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__("Tools", parent)
        self.parent = parent
        self.setMovable(False)
        self.setOrientation(Qt.Vertical)
        self.setIconSize(QSize(40, 40))
        
        # Текущий режим отображения связей
        self.link_display_mode = "delay"  # delay, bandwidth, loss, all

        # Получаем путь к папке с иконками
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_dir = os.path.join(base_dir, "..", "icons")
        
        # Создаем действия
        self._create_actions()
        logger.info("Toolbar initialized")

        

    def _create_actions(self):        
        # Файловые операции
        self.new_action = self._create_file_action(
            "new.svg", 
            "New (Ctrl+N)", 
            "NEW",
            "Ctrl+N"
        )
        self.new_action.triggered.connect(self.parent.new_file)
        
        self.open_action = self._create_file_action(
            "open.svg", 
            "Open (Ctrl+O)", 
            "OPEN",
            "Ctrl+O"
        )
        self.open_action.triggered.connect(self.parent.open_file)
        
        self.save_action = self._create_file_action(
            "save.svg", 
            "Save (Ctrl+S)", 
            "SAVE",
            "Ctrl+S"
        )
        self.save_action.triggered.connect(self.parent.save_file)
        # Действия для устройств
        self.addSeparator()
        self.device_actions = {}

        self.device_actions[DeviceType.HOST] = self._create_tool_action(
            "host.svg", 
            "Add Host (H)", 
            "ADD_HOST",
            "H"
        )
        self.device_actions[DeviceType.SWITCH] = self._create_tool_action(
            "switch.svg", 
            "Add Switch (W)", 
            "ADD_SWITCH",
            "W"
        )

        self.addSeparator()
        # Действие выбора
        self.select_action = self._create_tool_action(
            "select.svg", 
            "Select (S)", 
            "SELECT",
            "S"
        )

        # Действие для связей
        self.link_action = self._create_tool_action(
            "link.svg", 
            "Add Link (L)", 
            "ADD_LINK",
            "L"
        )

        self.connect_controller_action = self._create_tool_action(
            "controller.svg", 
            "Link to Controller", 
            "LINK_ALL",
            "Ctrl+k"
        )
        self.addSeparator()
    
        # Действие для запуска алгоритма сегментации
        self.algorithm_action = self._create_tool_action(
            "algorithm.svg", 
            "Run Segmentation Algorithm", 
            "ALGORITHM",
            "Ctrl+a"
        )
        self.algorithm_action.triggered.connect(self.parent.algorithm)
            
        self.addSeparator()
        # Действия экспорта с иконками
        self.export_xml_action = self._create_export_action(
            "xml_export.svg", 
            "Export XML", 
            "EXPORT_XML"
        )
        
        self.export_python_action = self._create_export_action(
            "python_export.svg", 
            "Export Python", 
            "EXPORT_PYTHON"
        )
        
        self.export_metric_action = self._create_export_action(
            "metric_export.svg", 
            "Export Metric Data", 
            "EXPORT_METRIC"
        )
        self.export_metric_action.triggered.connect(self.parent.export_metric)
        
        self.addSeparator()
        
        # Действие для переключения режима отображения связей
        self.display_mode_action = self._create_tool_action(
            "info.svg",  # Можно создать специальную иконку
            "Toggle Link Info (I)", 
            "TOGGLE_LINK_INFO",
            "I"
        )
        self.display_mode_action.triggered.connect(self.toggle_link_display_mode)

    def toggle_link_display_mode(self):
        """Переключает режим отображения информации на связях"""
        modes = ["delay", "bandwidth", "loss", "all"]
        current_index = modes.index(self.link_display_mode)
        next_index = (current_index + 1) % len(modes)
        self.link_display_mode = modes[next_index]
        
        # Отправляем сигнал об изменении режима
        self.link_display_mode_changed.emit(self.link_display_mode)
        logger.debug(f"Link display mode changed to: {self.link_display_mode}")
        
    def connect_to_controller(self):
        """Активирует функцию подключения к контроллеру в главном окне"""
        self.parent.connect_switches_to_controller()
    
        # Возвращаемся в режим выбора после создания связей
        self._set_active_tool("SELECT")
        
    def _create_file_action(self, icon_name, text, action_name, shortcut=None):
        """Создает действие для файловых операций"""
        icon_path = os.path.join(self.icon_dir, icon_name)
        
        if os.path.exists(icon_path):
            action = QAction(QIcon(icon_path), text, self)
        else:
            action = QAction(text, self)
            logger.warning(f"Icon not found: {icon_path}")
        
        action.setCheckable(False)
        if shortcut:
            action.setShortcut(shortcut)
        
        self.addAction(action)
        return action
    
    def _create_export_action(self, icon_name, text, action_name):
        """Создает действие для экспорта с иконкой"""
        icon_path = os.path.join(self.icon_dir, icon_name)
        
        if os.path.exists(icon_path):
            action = QAction(QIcon(icon_path), text, self)
        else:
            action = QAction(text, self)
            logger.warning(f"Icon not found: {icon_path}")
        
        action.setCheckable(False)
        self.addAction(action)
        return action
    
    def _create_tool_action(self, icon_name, text, tool_name, shortcut=None):
        """Создает действие для инструмента"""
        icon_path = os.path.join(self.icon_dir, icon_name)
        
        if os.path.exists(icon_path):
            action = QAction(QIcon(icon_path), text, self)
        else:
            action = QAction(text, self)
            logger.warning(f"Icon not found: {icon_path}")
        
        action.setCheckable(True)
        if shortcut:
            action.setShortcut(shortcut)
        
        action.triggered.connect(lambda: self._set_active_tool(tool_name))
        self.addAction(action)
        return action
    def _set_active_tool(self, tool):
        # Снимаем выделение со всех действий
        self.select_action.setChecked(False)
        for action in self.device_actions.values():
            action.setChecked(False)
        self.link_action.setChecked(False)
        
        # Устанавливаем выделение для текущего инструмента
        if tool == "SELECT":
            self.select_action.setChecked(True)
        elif tool == "ADD_LINK":
            self.link_action.setChecked(True)
        elif tool.startswith("ADD_"):
            device_type = tool.split("_")[1]
            if device_type == "HOST":
                self.device_actions[DeviceType.HOST].setChecked(True)
            elif device_type == "SWITCH":
                self.device_actions[DeviceType.SWITCH].setChecked(True)
            elif device_type == "CONTROLLER":
                self.device_actions[DeviceType.CONTROLLER].setChecked(True)
        elif tool == "LINK_ALL":
            self.connect_to_controller()
        elif tool == "RUN_ALGORITHM":
            self.parent.algorithm()
        # Отправляем сигнал об изменении инструмента
        self.active_tool_changed.emit(tool)
        logger.debug(f"Active tool set to: {tool}")