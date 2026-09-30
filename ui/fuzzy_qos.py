import numpy as np
from typing import List, Tuple, Dict

# algorithms.py - добавляем поддержку параметров

class FuzzyQoS:
    """
    Класс для расчета маршрутов на основе нечеткой логики
    """
    
    def __init__(self, delay_weight=0.4, loss_weight=0.3, bandwidth_weight=0.3, quality_threshold=0.7):
        self.metrics_weights = {
            'delay': delay_weight,
            'packet_loss': loss_weight,
            'bandwidth': bandwidth_weight
        }
        self.quality_threshold = quality_threshold
    
    def fuzzify_delay(self, delay: float) -> Dict[str, float]:
        """Фазификация задержки"""
        low = max(0, min(1, (50 - delay) / 30)) if delay <= 50 else 0
        medium = max(0, min(1, (delay - 20) / 30, (80 - delay) / 30)) if 20 <= delay <= 80 else 0
        high = max(0, min(1, (delay - 50) / 30)) if delay >= 50 else 0
        
        return {'low': low, 'medium': medium, 'high': high}
    
    def fuzzify_packet_loss(self, loss: float) -> Dict[str, float]:
        """Фазификация потерь пакетов"""
        low = max(0, min(1, (5 - loss) / 4)) if loss <= 5 else 0
        medium = max(0, min(1, (loss - 1) / 4, (10 - loss) / 5)) if 1 <= loss <= 10 else 0
        high = max(0, min(1, (loss - 5) / 5)) if loss >= 5 else 0
        
        return {'low': low, 'medium': medium, 'high': high}
    
    def fuzzify_bandwidth(self, bandwidth: float) -> Dict[str, float]:
        """Фазификация пропускной способности"""
        low = max(0, min(1, (50 - bandwidth) / 40)) if bandwidth <= 50 else 0
        medium = max(0, min(1, (bandwidth - 10) / 40, (100 - bandwidth) / 40)) if 10 <= bandwidth <= 100 else 0
        high = max(0, min(1, (bandwidth - 50) / 50)) if bandwidth >= 50 else 0
        
        return {'low': low, 'medium': medium, 'high': high}
    
    def fuzzy_rules(self, delay_fuzzy: Dict, loss_fuzzy: Dict, bandwidth_fuzzy: Dict) -> Dict[str, float]:
        """Применение нечетких правил"""
        rules_output = {
            'excellent': 0,
            'good': 0,
            'average': 0,
            'poor': 0
        }
        
        # Правило 1: Если задержка низкая И потери низкие И bandwidth высокий -> отличное качество
        rules_output['excellent'] = min(
            delay_fuzzy['low'],
            loss_fuzzy['low'], 
            bandwidth_fuzzy['high']
        )
        
        # Правило 2: Если задержка низкая И (потери средние ИЛИ bandwidth средний) -> хорошее качество
        rules_output['good'] = min(
            delay_fuzzy['low'],
            max(loss_fuzzy['medium'], bandwidth_fuzzy['medium'])
        )
        
        # Правило 3: Если задержка средняя И потери средние -> среднее качество
        rules_output['average'] = min(
            delay_fuzzy['medium'],
            loss_fuzzy['medium']
        )
        
        # Правило 4: Если задержка высокая ИЛИ потери высокие -> плохое качество
        rules_output['poor'] = max(
            delay_fuzzy['high'],
            loss_fuzzy['high']
        )
        
        return rules_output
    
    def defuzzify(self, rules_output: Dict[str, float]) -> float:
        """Дефазификация - преобразование нечеткого вывода в четкое значение"""
        # Метод центра тяжести
        excellent_center, good_center, average_center, poor_center = 0.9, 0.7, 0.5, 0.2
        
        numerator = (
            rules_output['excellent'] * excellent_center +
            rules_output['good'] * good_center +
            rules_output['average'] * average_center +
            rules_output['poor'] * poor_center
        )
        
        denominator = sum(rules_output.values())
        
        return numerator / denominator if denominator > 0 else 0
    
    def calculate_link_quality(self, delay: float, loss: float, bandwidth: float) -> float:
        """Расчет качества связи на основе нечеткой логики"""
        # Фазификация входных параметров
        delay_fuzzy = self.fuzzify_delay(delay)
        loss_fuzzy = self.fuzzify_packet_loss(loss)
        bandwidth_fuzzy = self.fuzzify_bandwidth(bandwidth)
        
        # Применение нечетких правил
        rules_output = self.fuzzy_rules(delay_fuzzy, loss_fuzzy, bandwidth_fuzzy)
        
        # Дефазификация
        quality_score = self.defuzzify(rules_output)
        
        return quality_score
    
    def find_optimal_routes(self, src: int, dst: int, delay_matrix: List[List[float]], 
                           loss_matrix: List[List[float]], bandwidth_matrix: List[List[float]], 
                           k: int = 3) -> List[List[int]]:
        """Поиск оптимальных маршрутов с использованием нечеткой логики"""
        from ui.algorithms import yen  # Используем существующий алгоритм Йена
        
        n = len(delay_matrix)
        
        # Создаем матрицу весов на основе нечеткой оценки качества
        fuzzy_weights = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j and delay_matrix[i][j] > 0:
                    # Рассчитываем качество связи
                    quality = self.calculate_link_quality(
                        delay_matrix[i][j],
                        loss_matrix[i][j],
                        bandwidth_matrix[i][j]
                    )
                    # Преобразуем качество в вес (чем выше качество, тем меньше вес)
                    fuzzy_weights[i][j] = 1.0 - quality
                else:
                    fuzzy_weights[i][j] = float('inf')
        
        # Используем алгоритм Йена для поиска k лучших маршрутов
        routes = yen(fuzzy_weights, src, dst, k)
        
        return routes

def fuzzy_qos(src, dst, delay_matrix, loss_matrix, bandwidth_matrix, k, 
              delay_weight=0.4, loss_weight=0.3, bandwidth_weight=0.3, quality_threshold=0.7):
    """
    Алгоритм маршрутизации на основе нечеткой логики
    
    Аргументы:
    src - начальная вершина
    dst - конечная вершина  
    delay_matrix - матрица задержек
    loss_matrix - матрица потерь пакетов
    bandwidth_matrix - матрица пропускной способности
    k - количество маршрутов
    delay_weight - вес метрики задержки
    loss_weight - вес метрики потерь
    bandwidth_weight - вес метрики пропускной способности
    quality_threshold - порог качества
    
    Возвращает:
    list: список оптимальных маршрутов
    """
    fuzzy_engine = FuzzyQoS(delay_weight, loss_weight, bandwidth_weight, quality_threshold)
    return fuzzy_engine.find_optimal_routes(src, dst, delay_matrix, loss_matrix, bandwidth_matrix, k)