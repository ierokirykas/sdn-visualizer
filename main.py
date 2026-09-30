import sys
import logging
from PyQt5.QtWidgets import QApplication
from core.app import SDNVisualizerApp

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sdn_visualizer.log',
    filemode='w'
)

logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Обработчик неотловленных исключений"""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Установка обработчика исключений
sys.excepthook = handle_exception

if __name__ == '__main__':
    try:
        logger.info("Starting SDN Visualizer")  
        app = QApplication(sys.argv)
        window = SDNVisualizerApp()
        window.show()
        # Добавим лог для проверки
        logger.debug("Main window shown")

        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"Application failed: {e}", exc_info=True)

