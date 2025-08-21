# -*- encoding:utf-8 -*-


def _get_default_font():
    import sys
    if sys.platform == 'win32':  # Windows
        return 'Microsoft Yahei'
    elif sys.platform == 'darwin':  # macOS
        return 'Helvetica'
    else:  # Linux
        return 'DejaVu Sans'


GLOBAL_STYLESHEET = f"""
* {{
    font-family: {_get_default_font()};
}}

QPushButton {{
    background-color: #FAFBFC;
    border: 1px solid rgba(27, 31, 35, 0.15);
    border-radius: 3px;
    color: #24292E;
    font-size: 12px;
    padding: 6px 10px;
}}

QPushButton:hover {{
    background-color: #F3F4F6;
}}

QPushButton:pressed {{
    background-color: #EDEFF2;
}}

QPushButton:checked {{
    background-color: #EDEFF2;
}}

QPushButton:disabled {{
    background-color: #FAFBFC;
    border-color: rgba(27, 31, 35, 0.15);
    color: #959DA5;
}}

QLineEdit {{
    border: 1px solid #D1D5DA;
    border-radius: 3px;
    padding: 6px 8px;
    font-size: 12px;
    color: #24292E;
}}

QLineEdit:hover {{
    border-color: #0366D6;
}}

QLineEdit:focus {{
    border-color: #0366D6;
    outline: none;
}}

QLineEdit:disabled {{
    background-color: #F0F0F0;
    border-color: rgba(27, 31, 35, 0.15);
    color: #959DA5;
}}

QLineEdit#codeStyleLineEdit {{
    font: 13px "Consolas";
}}

CreateStacksListWidget {{
    border: none;
    font: 13px "Consolas";
    color: #24292E;
}}

CreateStacksListWidget::item {{
    padding: 2px 0px;
}}

QGroupBox {{
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0px 5px;
}}

WidgetPropsTreeWidget {{
    border: none;
}}
"""
