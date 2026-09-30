import copy
import heapq
from collections import deque

def binarySegmentation(matrix, src, n_segments):
    """Алгоритм бинарного деления на заданное количество сегментов"""
    # Шаг 1: Разметка вершин (BFS)
    labels = {src: 0}
    visited = set([src])
    queue = deque([src])
    
    while queue:
        current = queue.popleft()
        for neighbor in range(len(matrix[current])):
            if matrix[current][neighbor] > 0 and neighbor not in visited:
                labels[neighbor] = labels[current] + 1
                visited.add(neighbor)
                queue.append(neighbor)
    
    # Шаг 2: Инициализация segments (всё в одном сегменте)
    segments = [list(range(len(matrix)))]
    
    # Шаг 3-8: Деление на n_segments сегментов
    while len(segments) < n_segments:
        new_segments = []
        for segment in segments:
            if len(new_segments) + len(segments) >= n_segments:
                new_segments.append(segment)
                continue
            
            # Делим сегмент на два подсегмента
            sorted_nodes = sorted(segment, key=lambda x: labels[x])
            split_point = len(sorted_nodes) // 2
            new_segments.append(sorted_nodes[:split_point])
            new_segments.append(sorted_nodes[split_point:])
        
        segments = new_segments
    
    return segments

def greedySegmentation(matrix, src, n_seg):
    """Жадный алгоритм сегментирования"""
    # Шаг 1: Разметка вершин (BFS с учётом всех узлов)
    labels = {}
    queue = deque()
    
    # Инициализация для исходного узла
    labels[src] = 0
    queue.append(src)
    
    # Обработка связанных узлов
    while queue:
        current = queue.popleft()
        for neighbor in range(len(matrix[current])):
            if matrix[current][neighbor] > 0 and neighbor not in labels:
                labels[neighbor] = labels[current] + 1
                queue.append(neighbor)
    
    # Для несвязанных узлов устанавливаем большую метку
    for node in range(len(matrix)):
        if node not in labels:
            labels[node] = float('inf')
    
    # Шаг 2: Сортировка узлов по меткам
    sorted_nodes = sorted(labels.keys(), key=lambda x: labels[x])
    
    # Шаг 3: Распределение по сегментам
    segments = []
    total_nodes = len(sorted_nodes)
    base_size = total_nodes // n_seg
    remainder = total_nodes % n_seg
    
    start = 0
    for i in range(n_seg):
        # Определяем размер текущего сегмента
        seg_size = base_size + (1 if i < remainder else 0)
        end = start + seg_size
        segments.append(sorted_nodes[start:end])
        start = end
    
    return segments

def Girvan_Newman_Segmentation(matrix):
    """Алгоритм Гирвана-Ньюмана для сегментирования сети"""
    # Шаг 1: Инициализация
    matrix_copy = copy.deepcopy(matrix)
    segments = []
    
    def edge_betweenness(graph):
        """Вычисление betweenness для всех рёбер"""
        betweenness = {}
        nodes = range(len(graph))
        
        # Инициализация betweenness для всех ребер
        for i in nodes:
            for j in nodes:
                if i < j and graph[i][j] > 0:
                    betweenness[(i, j)] = 0
        
        for src in nodes:
            # BFS для нахождения кратчайших путей
            pred = [[] for _ in nodes]
            dist = {n: -1 for n in nodes}
            dist[src] = 0
            queue = deque([src])
            sigma = [0] * len(nodes)
            sigma[src] = 1
            
            while queue:
                v = queue.popleft()
                for w in [n for n in nodes if graph[v][n] > 0]:
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)
            
            # Накопление betweenness
            delta = [0] * len(nodes)
            stack = sorted(nodes, key=lambda x: -dist[x])
            
            for w in stack:
                for v in pred[w]:
                    c = sigma[v] / sigma[w] * (1 + delta[w])
                    edge = (min(v, w), max(v, w))
                    betweenness[edge] += c
                    delta[v] += c
        
        return betweenness
    
    def is_segmentation_complete(graph):
        """Проверка условия завершения"""
        centralities = edge_betweenness(graph)
        if not centralities:
            return True
        values = list(centralities.values())
        return all(v == values[0] for v in values)
    
    # Основной цикл алгоритма
    while not is_segmentation_complete(matrix_copy):
        # Шаг 2: Вычисление betweenness
        centralities = edge_betweenness(matrix_copy)
        
        if not centralities:
            break
        
        # Шаг 4: Нахождение ребра с максимальной betweenness
        max_edge = max(centralities.items(), key=lambda x: x[1])[0]
        
        # Шаг 5: Удаление ребра
        matrix_copy[max_edge[0]][max_edge[1]] = 0
        matrix_copy[max_edge[1]][max_edge[0]] = 0
    
    # Шаг 6-8: Нахождение сегментов (компонент связности)
    visited = set()
    for node in range(len(matrix_copy)):
        if node not in visited:
            component = []
            stack = [node]
            visited.add(node)
            
            while stack:
                current = stack.pop()
                component.append(current)
                
                for neighbor in range(len(matrix_copy[current])):
                    if matrix_copy[current][neighbor] > 0 and neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            
            segments.append(component)
    
    return segments

def connectivitySegmentation(matrix):
    """Алгоритм сегментирования на основе связности"""
    # Шаг 1: Построение минимального остовного дерева (алгоритм Прима)
    def prim_mst(graph):
        """Алгоритм Прима для построения MST"""
        n = len(graph)
        mst = [[0]*n for _ in range(n)]  # Матрица смежности MST
        visited = [False]*n
        heap = []
        
        # Начинаем с узла 0
        visited[0] = True
        for j in range(n):
            if graph[0][j] > 0:
                heapq.heappush(heap, (graph[0][j], 0, j))
        
        while heap:
            weight, u, v = heapq.heappop(heap)
            if not visited[v]:
                visited[v] = True
                mst[u][v] = weight
                mst[v][u] = weight
                for j in range(n):
                    if graph[v][j] > 0 and not visited[j]:
                        heapq.heappush(heap, (graph[v][j], v, j))
        return mst
    
    mst = prim_mst(matrix)
    
    # Шаг 2: Формирование первичных сегментов (листья + их родители)
    segments = []
    allocated = set()
    
    # Находим все листья в MST (узлы с одной связью)
    leaves = [i for i in range(len(mst)) if sum(1 for j in range(len(mst[i])) if mst[i][j] > 0) == 1]
    
    for leaf in leaves:
        if leaf not in allocated:
            # Находим родителя листа
            parent = next(j for j in range(len(mst[leaf])) if mst[leaf][j] > 0)
            
            # Проверяем, есть ли сегмент с этим родителем
            segment_found = False
            for seg in segments:
                if parent in seg:
                    seg.add(leaf)
                    allocated.add(leaf)
                    segment_found = True
                    break
            
            if not segment_found:
                new_segment = {leaf, parent}
                segments.append(new_segment)
                allocated.update(new_segment)
    
    # Шаг 3: Добавление оставшихся узлов к сегментам
    remaining_nodes = set(range(len(matrix))) - allocated
    
    while remaining_nodes:
        # Для каждого оставшегося узла находим лучший сегмент
        best_connections = []
        
        for node in remaining_nodes:
            max_connection = -1
            best_segment_idx = -1
            
            # Ищем сегмент с максимальной связностью
            for i, seg in enumerate(segments):
                connection = sum(matrix[node][x] for x in seg if matrix[node][x] > 0)
                if connection > max_connection:
                    max_connection = connection
                    best_segment_idx = i
            
            if best_segment_idx != -1:
                best_connections.append((node, best_segment_idx, max_connection))
        
        if not best_connections:
            # Если нет связей, создаем новый сегмент из первого оставшегося узла
            segments.append({remaining_nodes.pop()})
            continue
        
        # Находим узел с максимальной связностью к своему лучшему сегменту
        node_to_add, seg_idx, _ = max(best_connections, key=lambda x: x[2])
        
        # Добавляем узел в сегмент
        segments[seg_idx].add(node_to_add)
        remaining_nodes.remove(node_to_add)
    
    # Шаг 4: Объединение сегментов с низкой связностью (Q < 0.3)
    def calculate_connectivity(segment):
        """Вычисление показателя связности сегмента"""
        internal = 0
        external = 0
        
        for i in segment:
            for j in range(len(matrix[i])):
                if matrix[i][j] > 0:
                    if j in segment:
                        internal += matrix[i][j]
                    else:
                        external += matrix[i][j]
        
        # Добавляем малое число, чтобы избежать деления на 0
        return internal / (external + 1e-9)
    
    changed = True
    while changed:
        changed = False
        connectivity_values = [calculate_connectivity(seg) for seg in segments]
        
        # Находим сегмент с минимальной связностью
        min_q = min(connectivity_values)
        if min_q < 0.3:
            min_idx = connectivity_values.index(min_q)
            
            # Находим сегмент с максимальной связностью к текущему
            max_connection = -1
            best_merge_idx = -1
            
            for i in range(len(segments)):
                if i != min_idx:
                    # Считаем суммарный вес связей между сегментами
                    connection = sum(matrix[u][v] for u in segments[min_idx] for v in segments[i] if matrix[u][v] > 0)
                    
                    if connection > max_connection:
                        max_connection = connection
                        best_merge_idx = i
            
            if best_merge_idx != -1:
                # Объединяем сегменты
                segments[best_merge_idx].update(segments[min_idx])
                del segments[min_idx]
                changed = True
    
    # Преобразуем множества в списки и сортируем для удобства
    return [sorted(list(seg)) for seg in segments]

import copy
import heapq
from collections import deque

def binarySegmentation(matrix, src, n_segments):
    """Алгоритм бинарного деления на заданное количество сегментов"""
    # Шаг 1: Разметка вершин (BFS)
    labels = {src: 0}
    visited = set([src])
    queue = deque([src])
    
    while queue:
        current = queue.popleft()
        for neighbor in range(len(matrix[current])):
            if matrix[current][neighbor] > 0 and neighbor not in visited:
                labels[neighbor] = labels[current] + 1
                visited.add(neighbor)
                queue.append(neighbor)
    
    # Шаг 2: Инициализация segments (всё в одном сегменте)
    segments = [list(range(len(matrix)))]
    
    # Шаг 3-8: Деление на n_segments сегментов
    while len(segments) < n_segments:
        new_segments = []
        for segment in segments:
            if len(new_segments) + len(segments) >= n_segments:
                new_segments.append(segment)
                continue
            
            # Делим сегмент на два подсегмента
            sorted_nodes = sorted(segment, key=lambda x: labels[x])
            split_point = len(sorted_nodes) // 2
            new_segments.append(sorted_nodes[:split_point])
            new_segments.append(sorted_nodes[split_point:])
        
        segments = new_segments
    
    return segments

def greedySegmentation(matrix, src, n_seg):
    """Жадный алгоритм сегментирования"""
    # Шаг 1: Разметка вершин (BFS с учётом всех узлов)
    labels = {}
    queue = deque()
    
    # Инициализация для исходного узла
    labels[src] = 0
    queue.append(src)
    
    # Обработка связанных узлов
    while queue:
        current = queue.popleft()
        for neighbor in range(len(matrix[current])):
            if matrix[current][neighbor] > 0 and neighbor not in labels:
                labels[neighbor] = labels[current] + 1
                queue.append(neighbor)
    
    # Для несвязанных узлов устанавливаем большую метку
    for node in range(len(matrix)):
        if node not in labels:
            labels[node] = float('inf')
    
    # Шаг 2: Сортировка узлов по меткам
    sorted_nodes = sorted(labels.keys(), key=lambda x: labels[x])
    
    # Шаг 3: Распределение по сегментам
    segments = []
    total_nodes = len(sorted_nodes)
    base_size = total_nodes // n_seg
    remainder = total_nodes % n_seg
    
    start = 0
    for i in range(n_seg):
        # Определяем размер текущего сегмента
        seg_size = base_size + (1 if i < remainder else 0)
        end = start + seg_size
        segments.append(sorted_nodes[start:end])
        start = end
    
    return segments

def Girvan_Newman_Segmentation(matrix):
    """Алгоритм Гирвана-Ньюмана для сегментирования сети"""
    # Шаг 1: Инициализация
    matrix_copy = copy.deepcopy(matrix)
    segments = []
    
    def edge_betweenness(graph):
        """Вычисление betweenness для всех рёбер"""
        betweenness = {}
        nodes = range(len(graph))
        
        # Инициализация betweenness для всех ребер
        for i in nodes:
            for j in nodes:
                if i < j and graph[i][j] > 0:
                    betweenness[(i, j)] = 0
        
        for src in nodes:
            # BFS для нахождения кратчайших путей
            pred = [[] for _ in nodes]
            dist = {n: -1 for n in nodes}
            dist[src] = 0
            queue = deque([src])
            sigma = [0] * len(nodes)
            sigma[src] = 1
            
            while queue:
                v = queue.popleft()
                for w in [n for n in nodes if graph[v][n] > 0]:
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        pred[w].append(v)
            
            # Накопление betweenness
            delta = [0] * len(nodes)
            stack = sorted(nodes, key=lambda x: -dist[x])
            
            for w in stack:
                for v in pred[w]:
                    c = sigma[v] / sigma[w] * (1 + delta[w])
                    edge = (min(v, w), max(v, w))
                    betweenness[edge] += c
                    delta[v] += c
        
        return betweenness
    
    def is_segmentation_complete(graph):
        """Проверка условия завершения"""
        centralities = edge_betweenness(graph)
        if not centralities:
            return True
        values = list(centralities.values())
        return all(v == values[0] for v in values)
    
    # Основной цикл алгоритма
    while not is_segmentation_complete(matrix_copy):
        # Шаг 2: Вычисление betweenness
        centralities = edge_betweenness(matrix_copy)
        
        if not centralities:
            break
        
        # Шаг 4: Нахождение ребра с максимальной betweenness
        max_edge = max(centralities.items(), key=lambda x: x[1])[0]
        
        # Шаг 5: Удаление ребра
        matrix_copy[max_edge[0]][max_edge[1]] = 0
        matrix_copy[max_edge[1]][max_edge[0]] = 0
    
    # Шаг 6-8: Нахождение сегментов (компонент связности)
    visited = set()
    for node in range(len(matrix_copy)):
        if node not in visited:
            component = []
            stack = [node]
            visited.add(node)
            
            while stack:
                current = stack.pop()
                component.append(current)
                
                for neighbor in range(len(matrix_copy[current])):
                    if matrix_copy[current][neighbor] > 0 and neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            
            segments.append(component)
    
    return segments

def connectivitySegmentation(matrix):
    """Алгоритм сегментирования на основе связности"""
    # Шаг 1: Построение минимального остовного дерева (алгоритм Прима)
    def prim_mst(graph):
        """Алгоритм Прима для построения MST"""
        n = len(graph)
        mst = [[0]*n for _ in range(n)]  # Матрица смежности MST
        visited = [False]*n
        heap = []
        
        # Начинаем с узла 0
        visited[0] = True
        for j in range(n):
            if graph[0][j] > 0:
                heapq.heappush(heap, (graph[0][j], 0, j))
        
        while heap:
            weight, u, v = heapq.heappop(heap)
            if not visited[v]:
                visited[v] = True
                mst[u][v] = weight
                mst[v][u] = weight
                for j in range(n):
                    if graph[v][j] > 0 and not visited[j]:
                        heapq.heappush(heap, (graph[v][j], v, j))
        return mst
    
    mst = prim_mst(matrix)
    
    # Шаг 2: Формирование первичных сегментов (листья + их родители)
    segments = []
    allocated = set()
    
    # Находим все листья в MST (узлы с одной связью)
    leaves = [i for i in range(len(mst)) if sum(1 for j in range(len(mst[i])) if mst[i][j] > 0) == 1]
    
    for leaf in leaves:
        if leaf not in allocated:
            # Находим родителя листа
            parent = next(j for j in range(len(mst[leaf])) if mst[leaf][j] > 0)
            
            # Проверяем, есть ли сегмент с этим родителем
            segment_found = False
            for seg in segments:
                if parent in seg:
                    seg.add(leaf)
                    allocated.add(leaf)
                    segment_found = True
                    break
            
            if not segment_found:
                new_segment = {leaf, parent}
                segments.append(new_segment)
                allocated.update(new_segment)
    
    # Шаг 3: Добавление оставшихся узлов к сегментам
    remaining_nodes = set(range(len(matrix))) - allocated
    
    while remaining_nodes:
        # Для каждого оставшегося узла находим лучший сегмент
        best_connections = []
        
        for node in remaining_nodes:
            max_connection = -1
            best_segment_idx = -1
            
            # Ищем сегмент с максимальной связностью
            for i, seg in enumerate(segments):
                connection = sum(matrix[node][x] for x in seg if matrix[node][x] > 0)
                if connection > max_connection:
                    max_connection = connection
                    best_segment_idx = i
            
            if best_segment_idx != -1:
                best_connections.append((node, best_segment_idx, max_connection))
        
        if not best_connections:
            # Если нет связей, создаем новый сегмент из первого оставшегося узла
            segments.append({remaining_nodes.pop()})
            continue
        
        # Находим узел с максимальной связностью к своему лучшему сегменту
        node_to_add, seg_idx, _ = max(best_connections, key=lambda x: x[2])
        
        # Добавляем узел в сегмент
        segments[seg_idx].add(node_to_add)
        remaining_nodes.remove(node_to_add)
    
    # Шаг 4: Объединение сегментов с низкой связностью (Q < 0.3)
    def calculate_connectivity(segment):
        """Вычисление показателя связности сегмента"""
        internal = 0
        external = 0
        
        for i in segment:
            for j in range(len(matrix[i])):
                if matrix[i][j] > 0:
                    if j in segment:
                        internal += matrix[i][j]
                    else:
                        external += matrix[i][j]
        
        # Добавляем малое число, чтобы избежать деления на 0
        return internal / (external + 1e-9)
    
    changed = True
    while changed:
        changed = False
        connectivity_values = [calculate_connectivity(seg) for seg in segments]
        
        # Находим сегмент с минимальной связностью
        min_q = min(connectivity_values)
        if min_q < 0.3:
            min_idx = connectivity_values.index(min_q)
            
            # Находим сегмент с максимальной связностью к текущему
            max_connection = -1
            best_merge_idx = -1
            
            for i in range(len(segments)):
                if i != min_idx:
                    # Считаем суммарный вес связей между сегментами
                    connection = sum(matrix[u][v] for u in segments[min_idx] for v in segments[i] if matrix[u][v] > 0)
                    
                    if connection > max_connection:
                        max_connection = connection
                        best_merge_idx = i
            
            if best_merge_idx != -1:
                # Объединяем сегменты
                segments[best_merge_idx].update(segments[min_idx])
                del segments[min_idx]
                changed = True
    
    # Преобразуем множества в списки и сортируем для удобства
    return [sorted(list(seg)) for seg in segments]

