from dataclasses import dataclass
from enum import Enum

class DeviceType(Enum):
    HOST = "Host"
    SWITCH = "Switch"
    CONTROLLER = "Controller"

@dataclass
class Device:
    id: str
    type: DeviceType
    x: float
    y: float
    ip: str = ""
    mac: str = ""
    port: int = 0  # Порт для контроллера
    
@dataclass
class Link:
    source: str
    target: str
    bandwidth: float = 1.0  # Mbps
    delay: float = 1.0      # ms
    loss: float = 0.0       # %
