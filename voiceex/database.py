import os
import sqlite3
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

    def get_story_text_ids(self, chara_id, base="04"):
        cursor = self.meta_conn.cursor()
        query = cursor.execute("SELECT h, n from a WHERE n LIKE ?",
                               [f"story/data/{base}/{chara_id}/storytimeline_{base}{chara_id}%"]).fetchall()
        ret = [(i[0], i[1]) for i in query]
        cursor.close()
        return ret

    def get_character_system_text(self, chara_id: int):
        cursor = self.master_conn.cursor()
        query = cursor.execute(
            "SELECT character_id, text, cue_sheet, cue_id FROM character_system_text WHERE character_id = ?", [chara_id]
        ).fetchall()
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
