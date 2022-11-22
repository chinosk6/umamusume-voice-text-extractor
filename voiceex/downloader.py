import requests
import typing as t
import os


class UmaDownloader:
    def __init__(self):
        self.base_host = "https://prd-storage-umamusume.akamaized.net/dl/resources"
        self.proxies = None

    def set_proxies(self, proxy_url: str):
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

    def get_sound_download_url(self, abhash: str):
        return f"{self.base_host}/Generic/{abhash:.2}/{abhash}"

    def download_sound(self, abhash: str, save_name: str,
                       down_progress_callback: t.Optional[t.Callable[[str], t.Any]] = None):
        url = self.get_sound_download_url(abhash)
        resp = requests.get(url, headers={
            "User-Agent": "UnityPlayer/2019.4.21f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)"
        },
                            stream=True, proxies=self.proxies)
        if resp.status_code != 200:
            raise RuntimeError(f"Can't download file from {url} (HTTP {resp.status_code}).")

        save_path = os.path.split(save_name)[0]
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        total = int(resp.headers.get('content-length', 0))
        with open(save_name, "wb") as f:
            down_size = 0
            for data in resp.iter_content(chunk_size=1024):
                size = f.write(data)
                down_size += size
                down_progress = f"{int(down_size / total * 100)}%" if total != 0 else "?%"
                if down_progress_callback is not None:
                    down_progress_callback(down_progress)
