# umamusume-voice-text-extractor

- [Chinese/中文](README-ZH.md)

- Extract the voice and corresponding text



# Usage

- Required Environment: `Python 3.8+`、`.Net 6.0`
- Install python package: `pip install -r requirements.txt`

```
pydantic~=1.8.2
colorama~=0.4.4
pythonnet~=3.0.1
UnityPy~=1.8.15
requests~=2.28.1
```



- Edit and run `main.py`: `python main.py`

```python
import voiceex

# set save folder, download when missing awb/acb files, get voice from all character stories (takes a long time)
ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True, get_voice_from_all_stories=False)

# set wave sampling rate, bits, channels (optional)
ex.set_wav_format(22050, 16, 1)

# set download proxy (optional)
ex.set_proxies("http://127.0.0.1:10087")
```

 - Single Character Mode

```python
# Single Character Mode
# start extract character No.1024 (MayanoTopgun)
ex.extract_all_char_text_single(1024)
```

 - Multi Character Mode

```python
# Multi Character Mode
# Set character output id (Union[int, str])
ex.set_multi_char_out_ids([
    (1024, "0"), (1046, 1)
])
# start extract character No.1024 (MayanoTopgun) and No.1046 (SmartFalcon)
ex.extract_all_char_text_multi([1024, 1046])
```



- The voice-text file is in `{your save_path}/output.txt`.



# Extract Result

 - Voice files
<img src="img/file.jpg" style="zoom:35%;" />

 - Single character mode
<img src="img/text.jpg" style="zoom:30%;" />

 - Multi character mode
<img src="img/text_multi.jpg" style="zoom:30%;" />



# Special Thanks

- [MarshmallowAndroid/UmaMusumeExplorer](https://github.com/MarshmallowAndroid/UmaMusumeExplorer)

