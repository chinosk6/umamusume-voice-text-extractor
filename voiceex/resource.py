import os
from . import database as udb
from pythonnet import set_runtime
from clr_loader import get_coreclr
from .ulogger import logger as log
from typing import List, Optional
from . import models as m

rt = get_coreclr(
    runtime_config="./voice extractor/voice extractor/bin/Release/net6.0/voice extractor.runtimeconfig.json"
)
set_runtime(rt)
import clr

# clr.FindAssembly("voice_extractor.dll")
clr.AddReference("./voice extractor/voice extractor/bin/Release/net6.0/voice extractor")
from System.Collections.Generic import List as CsList
from System import UInt64, String
from System.IO import InvalidDataException

import voice_extractor


class ResourceEx(udb.UmaDatabase):
    def __init__(self, download_missing_voice_files=False):
        super().__init__()
        self.download_missing_voice_files = download_missing_voice_files
        self.wav_format = None

    def set_wav_format(self, rate: int, bits: int, channels: int):
        self.wav_format = (rate, bits, channels)

    def extract_all_wav(self, acb_path: str, awb_path: str, save_path: str, save_file_prefix: str):
        extractor = voice_extractor.UmaVoiceEx(acb_path, awb_path)
        if self.wav_format is not None:
            extractor.SetWaveFormat(*self.wav_format)

        wav_count = extractor.GetAudioCount()
        ret = []
        for i in range(wav_count):
            save_name = extractor.ExtractAudioFromWaveId(save_path, save_file_prefix, i)
            ret.append(save_name)
        extractor.Close()
        return ret

    def check_and_download_sound(self, file_hash, file_path):
        if not os.path.isfile(file_path):
            if self.download_missing_voice_files:
                log.logger(f"{file_hash} not found, try download...", warning=True)
                self.download_sound(file_hash, file_path)
                log.logger(f"Download success: {file_path}")

    def get_extractor(self, awb_bundle_path: str, acb_bundle_path: str = None, volume: Optional[float] = None):
        if acb_bundle_path is None:
            acb_bundle_hash = self.awb_bundle_path_to_acb_bundle_path(awb_bundle_path)[1]
            acb_bundle_path = self.bundle_hash_to_path(acb_bundle_hash)
        else:
            acb_bundle_hash = os.path.split(acb_bundle_path)[1]
        self.check_and_download_sound(acb_bundle_hash, acb_bundle_path)
        self.check_and_download_sound(os.path.split(awb_bundle_path)[1], awb_bundle_path)

        extractor = voice_extractor.UmaVoiceEx(acb_bundle_path, awb_bundle_path)
        if self.wav_format is not None:
            extractor.SetWaveFormat(*self.wav_format)
        extractor.SetVolume(volume if volume is not None else m.user_config.volume)
        return extractor

    @staticmethod
    def get_uninited_extractor():
        return voice_extractor.UmaVoiceEx

    @staticmethod
    def cut_wav_batch(file_name: str, save_name_prefix: str, time_ms_list: List[List[int]]):
        lst_param = CsList[CsList[UInt64]]()
        for i in time_ms_list:
            add = CsList[UInt64]()
            for j in i:
                add.Add(j)
            lst_param.Add(add)
        result = voice_extractor.UmaVoiceEx.CutWavFileBatch(file_name, save_name_prefix, lst_param)
        return list(result)

    @staticmethod
    def mix_wavs(files: List[str], save_name: str, volume: float):
        lst_param = CsList[String]()
        for i in files:
            lst_param.Add(i)
        save_dir = os.path.split(save_name)[0]
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        voice_extractor.UmaVoiceEx.MixWav(lst_param, save_name, volume)

    @staticmethod
    def ConcatenateWavFiles(save_name: str, files: List[str]):
        lst_param = CsList[String]()
        for i in files:
            lst_param.Add(i)
        voice_extractor.UmaVoiceEx.ConcatenateWavFiles(save_name, lst_param)

    @staticmethod
    def SilenceWavPartsByActivePos(file_name: str, save_name: str, active_ms: List[List[int]]):
        lst_param = CsList[CsList[UInt64]]()
        for i in active_ms:
            add_p = CsList[UInt64]()
            for j in i:
                add_p.Add(j)
            lst_param.Add(add_p)
        voice_extractor.UmaVoiceEx.SilenceWavPartsByActivePos(file_name, save_name, lst_param)
