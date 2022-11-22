# umamusume-voice-text-extractor

- [English](README-EN.md)

- 提取语音和对应的文本



# 使用方法

- 需要环境: `Python 3.8+`、`.Net 6.0`
- 安装 Python 包: `pip install -r requirements.txt`

```
pydantic~=1.8.2
colorama~=0.4.4
pythonnet~=3.0.1
UnityPy~=1.8.15
requests~=2.28.1
```

- 根据自己的需求修改 `main.py`, 然后运行: `python main.py`

```python
import voiceex

# 设置保存路径 和 当缺失文件时是否直接下载
ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True)

# 设置下载代理 (可选, 若不需要, 直接注释掉即可)
ex.set_proxies("http://127.0.0.1:10087")

# start extract character No.1024 (Mayano)
ex.extract_all_char_text(1024)
```

- 音频文本对应文件在 `{你设置的 save_path}/output.txt`.



# 特别感谢

- [MarshmallowAndroid/UmaMusumeExplorer](https://github.com/MarshmallowAndroid/UmaMusumeExplorer)

