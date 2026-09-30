# ui/segmentation_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                             QSpinBox, QDialogButtonBox, QFormLayout, QGroupBox)
import logging

logger = logging.getLogger(__name__)

class SegmentationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка сегментации")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # Группа выбора алгоритма
        algorithm_group = QGroupBox("Алгоритм сегментации")
        algorithm_layout = QFormLayout()
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItem("Girvan-Newman", "girvan_newman")
        self.algorithm_combo.addItem("Бинарное деление", "binary")
        self.algorithm_combo.addItem("Жадный алгоритм", "greedy")
        self.algorithm_combo.addItem("На основе связности", "connectivity")
        
        algorithm_layout.addRow("Алгоритм:", self.algorithm_combo)
        algorithm_group.setLayout(algorithm_layout)
        
        # Группа параметров
        self.params_group = QGroupBox("Параметры алгоритма")
        params_layout = QFormLayout()
        
        self.segments_spin = QSpinBox()
        self.segments_spin.setRange(2, 20)
        self.segments_spin.setValue(4)
        self.segments_spin.setEnabled(False)  # По умолчанию выключен
        
        params_layout.addRow("Количество сегментов:", self.segments_spin)
        self.params_group.setLayout(params_layout)
        
        # Кнопки
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Связываем изменение алгоритма с активацией параметров
        self.algorithm_combo.currentIndexChanged.connect(self.update_parameters)
        
        layout.addWidget(algorithm_group)
        layout.addWidget(self.params_group)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        
        logger.debug("Segmentation dialog initialized")
    
    def update_parameters(self):
        """Активирует параметры в зависимости от выбранного алгоритма"""
        algorithm = self.algorithm_combo.currentData()
        self.segments_spin.setEnabled(algorithm in ["binary", "greedy"])
    
    def get_segmentation_parameters(self):
        """Возвращает выбранные параметры сегментации"""
        return {
            "algorithm": self.algorithm_combo.currentData(),
            "num_segments": self.segments_spin.value() if self.segments_spin.isEnabled() else None
        }