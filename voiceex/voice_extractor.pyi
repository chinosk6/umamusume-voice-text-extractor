
class UmaVoiceEx:
    def __init__(self, acbPath: str, awbPath: str):
        """
        From voice_ex.cs
        :param acbPath: acb file path
        :param awbPath: awb file path
        """
        ...
    @staticmethod
    def GetSaveName(savePath: str, saveFileprefix: str, waveId: int) -> str: ...
    def ExtractAudioFromWaveId(self, savePath: str, saveFileprefix: str, waveId: int) -> str: ...
    def ExtractAudioFromCueId(self, savePath: str, saveFileprefix: str, cueId: int) -> str: ...
    def SetWaveFormat(self, rate: int, bits: int, channels: int): ...
    def GetAudioCount(self) -> int: ...
    def SetVolume(self, value: float): ...
    def Close(self): ...