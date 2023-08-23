import os
import sqlite3
import time

from . import downloader


class UmaDatabase(downloader.UmaDownloader):
    def __init__(self):
        super().__init__()

        profile_path = os.environ.get("UserProfile")
        self.base_path = f"{profile_path}/AppData/LocalLow/Cygames/umamusume"
        self.meta_conn = sqlite3.connect(f"{self.base_path}/meta")
        self.master_conn = sqlite3.connect(f"{self.base_path}/master/master.mdb")

    def bundle_hash_to_path(self, bundle_hash: str):
        return f"{self.base_path}/dat/{bundle_hash[:2]}/{bundle_hash}"

    def get_bundle_hash_from_path(self, path: str):
        cursor = self.meta_conn.cursor()
        query = cursor.execute("SELECT h FROM a WHERE n=?", [path]).fetchone()
        if query is not None:
            return query[0]

    def get_awb_hash_from_sheetname(self, n: str):
        cursor = self.meta_conn.cursor()
        query = cursor.execute("SELECT h FROM a WHERE n LIKE ?", [f"%{n}.awb"]).fetchone()
        cursor.close()
        if query:
            return query[0]
        else:
            return None

    def get_story_sound_id(self, voicesheetid):
        cursor = self.meta_conn.cursor()
        query = cursor.execute("SELECT h from a WHERE n LIKE ?", [f"sound/c/snd_voi_story_{voicesheetid}.awb"])\
            .fetchone()
        if query:
            ret = query[0]
        else:
            raise FileNotFoundError(f"voicesheetid: {voicesheetid} not found!")
        cursor.close()
        return ret

    def get_story_text_ids(self, chara_id=None, base="04"):
        cursor = self.meta_conn.cursor()

        query_sql = f"story/data/{base}/{chara_id}/storytimeline_{base}{chara_id}%" if chara_id is not None else \
            f"story/data/{base}/____/storytimeline_{base}%"
        query = cursor.execute("SELECT h, n from a WHERE n LIKE ?", [query_sql]).fetchall()
        ret = [(i[0], i[1]) for i in query]
        cursor.close()
        return ret

    def get_character_system_text(self, chara_id: int):
        cursor = self.master_conn.cursor()
        query = cursor.execute(
            "SELECT character_id, text, cue_sheet, cue_id, gender FROM character_system_text WHERE character_id = ?",
            [chara_id]).fetchall()
        cursor.close()
        return query

    def awb_bundle_path_to_acb_bundle_path(self, awb_bundle_path: str):
        awb_hash = os.path.split(awb_bundle_path)[-1]
        cursor = self.meta_conn.cursor()
        query = cursor.execute("SELECT n FROM a WHERE h=?", [awb_hash]).fetchone()
        if not query:
            return None

        awb_full_name = query[0]
        acb_full_name = f"{awb_full_name[:-4]}.acb"
        query = cursor.execute("SELECT n, h FROM a WHERE n=?", [acb_full_name]).fetchone()
        cursor.close()
        return query

    def get_live_ids(self):
        cursor = self.master_conn.cursor()
        query = cursor.execute("SELECT music_id FROM live_data WHERE has_live=1 OR music_type=99 ORDER BY music_id").fetchall()
        cursor.close()
        return [i[0] for i in query]

    def get_jukebox_ids(self):
        cursor = self.master_conn.cursor()
        query = cursor.execute("SELECT music_id FROM jukebox_music_data").fetchall()
        cursor.close()
        return [i[0] for i in query]

    def get_live_permission(self, music_id: int):
        cursor = self.master_conn.cursor()
        query = cursor.execute("SELECT chara_id FROM live_permission_data WHERE music_id=?", [music_id]).fetchall()
        if query:
            cursor.close()
            return [i[0] for i in query]
        else:
            query = cursor.execute("SELECT song_chara_type FROM live_data WHERE music_id=?", [music_id]).fetchone()
            if query is None:
                return []
            if query[0] != 1:
                return []
            else:
                cursor.close()
                cursor = self.meta_conn.cursor()
                query = cursor.execute("SELECT n FROM a WHERE n LIKE ?",
                                       [f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara______01.awb"]).fetchall()
                ret = []
                for i in query:
                    try:
                        p_id = int(i[0][len(f"sound/l/{music_id}/snd_bgm_live_{music_id}_chara_"):-len("_01.awb")])
                        ret.append(p_id)
                    except:
                        continue
                cursor.close()
                return ret

    def get_all_chara_ids(self):
        cursor = self.master_conn.cursor()
        query = cursor.execute("SELECT id FROM chara_data").fetchall()
        cursor.close()
        return [i[0] for i in query]
