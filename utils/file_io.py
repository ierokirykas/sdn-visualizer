from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from xml.etree import ElementTree as ET
from core.models import DeviceType, Device, Link
import logging

logger = logging.getLogger(__name__)

def import_from_xml(file_path):
    """Импортирует топологию сети из XML-файла в формате topology.sdn12.xml"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        devices = {}
        links = {}
        
        # Словари для хранения устройств по порядку
        hosts = []
        switches = []
        controllers = []
        
        # Импорт хостов
        hosts_elem = root.find('Hosts')
        if hosts_elem is not None:
            for i, host in enumerate(hosts_elem.findall('Host')):
                device_id = f"host{i+1}"
                device = Device(
                    id=device_id,
                    type=DeviceType.HOST,
                    x=float(host.get('x')),
                    y=float(host.get('y')),
                    ip=host.get('ip', ""),
                    mac=host.get('mac', "")
                )
                devices[device_id] = device
                hosts.append(device_id)
        
        # Импорт коммутаторов
        switches_elem = root.find('Switches')
        if switches_elem is not None:
            for i, switch in enumerate(switches_elem.findall('Switch')):
                device_id = f"switch{i+1}"
                device = Device(
                    id=device_id,
                    type=DeviceType.SWITCH,
                    x=float(switch.get('x')),
                    y=float(switch.get('y'))
                )
                devices[device_id] = device
                switches.append(device_id)
        
        # Импорт контроллеров
        controllers_elem = root.find('Controllers')
        if controllers_elem is not None:
            for i, controller in enumerate(controllers_elem.findall('Controller')):
                device_id = f"controller{i+1}"
                device = Device(
                    id=device_id,
                    type=DeviceType.CONTROLLER,
                    x=float(controller.get('x')),
                    y=float(controller.get('y')),
                    ip=controller.get('ip', "127.0.0.1"),
                    port=int(controller.get('port', 6653))
                )
                devices[device_id] = device
                controllers.append(device_id)
        
        # Функция для получения устройства по его ролевому имени
        def get_device_by_role_name(role_name):
            """Преобразует ролевое имя (h1, s2, c0) в реальное устройство"""
            if not role_name:
                return None
                
            prefix = role_name[0].lower()
            try:
                index = int(role_name[1:])
            except ValueError:
                return None
                
            if prefix == 'h' and 1 <= index <= len(hosts):
                return hosts[index-1]
            elif prefix == 's' and 1 <= index <= len(switches):
                return switches[index-1]
            elif prefix == 'c' and 0 <= index < len(controllers):
                return controllers[index]
            return None
        
        # Импорт связей типа Switch-Host (SSLinks)
        sslinks = root.find('SSLinks')
        if sslinks is not None:
            for link in sslinks.findall('Link'):
                node1 = get_device_by_role_name(link.get('node1'))
                node2 = get_device_by_role_name(link.get('node2'))
                
                if node1 and node2:
                    link_id = f"{node1}-{node2}"
                    links[link_id] = Link(
                        source=node1,
                        target=node2,
                        bandwidth=float(link.get('bandwidth', 1.0)),
                        delay=float(link.get('delay', 1.0)),
                        loss=float(link.get('loss', 0.0))
                    )
        
        # Импорт связей типа Controller-Switch (CSLinks)
        cslinks = root.find('CSLinks')
        if cslinks is not None:
            for link in cslinks.findall('Link'):
                node1 = get_device_by_role_name(link.get('node1'))
                node2 = get_device_by_role_name(link.get('node2'))
                
                if node1 and node2:
                    link_id = f"{node1}-{node2}"
                    links[link_id] = Link(
                        source=node1,
                        target=node2,
                        bandwidth=1.0,  # По умолчанию
                        delay=1.0,     # По умолчанию
                        loss=0.0        # По умолчанию
                    )
        
        logger.info(f"Imported {len(devices)} devices and {len(links)} links from {file_path}")
        return {"devices": devices, "links": links}
    
    except Exception as e:
        logger.error(f"Error importing XML: {e}", exc_info=True)
        return {"devices": {}, "links": {}}

def export_to_xml(devices, links, file_path):
    """Экспортирует топологию сети в XML-формате topology.sdn12.xml"""
    try:
        # Создаем корневой элемент
        network = ET.Element("Network")
        
        # Группируем устройства по типам
        hosts = [d for d in devices.values() if d.type == DeviceType.HOST]
        switches = [d for d in devices.values() if d.type == DeviceType.SWITCH]
        controllers = [d for d in devices.values() if d.type == DeviceType.CONTROLLER]
        
        # Создаем отображение ID -> короткое имя
        device_to_role = {}
        
        # Хосты: h1, h2, ...
        for i, host in enumerate(hosts, start=1):
            device_to_role[host.id] = f"h{i}"
        
        # Коммутаторы: s1, s2, ...
        for i, switch in enumerate(switches, start=1):
            device_to_role[switch.id] = f"s{i}"
        
        # Контроллеры: c0, c1, ...
        for i, controller in enumerate(controllers):
            device_to_role[controller.id] = f"c{i}"
        
        # Добавляем хосты
        hosts_elem = ET.SubElement(network, "Hosts")
        for host in hosts:
            ET.SubElement(hosts_elem, "Host",
                x=str(host.x),
                y=str(host.y),
                ip=host.ip,
                mac=host.mac
            )
        
        # Добавляем коммутаторы
        switches_elem = ET.SubElement(network, "Switches")
        for switch in switches:
            ET.SubElement(switches_elem, "Switch",
                x=str(switch.x),
                y=str(switch.y)
            )
        
        # Добавляем контроллеры
        controllers_elem = ET.SubElement(network, "Controllers")
        for controller in controllers:
            ET.SubElement(controllers_elem, "Controller",
                x=str(controller.x),
                y=str(controller.y),
                ip=controller.ip,
                port=str(controller.port)
            )
        
        # Создаем разделы для связей
        sslinks_elem = ET.SubElement(network, "SSLinks")
        cslinks_elem = ET.SubElement(network, "CSLinks")
        
        # Обрабатываем все связи
        for link in links.values():
            src_type = devices[link.source].type
            dst_type = devices[link.target].type
            
            # Определяем устройства связи в правильном порядке
            if src_type == DeviceType.SWITCH:
                node1 = device_to_role[link.source]
                node2 = device_to_role[link.target]
            else:
                node1 = device_to_role[link.target]
                node2 = device_to_role[link.source]
            
            # CSLinks: только контроллер ↔ коммутатор
            if {src_type, dst_type} == {DeviceType.CONTROLLER, DeviceType.SWITCH}:
                # Для CSLinks контроллер всегда node1, коммутатор всегда node2
                if src_type == DeviceType.CONTROLLER:
                    cs_node1 = device_to_role[link.source]
                    cs_node2 = device_to_role[link.target]
                else:
                    cs_node1 = device_to_role[link.target]
                    cs_node2 = device_to_role[link.source]
                
                ET.SubElement(cslinks_elem, "Link",
                    node1=cs_node1,
                    node2=cs_node2
                )
            # Все остальные связи - SSLinks
            else:
                ET.SubElement(sslinks_elem, "Link",
                    node1=node1,
                    node2=node2,
                    bandwidth=str(link.bandwidth),
                    delay=str(link.delay),
                    loss=str(link.loss)
                )
        
        # Добавляем пустой раздел Texts для совместимости
        ET.SubElement(network, "Texts")
        
        # Форматируем и сохраняем XML
        xml_str = minidom.parseString(ET.tostring(network)).toprettyxml(indent="\t")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        return True
    
    except Exception as e:
        logger.error(f"Error exporting XML: {e}", exc_info=True)
        return False

def export_to_python(devices, links, file_path):
    """Экспортирует топологию в Python-скрипт для Mininet"""
    try:
        # Генерируем разделы
        controllers = generate_controllers(devices)
        hosts = generate_hosts(devices)
        switches = generate_switches(devices)
        switch_links = generate_links(devices, links)
        switch_starts = generate_switch_starts(devices)
        
        template = f"""from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

def topology():
    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)
    
    # Add controllers
{controllers}
    
    # Add hosts
{hosts}
    
    # Add switches
{switches}
    
    # Add links
{switch_links}
    
    # Start controllers and switches
{switch_starts}
    net.build()
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
"""
        with open(file_path, 'w') as f:
            f.write(template)
        return True
    except Exception as e:
        logger.error(f"Error exporting Python: {e}")
        return False

def generate_controllers(devices):
    """Генерирует код для добавления контроллеров"""
    controllers = [d for d in devices.values() if d.type == DeviceType.CONTROLLER]
    if not controllers:
        return "    # No controllers defined"
    
    return "\n".join(
        f"    c{i} = net.addController('c{i}', controller=RemoteController, ip='{d.ip}', port={d.port})"
        for i, d in enumerate(controllers)
    )

def generate_hosts(devices):
    """Генерирует код для добавления хостов"""
    hosts = [d for d in devices.values() if d.type == DeviceType.HOST]
    if not hosts:
        return "    # No hosts defined"
    
    return "\n".join(
        f"    {d.id} = net.addHost('{d.id}', mac='{d.mac}', ip='{d.ip}')"
        for d in hosts
    )

def generate_switches(devices):
    """Генерирует код для добавления свитчей"""
    switches = [d for d in devices.values() if d.type == DeviceType.SWITCH]
    if not switches:
        return "    # No switches defined"
    
    return "\n".join(
        f"    {d.id} = net.addSwitch('{d.id}')"
        for d in switches
    )

def generate_links(devices, links):
    """Генерирует код для добавления линков (исключая контроллеры)"""
    link_lines = []
    for link in links.values():
        src = devices[link.source]
        dst = devices[link.target]
        
        # Пропускаем связи с контроллерами
        if src.type == DeviceType.CONTROLLER or dst.type == DeviceType.CONTROLLER:
            continue
            
        link_lines.append(
            f"    net.addLink({src.id}, {dst.id}, "
            f"bw={link.bandwidth}, delay='{link.delay}ms', loss={link.loss})"
        )
    
    if not link_lines:
        return "    # No links defined"
    
    return "\n".join(link_lines)

def generate_switch_starts(devices):
    """Генерирует код для старта свитчей"""
    switches = [d for d in devices.values() if d.type == DeviceType.SWITCH]
    controllers = [d for d in devices.values() if d.type == DeviceType.CONTROLLER]
    
    if not switches:
        return "    # No switches to start"
    
    if not controllers:
        return "    # No controllers defined for switch startup"
    
    # Используем первый контроллер
    controller_name = "c0"
    
    lines = [f"    {controller_name}.start()"]
    lines += [f"    {switch.id}.start([{controller_name}])" for switch in switches]
    
    return "\n".join(lines)

def export_to_metric_file(devices, links, file_path):
    """Экспортирует данные о связях между коммутаторами в текстовый формат"""
    try:
        # Создаем словарь для преобразования ID коммутаторов в числовой формат
        switch_id_map = {}
        switch_counter = 1
        
        # Собираем все коммутаторы и присваиваем им числовые ID
        for device in devices.values():
            if device.type == DeviceType.SWITCH:
                # Извлекаем числовую часть из ID (например, "switch1" -> 1)
                try:
                    num_part = ''.join(filter(str.isdigit, device.id))
                    if num_part:
                        switch_id_map[device.id] = int(num_part)
                    else:
                        switch_id_map[device.id] = switch_counter
                        switch_counter += 1
                except Exception:
                    switch_id_map[device.id] = switch_counter
                    switch_counter += 1
        
        # Собираем все связи между коммутаторами
        switch_links = []
        for link in links.values():
            src_device = devices.get(link.source)
            dst_device = devices.get(link.target)
            
            if not src_device or not dst_device:
                continue
            
            if src_device.type == DeviceType.SWITCH and dst_device.type == DeviceType.SWITCH:
                src_num = switch_id_map.get(src_device.id)
                dst_num = switch_id_map.get(dst_device.id)
                
                if src_num and dst_num:
                    # Преобразуем значения в целые числа
                    delay = int(link.delay)
                    bandwidth = int(link.bandwidth)
                    loss = int(link.loss)
                    
                    # Упорядочиваем ID по возрастанию
                    min_id = min(src_num, dst_num)
                    max_id = max(src_num, dst_num)
                    switch_links.append((min_id, max_id, delay, bandwidth, loss))
        
        # Удаляем дубликаты (если есть)
        unique_links = list(set(switch_links))
        
        # Сортируем по первому узлу, затем по второму
        unique_links.sort(key=lambda x: (x[0], x[1]))
        
        # Записываем в файл
        with open(file_path, 'w') as f:
            for link in unique_links:
                line = f"{link[0]}-{link[1]}:{link[2]},{link[3]},{link[4]}\n"
                f.write(line)
        
        return True
    except Exception as e:
        logger.error(f"Error exporting metric file: {e}")
        return False