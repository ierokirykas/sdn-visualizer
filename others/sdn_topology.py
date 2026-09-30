# others/sdn_topology.py
import re

def __read_metrics(metric_data_file_name):
    """
    Функция возвращает метрики каналов связи
    """
    try:
        with open(metric_data_file_name, 'r') as metric_data_file:
            metric_data_file_lines = metric_data_file.readlines()
    except Exception as e:
        print(f"Error reading metric file: {e}")
        return []
 
    metrics = []
    pattern = re.compile(
        r'(?P<node1>\d+)-(?P<node2>\d+):'
        r'(?P<metric1>\d+),(?P<metric2>\d+),(?P<metric3>\d+)'
    )
    
    for line in metric_data_file_lines:
        match = pattern.search(line)
        if match:
            groupdict = match.groupdict()
            metrics.append([
                int(groupdict['node1']),
                int(groupdict['node2']),
                int(groupdict['metric1']),
                int(groupdict['metric2']),
                int(groupdict['metric3'])
            ])
    
    return metrics

def read_matrix(size, metric_data_file):
    """
    Функция возвращает матрицу смежности графа сети
    """
    metrics = __read_metrics(metric_data_file)
    graph = []
    
    for i in range(3): 
        graph.append([])
        
    for k in range(3):
        for i in range(size):
            graph[k].append([])
            for j in range(size):
                graph[k][i].append(0)

        for link in metrics:
            vertex1 = link[0] - 1
            vertex2 = link[1] - 1
            weight = link[2+k]
            graph[k][vertex1][vertex2] = weight

    return graph