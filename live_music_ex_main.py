import voiceex

music_ex = voiceex.live_music.LiveMusicExtractor("./save")
# music_ex.extract_live_music_bgm(1053)
music_ex.extract_live_chara_sound(1053, 1046, 0)
# music_ex.extract_live_chara_sound(1053, 1046, 1)
# music_ex.cut_live_chara_song_by_lrc(1053, 1046, remove_audio_blank=True)
# print(music_ex.mix_live_song_all_sing(1059, None))
print(music_ex.mix_live_song_by_parts(1059, [1065, 1085], [1078], [1093]))

