from PyQt5.QtWidgets import QMainWindow

def setLightMode(window: QMainWindow):
    window.setStyleSheet('''
        QWidget {
            color: #000000;
            selection-background-color: #0078D7;
            selection-color: #DFE1E2;
        }
        QWidget:disabled {
            color: #7F7F7F;
        }
        QLineEdit {
            background-color: #F0F0F0;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
        }
        QLineEdit {
            background-color: white;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
        }
        QComboBox {
            background-color: #F0F0F0;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
        }
        QTabWidget {
            background-color: white;
        }
    ''')

def setDarkMode(window: QMainWindow):
    window.setStyleSheet('''
        QWidget {
            color: #DFE1E2;
            background-color: #202020;
            selection-background-color: #0078D7;
            selection-color: #DFE1E2;
        }
        QWidget:disabled {
            background-color: #202020;
            color: #9C9C9C;
        }
        QLineEdit {
            color: #DFE1E2;
            background-color: #2A2A2A;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
        }
        QCheckBox {
            color: #DFE1E2;
            background-color: #2A2A2A;
            border-style: solid;
            border: 1px solid #474747;
            border-radius: 2px;
        }
        QComboBox {
            background-color: #2A2A2A;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
        }
        QTabBar {
            background-color: #202020;
        }
        QSpinBox {
            background-color: #2A2A2A;
        }
    ''')