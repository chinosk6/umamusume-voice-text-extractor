import voiceex


if __name__ == "__main__":

    # set save folder and download when missing awb/acb files
    ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True, get_voice_from_all_stories=False)

    # set download proxy
    ex.set_proxies("http://127.0.0.1:10087")

    # start extract character No.1024 (Mayano)
    ex.extract_all_char_text(1024)
