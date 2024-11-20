from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPlainTextEdit, QSplitter, QTextEdit, QVBoxLayout, QWidget
from texttable import Texttable
from widgets.numbered_text_edit import NumberedTextEdit
import json
import mimetypes
import os
import re
import subprocess

class FileInfoWidget(QWidget):
    def __init__(self, text_convert, text_edit_middle, text_edit_right, current_fileName, parent=None):
        super(FileInfoWidget, self).__init__(parent)

         # Устанавливаем атрибут, чтобы игнорировать события мыши
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.current_fileName = current_fileName
        self.text_edit_left = text_convert
        self.text_edit_middle = text_edit_middle
        self.text_edit_right = text_edit_right
        self.parent_ui = parent  # Сохраняем ссылку на родительский объект

        # Синхронизация скроллинга между окнами
        self.text_edit_left.verticalScrollBar().valueChanged.connect(self.sync_scrolls)
        self.text_edit_middle.verticalScrollBar().valueChanged.connect(self.sync_scrolls)
        self.text_edit_right.verticalScrollBar().valueChanged.connect(self.sync_scrolls)

        # Обновляем среднее окно при изменении текста
        self.text_edit_left.textChanged.connect(self.update_middle_editor)
        self.text_edit_left.textChanged.connect(self.update_right_editor_if_enabled)

        # Обновляем среднее окно при изменении текста в QComboBox
        self.current_fileName.currentTextChanged.connect(self.update_middle_editor)

        # Подключаем сигнал изменения состояния action_textEdit3 и action_textEdit3_refresh
        if self.parent_ui:
            if hasattr(self.parent_ui, 'action_textEdit3'):
                self.parent_ui.action_textEdit3.toggled.connect(self.on_action_textEdit3_toggled)

            if hasattr(self.parent_ui, 'action_textEdit3_refresh'):
                self.parent_ui.action_textEdit3_refresh.toggled.connect(self.on_action_textEdit3_refresh_toggled)

    def on_action_textEdit3_toggled(self, checked):
        # Если action_textEdit3 включен, обновляем right editor, если refresh тоже включен
        if checked and self.parent_ui.action_textEdit3_refresh.isChecked():
            self.update_right_editor()

    def on_action_textEdit3_refresh_toggled(self, checked):
        if checked:
            self.update_right_editor_if_enabled()  # Обновляем right editor, если галочка установлена

    def sync_scrolls(self, value):
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

    def update_middle_editor(self):
        # Обновляем среднее текстовое поле с фактическими именами файлов
        template = self.current_fileName.currentText()
        input_files = self.text_edit_left.toPlainText().splitlines()
        output_names = []

        for index, file in enumerate(input_files):
            if file.strip():  # Проверяем, не является ли строка пустой или содержащей только пробелы
                if file.startswith("http://") or file.startswith("https://"):
                    video_title = self.get_video_title(file)
                    output_names.append(video_title)
                else:
                    file_name = os.path.splitext(os.path.basename(file))[0]
                    counter = index + 1
                    output_name = template
                    output_name = output_name.replace('[N]', file_name)

                    def replace_placeholder(match):
                        num_hashes = len(match.group(1))
                        return str(counter).zfill(num_hashes)

                    output_name = re.sub(r'\[(#+)\]', replace_placeholder, output_name)
                    output_name = re.sub(r'\[\]', '[]', output_name)
                    output_names.append(output_name)
            else:
                output_names.append('')  # Добавляем пустую строку, если входная строка пустая

        self.text_edit_middle.setPlainText('\n'.join(output_names))

    def update_right_editor_if_enabled(self):
        # Проверяем состояние action_textEdit3 и action_textEdit3_refresh
        if self.parent_ui.action_textEdit3.isChecked() and self.parent_ui.action_textEdit3_refresh.isChecked():
            self.update_right_editor()

    def update_right_editor(self):
        # Проверяем состояние action_textEdit3
        if not (self.parent_ui and hasattr(self.parent_ui, 'action_textEdit3') and self.parent_ui.action_textEdit3.isChecked()):
            self.text_edit_right.setPlainText("")  # Оставляем текстовое поле пустым
            return

        text = self.text_edit_left.toPlainText()
        file_paths = text.splitlines()

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["l", "r", "l", "c", "l", "l"])  # Выравнивание по столбцам
        table.set_cols_valign(["m"] * 6)  # Вертикальное выравнивание по центру

        # Проверка на наличие путей к файлам
        if not file_paths or all(path.strip() == "" for path in file_paths):
            self.text_edit_right.setPlainText("")  # Оставляем текстовое поле пустым
            return

        for file_path in file_paths:
            normalized_path = self.normalize_path(file_path)

            if os.path.exists(normalized_path):
                file_size = os.path.getsize(normalized_path)
                file_date = datetime.fromtimestamp(os.path.getmtime(normalized_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_info = self.get_file_info(normalized_path)

                if file_info['is_video']:
                    table.add_row([
                        file_info['duration'],
                        self.format_size(file_size),
                        file_info['resolution'],
                        f"a:{file_info['audio_count']}",
                        file_info['fps'],
                        file_date
                    ])
                else:
                    table.add_row([
                        file_info['duration'],
                        self.format_size(file_size),
                        '',
                        '',
                        '',
                        file_date
                    ])
            else:
                table.add_row(['', '', '', '', '', ''])  # Добавляем пустую строку вместо сообщения о не найденном файле

        # Получаем вывод таблицы
        output = table.draw()

        # Проверка на случай, если таблица пустая
        if output is None or output.strip() == "":
            self.text_edit_right.setPlainText("")  # Оставляем текстовое поле пустым
            return
        self.text_edit_right.setPlainText(output)

    def normalize_path(self, file_path):
        if file_path.startswith("file:///"):
            file_path = file_path[8:]

        file_path = file_path.strip('"')

        file_path = file_path.replace("/", "\\")

        return file_path

    def get_file_info(self, file_path):
        # Проверяем состояние action_textEdit3
        if not self.parent_ui.action_textEdit3.isChecked():
            return {"duration": "", "resolution": "", "is_video": False}

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('video') or mime_type.startswith('audio'):
                return self.extract_media_info(file_path)
        return {"duration": "", "resolution": "", "is_video": False}

    def extract_media_info(self, file_path):
        # Проверяем состояние action_textEdit3
        if not self.parent_ui.action_textEdit3.isChecked():
            return {"duration": "", "resolution": "", "fps": "", "audio_count": 0, "is_video": False}

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
                audio_streams = [s for s in metadata['streams'] if s['codec_type'] == 'audio']  # Получаем аудиодорожки

                if video_streams:
                    width = video_streams[0]['width']
                    height = video_streams[0]['height']
                    fps = eval(video_streams[0]['r_frame_rate'])  # Добавляем FPS
                    audio_count = len(audio_streams)  # Считаем количество аудиодорожек
                    return {
                        "duration": self.format_duration(duration),
                        "resolution": f"{width}x{height}",
                        "fps": f"{fps:.3f} fps",  # Форматируем FPS
                        "audio_count": audio_count,  # Добавляем количество аудиодорожек
                        "is_video": True
                    }
                else:
                    return {
                        "duration": self.format_duration(duration),
                        "resolution": "",
                        "audio_count": 0,  # Если видео дорожек нет, то аудио тоже 0
                        "is_video": False
                    }
        except Exception as e:
            print(f"Ошибка извлечения информации о файле: {e}")
        return {"duration": "", "resolution": "", "fps": "", "audio_count": 0, "is_video": False}

    def format_duration(self, seconds):
        # Проверяем состояние action_textEdit3
        if not self.parent_ui.action_textEdit3.isChecked():
            return ""

        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def format_size(self, size_bytes):
        # Проверяем состояние action_textEdit3
        if not self.parent_ui.action_textEdit3.isChecked():
            return ""

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / 1024**2:.2f} MB"
        else:
            return f"{size_bytes / 1024**3:.2f} GB"

    def get_video_title(self, url):
        command = ['yt-dlp', '--get-title', url]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                return result.stdout.strip()  # Возвращаем заголовок
        except Exception as e:
            print(f"Ошибка при получении заголовка видео: {e}")
        return "Не удалось получить заголовок"  # Если произошла ошибка