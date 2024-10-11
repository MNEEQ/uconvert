from datetime import datetime
import json
import mimetypes
import os
import re
import subprocess
import sys
from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QMainWindow, QPlainTextEdit, QProgressBar,
    QSplitter, QStatusBar, QVBoxLayout, QWidget, QComboBox, QTextEdit
)
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import pyqtSignal, QRect, Qt, QThread
from PyQt5.QtGui import QColor, QFont, QPainter, QTextFormat
from PyQt5.uic import loadUi

class LineNumberArea(QWidget):
    def __init__(self, parent=None):
        super(LineNumberArea, self).__init__(parent)
        self.line_number_font = QFont("Consolas", 8)

    def sizeHint(self):
        return self.editor.lineNumberAreaSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.lightGray)
        painter.setFont(self.line_number_font)
        block = self.parent().firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.parent().blockBoundingGeometry(block).translated(self.parent().contentOffset()).top()
        bottom = top + self.parent().blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                rect = QRect(0, int(top), self.width() - 6, int(self.parent().fontMetrics().height()))
                painter.drawText(rect, Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.parent().blockBoundingRect(block).height()
            blockNumber += 1

class NumberedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(NumberedTextEdit, self).__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.lineNumberArea.setStyleSheet("background-color: lightgray; border: 12px solid gray")
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 4
        return space

    def updateLineNumberAreaWidth(self):
        self.setViewportMargins(self.lineNumberAreaWidth() + 4, 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberAreaWidth() + 4, rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def resizeEvent(self, event):
        super(NumberedTextEdit, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(cr.x(), cr.y(), self.lineNumberAreaWidth() + 4, cr.height())
        self.setViewportMargins(self.lineNumberAreaWidth() + 4, 0, 0, 0)

class ConvertVideoThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)

    _DURATION_RX = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2})\.\d{2}")
    _PROGRESS_RX = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.\d{2}")

    def __init__(self, codec, crf, fps, preset, input_files, output_dir, ffmpeg_path, current_file_name):
        super(ConvertVideoThread, self).__init__()
        self.codec = codec
        self.crf = crf
        self.fps = fps
        self.preset = preset
        self.input_files = input_files
        self.output_dir = output_dir
        self.ffmpeg_path = ffmpeg_path
        self.current_file_name = current_file_name
        self.total_duration = None

    def run(self):
        total_files = len(self.input_files)
        current_file = 0

        for input_file in self.input_files:
            filename = os.path.basename(input_file)

            output_name = self.current_file_name.replace('[N]', os.path.splitext(filename)[0])
            output_file = os.path.join(self.output_dir, output_name + ".mp4")

            self.status_signal.emit(f"Начинаем конвертацию файла ({current_file + 1}/{total_files}) {filename}")

            command = [self.ffmpeg_path, '-i', input_file]
            if self.fps is not None:
                command.extend(['-r', str(self.fps)])
            command.extend(['-c:v', self.codec, '-crf', str(self.crf), '-preset', self.preset, '-c:a', 'aac', '-b:a', '128k', output_file])

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)

            self.total_duration = None
            for line in process.stderr:
                if self.total_duration is None:
                    self.total_duration = self._get_duration(line)

                if self.total_duration:
                    progress = self._get_progress(line, self.total_duration)
                    if progress is not None:
                        self.progress_signal.emit(progress)

            process.wait()
            self.progress_signal.emit(100)
            current_file += 1
            self.status_signal.emit(f"Конвертация файла ({current_file}/{total_files}) {filename} завершена")

    def _get_duration(self, line):
        match = self._DURATION_RX.search(line)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            return (hours * 3600) + (minutes * 60) + seconds
        return None

    def _get_progress(self, line, total_duration):
        match = self._PROGRESS_RX.search(line)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            current_time = (hours * 3600) + (minutes * 60) + seconds
            progress = int((current_time / total_duration) * 100)
            return progress
        return None

class FileInfoWidget(QWidget):
    def __init__(self, text_convert, current_fileName, parent=None):
        super(FileInfoWidget, self).__init__(parent)

        self.current_fileName = current_fileName

        font = QFont("Consolas", 8)

        self.text_edit_left = text_convert
        self.text_edit_left.setFont(font)
        self.text_edit_left.setStyleSheet("QPlainTextEdit { padding-top: 0px; padding-bottom: 0px; }")

        self.text_edit_middle = NumberedTextEdit()
        self.text_edit_middle.setFont(font)
        self.text_edit_middle.setStyleSheet("QPlainTextEdit { padding-top: 0px; padding-bottom: 0px; }")
        self.text_edit_middle.setReadOnly(True)

        self.text_edit_right = NumberedTextEdit()
        self.text_edit_right.setFont(font)
        self.text_edit_right.setStyleSheet("QPlainTextEdit { padding-top: 0px; padding-bottom: 0px; }")
        self.text_edit_right.setReadOnly(True)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(4)  # Устанавливаем минимальную ширину разделителя
        self.splitter.addWidget(self.text_edit_left)
        self.splitter.addWidget(self.text_edit_middle)
        self.splitter.addWidget(self.text_edit_right)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы
        layout.setSpacing(0)  # Убираем промежутки между элементами
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        # Синхронизация скроллинга между окнами
        self.text_edit_left.verticalScrollBar().valueChanged.connect(self.sync_scrolls)
        self.text_edit_middle.verticalScrollBar().valueChanged.connect(self.sync_scrolls)
        self.text_edit_right.verticalScrollBar().valueChanged.connect(self.sync_scrolls)

        # Обновляем среднее и правое окно при изменении текста
        self.text_edit_left.textChanged.connect(self.update_middle_editor)
        self.text_edit_left.textChanged.connect(self.update_right_editor)
        self.syncing = False

        # Обновляем среднее окно при изменении текста в QComboBox
        self.current_fileName.currentTextChanged.connect(self.update_middle_editor)

    def sync_scrolls(self, value):
        if self.syncing:
            return
        self.syncing = True
        sender = self.sender()
        if sender == self.text_edit_left.verticalScrollBar():
            self.text_edit_middle.verticalScrollBar().setValue(value)
            self.text_edit_right.verticalScrollBar().setValue(value)
        elif sender == self.text_edit_middle.verticalScrollBar():
            self.text_edit_left.verticalScrollBar().setValue(value)
            self.text_edit_right.verticalScrollBar().setValue(value)
        else:
            self.text_edit_left.verticalScrollBar().setValue(value)
            self.text_edit_middle.verticalScrollBar().setValue(value)
        self.syncing = False

    def update_middle_editor(self):
        # Обновляем среднее текстовое поле с фактическими именами файлов
        template = self.current_fileName.currentText()
        input_files = self.text_edit_left.toPlainText().splitlines()
        output_names = []

        for file in input_files:
            if file.strip():  # Проверяем, не является ли строка пустой или содержащей только пробелы
                if '[N]' in template:
                    file_name = os.path.splitext(os.path.basename(file))[0]
                    output_name = template.replace('[N]', file_name)
                else:
                    output_name = template
                output_names.append(output_name)
            else:
                output_names.append('')  # Добавляем пустую строку, если входная строка пустая

        self.text_edit_middle.setPlainText('\n'.join(output_names))

    def normalize_path(self, file_path):
        if file_path.startswith("file:///"):
            file_path = file_path[8:]

        file_path = file_path.strip('"')

        file_path = file_path.replace("/", "\\")

        return file_path

    def update_right_editor(self):
        text = self.text_edit_left.toPlainText()
        file_paths = text.splitlines()

        output_lines = []
        for file_path in file_paths:
            normalized_path = self.normalize_path(file_path)

            if os.path.exists(normalized_path):
                file_size = os.path.getsize(normalized_path)
                file_date = datetime.fromtimestamp(os.path.getmtime(normalized_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_info = self.get_file_info(normalized_path)
                if file_info['is_video']:
                    output_lines.append(f"{file_info['duration']}\t{self.format_size(file_size)}\t{file_info['resolution']}\t{file_info['fps']}\t{file_date}")
                else:
                    output_lines.append(f"{file_info['duration']}\t{self.format_size(file_size)}\t\t{file_date}")
            else:
                output_lines.append(f"\t\t\t") #output_lines.append(f"Файл не найден\t\t\t")

        self.text_edit_right.setPlainText("\n".join(output_lines))

    def get_file_info(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('video') or mime_type.startswith('audio'):
                return self.extract_media_info(file_path)
        return {"duration": "", "resolution": "", "is_video": False}

    def extract_media_info(self, file_path):
        command = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-show_streams', '-of', 'json', file_path
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                duration = float(metadata['format']['duration'])
                video_streams = [s for s in metadata['streams'] if s['codec_type'] == 'video']

                if video_streams:
                    width = video_streams[0]['width']
                    height = video_streams[0]['height']
                    fps = eval(video_streams[0]['r_frame_rate'])  # Добавляем FPS
                    return {
                        "duration": self.format_duration(duration),
                        "resolution": f"{width}x{height}",
                        "fps": f"{fps:.3f} fps",  # Форматируем FPS
                        "is_video": True
                    }
                else:
                    return {
                        "duration": self.format_duration(duration),
                        "resolution": "",
                        "is_video": False
                    }
        except Exception as e:
            print(f"Ошибка извлечения информации о файле: {e}")
        return {"duration": "", "resolution": "", "fps": "", "is_video": False}

    def format_duration(self, seconds):
        hours, rem = divmod(int(seconds), 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / 1024**2:.2f} MB"
        else:
            return f"{size_bytes / 1024**3:.2f} GB"

class MainUI(QMainWindow):
    CUSTOM_FPS_ENABLED = 2

    def __init__(self):
        super(MainUI, self).__init__()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, "interface.ui")

        loadUi(ui_path, self)

        self.layout_text = self.tab_convert.layout()

        self.text_convert = NumberedTextEdit(self)
        self.file_info_widget = FileInfoWidget(self.text_convert, self.current_fileName)
        self.layout_text.addWidget(self.file_info_widget)

        self.progressBar_convert: QProgressBar = self.findChild(QtWidgets.QProgressBar, "progressBar_convert")
        self.layout_text.addWidget(self.progressBar_convert)
        self.path_save: QLineEdit = self.findChild(QtWidgets.QLineEdit, "path_save")
        self.path_ffmpeg: QLineEdit = self.findChild(QtWidgets.QLineEdit, "path_ffmpeg")
        self.path_ytdlp: QLineEdit = self.findChild(QtWidgets.QLineEdit, "path_ytdlp")
        self.statusbar: QStatusBar = self.findChild(QtWidgets.QStatusBar, "statusbar")
        self.btn_render = self.findChild(QtWidgets.QPushButton, "btn_render")

        self.fpsEnable.stateChanged.connect(self.fpsCustom)
        self.btn_render.clicked.connect(self.newPressed)
        self.btn_path_save.clicked.connect(self.select_folder_path_save)
        self.btn_path_ffmpeg.clicked.connect(self.select_path_ffmpeg)
        self.btn_path_ytdlp.clicked.connect(self.select_ytdlp_path)
        self.current_fileName.setEditable(True)
        self.current_fileName: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "current_fileName")

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
            print("Курсор мыши находится вне полей ввода.")

    def _process_path(self, path: str) -> str:
        drive, path = os.path.splitdrive(path)
        return drive + path.replace("/", "\\")

    def select_folder_path_save(self):
        folder_path: str = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения")
        if folder_path:
            self.path_save.setText(self._process_path(folder_path))
            print(f"Выбрана папка для сохранения: {folder_path}")

    def newPressed(self):
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
        file_path: str = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите путь к ffmpeg")[0]
        if file_path:
            if os.path.exists(file_path):
                self.path_ffmpeg.setText(self._process_path(file_path))
                print(f"Выбран путь к ffmpeg: {file_path}")

    def select_ytdlp_path(self):
        file_path: str = QtWidgets.QFileDialog.getOpenFileName(self, "Выберите путь к ytdlp")[0]
        if file_path:
            if os.path.exists(file_path):
                self.path_ytdlp.setText(self._process_path(file_path))
                print(f"Выбран путь к ytdlp: {file_path}")

    def convert_video(self):
        codec = self.list_codec.currentText()
        crf = self.crfCount.value()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec_())