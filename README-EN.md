# umamusume-voice-text-extractor
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

# set save folder and download when missing awb/acb files
ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True)

# set download proxy (Optional)
ex.set_proxies("http://127.0.0.1:10087")

# start extract character No.1024 (Mayano)
ex.extract_all_char_text(1024)
```

- The voice-text file is in `{your save_path}/output.txt`.



# Special Thanks

- [MarshmallowAndroid/UmaMusumeExplorer](https://github.com/MarshmallowAndroid/UmaMusumeExplorer)

