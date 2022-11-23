import voiceex


if __name__ == "__main__":

    # set save folder, download when missing awb/acb files, get voice from all character stories (takes a long time)
    ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True, get_voice_from_all_stories=False)

    # set wave sampling rate, bits, channels (optional)
    ex.set_wav_format(22050, 16, 1)

    # set download proxy (optional)
    ex.set_proxies("http://127.0.0.1:10087")

    # start extract character No.1024 (Mayano)
    ex.extract_all_char_text(1024)
