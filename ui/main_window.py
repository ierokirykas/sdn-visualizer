from PyQt5.QtWidgets import (QMainWindow, QGraphicsView, QFileDialog, QMessageBox, QAction, QDockWidget,
                             QDialog, QTableWidgetItem, QTableWidget,QDialogButtonBox, QHeaderView,QLabel, QVBoxLayout)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QCursor
from ui.toolbar import MainToolBar
from core.scene import NetworkScene, NetworkLinkItem
from core.models import DeviceType
from utils.file_io import export_to_xml, export_to_python
import logging
from ui.device_panel import DevicePropertiesPanel
from ui.link_panel import LinkPropertiesPanel
# Заменяем старые импорты алгоритмов сегментации на новые QoS-алгоритмы
from ui.algorithms import (
    MCP, 
    MCOP, 
    CSP, 
    LARAC,
)
from ui.segmentation_dialog import SegmentationDialog
from ui.floating_windows import FloatingDevicePanel, FloatingLinkPanel

logger = logging.getLogger(__name__)
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDN Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create scene and view
        self.scene = NetworkScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view) 
        
        # Create toolbar
        self.toolbar = MainToolBar(self)
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        
        # Connect export actions
        self.toolbar.export_xml_action.triggered.connect(self.export_xml)
        self.toolbar.export_python_action.triggered.connect(self.export_python)

        # Подключаем сигнал изменения режима отображения связей
        self.toolbar.link_display_mode_changed.connect(self.update_link_display_mode)

        # Create menu bar
        self.create_menu_bar()

        # Скрываем меню-бар по умолчанию
        self.menu_bar = self.menuBar()
        self.menu_bar.hide()
        self.menu_bar.installEventFilter(self)

        # Создаем панель свойств устройства
        self.device_panel = DevicePropertiesPanel(self)
        self.device_dock = QDockWidget("Свойства устройства", self)
        self.device_dock.setWidget(self.device_panel)
        self.device_dock.setFeatures(QDockWidget.DockWidgetClosable | 
                                    QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.device_dock)
        
        # Скрываем панель по умолчанию
        self.device_dock.hide()

        # Создаем панель свойств связи
        self.link_panel = LinkPropertiesPanel(self)
        self.link_dock = QDockWidget("Свойства связи", self)
        self.link_dock.setWidget(self.link_panel)
        self.link_dock.setFeatures(QDockWidget.DockWidgetClosable | 
                                  QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.link_dock)

        self.link_dock.hide()


        self.floating_device_panels = {}
        self.floating_link_panels = {}
     

    def eventFilter(self, obj, event):
        """Обработчик событий для скрытия меню-бара"""
        if obj == self.menu_bar:
            if event.type() == QEvent.FocusOut:
                return True
            elif event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Alt :
                    self.menu_bar.hide()
                    return True
        return super().eventFilter(obj, event)
    
    def show_link_properties(self, link):
        """Показывает панель свойств для связи"""
        # Получаем графический элемент связи
        link_item = self.scene.link_items.get(f"{link.source}-{link.target}")
        if not link_item:
            link_item = self.scene.link_items.get(f"{link.target}-{link.source}")
        if link_item:
            # Передаем нотификатор из графического элемента
            self.link_panel.set_link(link, link_item.notifier)
        else:
            self.link_panel.set_link(link)
        
        self.link_dock.show()
            
    def handle_link_properties_changed(self, link_id):
        """Обрабатывает изменения свойств связи"""
        self.scene.update_link_graphics(link_id)
        logger.info(f"Link properties changed: {link_id}")

    def show_device_properties(self, device, notifier):
        """Показывает панель свойств для устройства"""
        self.device_panel.set_device(device, notifier)
        self.device_dock.show()
        logger.info(f"Showing properties for device: {device.id}")

    def handle_properties_changed(self, device):
        """Обрабатывает изменения свойств устройства"""
        self.scene.update_device_graphics(device)
        logger.info(f"Properties changed for device: {device.id}")

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Alt and not self.menu_bar.isVisible():
            self.menu_bar.show()
            self.menu_bar.setFocus()
            return
        elif event.key() == Qt.Key_Delete:
            self.delete_selected_devices()
        else:
            super().keyPressEvent(event)
    
    def delete_selected_devices(self):
        """Удаляет выделенные устройства"""
        selected_devices = self.scene.get_selected_devices()
        if selected_devices:
            self.scene.delete_devices(selected_devices)
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # New action
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def new_file(self):
        """Создает новую пустую топологию"""
        reply = QMessageBox.question(
            self, "New File",
            "Create new topology? Current changes will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.scene.clear()
            self.scene.devices = {}
            self.scene.links = {}
    
    def open_file(self):
        """Открывает диалог выбора файла и импортирует топологию"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Topology", "", "XML Files (*.xml)")
        
        if file_path:
            # Импортируем данные из XML
            from utils.file_io import import_from_xml
            data = import_from_xml(file_path)
            
            if data["devices"]:
                self.scene.import_topology(data)
            else:
                QMessageBox.warning(
                    self, "Import Error",
                    "Failed to import topology from the selected file."
                )
    
    def save_file(self):
        """Сохраняет текущую топологию в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Topology", "", "XML Files (*.xml)")
        
        if file_path:
            from utils.file_io import export_to_xml
            export_to_xml(self.scene.devices, self.scene.links, file_path)
            QMessageBox.information(
                self, "Save Successful",
                f"Topology saved to {file_path}"
            )
    
    def show_about(self):
        """Показывает информацию о программе"""
        QMessageBox.about(
            self, "SDN Visualizer",
            "Визуальная среда ПКС\n\n"
            "Версия 2.0\n"
            "Среда для визуализации ПКС.\n"
            "Автор: Анна Бугаенко"
        )
    
    def export_xml(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export XML", "", "XML Files (*.sdn.xml)")
        if file_path:
            export_to_xml(self.scene.devices, self.scene.links, file_path)
    
    def export_python(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Python", "", "Python Files (*.sdn.py)")
        if file_path:
            export_to_python(self.scene.devices, self.scene.links, file_path)

    def connect_switches_to_controller(self):
        """Подключает все коммутаторы к контроллеру (создает контроллер при необходимости)"""
        # Ищем существующий контроллер
        controller = None
        for device in self.scene.devices.values():
            if device.type == DeviceType.CONTROLLER:
                controller = device
                break
        
        # Если контроллера нет - создаем один
        if not controller:
            # Размещаем контроллер в центре сцены
            view = self.view
            scene_center = view.mapToScene(view.viewport().rect().center())
            controller = self.scene.add_device(DeviceType.CONTROLLER, scene_center.x(), scene_center.y())
            logger.info(f"Created new controller: {controller.id}")
        
        # Находим все коммутаторы
        switches = [d for d in self.scene.devices.values() if d.type == DeviceType.SWITCH]
        
        if not switches:
            QMessageBox.warning(self, "No Switches", "No switches found in the network.")
            return
        
        # Создаем связи
        new_links = 0
        for switch in switches:
            # Проверяем, нет ли уже связи
            link_exists = any(
                (link.source == controller.id and link.target == switch.id) or 
                (link.source == switch.id and link.target == controller.id)
                for link in self.scene.links.values()
            )
            
            if not link_exists:
                self.scene.add_link(controller.id, switch.id)
                new_links += 1
        
        if new_links > 0:
            QMessageBox.information(
                self, "Success", 
                f"Connected {new_links} switches to controller {controller.id}"
            )
        else:
            QMessageBox.information(
                self, "Info", 
                "All switches are already connected to the controller"
            )

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.device_panel.clear()  # Очищаем панель устройств
        self.link_panel.clear()    # Очищаем панель связей
        
        self.device_dock.close()   # Закрываем док-панель устройств
        self.link_dock.close()     # Закрываем док-панель связей
        
        super().closeEvent(event)

    def close_panel(self):
        """Закрывает панель и очищает данные"""
        self.clear()
        self.hide()
    def export_metric(self):
        """Экспортирует данные о связях между коммутаторами в текстовый формат metric_data.txt"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Metric Data", "", "Text Files (*.txt)")
        
        if file_path:
            from utils.file_io import export_to_metric_file
            if export_to_metric_file(self.scene.devices, self.scene.links, file_path):
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Metric data exported to {file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Export Error", 
                    "Failed to export metric data."
                )

    def algorithm(self):
        """Применяет алгоритм QoS-маршрутизации и визуализирует результат"""
        try:
            # Фиксированный путь к файлу метрик
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            metric_file = os.path.join(base_dir, "others", "metric_data.txt")
            
            # Экспортируем метрики
            from utils.file_io import export_to_metric_file
            if not export_to_metric_file(self.scene.devices, self.scene.links, metric_file):
                raise Exception("Failed to export metric data")
            
            # Получаем список коммутаторов
            switches = self.get_switches()
            num_switches = len(switches)
            if num_switches < 2:
                raise Exception("Need at least 2 switches for QoS routing")
            
            # Читаем матрицы смежности (3 метрики: bandwidth, delay, loss)
            from others.sdn_topology import read_matrix
            matrices = read_matrix(num_switches, metric_file)
            
            # matrices содержит 3 матрицы: [bandwidth_matrix, delay_matrix, loss_matrix]
            delay_matrix = matrices[0]
            bandwidth_matrix = matrices[1] 
            loss_matrix = matrices[2]
            #print(bandwidth_matrix,delay_matrix,loss_matrix)
            #print(matrices)
            
            # Показываем диалог выбора алгоритма QoS
            from ui.floating_windows import QoSDialog
            dialog = QoSDialog(self, num_switches)
            if dialog.exec_() != QDialog.Accepted:
                return
            
            params = dialog.get_qos_parameters()

            algorithm_name = params["algorithm"]
            logger.info(f"ALGORITHM INFO -> {params["algorithm"]}")
            routes = []
            
            if algorithm_name == "fuzzy logic":
                # Используем алгоритм нечеткой логики
                from ui.fuzzy_qos import fuzzy_qos
                routes = fuzzy_qos(
                    params["src"], 
                    params["dst"], 
                    delay_matrix, 
                    loss_matrix, 
                    bandwidth_matrix, 
                    params["k"],
                    delay_weight=params.get("delay_weight", 0.4),
                    loss_weight=params.get("loss_weight", 0.3),
                    bandwidth_weight=params.get("bandwidth_weight", 0.3),
                    quality_threshold=params.get("quality_threshold", 0.7)
                )
            else:
                # Для остальных алгоритмов используем стандартную логику
                # Выбираем соответствующие матрицы на основе выбранных метрик
                metric_matrices = {
                    'delay': delay_matrix,
                    'packet_loss_rate': loss_matrix,
                    'bandwidth': bandwidth_matrix
                }
                
                matrix1 = metric_matrices[params["metric1_type"]]
                matrix2 = metric_matrices[params["metric2_type"]]
                
                # Для bandwidth преобразуем метрику (чем больше bandwidth, тем лучше,
                # но алгоритмы минимизируют метрики, поэтому используем обратное значение)
                if params["metric1_type"] == "bandwidth":
                    matrix1 = [[1.0 / value if value > 0 else float('inf') for value in row] for row in matrix1]
                    params["metric1_limit"] = 1.0 / params["metric1_limit"] if params["metric1_limit"] > 0 else float('inf')
                
                if params["metric2_type"] == "bandwidth":
                    matrix2 = [[1.0 / value if value > 0 else float('inf') for value in row] for row in matrix2]
                    params["metric2_limit"] = 1.0 / params["metric2_limit"] if params["metric2_limit"] > 0 else float('inf')
                
                # Применяем выбранный алгоритм QoS
                if algorithm_name == "mcp":
                    routes = MCP(params["src"], params["dst"], matrix1, matrix2, 
                                params["metric1_limit"], params["metric2_limit"], params["k"])
                elif algorithm_name == "mcop":
                    routes = MCOP(params["src"], params["dst"], matrix1, matrix2, params["k"])
                elif algorithm_name == "csp":
                    # Для CSP используем первую метрику для оптимизации, вторую для ограничения
                    routes = CSP(params["src"], params["dst"], matrix1, matrix2, 
                                params["metric2_limit"], params["k"])
                elif algorithm_name == "larac":
                    routes = LARAC(params["src"], params["dst"], matrix1, matrix2,
                                params["metric1_limit"], params["metric2_limit"], params["lambda_val"], params["k"])
                else:
                    # По умолчанию используем MCP
                    routes = MCP(params["src"], params["dst"], matrix1, matrix2,
                                params["metric1_limit"], params["metric2_limit"], params["k"])
            
            # Окрашиваем каналы на найденных маршрутах
            self.color_links_by_routes(routes, switches)
            # Показываем информацию о найденных маршрутах
            # Для нечеткой логики показываем специальные метрики
            if algorithm_name == "fuzzy logic":
                self.show_fuzzy_qos_results(routes, delay_matrix, loss_matrix, bandwidth_matrix)
                print("woof")
            else:
                # Показываем стандартные результаты
                from ui.floating_windows import QoSResultsDialog
                results_dialog = QoSResultsDialog(self, routes, delay_matrix, loss_matrix, 
                                                params["metric1_type"], params["metric2_type"])
                results_dialog.exec_()
            
            # Переключаемся в режим SELECT
            self.toolbar._set_active_tool("SELECT")
                
        except Exception as e:
            QMessageBox.critical(self, "QoS Algorithm Error", f"Failed to apply QoS algorithm: {str(e)}")
            logger.error(f"QoS algorithm failed: {e}", exc_info=True)
    
    def show_fuzzy_qos_results(self, routes, delay_matrix, loss_matrix, bandwidth_matrix):
        """Показывает результаты для нечеткой логики с расширенными метриками"""
        if not routes:
            QMessageBox.information(self, "Fuzzy QoS Results", "No routes found satisfying the quality constraints")
            return
        
        # Создаем кастомный диалог для нечеткой логики
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, 
                                    QTableWidgetItem, QHeaderView, QDialogButtonBox)
        from PyQt5.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Fuzzy QoS Routing Results")
        dialog.setMinimumWidth(800)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("<h2>Fuzzy Logic QoS Routing Results</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Создаем таблицу для отображения результатов
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["Route", "Path", "Total Delay (ms)", "Total Loss (%)", 
                                    "Min Bandwidth (Mbps)", "Quality Score", "Status"])
        table.setRowCount(len(routes))
        
        # Заполняем таблицу данными
        for i, route in enumerate(routes):
            # Вычисляем метрики для маршрута
            total_delay = 0
            success_rate = 1.0
            min_bandwidth = float('inf')
            
            for j in range(len(route) - 1):
                u = route[j]
                v = route[j + 1]
                total_delay += delay_matrix[u][v]
                # Рассчитываем коэффициент успешной доставки для каждого звена
                loss_fraction = loss_matrix[u][v] / 100.0
                success_rate *= (1 - loss_fraction)
                # Находим минимальную пропускную способность на маршруте
                min_bandwidth = min(min_bandwidth, bandwidth_matrix[u][v])
            
            # Общий процент потерь
            total_loss = (1 - success_rate) * 100
            
            # Вычисляем оценку качества на основе нечеткой логики
            quality_score = self.calculate_fuzzy_quality(total_delay, total_loss, min_bandwidth)
            
            # Определяем статус маршрута
            if quality_score >= 0.8:
                status = "Excellent"
            elif quality_score >= 0.6:
                status = "Good"
            elif quality_score >= 0.4:
                status = "Average"
            else:
                status = "Poor"
            
            # Заполняем строку таблицы
            table.setItem(i, 0, QTableWidgetItem(f"{i + 1}"))
            table.setItem(i, 1, QTableWidgetItem(" → ".join(str(node + 1) for node in route)))
            table.setItem(i, 2, QTableWidgetItem(f"{total_delay:.1f}"))
            table.setItem(i, 3, QTableWidgetItem(f"{total_loss:.2f}"))
            table.setItem(i, 4, QTableWidgetItem(f"{min_bandwidth:.1f}"))
            table.setItem(i, 5, QTableWidgetItem(f"{quality_score:.3f}"))
            table.setItem(i, 6, QTableWidgetItem(status))
        
        # Настраиваем внешний вид таблицы
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.resizeColumnsToContents()
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        layout.addWidget(table)
        
        # Добавляем пояснение
        explanation = QLabel(
            "<b>Quality Score Interpretation:</b><br>"
            "0.8-1.0: Excellent &nbsp;&nbsp; 0.6-0.8: Good &nbsp;&nbsp; "
            "0.4-0.6: Average &nbsp;&nbsp; 0.0-0.4: Poor"
        )
        explanation.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 5px;")
        layout.addWidget(explanation)
        
        # Добавляем кнопку закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def calculate_fuzzy_quality(self, delay, loss, bandwidth):
        """Вычисляет оценку качества на основе нечеткой логики"""
        # Упрощенная реализация нечеткой оценки качества
        # В реальной реализации это должно совпадать с логикой в fuzzy_qos.py
        
        # Нормализуем метрики
        delay_score = max(0, 1 - delay / 100)  # Чем меньше задержка, тем лучше
        loss_score = max(0, 1 - loss / 10)     # Чем меньше потерь, тем лучше
        bandwidth_score = min(1, bandwidth / 100)  # Чем больше bandwidth, тем лучше
        
        # Взвешенная сумма (можно настроить веса)
        quality = (0.4 * delay_score + 0.4 * loss_score + 0.2 * bandwidth_score)
        
        return min(1.0, max(0.0, quality))

    def get_switches(self):
        """Возвращает список всех коммутаторов в сцене"""
        return [d for d in self.scene.devices.values() if d.type == DeviceType.SWITCH]
    
    def color_links_by_routes(self, routes, switches):
        """Окрашивает каналы разными цветами в зависимости от найденных QoS-маршрутов"""
        # Предопределенная палитра цветов для разных маршрутов
        self.clear_link_highlights()
        
        colors = [
            QColor(255, 0, 0),    # Красный
            QColor(0, 0, 255),    # Синий
            QColor(0, 255, 0),    # Зеленый
            QColor(255, 255, 0),  # Желтый
            QColor(255, 0, 255),  # Пурпурный
            QColor(0, 255, 255),  # Голубой
            QColor(255, 128, 0),  # Оранжевый
            QColor(128, 0, 255),  # Фиолетовый
        ]
        
        # Создаем mapping: индекс -> устройство
        switch_mapping = {i: switches[i] for i in range(len(switches))}
        
        # Окрашиваем каждый маршрут своим цветом
        for route_idx, route in enumerate(routes):
            color = colors[route_idx % len(colors)]
            
            # Проходим по всем каналам в маршруте
            for i in range(len(route) - 1):
                src_switch = switch_mapping.get(route[i])
                dst_switch = switch_mapping.get(route[i + 1])
                
                if src_switch and dst_switch:
                    # Ищем соответствующий канал в сцене
                    link_id1 = f"{src_switch.id}-{dst_switch.id}"
                    link_id2 = f"{dst_switch.id}-{src_switch.id}"
                    
                    link_item = None
                    if link_id1 in self.scene.link_items:
                        link_item = self.scene.link_items[link_id1]
                    elif link_id2 in self.scene.link_items:
                        link_item = self.scene.link_items[link_id2]
                    
                    if link_item:
                        # Окрашиваем канал
                        link_item.set_highlight(True, color)

    def clear_link_highlights(self):
        """Очищает все выделения с каналов"""
        for link_item in self.scene.link_items.values():
            link_item.set_highlight(False)

    def show_floating_device_properties(self, device, notifier):
        """Показывает плавающее окно свойств устройства"""
        if device.id not in self.floating_device_panels:
            self.floating_device_panels[device.id] = FloatingDevicePanel(self)
        
        panel = self.floating_device_panels[device.id]
        panel.set_device(device, notifier)
        
        # Позиционируем окно рядом с курсором
        cursor_pos = QCursor.pos()
        panel.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        panel.show()
    
    def show_floating_link_properties(self, link, notifier):
        """Показывает плавающее окно свойств связи"""
        link_id = f"{link.source}-{link.target}"
        if link_id not in self.floating_link_panels:
            self.floating_link_panels[link_id] = FloatingLinkPanel(self)
        
        panel = self.floating_link_panels[link_id]
        panel.set_link(link, notifier)
        
        # Позиционируем окно рядом с курсором
        cursor_pos = QCursor.pos()
        panel.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        panel.show()
    
    def closeEvent(self, event):
        """Закрывает все плавающие окна при закрытии главного окна"""
        for panel in self.floating_device_panels.values():
            panel.close()
        for panel in self.floating_link_panels.values():
            panel.close()
        super().closeEvent(event)

    def update_link_display_mode(self, mode):
        """Обновляет режим отображения для всех связей на сцене"""
        for item in self.scene.items():
            if isinstance(item, NetworkLinkItem):
                item.set_display_mode(mode)

    def show_qos_results(self, routes, delay_matrix, loss_matrix):
        """Показывает информацию о найденных QoS-маршрутах с правильным расчетом потерь"""
        if not routes:
            QMessageBox.information(self, "QoS Results", "No routes found satisfying the constraints")
            return
        
        result_text = "Found QoS routes:\n\n"
        for i, route in enumerate(routes):
            # Вычисляем метрики для маршрута
            total_delay = 0
            success_rate = 1.0  # Начальный коэффициент успешной доставки (100%)
            
            # Создаем кастомный диалог
            dialog = QDialog(self)
            dialog.setWindowTitle("QoS Routing Results")
            dialog.setMinimumWidth(700)
            
            layout = QVBoxLayout()
            
            # Заголовок
            title = QLabel("<h2>QoS Routing Results</h2>")
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Создаем таблицу для отображения результатов
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Route", "Path", "Total Delay", "Total Loss", "Success Rate"])
            table.setRowCount(len(routes))
        # Заполняем таблицу данными
        for i, route in enumerate(routes):
            # Вычисляем метрики для маршрута
            total_delay = 0
            success_rate = 1.0  # Начальный коэффициент успешной доставки (100%)
            
            for j in range(len(route) - 1):
                u = route[j]
                v = route[j + 1]
                total_delay += delay_matrix[u][v]
                # Рассчитываем коэффициент успешной доставки для каждого звена
                loss_fraction = loss_matrix[u][v] / 100.0
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
        
        layout.addWidget(table)
        
        # Добавляем кнопку закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()