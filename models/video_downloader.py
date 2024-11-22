import subprocess
import os
from PyQt5.QtCore import QThread, pyqtSignal

class VideoDownloader:
    def __init__(self, ytdlp_path):
        self.ytdlp_path = ytdlp_path

    def download_video(self, url, output_dir, filename_template='%(title)s.%(ext)s', proxy=None):
        command = [self.ytdlp_path]

        if proxy:
            command += ['--proxy', proxy]

        command += [url, '-o', os.path.join(output_dir, filename_template)]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            subprocess.run(command, check=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при скачивании видео: {e}")
            return False

class DownloadThread(QThread):
    def __init__(self, urls, output_dir, ytdlp_path, proxy=None, parent_ui=None, file_info_widget=None):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.ytdlp_path = ytdlp_path
        self.proxy = proxy
        self.parent_ui = parent_ui
        self.file_info_widget = file_info_widget

    def run(self):
        downloader = VideoDownloader(self.ytdlp_path)
        for url in self.urls:
            video_title = self.file_info_widget.get_video_title(url)
            filename_template = f"{video_title}.%(ext)s"
            downloader.download_video(url, self.output_dir, filename_template, self.proxy)