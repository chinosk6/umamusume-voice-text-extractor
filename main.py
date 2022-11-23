import voiceex


if __name__ == "__main__":

    # set save folder, download when missing awb/acb files, get voice from all character stories (takes a long time)
    ex = voiceex.VoiceEx(save_path="save", download_missing_voice_files=True, get_voice_from_all_stories=False)

    # set wave sampling rate, bits, channels (optional)
    ex.set_wav_format(22050, 16, 1)

    # set download proxy (optional)
    ex.set_proxies("http://127.0.0.1:10087")

    extract_multi = True

    if not extract_multi:
        # Single Character Mode
        # start extract character No.1024 (MayanoTopgun)
        ex.extract_all_char_text_single(1024)

    else:
        # Multi Character Mode
        # Set character output id (Union[int, str])
        ex.set_multi_char_out_ids([
            (1024, "0"), (1046, 1)
        ])
        # start extract character No.1024 (MayanoTopgun) and No.1046 (SmartFalcon)
        ex.extract_all_char_text_multi([1024, 1046])
