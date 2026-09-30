from PyQt5.QtGui import QColor


# Базовая палитра на основе цветов иконок
THEME = {
    "bg_start": "#93b2f4",   # основной цвет иконок
    "bg_end": "#f8f9fa",     # очень светлый серый
    "surface": "#59698c",    # светлый оттенок основного
    "primary": "#ffffff",    # акцент (основной цвет)
    "primary_dark": "#30487b",  # теневой цвет иконок
    "chip": "#e8ecf7",       # очень светлый оттенок основного
    "text_on_light": "#2c3e50",
    "text_on_dark": "#ffffff",
}


def qcolor(hex_color: str) -> QColor:
    """Утилита для получения QColor из HEX."""
    return QColor(hex_color)


def build_stylesheet() -> str:
    """Возвращает общий стиль приложения на базе палитры."""
    return f"""
    QMainWindow {{
        background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
            stop:0 {THEME['bg_start']}, stop:1 {THEME['bg_end']});
    }}

    QMenuBar {{
        background: {THEME['primary_dark']};
        color: {THEME['text_on_dark']};
    }}
    QMenuBar::item:selected {{
        background: {THEME['surface']};
    }}

    QMenu {{
        background: {THEME['primary_dark']};
        color: {THEME['text_on_dark']};
        border: 1px solid {THEME['surface']};
    }}
    QMenu::item:selected {{
        background: {THEME['surface']};
    }}

    QToolBar {{
        background: {THEME['primary_dark']};
        border: none;
        spacing: 6px;
    }}
    QToolButton {{
        color: {THEME['text_on_dark']};
        background: transparent;
    }}
    QToolButton:hover {{
        background: {THEME['surface']};
    }}

    QDockWidget::title {{
        background: transparent;
        color: transparent;
        padding: 0px;
        border: none;
    }}
    QDockWidget {{
        titlebar-close-icon: url(none);
        titlebar-normal-icon: url(none);
        background: transparent;
        border: none;
    }}

    QMessageBox {{
        background: {THEME['chip']};
        color: {THEME['text_on_light']};
    }}
    QLabel {{ color: {THEME['text_on_light']}; }}
    QPushButton {{
        background: {THEME['surface']};
        color: {THEME['text_on_dark']};
        border: none;
        padding: 6px 10px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background: {THEME['primary']};
    }}
    """


def apply_theme(widget) -> None:
    """Применяет стиль к переданному виджету (обычно главное окно)."""
    widget.setStyleSheet(build_stylesheet())


