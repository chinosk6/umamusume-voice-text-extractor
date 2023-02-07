import json
import os
from pydantic import BaseModel
import typing as t


class VoiceBaseInfo(BaseModel):
    CharaId: int
    # Name: str
    Text: str
    VoiceSheetId: t.Optional[str]
    CueId: int

    story_resource_name: str
    # story_ab_hash: str
    voice_ab_hash: str
    gender: t.Optional[int] = 0

    def __eq__(self, other):
        if isinstance(other, VoiceBaseInfo):
            return (self.voice_ab_hash == other.voice_ab_hash) and (self.CueId == other.CueId) \
                   and (self.gender == other.gender)
        else:
            return False


class UserConfig(BaseModel):
    proxy_ve: t.Optional[str] = ""
    proxy_me: t.Optional[str] = ""
    save_path_ve: t.Optional[str] = "./save"
    save_path_me: t.Optional[str] = "./save"
    use_proxy_ve: t.Optional[bool] = False
    use_proxy_me: t.Optional[bool] = False

    def __init__(self):
        if os.path.isfile("ex_config.json"):
            with open("ex_config.json", "r", encoding="utf8") as f:
                data = json.load(f)
        else:
            data = {}
        super().__init__(**data)

    def save_data(self):
        with open("ex_config.json", "w", encoding="utf8") as f:
            json.dump(self.dict(), f, indent=4, ensure_ascii=False)


user_config = UserConfig()
