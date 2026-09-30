from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsEllipseItem, 
                             QGraphicsTextItem,QGraphicsItem, QGraphicsLineItem, QMessageBox,
                             QMenu, QAction, QDialog, QGraphicsRectItem,QStyle, QMainWindow, 
                             QGraphicsSimpleTextItem, QGraphicsPathItem)
from PyQt5.QtCore import Qt, QLineF, QPointF, QObject, pyqtSignal, QRectF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QCursor, QPainterPath
from core.models import DeviceType, Device, Link
import logging, os
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from ui.theme import THEME



logger = logging.getLogger(__name__)

class LinkNotifier(QObject):
    """Вспомогательный класс для отправки сигналов об изменении связи"""
    propertiesChanged = pyqtSignal()

class DevicePositionNotifier(QObject):
    """Вспомогательный класс для отправки сигналов об изменении позиции"""
    positionChanged = pyqtSignal()
    propertiesChanged = pyqtSignal(object)  # Новый сигнал об изменении свойств

    def __init__(self, parent=None):
        super().__init__(parent)

class NetworkDeviceItem(QGraphicsEllipseItem):
    """Кастомный графический элемент для устройств сети"""
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.notifier = DevicePositionNotifier()  # Объект для отправки сигналов
        
        # Устанавливаем позицию элемента в сцене
        self.setPos(device.x, device.y)
        
        # Рисуем круг вокруг центра (позиция элемента теперь в центре)
        self.setRect(-20, -20, 40, 40)
        
        self.setPen(QPen(QColor(THEME["primary"]), 4))
        
        # Устанавливаем цвет в зависимости от типа устройства
        if device.type == DeviceType.HOST:
            self.setBrush(QBrush(QColor(0, 200, 0)))  # Зеленый
        elif device.type == DeviceType.SWITCH:
            self.setBrush(QBrush(QColor(0, 0, 200)))  # Синий
        elif device.type == DeviceType.CONTROLLER:
            self.setBrush(QBrush(QColor(200, 0, 0)))  # Красный
        
        # Настройка флагов
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges, True)
        self.setZValue(10)
    
    def itemChange(self, change, value):
        """Обновляем позицию устройства при перемещении"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Обновляем координаты устройства
            pos = self.scenePos()
            self.device.x = pos.x()
            self.device.y = pos.y()
            
            # Отправляем сигнал об изменении позиции
            self.notifier.positionChanged.emit()
        return super().itemChange(change, value)
    
class NetworkLinkItem(QGraphicsLineItem):
    """Кастомный графический элемент для связей сети"""
    def __init__(self, source_item, target_item, link_data, parent=None):
        super().__init__(parent)
        self.source_item = source_item
        self.target_item = target_item
        self.link_data = link_data
        self.text_item = None
        self.notifier = LinkNotifier()  # Создаем нотификатор

        # Режим отображения информации (по умолчанию - задержка)
        self.display_mode = "delay"

        # Подписываемся на изменения позиций устройств
        source_item.notifier.positionChanged.connect(self.update_position)
        target_item.notifier.positionChanged.connect(self.update_position)
        
        self.update_position()
        
        # Определяем стиль линии в зависимости от типа связи
        self.update_line_style()
        # Создаем текстовые элементы только для связей не с контроллером

        src_type = source_item.device.type
        dst_type = target_item.device.type
        
        if not ({src_type, dst_type} == {DeviceType.CONTROLLER, DeviceType.SWITCH}):
            self.create_text_items()

        # Подписываемся на изменения свойств связи
        self.notifier.propertiesChanged.connect(self.update_link_properties)

    def update_link_properties(self):
        """Обновляет графическое представление при изменении свойств"""
        self.update_line_style()  # Обновляем стиль линии
        self.update_text()        # Обновляем текст
        self.update_text_position()
            
    def create_text_items(self):
        """Создает текстовые элементы для отображения задержки"""
        self.text_item = QGraphicsSimpleTextItem(self)
        self.text_item.setBrush(QColor(THEME["text_on_light"]))
        self.text_item.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Создаем закругленный фон вместо прямоугольного
        self.text_bg = QGraphicsPathItem(self)
        self.text_bg.setBrush(QColor(THEME["chip"]))
        self.text_bg.setPen(QPen(Qt.NoPen))
        self.text_bg.setZValue(-1)  # Фон под текстом
        
        self.update_text()
        self.update_text_position()

    def update_line_style(self):
        """Определяет стиль линии в зависимости от типов устройств"""
        src_type = self.source_item.device.type
        dst_type = self.target_item.device.type
        
        # Для связей контроллер-коммутатор используем мягкий пунктир из темы
        if {src_type, dst_type} == {DeviceType.CONTROLLER, DeviceType.SWITCH}:
            pen = QPen(QColor(THEME["surface"]), 2, Qt.DashLine)
        else:
            # Для остальных связей - темная сплошная линия темы
            pen = QPen(QColor(THEME["primary_dark"]), 3)
        
        self.setPen(pen)
        self.setZValue(5)

    def get_center_position(self, item):
        """Возвращает центральную позицию элемента в координатах сцены"""
        # Получаем сценарную позицию (верхний левый угол)
        scene_pos = item.scenePos()
        
        # Получаем размеры элемента
        if isinstance(item, SvgDeviceItem):
            # Для SVG-элементов используем сохраненные размеры
            width = item.actual_width
            height = item.actual_height
        else:
            # Для других элементов используем boundingRect
            rect = item.boundingRect()
            width = rect.width()
            height = rect.height()
        
        # Рассчитываем центр
        center_x = scene_pos.x() + width / 2
        center_y = scene_pos.y() + height / 2
        
        return QPointF(center_x, center_y)
    
    def update_position(self):
        """Обновляет положение линии и текста"""
        # Получаем центральные позиции устройств
        start_center = self.get_center_position(self.source_item)
        end_center = self.get_center_position(self.target_item)
        
        # Устанавливаем новую линию
        self.setLine(QLineF(start_center, end_center))
        
        # Обновляем позицию текста (если есть)
        if hasattr(self, 'text_item') and self.text_item:
            self.update_text_position()
    
    def update_text_position(self):
        """Обновляет позицию текста и фона по центру линии"""
        if not hasattr(self, 'text_item') or not self.text_item:
            return
            
        line = self.line()
        center = line.pointAt(0.5)
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            center.x() - text_rect.width() / 2,
            center.y() - text_rect.height() / 2
        )
        # Обновляем фон
        if hasattr(self, 'text_bg') and self.text_bg:
            bg_rect = self.text_bg.boundingRect()
            self.text_bg.setPos(
                center.x() - bg_rect.width() / 2,
                center.y() - bg_rect.height() / 2
            )
    
    def update_text(self):
        """Обновляет текст с параметрами связи"""
        if not hasattr(self, 'text_item') or not self.text_item:
            return
            
        # Выбираем текст в зависимости от режима отображения
        if self.display_mode == "delay":
            text = f"{self.link_data.delay:.1f} ms"
        elif self.display_mode == "bandwidth":
            text = f"{self.link_data.bandwidth:.1f} Mbps"
        elif self.display_mode == "loss":
            text = f"{self.link_data.loss:.1f} %"
        else:  # all
            text = (
                f"{self.link_data.bandwidth:.1f}Mbps\n"
                f"{self.link_data.delay:.1f}ms\n"
                f"{self.link_data.loss:.1f}%"
            )
        
        self.text_item.setText(text)
        
        # Обновляем размер и форму фона с закругленными углами
        if hasattr(self, 'text_bg') and self.text_bg:
            text_rect = self.text_item.boundingRect()
            padding = 4
            width = text_rect.width() + padding * 2
            height = text_rect.height() + padding * 2
            radius = 10  # Радиус закругления углов
            
            # Создаем путь с закругленным прямоугольником
            path = QPainterPath()
            path.addRoundedRect(0, 0, width, height, radius, radius)
            self.text_bg.setPath(path)
            
            # Центрируем фон относительно текста
            self.text_bg.setPos(-padding, -padding)
        
    def set_display_mode(self, mode):
        """Устанавливает режим отображения информации на связи"""
        self.display_mode = mode
        self.update_text()
        self.update_text_position()

    def get_link_info(self):
        """Возвращает текстовое описание параметров связи"""
        return f"{self.link_data.bandwidth}Mbps\n{self.link_data.delay}ms\n{self.link_data.loss}%"
    
    def paint(self, painter, option, widget=None):
        """Добавляем визуальное выделение"""
        super().paint(painter, option, widget)
        
        # Рисуем выделение при выборе
        if option.state & QStyle.State_Selected:
            painter.save()
            pen = QPen(QColor(QColor(THEME["primary"])), 3, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.line())
            painter.restore()

    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика - открываем свойства связи"""
        # Передаем событие в сцену
        if self.scene():
            self.scene().link_double_clicked(self.link_data)
            
        super().mouseDoubleClickEvent(event)
    def set_highlight(self, highlighted, color=None):
        """Устанавливает или снимает выделение канала"""
        if highlighted and color:
            # Создаем толстую цветную линию для выделения
            pen = QPen(color, 6)  # Толстая линия
            self.setPen(pen)
            self.setZValue(10)  # Поверх других элементов
        else:
            # Возвращаем обычный стиль
            self.update_line_style()
            self.setZValue(5)  # Обычный уровень


class SvgDeviceItem(QGraphicsSvgItem):
    """Графический элемент устройства на основе SVG с корректным масштабированием"""
    def __init__(self, device, icon_path, desired_size=40, parent=None):
        super().__init__(parent)
        self.device = device
        self.desired_size = desired_size
        self.notifier = DevicePositionNotifier()
        # Разрешаем выделение
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        # Загружаем SVG-рендерер
        self.renderer = QSvgRenderer(icon_path)
        if not self.renderer.isValid():
            logger.error(f"Invalid SVG: {icon_path}")
        
        # Рассчитываем масштаб
        default_size = self.renderer.defaultSize()
        if default_size.width() > 0 and default_size.height() > 0:
            self.scale_factor = min(
                desired_size / default_size.width(),
                desired_size / default_size.height()
            )
        else:
            self.scale_factor = 1.0
            logger.warning(f"Invalid SVG size: {icon_path}")
        
        # Рассчитываем фактические размеры после масштабирования
        self.actual_width = default_size.width() * self.scale_factor
        self.actual_height = default_size.height() * self.scale_factor
        
        # Устанавливаем позицию (центр иконки)
        self.setPos(device.x - self.actual_width / 2, 
                    device.y - self.actual_height / 2)
        
        # Создаем текстовую метку с кратким ID
        if device.type == DeviceType.CONTROLLER:
            short_id = "c0"  # Всегда c0 для контроллера
        else:
            # Извлекаем числовую часть из ID
            num_part = ''.join(filter(str.isdigit, device.id))
            if num_part:
                if device.type == DeviceType.SWITCH:
                    short_id = f"s{num_part}"
                else:  # HOST
                    short_id = f"h{num_part}"
            else:
                short_id = device.id

        self.label = QGraphicsTextItem(short_id, self)
        self.label.setFont(QFont("Helvetica", 10, QFont.Bold))  # Увеличим шрифт и сделаем жирным
        self.label.setDefaultTextColor(QColor(THEME["text_on_light"]))
        
        # Центрируем текст под иконкой
        label_width = self.label.boundingRect().width()
        self.label.setPos(-label_width / 2 + 20, self.actual_height - 10)  # Центр по X, ниже по Y
        
        # Настройка флагов
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setZValue(10)
    
    def boundingRect(self):
        """Возвращает ограничивающий прямоугольник с учетом масштаба"""
        return QRectF(0, 0, self.actual_width, self.actual_height)
    
    def paint(self, painter, option, widget=None):
        """Добавляем визуальное выделение"""
        super().paint(painter, option, widget)
        
        # Если элемент выделен - рисуем рамку
        if option.state & QStyle.State_Selected:
            painter.save()
            pen = QPen(QColor(THEME["primary"]), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())
            painter.restore()
        """Отрисовывает SVG с учетом масштабирования"""
        if not self.renderer.isValid():
            return
        painter.save()
        
        # Применяем масштабирование
        painter.scale(self.scale_factor, self.scale_factor)
        
        # Отрисовываем SVG
        self.renderer.render(painter, QRectF(0, 0, 
                                            self.renderer.defaultSize().width(),
                                            self.renderer.defaultSize().height()))
        
        painter.restore()
    
    def itemChange(self, change, value):
        """Обновляем позицию устройства при перемещении"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Обновляем координаты устройства (центр иконки)
            pos = self.scenePos()
            self.device.x = pos.x() + self.actual_width / 2
            self.device.y = pos.y() + self.actual_height / 2
            
            # Обновляем позицию текста
            label_width = self.label.boundingRect().width()
            self.label.setPos(-label_width / 2 + 20, self.actual_height - 10)  # Центр по X, ниже по Y
            
            # Отправляем сигнал об изменении позиции
            self.notifier.positionChanged.emit()
        return super().itemChange(change, value)
    
    def get_notifier(self):
        """Возвращает нотификатор устройства"""
        return self.notifier
    
    def set_highlight(self, highlighted, color=QColor(THEME["primary"])):
        """Устанавливает или снимает выделение устройства заданным цветом"""
        if highlighted:
            # Удаляем старое выделение, если есть
            if hasattr(self, 'highlight'):
                self.scene().removeItem(self.highlight)
            
            # Создаем цветную рамку выделения
            self.highlight = QGraphicsRectItem(
                -5, -5, 
                self.actual_width + 10, 
                self.actual_height + 10, 
                self
            )
            pen = QPen(color, 4)
            self.highlight.setPen(pen)
            self.highlight.setZValue(9)  # Ниже основного элемента
        else:
            # Удаляем рамку выделения
            if hasattr(self, 'highlight'):
                self.scene().removeItem(self.highlight)
                del self.highlight

class NetworkScene(QGraphicsScene):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = {}
        self.links = {}
        self.current_action = "SELECT"
        self.temp_line = None
        self.link_start_device = None
        self.link_start_item = None
        self.device_items = {}  # Словарь для хранения графических элементов устройств
        self.link_items = {}    # Словарь для хранения графических элементов связей
        self.setBackgroundBrush(QBrush(QColor(THEME["bg_start"])))
        self.link_hover_device = False

        # Размер иконок устройств
        self.device_icon_size = 50  # Пикселей

        # Путь к иконкам
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_dir = os.path.join(base_dir, "..", "icons")
        
        # Соответствие типов устройств и файлов иконок
        self.device_icons = {
            DeviceType.HOST: "host.svg",
            DeviceType.SWITCH: "switch.svg",
            DeviceType.CONTROLLER: "controller.svg"
        }
    def set_current_action(self, action):
        """Устанавливает текущее действие из тулбара"""
        self.current_action = action
        logger.debug(f"Scene action changed to: {action}")
        
        # Сброс временных объектов при смене инструмента
        self.reset_link_creation()

        # Путь к иконкам
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_dir = os.path.join(base_dir, "..", "icons")

        # Соответствие типов устройств и файлов иконок
        self.device_icons = {
            DeviceType.HOST: "host.svg",
            DeviceType.SWITCH: "switch.svg",
            DeviceType.CONTROLLER: "controller.svg"
        }

        # Меняем курсор в зависимости от режима
        view = self.views()[0] if self.views() else None
        if view:
            if action == "SELECT":
                view.setCursor(Qt.ArrowCursor)
                self.set_items_movable(True)
            elif action == "ADD_LINK":
                view.setCursor(Qt.PointingHandCursor)
                self.set_items_movable(False)
            else:
                view.setCursor(Qt.CrossCursor)
                self.set_items_movable(False)

    def set_items_movable(self, movable):
        """Устанавливает возможность перемещения для всех устройств"""
        for item in self.device_items.values():
            item.setFlag(QGraphicsItem.ItemIsMovable, movable)

    def reset_link_creation(self):
        """Сбрасывает состояние создания связи"""
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
        
        # Сбрасываем выделение начального устройства
        if self.link_start_item:
            if isinstance(self.link_start_item, SvgDeviceItem):
                # Для SVG-элементов
                self.link_start_item.set_highlight(False)
            else:
                # Для старых элементов
                self.link_start_item.setPen(QPen(Qt.black, 2))
            
            self.link_start_item = None
        
        self.link_start_device = None
    def get_device_amount(self,device_type):
        count = 0
        for device in self.devices.values():
            if device.type == device_type:
                count += 1
        return count
    def add_device(self, device_type, x, y):
        #print(device_type, x, y)
        """Добавляет новое устройство на сцену с автоматической генерацией IP/MAC"""
        try:
            count = self.get_device_amount(device_type) + 1
            # Генерируем уникальный ID устройства
            device_id = f"{device_type.value.lower()}{count}"
            logger.debug(f"Adding device: {device_id} at ({x}, {y})")
            # Генерация IP и MAC только для хостов
            ip = ""
            mac = ""
            port = 0
            if device_type == DeviceType.HOST:
                # Подсчитываем количество хостов
                ip = f"10.0.0.{count}"
                mac = f"00:00:00:00:00:{count:02x}"
            
            elif device_type == DeviceType.CONTROLLER:
                ip = f"127.0.0.{count}"
                port = 6653 + count - 1
            
            device = Device(
                id=device_id,
                type=device_type,
                x=x,
                y=y,
                ip=ip,
                mac=mac,
                port=port
            )
            self.devices[device_id] = device

            # Создаем графическое представление
            self.create_device_graphics(device)
            
            return device
        except Exception as e:
            logger.error(f"Error adding device: {e}")
            return None

    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        try:
            pos = event.scenePos()
            
            # Режим добавления устройства
            if self.current_action.startswith("ADD_"):
                device_type_str = self.current_action.split("_")[1]
                device_type = {
                    "HOST": DeviceType.HOST,
                    "SWITCH": DeviceType.SWITCH,
                    "CONTROLLER": DeviceType.CONTROLLER
                }.get(device_type_str)
                
                if device_type:
                    self.add_device(device_type, pos.x(), pos.y())
                    return
            
            # Режим добавления связи
            if self.current_action == "ADD_LINK":
                # Находим устройство под курсором
                for item in self.items(pos):
                    # ИСПРАВЛЕНИЕ: проверяем как SvgDeviceItem, так и другие возможные типы
                    if isinstance(item, SvgDeviceItem) or (hasattr(item, 'device') and isinstance(item.device, Device)):
                        device = item.device if isinstance(item, SvgDeviceItem) else item.data(0)
                        
                        # Запрещаем выбор контроллера как начальной точки
                        if device.type == DeviceType.CONTROLLER:
                            QMessageBox.warning(
                                self.views()[0] if self.views() else None,
                                "Invalid Selection",
                                "Cannot link to controller. Use the 'Connect to Controller' button."
                            )
                            return
                        
                        # Если это первое устройство для связи
                        if not self.link_start_device:
                            self.link_start_device = device
                            self.link_start_item = item
                            # Выделяем устройство
                            if isinstance(item, SvgDeviceItem):
                                item.set_highlight(True)
                            else:
                                # Для старых элементов используем setPen
                                item.setPen(QPen(Qt.red, 3))
                            logger.debug(f"Link started from: {device.id}")
                            # Меняем курсор на крест
                            if self.views():
                                self.views()[0].setCursor(Qt.CrossCursor)
                        # Если это второе устройство
                        elif device != self.link_start_device:
                            # Создаем связь
                            self.add_link(self.link_start_device.id, device.id)
                            logger.debug(f"Link created: {self.link_start_device.id} -> {device.id}")
                            # Сбрасываем состояние
                            self.reset_link_creation()
                            # Возвращаем курсор
                            if self.views():
                                self.views()[0].setCursor(Qt.PointingHandCursor)
                        return
                # Клик на пустой области - сброс
                self.reset_link_creation()
                if self.views():
                    self.views()[0].setCursor(Qt.PointingHandCursor)
                return
            
            # Режим SELECT - передаем обработку базовому классу
            super().mousePressEvent(event)
            
        except Exception as e:
            logger.error(f"Mouse press error: {e}")
            self.reset_link_creation()

    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика мышью"""
        try:
            pos = event.scenePos()
            
            # Проверяем, кликнули ли на тексте связи
            for item in self.items(pos):
                if isinstance(item, (QGraphicsSimpleTextItem, QGraphicsRectItem)):
                    if isinstance(item.parentItem(), NetworkLinkItem):
                        # Получаем главное окно
                        view = self.views()[0] if self.views() else None
                        if view and hasattr(view, "window") and callable(view.window):
                            main_window = view.window()
                            if isinstance(main_window, QMainWindow):
                                # Открываем свойства связи
                                link_item = item.parentItem()
                                if hasattr(main_window, "show_floating_link_properties"):
                                    main_window.show_floating_link_properties(link_item.link_data, link_item.notifier)
                        return
                elif isinstance(item, NetworkLinkItem):
                    # Получаем главное окно
                    view = self.views()[0] if self.views() else None
                    if view and hasattr(view, "window") and callable(view.window):
                        main_window = view.window()
                        if isinstance(main_window, QMainWindow):
                            # Открываем свойства связи
                            if hasattr(main_window, "show_floating_link_properties"):
                                main_window.show_floating_link_properties(item.link_data, item.notifier)
                    return
                elif isinstance(item, SvgDeviceItem):
                    # Получаем главное окно через цепочку родителей
                    view = self.views()[0] if self.views() else None
                    if view and hasattr(view, "window") and callable(view.window):
                        main_window = view.window()
                        if isinstance(main_window, QMainWindow):
                            # Вызываем метод главного окна
                            if hasattr(main_window, "show_floating_device_properties"):
                                main_window.show_floating_device_properties(item.device, item.get_notifier())
                    return
            
            super().mouseDoubleClickEvent(event)
        except Exception as e:
            logger.error(f"Double click error: {e}")
    
    def handle_right_click(self, pos):
        """Обработка правого клика - контекстное меню"""
        try:
            # Ищем устройство в точке клика
            self.selected_device = None
            for item in self.items(pos):
                if isinstance(item, SvgDeviceItem):
                    self.selected_device = item.device
                    break
                elif isinstance(item, QGraphicsEllipseItem) and item.data(0):
                    self.selected_device = item.data(0)
                    break
            
            if self.selected_device:
                # Создаем контекстное меню
                menu = QMenu()
        
                # Действие для открытия свойств
                properties_action = QAction("Свойства", self)
                properties_action.triggered.connect(self.open_properties_panel)
                menu.addAction(properties_action)
                
                menu.exec_(self.views()[0].mapToGlobal(pos.toPoint()))
        except Exception as e:
            logger.error(f"Context menu error: {e}")
    
    def open_properties_panel(self):
        """Открывает панель свойств для выбранного устройства"""
        if not self.selected_device:
            return
            
        # Получаем главное окно через цепочку родителей
        view = self.views()[0] if self.views() else None
        if not view or not hasattr(view, "window") or not callable(view.window):
            return
            
        main_window = view.window()
        if not isinstance(main_window, QMainWindow):
            return
            
        # Получаем графический элемент устройства
        device_item = self.device_items.get(self.selected_device.id)
        if device_item:
            # Для новых SVG-элементов
            main_window.show_device_properties(
                self.selected_device, 
                device_item.get_notifier()
            )
        else:
            # Для старых элементов создаем временный нотификатор
            notifier = DevicePositionNotifier()
            main_window.show_device_properties(self.selected_device, notifier)

    def handle_device_properties_changed(self, device):
        """Обрабатывает изменения свойств устройства"""
        logger.info(f"Properties changed for device: {device.id}")
        # Можно добавить дополнительную логику, например:
        # - Обновление статусбара
        # - Отметка о сохранении
        # - Перерисовка связанных элементов
    
    def update_device_graphics(self, device):
        """Обновляет графическое представление устройства"""
        try:
            # Удаляем старое представление
            if device.id in self.device_items:
                old_item = self.device_items[device.id]
                self.removeItem(old_item)
            
            # Создаем новое представление
            icon_file = self.device_icons.get(device.type)
            if icon_file:
                icon_path = os.path.join(self.icon_dir, icon_file)
                device_item = SvgDeviceItem(
                    device, 
                    icon_path, 
                    desired_size=self.device_icon_size
                )
                self.addItem(device_item)
                self.device_items[device.id] = device_item
                
                # Добавляем текстовую метку
                text_item = QGraphicsTextItem(device.id)
                text_item.setFont(QFont("Arial", 10))
                text_item.setPos(device.x - 20, device.y + self.device_icon_size / 2 + 5)
                text_item.setZValue(11)
                self.addItem(text_item)
            
            logger.info(f"Graphics updated for device: {device.id}")
        except Exception as e:
            logger.error(f"Error updating device graphics: {e}")

    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши"""
        try:
            # Режим добавления связи - обновляем временную линию
            if self.current_action == "ADD_LINK" and self.link_start_item:
                # Получаем центр начального устройства
                start_center = self.get_center_position(self.link_start_item)
                
                # Обновляем линию до текущей позиции мыши
                if not self.temp_line:
                    # Создаем временную линию от центра к курсору
                    self.temp_line = QGraphicsLineItem(
                        QLineF(start_center, event.scenePos()))
                    self.temp_line.setPen(QPen(QColor(THEME["primary"]), 2, Qt.DashLine))
                    self.addItem(self.temp_line)
                else:
                    # Обновляем существующую линию
                    line = self.temp_line.line()
                    line.setP2(event.scenePos())
                    self.temp_line.setLine(line)
                return
            
            # Для других режимов передаем обработку базовому классу
            super().mouseMoveEvent(event)
            
        except Exception as e:
            logger.error(f"Mouse move error: {e}")
            self.reset_link_creation()
    
    def get_center_position(self, item):
        """Возвращает центральную позицию элемента в координатах сцены"""
        # Получаем сценарную позицию (верхний левый угол)
        scene_pos = item.scenePos()
        
        # Получаем размеры элемента
        if isinstance(item, SvgDeviceItem):
            # Для SVG-элементов используем сохраненные размеры
            width = item.actual_width
            height = item.actual_height
        else:
            # Для других элементов используем boundingRect
            rect = item.boundingRect()
            width = rect.width()
            height = rect.height()
        
        # Рассчитываем центр
        center_x = scene_pos.x() + width / 2
        center_y = scene_pos.y() + height / 2
        
        return QPointF(center_x, center_y)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        try:
            # Режим SELECT - передаем обработку базовому классу
            super().mouseReleaseEvent(event)
            
        except Exception as e:
            logger.error(f"Mouse release error: {e}")
            self.reset_link_creation()

    def get_selected_devices(self):
        """Возвращает список выделенных устройств"""
        selected_devices = []
        for item in self.selectedItems():
            # Для новых SVG-элементов
            if isinstance(item, SvgDeviceItem):
                selected_devices.append(item.device)
            # Для старых элементов (обратная совместимость)
            elif hasattr(item, 'data') and item.data(0) and isinstance(item.data(0), Device):
                selected_devices.append(item.data(0))
        return selected_devices
    
    def delete_devices(self, devices):
        """Удаляет несколько устройств"""
        try:
            # Собираем все ID устройств для удаления
            device_ids = [device.id for device in devices]
            
            # Удаляем связи, связанные с этими устройствами
            links_to_remove = []
            for link_id, link in self.links.items():
                if link.source in device_ids or link.target in device_ids:
                    links_to_remove.append(link_id)
            
            for link_id in links_to_remove:
                # Удаляем графическое представление связи
                if link_id in self.link_items:
                    link_item = self.link_items[link_id]
                    self.removeItem(link_item)
                    del self.link_items[link_id]
                del self.links[link_id]
            
            # Удаляем сами устройства
            for device in devices:
                device_id = device.id
                # Удаляем графическое представление устройства
                if device_id in self.device_items:
                    device_item = self.device_items[device_id]
                    self.removeItem(device_item)
                    del self.device_items[device_id]
                # Удаляем из словаря устройств
                if device_id in self.devices:
                    del self.devices[device_id]
            
            logger.info(f"Deleted {len(devices)} devices")
        except Exception as e:
            logger.error(f"Error deleting devices: {e}")
    
    # Обновим старый метод для совместимости
    def delete_selected_device(self):
        """Удаляет устройство, выбранное в контекстном меню"""
        if self.selected_device:
            self.delete_devices([self.selected_device])

    def create_device_graphics(self, device):
        """Создает графическое представление устройства с использованием SVG-иконки"""
        try:
            # Определяем путь к иконке
            icon_file = self.device_icons.get(device.type)
            if not icon_file:
                logger.error(f"No icon for device type: {device.type}")
                return
            
            icon_path = os.path.join(self.icon_dir, icon_file)
            
            # Создаем SVG-представление устройства с указанием размера
            device_item = SvgDeviceItem(
                device, 
                icon_path, 
                desired_size=self.device_icon_size
            )
            self.addItem(device_item)
            self.device_items[device.id] = device_item
            
            # Связываем нотификатор с обработчиком
            device_item.get_notifier().propertiesChanged.connect(
                self.handle_device_properties_changed
            )

            logger.debug(f"Created SVG graphics for device: {device.id}")
        except Exception as e:
            logger.error(f"Error creating device graphics: {e}")

    def add_link(self, source_id, target_id, bandwidth=1.0, delay=1.0, loss=0.0):
        """Добавляет новую связь между устройствами"""
        try:
            # Проверка на самосоединение
            if source_id == target_id:
                logger.warning("Cannot create link to self")
                return None
                
            link_id = f"{source_id}-{target_id}"
            reverse_id = f"{target_id}-{source_id}"
            
            # Проверка дубликатов
            if link_id in self.links or reverse_id in self.links:
                logger.warning(f"Link already exists: {link_id}")
                return None
                
            src_device = self.devices.get(source_id)
            dst_device = self.devices.get(target_id)
            
            if not src_device or not dst_device:
                logger.error(f"Invalid devices for link: {source_id} -> {target_id}")
                return None
                
            logger.debug(f"Adding link: {link_id}")
            #print(source_id, target_id, bandwidth, delay, loss)
            # Создаем объект связи
            link = Link(
                source=source_id,
                target=target_id,
                bandwidth=bandwidth,
                delay=delay,
                loss=loss
            )
            self.links[link_id] = link

            # Получаем графические элементы
            source_item = self.device_items[source_id]
            target_item = self.device_items[target_id]
            
            # Создаем линию между центрами
            link_item = NetworkLinkItem(source_item, target_item, link)
            self.addItem(link_item)
            self.link_items[link_id] = link_item
            
            # Обновляем стиль связи (на случай, если это связь с контроллером)
            link_item.update_line_style()
            
            logger.info(f"Created link: {source_id} -> {target_id}")
            return link
        except Exception as e:
            logger.error(f"Error adding link: {e}")
            return None

    def create_link_graphics(self, link, src_device, dst_device):
        """Создает графическое представление связи"""
        try:
            # Линия связи
            line = QLineF(src_device.x, src_device.y, dst_device.x, dst_device.y)
            line_item = QGraphicsLineItem(line)
            line_item.setPen(QPen(Qt.darkGray, 4))
            line_item.setZValue(5)
            line_item.setData(0, link)
            self.addItem(line_item)

            
            logger.debug(f"Created graphics for link: {link.source}-{link.target}")
            
        except Exception as e:
            logger.error(f"Error creating link graphics: {e}")
            
    def update_link_graphics(self, link_id):
        """Обновляет графическое представление связи"""
        if link_id in self.link_items:
            link_item = self.link_items[link_id]
            # Можно добавить визуальное отображение параметров
            # Например, обновить текст или цвет линии
            # Пока просто перерисовываем
            link_item.update()
            logger.info(f"Link graphics updated: {link_id}")

    def import_topology(self, data):
        """Импортирует топологию из данных XML"""
        try:
            # Очищаем текущую сцену
            self.clear()
            self.devices = {}
            self.links = {}
            self.device_items = {}
            self.link_items = {}
            
            # Добавляем устройства
            for device in data["devices"].values():
                # Проверяем, существует ли устройство с таким ID
                if device.id in self.devices:
                    # Генерируем новый уникальный ID
                    count = self.get_device_amount(device.type) + 1
                    new_id = f"{device.type.value.lower()}{count}"
                    logger.warning(f"Device ID conflict: {device.id} renamed to {new_id}")
                    device.id = new_id
                
                self.devices[device.id] = device
                self.create_device_graphics(device)
            
            # Добавляем связи, используя ту же логику, что и при интерактивном создании
            for link in data["links"].values():
                src_device = self.devices.get(link.source)
                dst_device = self.devices.get(link.target)
                
                if not src_device or not dst_device:
                    logger.warning(f"Link references missing device: {link.source}->{link.target}")
                    continue
                    
                # Создаем связь через метод add_link
                self.add_link(
                    src_device.id, 
                    dst_device.id,
                    link.bandwidth,
                    link.delay,
                    link.loss
                )
            
            logger.info(f"Imported topology with {len(self.devices)} devices and {len(self.links)} links")
        except Exception as e:
            logger.error(f"Error importing topology: {e}")

    def update_temp_line_style(self):
        """Обновляет стиль временной линии в зависимости от состояния"""
        if not self.temp_line:
            return
            
        if getattr(self, 'link_hover_device', False):
            # Если курсор над допустимым устройством - бирюзовая пунктирная линия
            pen = QPen(QColor(THEME["primary"]), 2, Qt.DashLine)
        else:
            # Если курсор не над устройством - мягкий пунктир
            pen = QPen(QColor(THEME["surface"]), 2, Qt.DashLine)
        
        self.temp_line.setPen(pen)

