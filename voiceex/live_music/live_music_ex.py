import os
import shutil
from .. import resource as umares
import UnityPy
from . import models
import typing as t
from tqdm import tqdm
import io


class LiveMusicExtractor(umares.ResourceEx):
    def __init__(self, save_path: str, download_missing_voice_files=False):
        super(LiveMusicExtractor, self).__init__(download_missing_voice_files=download_missing_voice_files)
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        self.save_path = save_path

    @staticmethod
    def load_csv(text: str):
        text = text.replace("\r", "\n")
        text = text.replace("\n\n", "\n")
        lines = text.split("\n")
        heads = []
        ret = []
        for n, i in enumerate(lines):
            if not i:
                continue
            items = i.split(",")
            if n == 0:
                heads = items
            else:
                appends = {}
                for nl, il in enumerate(items):
                    try:
                        appends[heads[nl]] = il
                    except IndexError:
                        continue
                ret.append(appends)
        return ret

    def get_unitypy_env(self, path: str):
        bundle_hash = self.get_bundle_hash_from_path(path)
        bundle_path = self.bundle_hash_to_path(bundle_hash)
        if not os.path.isfile(bundle_path):
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")
        return UnityPy.load(bundle_path), bundle_hash

    def get_csv_data(self, path, csv_name):
        env, bundle_hash = self.get_unitypy_env(path)
        objects = env.objects
        for obj in objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                if data.name == csv_name:
                    return self.load_csv(data.text), bundle_hash

    def get_lrc(self, music_id: int) -> t.Dict[int, str]:
        csv_data, bundle_hash = self.get_csv_data(f"live/musicscores/m{music_id}/m{music_id}_lyrics",
                                                  f"m{music_id}_lyrics")
        ret = {}
        for i in csv_data:
            ret[int(i["time"])] = i["lyrics"]
        return ret

    def get_parts(self, music_id: int) -> t.Dict[int, models.LivePart]:
        csv_data, bundle_hash = self.get_csv_data(f"live/musicscores/m{music_id}/m{music_id}_part",
                                                  f"m{music_id}_part")
        ret = {}
        for i in csv_data:
            ret[int(i["time"])] = models.LivePart(**i)
        return ret

    def extract_live_music_bgm(self, music_id):
        acb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_oke_01.acb")
        awb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_oke_01.awb")
        if not all([acb_hash, awb_hash]):
            acb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_oke_02.acb")
            awb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_oke_02.awb")
            if not all([acb_hash, awb_hash]):
                raise FileNotFoundError(f"Music bgm not found.")
        acb_path = self.bundle_hash_to_path(acb_hash)
        awb_path = self.bundle_hash_to_path(awb_hash)
        exactor = self.get_extractor(awb_path, acb_path)
        if self.wav_format is not None:
            exactor.SetWaveFormat(*self.wav_format)
        ret = exactor.ExtractAudioFromWaveId(f"{self.save_path}/music/{music_id}", "bgm", 0)
        exactor.Close()
        return ret

    @staticmethod
    def resample_file(data: t.Union[list, str], rate: int, bits: int, channels: int):
        if isinstance(data, str):
            fname = os.path.split(data)[1]
            umares.voice_extractor.UmaVoiceEx.ResampleWav(data, f"temp/{fname}", rate, bits, channels)
            if os.path.isfile(f"temp/{fname}"):
                shutil.move(f"temp/{fname}", data)
        elif isinstance(data, list):
            for i in data:
                fname = os.path.split(i)[1]
                umares.voice_extractor.UmaVoiceEx.ResampleWav(i, f"temp/{fname}", rate, bits, channels)
                if os.path.isfile(f"temp/{fname}"):
                    shutil.move(f"temp/{fname}", i)

    def extract_live_chara_sound(self, music_id, chara_id, wave_id: t.Optional[int] = 0):
        acb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara_{chara_id}_01.acb")
        awb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara_{chara_id}_01.awb")
        if not all([acb_hash, awb_hash]):
            raise FileNotFoundError(f"Character not found.")
        acb_path = self.bundle_hash_to_path(acb_hash)
        awb_path = self.bundle_hash_to_path(awb_hash)
        exactor = self.get_extractor(awb_path, acb_path)
        if self.wav_format is not None:
            exactor.SetWaveFormat(*self.wav_format)
        if wave_id is None:
            ret = [exactor.ExtractAudioFromWaveId(f"{self.save_path}/music/{music_id}/chara_{chara_id}", "chara_", i)
                    for i in exactor.GetWaveIds()]
        else:
            ret = exactor.ExtractAudioFromWaveId(f"{self.save_path}/music/{music_id}/chara_{chara_id}", "chara_",
                                                  wave_id)
        exactor.Close()
        return ret

    def cut_live_chara_song_by_lrc(self, music_id, chara_id, remove_audio_silence=False, output_chara_id=None):
        lrc_data = self.get_lrc(music_id)
        char_sound = self.extract_live_chara_sound(music_id, chara_id)
        cuts = [[]]
        lrc_list = []
        for time_ms in lrc_data:
            lrc = lrc_data[time_ms]
            if not lrc:
                continue

            if len(cuts[-1]) < 2:
                cuts[-1].append(time_ms)
            if len(cuts[-1]) >= 2:
                cuts.append([time_ms])

            lrc_list.append(lrc)
        if len(cuts[-1]) == 1:
            cuts[-1].append(cuts[-1][0] + 10000)
        cut_files = self.cut_wav_batch(char_sound, f"{self.save_path}/music/{music_id}/cutbylrc/{chara_id}/{chara_id}",
                                       cuts)
        if len(cut_files) != len(lrc_list):
            raise IndexError(f"LRC not match.")
        else:
            with open(f"{self.save_path}/output_song.txt", "a", encoding="utf8") as f:
                for n, i in enumerate(lrc_list):
                    if remove_audio_silence:
                        self.get_uninited_extractor().RemoveAudioSilence(cut_files[n])
                        # if self.wav_format is not None:
                        #     self.resample_file(cut_files[n], *self.wav_format)
                    lrc_out = i.replace("\r", " ").replace("\n", " ")
                    if output_chara_id is None:
                        f.write(f"{cut_files[n]}|{lrc_out}\n")
                    else:
                        f.write(f"{cut_files[n]}|{output_chara_id}|{lrc_out}\n")
            return f"{self.save_path}/output_song.txt"

    def get_charas_singing_data(self, music_id, chara_list: t.Optional[t.List[int]],
                                desc="Extracting chara singing data..."):
        chara_permission = self.get_live_permission(music_id)
        vaild_chara_ids = []
        if chara_list is None:
            vaild_chara_ids = chara_permission
        else:
            for i in chara_list:
                if i in chara_permission:
                    vaild_chara_ids.append(i)

        save_file_names = {}
        for i in tqdm(vaild_chara_ids, desc=desc):
            awb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara_{i}_01.awb")
            acb_hash = self.get_bundle_hash_from_path(f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara_{i}_01.acb")
            if not all([awb_hash, acb_hash]):
                continue
            awb_path = self.bundle_hash_to_path(awb_hash)
            acb_path = self.bundle_hash_to_path(acb_hash)
            extractor = self.get_extractor(awb_path, acb_path)
            wave_ids = extractor.GetWaveIds()
            for wave_id in wave_ids:
                ex_name = extractor.ExtractAudioFromWaveId(f"temp/live/{music_id}/{i}", "clear", wave_id)
                if i not in save_file_names:
                    save_file_names[i] = {}
                save_file_names[i][wave_id] = ex_name
            extractor.Close()
        return save_file_names

    def mix_live_song_all_sing(self, music_id: int, chara_list: t.Optional[t.List[int]], volume: float):
        music_bgm = self.extract_live_music_bgm(music_id)
        save_file_names = self.get_charas_singing_data(music_id, chara_list)
        save_name = f"{self.save_path}/music/{music_id}/mix_all.wav"
        file_list = [music_bgm]
        for chara_id in save_file_names:
            for wave_id in save_file_names[chara_id]:
                file_list.append(save_file_names[chara_id][wave_id])
        self.mix_wavs(file_list, save_name, volume)
        return save_name

    def mix_live_song_by_parts(self, music_id: int, *charas: t.List[int], volume: float):
        charas = charas[:7]
        music_bgm = self.extract_live_music_bgm(music_id)
        save_file_names = [self.get_charas_singing_data(music_id, i) for i in charas]
        save_name = f"{self.save_path}/music/{music_id}/mix_by_parts.wav"
        singing_data = self.get_parts(music_id)
        singing_data_keys = list(singing_data.keys())
        file_on_times = {}
        for t_index, time_ms in enumerate(singing_data_keys):
            part = singing_data[time_ms]
            part_stat = [part.center, part.left, part.right, part.left2, part.right2, part.left3, part.right3]
            for n, char_ids in enumerate(charas):
                for char_id in char_ids:
                    pos_stat = part_stat[n]
                    wave_id = pos_stat - 1
                    if wave_id >= 0:
                        try:
                            current_file_name = save_file_names[n][char_id][wave_id]
                        except (IndexError, KeyError):
                            continue
                        next_time_ms = singing_data_keys[t_index + 1] if t_index + 1 < len(singing_data_keys) \
                            else time_ms + 30000
                        if current_file_name not in file_on_times:
                            file_on_times[current_file_name] = []
                        file_on_times[current_file_name].append([time_ms, next_time_ms])
        target_files = []
        for file_name in tqdm(file_on_times, desc="Preprocessing files..."):
            ftimes = file_on_times[file_name]
            save_name_p = f"{file_name}_sl.wav"
            target_files.append(save_name_p)
            self.SilenceWavPartsByActivePos(file_name, save_name_p, ftimes)
        self.mix_wavs([music_bgm] + target_files, save_name, volume)
        for i in target_files:
            os.remove(i)
        return save_name

    def _get_image(self, db_path: str):
        bundle_path = self.bundle_hash_to_path(
            self.get_bundle_hash_from_path(db_path)
        )
        if not os.path.isfile(bundle_path):
            return None
        env = UnityPy.load(bundle_path)
        objects = env.objects
        for obj in objects:
            if obj.type.name == "Texture2D":
                fp = io.BytesIO()
                data = obj.read()
                data.image.save(fp, format="png")
                return fp
        return None

    def get_live_pos_count(self, music_id):
        on_indexs = []
        singing_data = self.get_parts(music_id)
        for time_ms in singing_data:
            part = singing_data[time_ms]
            part_stat = [part.center, part.left, part.right, part.left2, part.right2, part.left3, part.right3]
            for n, i in enumerate(part_stat):
                if i > 0:
                    if n not in on_indexs:
                        on_indexs.append(n)
        return len(on_indexs)

    def get_char_icon(self, chara_id):
        return self._get_image(f"chara/chr{chara_id}/chr_icon_{chara_id}")

    def get_song_jacket(self, music_id):
        return self._get_image(f"live/jacket/jacket_icon_l_{music_id}")
