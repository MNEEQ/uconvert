from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPlainTextEdit, QSplitter, QTextEdit, QVBoxLayout, QWidget
from widgets.numbered_text_edit import NumberedTextEdit
import json
import mimetypes
import os
import re
import subprocess

class FileInfoWidget(QWidget):
    def __init__(self, text_convert, text_edit_middle, text_edit_right, current_fileName, parent=None):
        super(FileInfoWidget, self).__init__(parent)

        self.current_fileName = current_fileName
        self.text_edit_left = text_convert
        self.text_edit_middle = text_edit_middle
        self.text_edit_right = text_edit_right

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

        for index, file in enumerate(input_files):
            if file.strip():  # Проверяем, не является ли строка пустой или содержащей только пробелы
                file_name = os.path.splitext(os.path.basename(file))[0]
                # Получаем номер с учетом индекса
                counter = index + 1
                
                # Обрабатываем шаблон
                output_name = template
                output_name = output_name.replace('[N]', file_name)

                # Обрабатываем флаги внутри квадратных скобок
                def replace_placeholder(match):
                    num_hashes = len(match.group(1))  # Количество символов #
                    return str(counter).zfill(num_hashes)  # Заменяем на номер с нужным количеством нулей

                output_name = re.sub(r'\[(#+)\]', replace_placeholder, output_name)

                # Обрабатываем случай с пустыми скобками
                output_name = re.sub(r'\[\]', '[]', output_name)

                output_names.append(output_name)
            else:
                output_names.append('')  # Добавляем пустую строку, если входная строка пустая

        self.text_edit_middle.setPlainText('\n'.join(output_names))

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

    def normalize_path(self, file_path):
        if file_path.startswith("file:///"):
            file_path = file_path[8:]

        file_path = file_path.strip('"')

        file_path = file_path.replace("/", "\\")

        return file_path

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
        
        # Создаем объект STARTUPINFO
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Скрываем окно консоли

        try:
            # Запускаем subprocess с использованием STARTUPINFO
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    universal_newlines=True, startupinfo=startupinfo)
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
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
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