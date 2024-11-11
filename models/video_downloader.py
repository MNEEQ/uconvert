import subprocess
import os
from PyQt5.QtCore import QThread, pyqtSignal

class VideoDownloader:
    def __init__(self, ytdlp_path):
        self.ytdlp_path = ytdlp_path

    def download_video(self, url, output_dir, proxy=None):
        command = [self.ytdlp_path]

        if proxy:  # Если указан прокси, добавляем его в команду
            command += ['--proxy', proxy]

        command += [url, '-o', os.path.join(output_dir, '%(title)s.%(ext)s')]
        
        # Скрытие окна консоли
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            subprocess.run(command, check=True, startupinfo=startupinfo)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при скачивании видео: {e}")
            return False

class DownloadThread(QThread):
    def __init__(self, urls, output_dir, ytdlp_path, proxy=None):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.ytdlp_path = ytdlp_path
        self.proxy = proxy  # Сохраняем прокси

    def run(self):
        downloader = VideoDownloader(self.ytdlp_path)
        for url in self.urls:
            downloader.download_video(url, self.output_dir, self.proxy)  # Передаем прокси