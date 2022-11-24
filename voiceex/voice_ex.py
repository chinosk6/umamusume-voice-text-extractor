from . import resource as ures
import UnityPy
import typing as t
from . import models as m
import os
from .ulogger import logger as log
import time
import json

class VoiceEx(ures.ResourceEx):
    def __init__(self, save_path="save", get_voice_from_all_stories=False, download_missing_voice_files=False,
                 use_cache=False):
        super().__init__(download_missing_voice_files=download_missing_voice_files)
        self.save_path = save_path
        self.get_voice_from_all_stories = get_voice_from_all_stories
        self.use_cache = use_cache

        self.multi_char_out_ids = {}

        if not os.path.isdir(self.save_path):
            os.makedirs(self.save_path)
        self.cache_path = "./umacache"
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        self.cache = self.load_cache()

    def load_cache(self):
        try:
            if os.path.isfile(f"{self.cache_path}/voice_text_cache.json"):
                with open(f"{self.cache_path}/voice_text_cache.json", "r", encoding="utf8") as f:
                    return json.load(f)
        except BaseException as e:
            log.logger(f"Load cache failed: {e}", error=True)
        return {}

    def save_cache(self):
        log.logger("Text cache saved.")
        with open(f"{self.cache_path}/voice_text_cache.json", "w", encoding="utf8") as f:
            json.dump(self.cache, f, ensure_ascii=False)

    def story_text_check(self, data: dict, story_ab_hash: str, story_resource_name: str,
                         chara_ids: t.Optional[t.List[int]] = None):
        if data["VoiceSheetId"]:
            if chara_ids is not None:
                if data["CharaId"] not in chara_ids:
                    return None
            return m.VoiceBaseInfo(story_ab_hash=story_ab_hash, story_resource_name=story_resource_name,
                                   voice_ab_hash=self.get_story_sound_id(data["VoiceSheetId"]), **data)
        return None

    def get_mono_trees(self, t_path):
        if self.use_cache:
            if t_path in self.cache:
                return self.cache[t_path]

        env = UnityPy.load(t_path)
        objects = env.objects
        ret = []
        for obj in objects:
            if obj.type.name == "MonoBehaviour":
                mono_tree = obj.read_typetree()
                if all([i in mono_tree for i in ["CharaId", "Name", "Text", "ChoiceDataList", "VoiceSheetId", "CueId"]]):
                    ret.append(mono_tree)
        self.cache[t_path] = ret
        return ret

    def get_story_text(self, chara_ids: t.List[int]) -> t.Dict[int, t.List[m.VoiceBaseInfo]]:
        char_results = {}
        for i in chara_ids:
            char_results[i] = []
        story_hashes = self.get_story_text_ids(None, base="02")  # 主线/main story
        story_hashes += self.get_story_text_ids(None, base="09")  # 额外故事/extra story
        story_hashes += self.get_story_text_ids(None, base="10")  # 周年庆/anniversary
        if self.get_voice_from_all_stories:
            story_hashes += self.get_story_text_ids(None, base="04")

        tLen = len(story_hashes)
        for n, (i, name) in enumerate(story_hashes):
            log.logger(f"Loading story text...  {n + 1}/{tLen}")
            t_path = self.bundle_hash_to_path(i)
            mono_trees = self.get_mono_trees(t_path)
            for mono_tree in mono_trees:
                text_info = self.story_text_check(mono_tree, i, name, chara_ids)
                if text_info is None:
                    continue
                _char_id = mono_tree["CharaId"]
                char_results[_char_id].append(text_info)

        if not self.get_voice_from_all_stories:
            for chara_id in chara_ids:
                chara_story_hashes = self.get_story_text_ids(chara_id, base="04")
                tLen = len(chara_story_hashes)
                for n, (i, name) in enumerate(chara_story_hashes):
                    log.logger(f"Loading character story text {chara_id}...  {n + 1}/{tLen}")
                    t_path = self.bundle_hash_to_path(i)
                    mono_trees = self.get_mono_trees(t_path)
                    for mono_tree in mono_trees:
                        text_info = self.story_text_check(mono_tree, i, name, [chara_id])
                        if text_info is None:
                            continue
                        _char_id = mono_tree["CharaId"]
                        char_results[_char_id].append(text_info)
        self.save_cache()
        return char_results

    @staticmethod
    def recheck_data(data: t.List[m.VoiceBaseInfo]):
        resultlist = []
        for i in data:
            resultlist.append(i) if i not in resultlist else ...
        ret = {}
        for i in resultlist:
            if i.voice_ab_hash not in ret:
                ret[i.voice_ab_hash] = []
            ret[i.voice_ab_hash].append(i)
        return ret

    def extract_text_and_voice(self, data: t.Dict[int, t.List[m.VoiceBaseInfo]], output_multi: bool):
        failed_names = []

        out_file = open(f"{self.save_path}/output.txt", "a", encoding="utf8")

        for char_id in data:
            stories = self.recheck_data(data[char_id])
            for voice_ab_hash in stories:
                bundle_name = self.bundle_hash_to_path(voice_ab_hash)
                try:
                    if bundle_name in failed_names:
                        continue
                    if not os.path.isfile(bundle_name):
                        if self.download_missing_voice_files:
                            log.logger(f"{bundle_name} not found, try download...", warning=True)
                            self.download_sound(voice_ab_hash, bundle_name)
                            log.logger(f"Download success: {bundle_name}")
                        else:
                            log.logger(f"{bundle_name} not found!", error=True)
                            failed_names.append(bundle_name)
                            continue
                    extractor = self.get_extractor(bundle_name)
                except BaseException as e:
                    log.logger(f"Exception occurred when loading bundle: {e}", error=True)
                    failed_names.append(bundle_name)
                    continue

                for i in stories[voice_ab_hash]:
                    try:
                        save_name = extractor.ExtractAudioFromCueId(
                            f"{self.save_path}/{i.story_resource_name}", "", i.CueId
                        )
                        save_text = i.Text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("|", " ")
                        log.logger(f"{save_name} {save_text}", debug=True)

                        if not output_multi:
                            out_file.write(f"{save_name[len(self.save_path) + 1:]}|{save_text}\n")
                        else:
                            out_file.write(f"{save_name[len(self.save_path) + 1:]}|"
                                           f"{self.multi_char_out_ids.get(char_id, char_id)}|"
                                           f"{save_text}\n")
                    except BaseException as e:
                        log.logger(f"Exception occurred when extract story text: {e}", error=True)
                extractor.Close()
        out_file.close()

    def get_extract_character_system_text(self, chara_id: int):
        chara_text = self.get_character_system_text(chara_id)
        tLen = len(chara_text)
        ex_text_list = []

        for n, (character_id, text, cue_sheet, cue_id) in enumerate(chara_text):
            log.logger(f"Loading character_system_text ({chara_id})...   {n + 1}/{tLen}")
            voice_hash = self.get_awb_hash_from_sheetname(cue_sheet)
            if voice_hash is None:
                log.logger(f"cue_sheet not found: {cue_sheet} ({cue_id}) character: {character_id} text: {text}",
                           error=True)
                continue

            voice_info = m.VoiceBaseInfo(
                CharaId=character_id, Text=text, VoiceSheetId=cue_sheet, CueId=cue_id,
                story_resource_name=f"character_system_text/{character_id}/{cue_sheet}", voice_ab_hash=voice_hash
            )
            ex_text_list.append(voice_info)

        return {chara_id: ex_text_list}

    def extract_chara_text(self, chara_ids: t.List[int], output_multi: bool):
        stories = self.get_story_text(chara_ids)
        for i in chara_ids:
            char_text_data = self.get_extract_character_system_text(i)
            if i not in stories:
                stories[i] = []
            stories[i] += char_text_data[i]
        self.extract_text_and_voice(stories, output_multi)

    def extract_all_char_text_single(self, char_id: int):
        self.extract_chara_text([char_id], False)
        log.logger("Done.")

    def set_multi_char_out_ids(self, char_ids_data: t.List[t.Tuple[int, t.Union[int, str]]]):
        for char_id, save_id in char_ids_data:
            self.multi_char_out_ids[char_id] = save_id

    def extract_all_char_text_multi(self, char_ids: t.List[int]):
        if not self.multi_char_out_ids:
            log.logger("Warning: You haven't set the character id yet, it will be saved as the game id", warning=True)
            time.sleep(3)
        self.extract_chara_text(char_ids, True)
        log.logger("Done.")
