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

    def __eq__(self, other):
        if isinstance(other, VoiceBaseInfo):
            return (self.voice_ab_hash == other.voice_ab_hash) and (self.CueId == other.CueId)
        else:
            return False
