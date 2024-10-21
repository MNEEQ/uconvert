from interface.theme_main_window import setLightMode, setDarkMode
from models.video_converter import ConvertVideoThread
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QLineEdit, QMainWindow, QProgressBar,
    QPushButton, QStatusBar, QVBoxLayout, QWidget
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
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))  # Корректный путь для PyInstaller
        ui_path = os.path.join(base_path, "interface", "main_window.ui")  # Используем base_path для формирования пути
        self.SETTINGS_FILE = "settings.json"

        # Проверяем существование файла
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")

        loadUi(ui_path, self)
        self.centralwidget.setContentsMargins(9, 0, 9, 9)
        self.tabWidget.setContentsMargins(9, 0, 9, 9)

        # Получаем основной макет для таба 'tab_convert'
        self.layout_text = self.tab_convert.layout()

        # Инициализируем и добавляем пользовательские виджеты
        self.text_convert = NumberedTextEdit(self)
        self.file_info_widget = FileInfoWidget(self.text_convert, self.current_fileName)
        self.layout_text.addWidget(self.file_info_widget, 1, 0, 1, 0)
        self.layout_text.addWidget(self.progressBar_convert)
        self.layout_text.addWidget(self.btn_render)

        # Инициализируем и добавляем пользовательские виджеты
        self.progressBar_convert: QProgressBar = self.findChild(QProgressBar, "progressBar_convert")
        self.path_save: QLineEdit = self.findChild(QLineEdit, "path_save")
        self.path_ffmpeg: QLineEdit = self.findChild(QLineEdit, "path_ffmpeg")
        self.path_ytdlp: QLineEdit = self.findChild(QLineEdit, "path_ytdlp")
        self.statusbar: QStatusBar = self.findChild(QStatusBar, "statusbar")
        self.btn_render: QPushButton = self.findChild(QPushButton, "btn_render")
        self.current_fileName: QComboBox = self.findChild(QComboBox, "current_fileName")

        # Настройка событий
        self.fpsEnable.stateChanged.connect(self.fpsCustom)
        self.checkBox_alwaysOnTop.stateChanged.connect(self.update_always_on_top)
        self.btn_render.clicked.connect(self.renderPressed)
        self.btn_path_save.clicked.connect(self.select_folder_path_save)
        self.btn_path_ffmpeg.clicked.connect(self.select_path_ffmpeg)
        self.btn_path_ytdlp.clicked.connect(self.select_ytdlp_path)
        self.current_fileName.setEditable(True)
        self.load_settings()

        # Проверка стоит ли галочка темной темы
        self.checkBox_setDarkMode = self.findChild(QCheckBox, "checkBox_setDarkMode")
        self.checkBox_setDarkMode.stateChanged.connect(self.toggleDarkMode)

    def mousePressEvent(self, event):
        if not (self.path_save.underMouse() or
                self.path_ffmpeg.underMouse() or
                self.path_ytdlp.underMouse() or
                self.text_convert.underMouse()):
            self.path_save.clearFocus()
            self.path_ffmpeg.clearFocus()
            self.path_ytdlp.clearFocus()
            self.text_convert.clearFocus()
            self.current_fileName.clearFocus()
            self.crfCount.clearFocus()
            self.fpsCount.clearFocus()
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
        else:
            setLightMode(self)

    def _process_path(self, path: str) -> str:
        drive, path = os.path.splitdrive(path)
        return drive + path.replace("/", "\\")

    def select_folder_path_save(self):
        folder_path: str = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if folder_path:
            self.path_save.setText(self._process_path(folder_path))
            print(f"Выбрана папка для сохранения: {folder_path}")

    def renderPressed(self):
        print("Кнопка нажата, начинаем конвертацию...")
        self.convert_video()

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

    def convert_video(self):
        codec = self.list_codec.currentText()
        crf = self.crfCount.value()
        # Передаем пользовательский FPS, если галочка установлена
        fps = self.fpsCount.value() if self.fpsEnable.isChecked() else None
        preset = self.list_ffmpeg_preset.currentText()
        input_files = self.text_convert.toPlainText().splitlines()
        output_dir = self.path_save.text()
        ffmpeg_path = self.path_ffmpeg.text()
        current_fileName = self.current_fileName.currentText()

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
        print(f"Current File Name: {current_fileName}")

        if processed_input_files and output_dir and ffmpeg_path:
            # Передаем выбранный FPS или None в поток для обработки
            self.thread = ConvertVideoThread(codec, crf, fps, preset, processed_input_files, output_dir, ffmpeg_path, current_fileName)
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
            "window_fullscreen": self.isFullScreen(),   # Сохраняем статус полноэкранного режима
            "window_maximized": self.isMaximized(),      # Сохраняем статус развернутого окна
            "checkBox_setDarkMode": self.checkBox_setDarkMode.isChecked()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Стиль
    window = MainUI()
    window.show()
    sys.exit(app.exec_())