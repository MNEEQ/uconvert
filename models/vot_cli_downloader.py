import subprocess
import os
from PyQt5.QtCore import QThread, pyqtSignal
from models.video_downloader import VideoDownloader

class VotCliDownloader(QThread):
    progress_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, urls, output_dir, ytdlp_path, file_info_widget):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.ytdlp_path = ytdlp_path
        self.file_info_widget = file_info_widget

    def run(self):
        for url in self.urls:
            video_title = self.file_info_widget.get_video_title(url)
            if video_title:
                self.download_translation(url, video_title)

    def download_translation(self, url, video_title):
        filename_template = f"{video_title}.mp3"
        command = f'vot-cli --output="{self.output_dir}" --output-file="{filename_template}" "{url}"'
        try:
            subprocess.run(command, shell=True, check=True, startupinfo=subprocess.STARTUPINFO())
            self.progress_signal.emit(f"Скачивание завершено: {video_title}")
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(f"Ошибка при скачивании {url}: {e}")