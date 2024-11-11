from interface.theme_main_window import setLightMode, setDarkMode
from models.find_replace import FindReplace
from models.video_converter import ConvertVideoThread
from models.video_downloader import VideoDownloader, DownloadThread
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAction, QApplication, QCheckBox, QComboBox, QFileDialog, QLineEdit,
    QMainWindow, QProgressBar, QPushButton, QStatusBar
)
from PyQt5.uic import loadUi
from widgets.file_info_widget import FileInfoWidget
from widgets.numbered_text_edit import NumberedTextEdit
import json
import os
import sys

class MainUI(QMainWindow):
    CUSTOM_FPS_ENABLED = 2

    def __init__(self):
        super(MainUI, self).__init__()
        self.SETTINGS_FILE = "settings.json"
        self.setup_ui()
        self.connect_signals()
        self.load_settings()

    def setup_ui(self):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))  # Корректный путь для PyInstaller
        ui_path = os.path.join(base_path, "interface", "main_window.ui")  # Используем base_path для формирования пути
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")

        loadUi(ui_path, self)
        self.centralwidget.setContentsMargins(9, 0, 9, 9)
        self.tabWidget.setContentsMargins(9, 0, 9, 9)

        # Инициализация виджетов
        self.text_convert: NumberedTextEdit = self.findChild(NumberedTextEdit, "textEdit1")
        self.text_edit_middle: NumberedTextEdit = self.findChild(NumberedTextEdit, "textEdit2")
        self.text_edit_right: NumberedTextEdit = self.findChild(NumberedTextEdit, "textEdit3")
        self.current_fileName: QComboBox = self.findChild(QComboBox, "current_fileName")
        self.comboBoxFind: QComboBox = self.findChild(QComboBox, "comboBoxFind")
        self.comboBoxReplace: QComboBox = self.findChild(QComboBox, "comboBoxReplace")
        self.file_info_widget = FileInfoWidget(self.text_convert, self.text_edit_middle, self.text_edit_right, self.current_fileName, self)
        self.progressBar_convert: QProgressBar = self.findChild(QProgressBar, "progressBar_convert")
        self.path_save: QLineEdit = self.findChild(QLineEdit, "path_save")
        self.path_ffmpeg: QLineEdit = self.findChild(QLineEdit, "path_ffmpeg")
        self.path_ytdlp: QLineEdit = self.findChild(QLineEdit, "path_ytdlp")
        self.statusbar: QStatusBar = self.findChild(QStatusBar, "statusbar")
        self.btn_render: QPushButton = self.findChild(QPushButton, "btn_render")
        self.checkBox_setDarkMode = self.findChild(QCheckBox, "checkBox_setDarkMode")
        self.find_replace = FindReplace(self.text_edit_middle, self.comboBoxFind, self.comboBoxReplace)
        self.comboBoxProxy: QComboBox = self.findChild(QComboBox, "comboBoxProxy")

        # QAction
        self.action_textEdit1 = self.findChild(QAction, "action_textEdit1")
        self.action_textEdit2 = self.findChild(QAction, "action_textEdit2")
        self.action_textEdit3 = self.findChild(QAction, "action_textEdit3")
        self.action_textEdit3_refresh = self.findChild(QAction, "action_textEdit3_refresh")
        self.action_replace = self.findChild(QAction, "action_replace")

    def connect_signals(self):
        # Настройка событий
        self.fpsEnable.stateChanged.connect(self.fpsCustom)
        self.checkBox_alwaysOnTop.stateChanged.connect(self.update_always_on_top)
        self.btn_render.clicked.connect(self.renderPressed)
        self.btn_path_save.clicked.connect(self.select_folder_path_save)
        self.btn_path_ffmpeg.clicked.connect(self.select_path_ffmpeg)
        self.btn_path_ytdlp.clicked.connect(self.select_ytdlp_path)
        self.text_edit_right.setReadOnly(True)
        self.checkBox_setDarkMode.stateChanged.connect(self.toggleDarkMode)

        # QAction сигналы
        self.action_textEdit1.triggered.connect(self.on_action_textEdit1_triggered)
        self.action_textEdit2.triggered.connect(self.on_action_textEdit2_triggered)
        self.action_textEdit3.triggered.connect(self.on_action_textEdit3_triggered)

        self.action_textEdit3_refresh.triggered.connect(self.textEdit3RectColor)

        self.btn_find.clicked.connect(self.find_replace.find_next)
        self.btn_find_all.clicked.connect(self.find_replace.find_all)
        self.btn_replace.clicked.connect(self.find_replace.replace)
        self.btn_replace_all.clicked.connect(self.find_replace.replace_all)

    def mousePressEvent(self, event):
        focus_widgets = [
            self.path_save,
            self.path_ffmpeg,
            self.path_ytdlp,
            self.text_convert,
            self.text_edit_middle,
            self.text_edit_right,
            self.current_fileName,
            self.crfCount,
            self.fpsCount,
            self.comboBoxFind,
            self.comboBoxReplace,
            self.comboBoxProxy
        ]

        if not any(widget.underMouse() for widget in focus_widgets):
            for widget in focus_widgets:
                widget.clearFocus()
            print("Курсор мыши находится вне полей ввода.")

    def update_always_on_top(self):
        if self.checkBox_alwaysOnTop.isChecked():
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()  # Обновление окна

    def toggleDarkMode(self):
        if self.checkBox_setDarkMode.isChecked():
            setDarkMode(self)
            self.text_convert.lineNumberArea.setDarkMode(True)
            self.text_edit_middle.lineNumberArea.setDarkMode(True)
            self.text_edit_right.lineNumberArea.setDarkMode(True)
        else:
            setLightMode(self)
            self.text_convert.lineNumberArea.setDarkMode(False)
            self.text_edit_middle.lineNumberArea.setDarkMode(False)
            self.text_edit_right.lineNumberArea.setDarkMode(False)

        # Обновляем цвет заливки области нумерации строк при переключении темы
        self.updateLineNumberAreaColors()

    def updateLineNumberAreaColors(self):
        # Определяем цвет в зависимости от состояния галочки
        if self.action_textEdit3_refresh.isChecked():
            custom_color = QColor("#F0F0F0") if not self.checkBox_setDarkMode.isChecked() else QColor("#2A2A2A")
        else:
            custom_color = QColor("#FFFFFF") if not self.checkBox_setDarkMode.isChecked() else QColor("#202020")

        # Применяем цвет к области нумерации строк
        self.text_edit_right.lineNumberArea.setRightRectColor(custom_color)

    def textEdit3RectColor(self):
        # Определяем цвет в зависимости от состояния галочки и темы
        custom_color = QColor("#F0F0F0") if (self.action_textEdit3_refresh.isChecked() and not self.checkBox_setDarkMode.isChecked()) else QColor("#2A2A2A") if self.action_textEdit3_refresh.isChecked() else QColor("#FFFFFF") if not self.checkBox_setDarkMode.isChecked() else QColor("#202020")

        # Применяем цвет к области нумерации строк textEdit3
        self.text_edit_right.lineNumberArea.setRightRectColor(custom_color)

    def _process_path(self, path: str) -> str:
        drive, path = os.path.splitdrive(path)
        return drive + path.replace("/", "\\")

    def select_folder_path_save(self):
        folder_path: str = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if folder_path:
            self.path_save.setText(self._process_path(folder_path))
            print(f"Выбрана папка для сохранения: {folder_path}")

    def renderPressed(self):
        print("Кнопка нажата, начинаем обработку...")

        input_text = self.text_convert.toPlainText().strip().splitlines()
        urls = []
        files = []

        for line in input_text:
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line)
            else:
                files.append(line)

        output_dir = self.path_save.text()
        ytdlp_path = self.path_ytdlp.text()
        proxy = self.comboBoxProxy.currentText().strip()  # Получаем текст из QComboBoxProxy

        if urls:
            self.download_thread = DownloadThread(urls, output_dir, ytdlp_path, proxy)  # Передаем прокси
            self.download_thread.start()

        if files:
            self.convert_video(files)

    def fpsCustom(self, state: int):
        if state == self.CUSTOM_FPS_ENABLED:
            self.fpsCount.setEnabled(True)
            print("Custom FPS включен.")
        else:
            self.fpsCount.setEnabled(False)
            print("Custom FPS выключен.")

    def select_path_ffmpeg(self):
        file_path: str = QFileDialog.getOpenFileName(self, "Выберите путь к ffmpeg")[0]
        if file_path:
            if os.path.exists(file_path):
                self.path_ffmpeg.setText(self._process_path(file_path))
                print(f"Выбран путь к ffmpeg: {file_path}")

    def select_ytdlp_path(self):
        file_path: str = QFileDialog.getOpenFileName(self, "Выберите путь к ytdlp")[0]
        if file_path:
            if os.path.exists(file_path):
                self.path_ytdlp.setText(self._process_path(file_path))
                print(f"Выбран путь к ytdlp: {file_path}")

    def convert_video(self, input_files):
        codec = self.list_codec.currentText()
        crf = self.crfCount.value()
        # Передаем пользовательский FPS, если галочка установлена
        fps = self.fpsCount.value() if self.fpsEnable.isChecked() else None
        preset = self.list_ffmpeg_preset.currentText()
        input_files = self.text_convert.toPlainText().splitlines()
        output_dir = self.path_save.text()
        ffmpeg_path = self.path_ffmpeg.text()
        current_file_name = self.current_fileName.currentText()

        processed_input_files = []
        for file in input_files:
            file = file.strip().strip('"')
            if file.startswith("file:///"):
                file = file[8:]
            processed_input_files.append(file)

        print(f"Codec: {codec}, CRF: {crf}, FPS: {fps}, PRESET: {preset}")
        print(f"Input Files: {processed_input_files}")
        print(f"Output Directory: {output_dir}")
        print(f"FFmpeg Path: {ffmpeg_path}")
        print(f"Current File Name: {current_file_name}")

        if processed_input_files and output_dir and ffmpeg_path:
            # Передаем выбранный FPS или None в поток для обработки
            self.thread = ConvertVideoThread(codec, crf, fps, preset, processed_input_files, output_dir, ffmpeg_path, current_file_name, self.text_edit_middle)
            self.thread.progress_signal.connect(self.update_progress_bar)
            self.thread.status_signal.connect(self.update_status)
            self.thread.start()
        else:
            print("Отсутствуют необходимые параметры для конвертации.")

    def update_progress_bar(self, value: int):
        self.progressBar_convert.setValue(value)

    def update_status(self, message: str):
        self.statusbar.showMessage(message)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def save_settings(self):
        settings = {
            "current_fileName": self.current_fileName.currentText(),
            "list_codec": self.list_codec.currentText(),
            "crfCount": self.crfCount.value(),
            "fpsEnable": self.fpsEnable.isChecked(),
            "fpsCount": self.fpsCount.value(),
            "list_ffmpeg_preset": self.list_ffmpeg_preset.currentText(),
            "path_save": self.path_save.text(),
            "path_ffmpeg": self.path_ffmpeg.text(),
            "path_ytdlp": self.path_ytdlp.text(),
            "checkBox_savePos": self.checkBox_savePos.isChecked(),
            "checkBox_saveSize": self.checkBox_saveSize.isChecked(),
            "checkBox_alwaysOnTop": self.checkBox_alwaysOnTop.isChecked(),
            "window_fullscreen": self.isFullScreen(),    # Сохраняем статус полноэкранного режима
            "window_maximized": self.isMaximized(),      # Сохраняем статус развернутого окна
            "checkBox_setDarkMode": self.checkBox_setDarkMode.isChecked(),
            "action_textEdit1": self.action_textEdit1.isChecked(),  # Сохраняем статус action_textEdit1
            "action_textEdit2": self.action_textEdit2.isChecked(),  # Сохраняем статус action_textEdit2
            "action_textEdit3": self.action_textEdit3.isChecked(),  # Сохраняем статус action_textEdit3
            "action_textEdit3_refresh": self.action_textEdit3_refresh.isChecked(),  # Сохраняем статус action_textEdit3_refresh
            "action_replace": self.action_replace.isChecked()
        }

        # Если окно не полноэкранное и не развернутое, сохраняем его положение и размеры
        if self.checkBox_savePos.isChecked() and not self.isFullScreen() and not self.isMaximized():
            settings["window_position"] = {
                "x": self.x(),
                "y": self.y()
            }

        if self.checkBox_saveSize.isChecked() and not self.isFullScreen() and not self.isMaximized():
            settings["window_size"] = {
                "width": self.width(),
                "height": self.height()
            }

        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            setLightMode(self)  # Если файл настроек не существует, устанавливаем светлую тему
            self.action_replace.setChecked(False)  # Устанавливаем action_replace как выключенный
            return

        with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        self.current_fileName.setCurrentText(settings.get("current_fileName", ""))
        self.list_codec.setCurrentText(settings.get("list_codec", ""))
        self.crfCount.setValue(settings.get("crfCount", 23))
        self.fpsEnable.setChecked(settings.get("fpsEnable", False))
        self.fpsCount.setValue(settings.get("fpsCount", 30))
        self.list_ffmpeg_preset.setCurrentText(settings.get("list_ffmpeg_preset", "medium"))
        self.path_save.setText(settings.get("path_save", ""))
        self.path_ffmpeg.setText(settings.get("path_ffmpeg", ""))
        self.path_ytdlp.setText(settings.get("path_ytdlp", ""))
        self.checkBox_savePos.setChecked(settings.get("checkBox_savePos", False))
        self.checkBox_saveSize.setChecked(settings.get("checkBox_saveSize", False))
        self.checkBox_alwaysOnTop.setChecked(settings.get("checkBox_alwaysOnTop", False))
        self.checkBox_setDarkMode.setChecked(settings.get("checkBox_setDarkMode", False))
        self.toggleDarkMode()  # Установить тему в зависимости от состояния чекбокса

        # Восстановление статусов галочек
        self.action_textEdit1.setChecked(settings.get("action_textEdit1", False))
        self.action_textEdit2.setChecked(settings.get("action_textEdit2", True))  # Устанавливаем значение по умолчанию
        self.action_textEdit3.setChecked(settings.get("action_textEdit3", True))  # Устанавливаем значение по умолчанию
        self.action_textEdit3_refresh.setChecked(settings.get("action_textEdit3_refresh", True))  # Устанавливаем значение по умолчанию
        self.action_replace.setChecked(settings.get("action_replace", True))  # Устанавливаем значение по умолчанию как False

        # Восстановление позиции и размера окна, если не включен полноэкранный/развернутый режим
        if self.checkBox_savePos.isChecked() and "window_position" in settings and not settings.get("window_fullscreen", False) and not settings.get("window_maximized", False):
            self.move(settings["window_position"]["x"], settings["window_position"]["y"])

        if self.checkBox_saveSize.isChecked() and "window_size" in settings and not settings.get("window_fullscreen", False) and not settings.get("window_maximized", False):
            self.resize(settings["window_size"]["width"], settings["window_size"]["height"])

        # Восстановление полноэкранного режима
        if settings.get("window_fullscreen", False):
            self.showFullScreen()
        # Восстановление развернутого окна
        elif settings.get("window_maximized", False):
            self.showMaximized()
        else:
            self.showNormal()  # Если окно не развернуто и не полноэкранное, показываем обычное окно

        self.textEdit3RectColor()

    def update_actions(self):
        # Если action_textEdit1 включена
        if self.action_textEdit1.isChecked():
            self.action_textEdit2.setChecked(False)
            self.action_textEdit3.setChecked(False)
        else:
            # Если action_textEdit1 выключена, проверяем другие действия
            if not self.action_textEdit2.isChecked() and not self.action_textEdit3.isChecked():
                self.action_textEdit1.setChecked(True)  # Включаем action_textEdit1

    def on_action_textEdit1_triggered(self):
        # Если action_textEdit1 выключена, включаем action_textEdit2 и action_textEdit3
        if not self.action_textEdit1.isChecked():
            self.action_textEdit2.setChecked(True)
            self.action_textEdit3.setChecked(True)

        # Обновляем действия
        self.update_actions()

    def on_action_textEdit2_triggered(self):
        # Если action_textEdit2 включена, выключаем action_textEdit1
        if self.action_textEdit2.isChecked():
            self.action_textEdit1.setChecked(False)
        # Обновляем действия
        self.update_actions()

    def on_action_textEdit3_triggered(self):
        # Если action_textEdit3 включена, выключаем action_textEdit1
        if self.action_textEdit3.isChecked():
            self.action_textEdit1.setChecked(False)
        # Обновляем действия
        self.update_actions()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Стиль
    window = MainUI()
    window.show()
    sys.exit(app.exec_())