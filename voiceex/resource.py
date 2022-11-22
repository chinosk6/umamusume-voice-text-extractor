import os
from . import database as udb
from pythonnet import set_runtime
from clr_loader import get_coreclr
from .ulogger import logger as log

rt = get_coreclr(
    runtime_config="./voice extractor/voice extractor/bin/Release/net6.0/voice extractor.runtimeconfig.json"
)
set_runtime(rt)
import clr

# clr.FindAssembly("voice_extractor.dll")
clr.AddReference("./voice extractor/voice extractor/bin/Release/net6.0/voice extractor")

import voice_extractor


class ResourceEx(udb.UmaDatabase):
    def __init__(self, download_missing_abfile=False):
        super().__init__()
        self.download_missing_abfile = download_missing_abfile

    @staticmethod
    def extract_all_wav(acb_path: str, awb_path: str, save_path: str, save_file_prefix: str):
        extractor = voice_extractor.UmaVoiceEx(acb_path, awb_path)
        extractor.SetVolume(2.0)

        wav_count = extractor.GetAudioCount()
        ret = []
        for i in range(wav_count):
            save_name = extractor.ExtractAudioFromWaveId(save_path, save_file_prefix, i)
            ret.append(save_name)
        extractor.Close()
        return ret


    def get_extractor(self, awb_bundle_path: str, acb_bundle_path: str = None, volume=2.0):
        if acb_bundle_path is None:
            acb_bundle_hash = self.awb_bundle_path_to_acb_bundle_path(awb_bundle_path)[1]
            acb_bundle_path = self.bundle_hash_to_path(acb_bundle_hash)
            if not os.path.isfile(acb_bundle_path):
                if self.download_missing_abfile:
                    log.logger(f"{acb_bundle_hash} not found, try download...", warning=True)
                    self.download_sound(acb_bundle_hash, acb_bundle_path)
                    log.logger(f"Download success: {acb_bundle_path}")

        extractor = voice_extractor.UmaVoiceEx(acb_bundle_path, awb_bundle_path)
        extractor.SetVolume(volume)
        return extractor
