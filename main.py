import voiceex


ex = voiceex.VoiceEx(save_path="save", download_missing_abfile=True)
ex.set_proxies("http://127.0.0.1:10087")


ex.extract_all_char_text(1024)
