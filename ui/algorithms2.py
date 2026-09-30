import copy

def dijkstra(matrix, src):
    """
    Реализация алгоритма Дейкстры для поиска кратчайших путей в графе
    
    Аргументы:
    matrix - матрица смежности (двумерный список)
    src - номер начальной вершины (индекс)
    
    Возвращает:
    tuple: (tags, prev) - метки вершин и список предыдущих вершин
    """
    n = len(matrix)
    
    # Шаг 1. Первичная инициализация
    tags = [float('inf')] * n  # метки вершин (расстояния)
    visited = [False] * n      # посещенные вершины
    prev = [float('inf')] * n  # предыдущие вершины
    
    # Шаг 2. Инициализация начальной вершины
    b = src
    
    # Шаг 3. Инициализация меток
    tags[b] = 0
    
    while True:
        # Шаг 4. Обновление меток
        for i in range(n):
            # Если есть связь и вершина не посещена
            if matrix[b][i] != 0 and not visited[i]:
                # Если найден более короткий путь
                if tags[i] > tags[b] + matrix[b][i]:
                    tags[i] = tags[b] + matrix[b][i]
                    prev[i] = b
        
        # Шаг 5. Обновление посещенных вершин
        visited[b] = True
        
        # Шаг 6. Выбор новой постоянной вершины
        min_tag = float('inf')
        b = -1  # временное значение для случая, когда все вершины посещены
        
        for i in range(n):
            if not visited[i] and tags[i] < min_tag:
                min_tag = tags[i]
                b = i
        
        # Если все вершины посещены или недостижимы
        if b == -1:
            break
    
    # Шаг 7. Возвращение данных
    return tags, prev


def recover(prev, src, dst = None):
        if dst == None:
                edges_list = []
                for i in range(1, len(prev)):
                        dst = i
                        edges = [dst]
                        while(src != dst):
                                edges.append(prev[dst])
                                dst = prev[dst]
                        edges.reverse()
                        edges_list.append(edges)
                return(edges_list)
        else:
                edges = [dst]
                while(src != dst):
                        edges.append(prev[dst])
                        dst = prev[dst]
                edges.reverse()
                return([edges])

def yen(matrix, src, dst, k):
    """
    Реализация алгоритма Йена для поиска K кратчайших путей
    
    Аргументы:
    matrix - матрица смежности
    src - начальная вершина
    dst - конечная вершина
    k - количество путей
    
    Возвращает:
    list: список K кратчайших путей
    """
    #print(k, "- K")
    # Первичная инициализация
    routes = []     # найденные пути
    lengths = []    # длины путей
    candidates = [] # пути-кандидаты
    cand_lengths = [] # длины кандидатов
    
    # Нахождение первого кратчайшего пути
    tags, prev = dijkstra(matrix, src)
    
    # Восстановление первого пути (без использования recover)
    first_path = []
    current = dst
    while current != src and current != float('inf'):
        first_path.insert(0, current)
        current = prev[current] if current < len(prev) else float('inf')
    if current == src:
        first_path.insert(0, src)
    else:
        return []
    
    routes.append(first_path)
    lengths.append(tags[dst])
    
    if k == 1:
        return routes[:k]

    # Основной цикл поиска K путей
    for count in range(1, k):
        last_route = routes[-1]
        
        # Перебор вершин для ветвления
        for i in range(len(last_route)-1):
            # Формирование корневого пути
            root_path = last_route[:i+1]
            branch_node = root_path[-1]
            
            # Создание временной матрицы
            temp_matrix = copy.deepcopy(matrix)
            
            # Блокировка предыдущих вершин
            for node in root_path[:-1]:
                # Обнуление строки
                for j in range(len(temp_matrix[node])):
                    temp_matrix[node][j] = 0
                # Обнуление столбца
                for row in temp_matrix:
                    row[node] = 0
            
            # Удаление ребер из существующих путей
            for path in routes:
                if len(path) > i+1 and path[:i+1] == root_path:
                    next_node = path[i+1]
                    temp_matrix[branch_node][next_node] = 0
            
            # Поиск пути от вершины ветвления
            bt_tags, bt_prev = dijkstra(temp_matrix, branch_node)
            
            # Проверка существования пути
            if bt_tags[dst] == float('inf'):
                continue
            
            # Восстановление пути вручную
            current = dst
            new_part = []
            while current != branch_node and current != float('inf'):
                new_part.insert(0, current)
                current = bt_prev[current] if current < len(bt_prev) else float('inf')
            
            if current != branch_node:
                continue
            
            # Формирование полного пути
            full_path = root_path[:-1] + [branch_node] + new_part
            
            # Расчет длины
            length = sum(matrix[full_path[i]][full_path[i+1]] for i in range(len(full_path)-1))
            
            # Проверка уникальности
            if full_path not in candidates:
                candidates.append(full_path)
                cand_lengths.append(length)
        
        # Выбор лучшего кандидата
        if not candidates:
            break
            
        min_index = cand_lengths.index(min(cand_lengths))
        routes.append(candidates.pop(min_index))
        lengths.append(cand_lengths.pop(min_index))
    return routes[:k]

def MCP(src, dst, graph_metric1, graph_metric2, restriction1, restriction2, k):
    """
    Реализация алгоритма MCP (Multi-Constrained Path) для QoS-маршрутизации.
    
    Аргументы:
    src - начальная вершина
    dst - конечная вершина
    graph_metric1 - матрица смежности по первой метрике
    graph_metric2 - матрица смежности по второй метрике
    restriction1 - ограничение по первой метрике
    restriction2 - ограничение по второй метрике
    k - количество кратчайших путей для поиска (передается в алгоритм Йена)
    
    Возвращает:
    list: список маршрутов, удовлетворяющих ограничениям
    """
    # Шаг 2: Находим все возможные маршруты с помощью алгоритма Йена
    all_routes = yen(graph_metric1, src, dst, k)
    
    routs = []
    
    # Шаг 3: Фильтрация по первой метрике
    for route in all_routes:
        # Вычисляем суммарное значение первой метрики для маршрута
        metric1_value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            metric1_value += graph_metric1[u][v]
        
        if metric1_value <= restriction1:
            routs.append(route)
    
    # Шаг 4: Фильтрация по второй метрике (добавляем маршруты, которых еще нет в routs)
    for route in all_routes:
        # Проверяем, не добавлен ли уже этот маршрут на шаге 3
        if route in routs:
            continue
        
        # Вычисляем суммарное значение второй метрики для маршрута
        metric2_value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            metric2_value += graph_metric2[u][v]
        
        if metric2_value <= restriction2:
            routs.append(route)
    
    # Шаг 5: Возвращаем результат
    return routs

def MCOP(src, dst, graph_metric1, graph_metric2, k):
    """
    Реализация алгоритма MCOP (Multi-Constrained Optimal Path) для QoS-маршрутизации.
    
    Аргументы:
    src - начальная вершина
    dst - конечная вершина
    graph_metric1 - матрица смежности по первой метрике (основной критерий оптимизации)
    graph_metric2 - матрица смежности по второй метрике (вторичный критерий оптимизации)
    k - количество кратчайших путей для поиска (передается в алгоритм Йена)
    
    Возвращает:
    list: оптимальный маршрут по двум метрикам или None, если путь не найден
    """
    # Шаг 2: Находим все возможные маршруты с помощью алгоритма Йена
    all_routes = yen(graph_metric1, src, dst, k)
    
    if not all_routes:
        return None
    
    # Шаг 3: Выбираем маршруты с оптимальным значением первой метрики
    # Сначала вычисляем значения первой метрики для всех маршрутов
    metric1_values = []
    for route in all_routes:
        value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            value += graph_metric1[u][v]
        metric1_values.append(value)
    
    # Находим минимальное значение первой метрики
    min_metric1 = min(metric1_values)
    
    # Отбираем маршруты с минимальным значением первой метрики
    temp_routs = []
    for i, route in enumerate(all_routes):
        if metric1_values[i] == min_metric1:
            temp_routs.append(route)
    
    # Шаг 4: Из отобранных маршрутов выбираем оптимальный по второй метрике
    # Вычисляем значения второй метрики для отобранных маршрутов
    metric2_values = []
    for route in temp_routs:
        value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            value += graph_metric2[u][v]
        metric2_values.append(value)
    
    # Находим индекс маршрута с минимальным значением второй метрики
    if not metric2_values:
        return None
    
    min_index = metric2_values.index(min(metric2_values))
    optimal_route = temp_routs[min_index]
    
    # Шаг 5: Возвращаем результат
    return [optimal_route]

def CSP(src, dst, matrix_metric_opt, matrix_metric_restrict, restriction, k):
    """
    Реализация алгоритма CSP (Constrained Shortest Path) для QoS-маршрутизации.
    
    Аргументы:
    src - начальная вершина
    dst - конечная вершина
    matrix_metric_opt - матрица смежности по оптимизируемой метрике (задержка)
    matrix_metric_restrict - матрица смежности по метрике-ограничителю (потери пакетов)
    restriction - максимально допустимое значение метрики-ограничителя
    k - количество кратчайших путей для поиска (передается в алгоритм Йена)
    
    Возвращает:
    list: оптимальный маршрут, удовлетворяющий ограничению, или None, если путь не найден
    """
    # Шаг 2: Находим все возможные маршруты с помощью алгоритма Йена
    # Используем оптимизируемую метрику (задержку) для поиска кратчайших путей
    all_routes = yen(matrix_metric_opt, src, dst, k)
    
    if not all_routes:
        return None
    
    # Шаг 3: Фильтруем маршруты по ограничению (потери пакетов)
    temp_routs = []
    for route in all_routes:
        # Вычисляем суммарное значение метрики-ограничителя для маршрута
        restrict_value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            restrict_value += matrix_metric_restrict[u][v]
        
        # Проверяем ограничение
        if restrict_value <= restriction:
            temp_routs.append(route)
    
    # Если нет маршрутов, удовлетворяющих ограничению
    if not temp_routs:
        return None
    
    # Шаг 4: Выбираем из оставшихся маршрутов оптимальный по оптимизируемой метрике
    # Вычисляем значения оптимизируемой метрики (задержки) для отфильтрованных маршрутов
    opt_values = []
    for route in temp_routs:
        value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            value += matrix_metric_opt[u][v]
        opt_values.append(value)
    
    # Находим маршрут с минимальным значением оптимизируемой метрики
    min_index = opt_values.index(min(opt_values))
    optimal_route = temp_routs[min_index]
    
    # Шаг 5: Возвращаем результат
    return [optimal_route]

def LARAC(src, dst, graph_metric1, graph_metric2, restriction1, restriction2, lambda_val, k):
    """
    Реализация алгоритма LARAC (Lagrangian Relaxation Based Aggregated Cost)
    
    Аргументы:
    src - начальная вершина
    dst - конечная вершина
    graph_metric1 - матрица смежности по первой метрике
    graph_metric2 - матрица смежности по второй метрике
    restriction1 - ограничение по первой метрике
    restriction2 - ограничение по второй метрике
    lambda_val - коэффициент значимости λ
    k - количество кратчайших путей для поиска
    
    Возвращает:
    list: список маршрутов, удовлетворяющих обобщенному ограничению
    """
    #print(k, "- K")
    # Шаг 2: Создание матрицы обобщенной метрики
    n = len(graph_metric1)
    graph_aggregat = [[0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            graph_aggregat[i][j] = graph_metric1[i][j] + lambda_val * graph_metric2[i][j]
    
    # Шаг 3: Вычисление обобщенного ограничения
    restriction_aggregat = restriction1 + lambda_val * restriction2
    
    # Шаг 4: Поиск всех возможных маршрутов алгоритмом Йена
    all_routes = yen(graph_aggregat, src, dst, k)
    #print(all_routes, "- All routes Ryu")
    # Шаг 5: Фильтрация маршрутов по обобщенному ограничению
    routs = []
    
    for route in all_routes:
        # Вычисление обобщенной метрики для маршрута
        aggregat_value = 0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            aggregat_value += graph_aggregat[u][v]
        
        # Проверка ограничения
        if aggregat_value <= restriction_aggregat:
            routs.append(route)
    #print(routs, "Routs")
    # Шаг 6: Возврат результата
    return routs

### Пример использования:
##if __name__ == "__main__":
##    # Пример матриц смежности
##    graph_metric1 = [
##        [0, 7, 9, 0, 0, 14],
##        [7, 0, 10, 15, 0, 0],
##        [9, 10, 0, 12, 0, 2],
##        [0, 15, 12, 0, 6, 0],
##        [0, 0, 0, 6, 0, 9],
##        [14, 0, 2, 0, 9, 0]
##    ]
##    
##    graph_metric2 = [
##        [0, 2, 1, 0, 0, 3],
##        [2, 0, 2, 4, 0, 0],
##        [1, 2, 0, 3, 0, 1],
##        [0, 4, 3, 0, 2, 0],
##        [0, 0, 0, 2, 0, 3],
##        [3, 0, 1, 0, 3, 0]
##    ]
##    
##    src = 0
##    dst = 4
##    k = 5
##    
##    result = CSP(src, dst, graph_metric1, graph_metric2,23)
##    print("Оптимальный маршрут:", result)
