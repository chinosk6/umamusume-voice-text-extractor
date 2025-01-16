import time
import requests
import typing as t
import os
from .ulogger import logger as log
from .progress_bar import track

class UmaDownloader:
    def __init__(self):
        self.base_host = "https://prd-storage-game-umamusume.akamaized.net/dl/resources"
        self.proxies = None

    def set_proxies(self, proxy_url: str):
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

    def get_sound_download_url(self, abhash: str):
        return f"{self.base_host}/Generic/{abhash:.2}/{abhash}"

    def download_sound(self, abhash: str, save_name: str,
                       down_progress_callback: t.Optional[t.Callable[[int, int], t.Any]] = None, retry_times=0):
        try:
            url = self.get_sound_download_url(abhash)
            resp = requests.get(url, headers={
                "User-Agent": "UnityPlayer/2019.4.21f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)"
            },
                                stream=True, proxies=self.proxies, timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(f"Can't download file from {url} (HTTP {resp.status_code}).")

            save_path = os.path.split(save_name)[0]
            if not os.path.isdir(save_path):
                os.makedirs(save_path)

            total = int(resp.headers.get('content-length', 0))

            with open(save_name, "wb") as f:
                down_size = 0
                for data in track(resp.iter_content(chunk_size=1024), total=total, description="Downloading...",
                                  is_sub_track=True, sub_remove_end=True, sub_advance_is_seq_len=True):
                    size = f.write(data)
                    down_size += size
                    if down_progress_callback is not None:
                        down_progress_callback(down_size, total * 100)

        except BaseException as e:
            if retry_times < 3:
                retry_times += 1
                log.logger(f"Download failed: {e}, retry: {retry_times}/3", error=True)
                time.sleep(3)
                return self.download_sound(abhash, save_name, down_progress_callback, retry_times)
            else:
                if os.path.isfile(save_name):
                    os.remove(save_name)
                raise e
