from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QTextEdit
import os
import re
import subprocess

class ConvertVideoThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)

    _DURATION_RX = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2})\.\d{2}")
    _PROGRESS_RX = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.\d{2}")
    _FPS_RX = re.compile(r"(\d+(?:\.\d+)?) fps")  # Регулярное выражение для поиска FPS в строке

    def __init__(self, codec, crf, fps, preset, input_files, output_dir, ffmpeg_path, current_file_name, text_edit_middle):
        super(ConvertVideoThread, self).__init__()
        self.codec = codec
        self.crf = crf
        self.user_fps = fps  # Пользовательский FPS, если передан
        self.preset = preset
        self.input_files = input_files
        self.output_dir = output_dir
        self.ffmpeg_path = ffmpeg_path
        self.current_file_name = current_file_name
        self.total_duration = None
        self.text_edit_middle = text_edit_middle

    def run(self):
        total_files = len(self.input_files)
        current_file = 0

        # Получаем имена выходных файлов из textEdit2
        output_names = self.text_edit_middle.toPlainText().splitlines()

        if len(output_names) != total_files:
            print(f"Ошибка: количество выходных имен ({len(output_names)}) не совпадает с количеством входных файлов ({total_files}).")
            return

        for input_file, output_name in zip(self.input_files, output_names):
            filename = os.path.basename(input_file)

            # Используем пользовательский FPS, если он задан
            if self.user_fps is not None:
                video_fps = self.user_fps
                print(f"Принудительный FPS: {video_fps} для видео {filename}")
            else:
                # Если пользовательский FPS не задан, извлекаем FPS из видео
                video_fps = self.get_video_fps(input_file)
                if video_fps is None:
                    print(f"Не удалось извлечь FPS для {filename}, используем FPS по умолчанию.")
                    video_fps = 30  # Можно установить FPS по умолчанию, если ничего не извлечено

            # Формирование имени выходного файла из textEdit2
            output_file = os.path.join(self.output_dir, output_name.strip() + ".mp4")  # Удаляем лишние пробелы и добавляем расширение

            print(f"Обработка файла: {input_file} -> {output_file}")  # Для отладки

            process = subprocess.Popen([self.ffmpeg_path, '-i', input_file, '-r', str(video_fps), '-c:v', self.codec, 
                                        '-crf', str(self.crf), '-preset', self.preset, '-c:a', 'aac', '-b:a', '128k', output_file],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)

            self.total_duration = None
            for line in process.stderr:
                if 'Duration:' in line:
                    self.total_duration = self._get_duration(line)

                if self.total_duration is not None:
                    current_frame = self._get_frame(line)
                    speed = self._get_speed(line)

                    remaining_time = self.calculate_remaining_time(current_frame, speed, video_fps)
                    remaining_time_str = self.format_time(remaining_time)

                    # Объединяем строки для статуса
                    status_message = (f"render: ({current_file + 1}/{total_files}) "
                                      f"remaining: {remaining_time_str} "
                                      f"name: {filename}")
                    self.status_signal.emit(status_message)

                    progress = self._get_progress(line)
                    if progress is not None:
                        self.progress_signal.emit(progress)

            process.wait()
            self.progress_signal.emit(100)
            current_file += 1
            self.status_signal.emit(f"render: ({current_file}/{total_files}) "
                                    f"remaining: 00:00:00 "
                                    f"name: {filename} status: done")

    def get_video_fps(self, input_file):
        # Функция для извлечения FPS из видео.
        process = subprocess.Popen([self.ffmpeg_path, '-i', input_file],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stderr = process.stderr.read()
        process.wait()

        fps_match = self._FPS_RX.search(stderr)
        if fps_match:
            return float(fps_match.group(1))
        return None

    def _get_duration(self, line):
        match = self._DURATION_RX.search(line)
        if match:
            hours, minutes, seconds = map(float, match.groups())
            return int(hours * 3600 + minutes * 60 + seconds)
        return None

    def calculate_remaining_time(self, current_frame, speed, fps):
        if speed <= 0 or self.total_duration is None:
            return 0

        # Преобразуем продолжительность в секунды
        total_seconds = self.total_duration
        total_frames = total_seconds * fps  # Используем реальный FPS, извлечённый из видео

        # Вычисляем оставшиеся кадры
        remaining_frames = total_frames - current_frame
        if remaining_frames < 0:
            return 0

        # Вычисляем оставшееся время в секундах
        remaining_time_seconds = remaining_frames / (fps * speed)
        return remaining_time_seconds

    def _get_frame(self, line):
        match = re.search(r'frame=\s*(\d+)', line)
        if match:
            return int(match.group(1))
        return 0

    def _get_speed(self, line):
        match = re.search(r'speed=([\d.]+)x', line)
        if match:
            return float(match.group(1))
        return 1.0

    def format_time(self, seconds):
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def _get_progress(self, line):
        match = self._PROGRESS_RX.search(line)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            current_time = (hours * 3600) + (minutes * 60) + seconds
            total_duration_seconds = self.total_duration  # Мы уже имеем общую продолжительность
            if total_duration_seconds:
                progress = int((current_time / total_duration_seconds) * 100)
                return progress
        return None