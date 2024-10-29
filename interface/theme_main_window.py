from PyQt5.QtWidgets import QMainWindow

def setLightMode(window: QMainWindow):
    window.setStyleSheet('''
        QWidget {
            alternate-background-color: #F0F0F0;
            color: #202020;
            selection-background-color: #0078D7;
            selection-color: #DFE1E2;
        }
        QWidget:disabled {
            background-color: #F0F0F0;
            color: #7F7F7F
        }
        QLineEdit {
            background-color: #FFFFFF;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
            border-style: solid;
            border: 1px solid #ABABAB;
            border-radius: 2px;
        }
    ''')

def setDarkMode(window: QMainWindow):
    window.setStyleSheet('''
        QWidget {
            background-color: #202020;
            color: #DFE1E2;
            selection-background-color: #0078D7;
            selection-color: #DFE1E2;
        }
        QWidget:disabled {
            background-color: #202020;
            color: #9C9C9C;
        }
        QLineEdit {
            background-color: #2A2A2A;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 4px;
            padding-right: 4px;
            border-style: solid;
            border: 1px solid #474747;
            border-radius: 2px;
            color: white;
        }
        QCheckBox {
            background-color: #2A2A2A;
            border-style: solid;
            border: 1px solid #474747;
            border-radius: 2px;
            color: white;
        }
    ''')