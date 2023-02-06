import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QStyleFactory, QFileDialog, QTableWidgetItem, \
    QListWidgetItem, QListWidget, QMenu, QAction
from .qtui.ui_import import MainUI
import ctypes
from threading import Thread
import voiceex

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
except:
    pass

local_language = ctypes.windll.kernel32.GetUserDefaultUILanguage()
sChinese_lang_id = [0x0004, 0x0804, 0x1004]  # zh-Hans, zh-CN, zh-SG
tChinese_lang_id = [0x0404, 0x0c04, 0x1404, 0x048E]  # zh-TW, zh-HK, zh-MO, zh-yue-HK

# translate = QtCore.QCoreApplication.translate

class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        self.ui = MainUI()
        self.ui.setupUi(self)


class UIChange(QObject):
    show_msgbox_signal = QtCore.pyqtSignal(str, str)
    set_start_btn_stat_signal = QtCore.pyqtSignal(bool)

    def __init__(self):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        QApplication.setStyle(QStyleFactory.create("windowsvista"))  # ['windowsvista', 'Windows', 'Fusion']
        super(UIChange, self).__init__()
        self.app = QApplication(sys.argv)

        self.trans = QtCore.QTranslator()
        self.load_i18n()

        self.window = QMainWindow()
        self.window.setWindowIcon(QtGui.QIcon(":/img/linqin_nawone.ico"))
        self.ui = MainUI()
        self.ui.setupUi(self.window)

        self.reg_clicked_connects()
        self.signal_reg()


    def load_i18n(self):
        if local_language in sChinese_lang_id:
            self.trans.load(":/trans/main_ui.qm")
            self.install_trans()

        elif local_language in tChinese_lang_id:
            self.trans.load(":/trans/main_ui.qm")
            self.install_trans()

    def install_trans(self):
        self.app.installTranslator(self.trans)

    def reg_clicked_connects(self):  # 点击回调注册
        self.ui.listWidget_chara_list.doubleClicked.connect(self.ve_chara_list_double_click)
        self.ui.listWidget_chara_list.clicked.connect(self.ve_chara_list_click)
        self.ui.pushButton_rm_selecting.clicked.connect(self.ve_remove_selecting_charas)
        self.ui.pushButton_single_start.clicked.connect(self.ve_start_extract_single)
        self.ui.pushButton_multi_start.clicked.connect(self.ve_start_extract_multi)
        self.ui.listWidget_music_list.clicked.connect(self.music_list_onclick)
        self.ui.listWidget_singing_chara_list.customContextMenuRequested.connect(self.singing_char_contex)
        self.ui.listWidget_singing_chara_list.clicked.connect(self.singing_char_onclick)
        self.ui.pushButton_extract_bgm.clicked.connect(self.extract_live_bgm)
        self.ui.pushButton_extract_chara_sound.clicked.connect(self.extract_live_chara_sound_full)
        self.ui.pushButton_extract_sound_by_lrc.clicked.connect(self.extract_live_chara_sound_by_lrc)
        self.ui.pushButton_me_delete_select.clicked.connect(self.delete_select_pos)
        self.ui.pushButton_me_clear.clicked.connect(self.clear_all_pos)
        self.ui.pushButton_start_mix.clicked.connect(self.live_start_mix)
        self.ui.pushButton_me_select_save_path.clicked.connect(self.set_path(self.ui.lineEdit_me_save_path))
        self.ui.pushButton_ve_select_save_path.clicked.connect(self.set_path(self.ui.lineEdit_ve_save_path))

    def signal_reg(self):  # 信号槽注册
        self.show_msgbox_signal.connect(self.show_message_box)
        self.set_start_btn_stat_signal.connect(self.set_extract_button_enable)

    def show_message_box(self, title, text, btn=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No):
        return QtWidgets.QMessageBox.information(self.window, title, text, btn)

    def set_path(self, target_lineedit):
        def _():
            folder_path = QFileDialog.getExistingDirectory(self.ui, "Choose a folder")
            if folder_path != "":
                target_lineedit.setText(folder_path)
        return _


    @staticmethod
    def open_file_path(checked: list):
        if checked:
            os.system(f'explorer /select, {os.path.realpath(checked[0].text())}')

    def ve_chara_list_click(self, click_index: QtCore.QModelIndex):
        chara_id = click_index.data().strip()
        self.ui.lineEdit_ve_single_id.setText(chara_id)

    def ve_chara_list_double_click(self, click_index: QtCore.QModelIndex):
        chara_id = click_index.data().strip()
        now_row_count = self.ui.tableWidget_ve_extarct.rowCount()
        for i in range(now_row_count):
            item = self.ui.tableWidget_ve_extarct.item(i, 0)
            if item is not None:
                if item.text() == chara_id:
                    return
        self.ui.tableWidget_ve_extarct.setRowCount(now_row_count + 1)
        self.ui.tableWidget_ve_extarct.setItem(now_row_count, 0, QTableWidgetItem(chara_id))
        self.ui.tableWidget_ve_extarct.setItem(now_row_count, 1, QTableWidgetItem(chara_id))

    def ve_remove_selecting_charas(self):
        for i in self.ui.tableWidget_ve_extarct.selectedItems():
            self.ui.tableWidget_ve_extarct.removeRow(i.row())
            break

    def build_ve_chara_list(self, chara_list: list, ex: voiceex.live_music.LiveMusicExtractor):
        self.ui.tableWidget_ve_extarct.horizontalHeader().setVisible(True)
        self.ui.listWidget_chara_list.setIconSize(QSize(64, 64))
        for n, chara_id in enumerate(chara_list):
            self.add_chara_to_list_widget(self.ui.listWidget_chara_list, chara_id, ex)

    @staticmethod
    def add_chara_to_list_widget(widget: QListWidget, chara_id, ex):
        chara_id = str(chara_id)

        for i in range(widget.count()):
            if widget.item(i).text() == chara_id:
                return

        img = ex.get_char_icon(chara_id)

        if img is not None:
            pm = QPixmap()
            pm.loadFromData(img.getvalue())
            icon = QIcon(pm)
            widget.addItem(QListWidgetItem(icon, str(chara_id)))
        else:
            widget.addItem(f"      {chara_id}")

    def set_extract_button_enable(self, stat: bool):
        self.ui.pushButton_single_start.setEnabled(stat)
        self.ui.pushButton_multi_start.setEnabled(stat)
        self.ui.pushButton_extract_bgm.setEnabled(stat)
        self.ui.pushButton_extract_chara_sound.setEnabled(stat)
        self.ui.pushButton_extract_sound_by_lrc.setEnabled(stat)
        self.ui.pushButton_start_mix.setEnabled(stat)

    def get_voice_ex(self):
        ex = voiceex.VoiceEx(save_path=self.ui.lineEdit_ve_save_path.text(),
                             download_missing_voice_files=self.ui.checkBox_ve_download_missing.isChecked(),
                             get_voice_from_all_stories=self.ui.checkBox_get_voice_from_all.isChecked(),
                             use_cache=self.ui.checkBox_ve_usecache.isChecked())
        if self.ui.checkBox_ve_use_proxy.isChecked():
            ex.set_proxies(self.ui.lineEdit_ve_proxy.text().strip())
        try:
            rate = int(self.ui.lineEdit_ve_rate.text())
            bits = int(self.ui.lineEdit_ve_bits.text())
            channels = int(self.ui.lineEdit_ve_channels.text())
            ex.set_wav_format(rate, bits, channels)
        except:
            self.ui.lineEdit_ve_rate.setText("")
            self.ui.lineEdit_ve_bits.setText("")
            self.ui.lineEdit_ve_channels.setText("")
        return ex

    def ve_start_extract_single(self):
        def _():
            self.set_start_btn_stat_signal.emit(False)
            try:
                ex = self.get_voice_ex()
                chara_id = int(self.ui.lineEdit_ve_single_id.text().strip())
                ex.extract_all_char_text_single(chara_id)
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def ve_start_extract_multi(self):
        def _():
            self.set_start_btn_stat_signal.emit(False)
            try:
                ex = self.get_voice_ex()
                now_row_count = self.ui.tableWidget_ve_extarct.rowCount()
                chara_ids = []
                save_ids = []
                for i in range(now_row_count):
                    item_chara_id = self.ui.tableWidget_ve_extarct.item(i, 0)
                    if item_chara_id is not None:
                        chara_id = item_chara_id.text()
                        item_save_id = self.ui.tableWidget_ve_extarct.item(i, 1)
                        save_id = item_save_id.text() if item_save_id is not None else chara_id
                        chara_ids.append(chara_id)
                        save_ids.append(save_id)
                ex.set_multi_char_out_ids([(i, save_ids[n]) for n, i in enumerate(chara_ids)])
                ex.extract_all_char_text_multi(chara_ids)
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def build_me_music_list(self, music_list: list, ex: voiceex.live_music.LiveMusicExtractor):
        # self.ui.listWidget_music_list.setStyleSheet("QListView::item { height: 100px; }")
        self.ui.listWidget_music_list.setIconSize(QSize(64, 64))
        for n, music_id in enumerate(music_list):
            img = ex.get_song_jacket(music_id)
            if img is not None:
                pm = QPixmap()
                pm.loadFromData(img.getvalue())
                icon = QIcon(pm)
                self.ui.listWidget_music_list.addItem(QListWidgetItem(icon, str(music_id)))
            else:
                self.ui.listWidget_music_list.addItem(f"      {music_id}")

    def music_list_onclick(self, index: QtCore.QModelIndex):
        try:
            music_id = int(index.data())
        except:
            return
        self.ui.listWidget_singing_chara_list.clear()
        music_ex = voiceex.live_music.LiveMusicExtractor("./temp")
        singing_chara_list = music_ex.get_live_permission(music_id)
        for i in singing_chara_list:
            self.add_chara_to_list_widget(self.ui.listWidget_singing_chara_list, i, music_ex)
        self.ui.lineEdit_music_id.setText(str(music_id))
        self.ui.label_singing_count.setText(str(music_ex.get_live_pos_count(music_id)))

    def singing_char_onlick(self, index: QtCore.QModelIndex):
        try:
            chara_id = int(index.data())
        except:
            return
        self.ui.lineEdit_chara_id.setText(str(chara_id))

    def add_char_to_mix_list(self, mx_index: int, chara_id, ex):
        def _():
            self.add_chara_to_list_widget(getattr(self.ui, f"listWidget_mx_{mx_index}"), chara_id, ex)
        return _

    def singing_char_contex(self, position):
        popMenu = QMenu()
        item = self.ui.listWidget_singing_chara_list.itemAt(position)
        if item:
            ex = voiceex.live_music.LiveMusicExtractor("./temp")
            for i in range(8)[1:]:
                creAct = QAction(f"Add to mixer position {i}", self)
                popMenu.addAction(creAct)
                creAct.triggered.connect(self.add_char_to_mix_list(i, item.text(), ex))
        popMenu.exec_(self.ui.listWidget_singing_chara_list.mapToGlobal(position))


    def init_main_window(self):
        music_ex = voiceex.live_music.LiveMusicExtractor("./temp")
        chara_list = music_ex.get_all_chara_ids()
        self.build_ve_chara_list(chara_list, music_ex)
        music_list = music_ex.get_live_ids()
        self.build_me_music_list(music_list, music_ex)
        self.ui.listWidget_singing_chara_list.setIconSize(QSize(48, 48))

    def singing_char_onclick(self, index: QtCore.QModelIndex):
        self.ui.lineEdit_chara_id.setText(str(index.data()))

    def get_live_extractor(self):
        music_ex = voiceex.live_music.LiveMusicExtractor(
            save_path=self.ui.lineEdit_me_save_path.text().strip(),
            download_missing_voice_files=self.ui.checkBox_me_download_missing.isChecked()
        )
        if self.ui.checkBox_me_proxy.isChecked():
            music_ex.set_proxies(self.ui.lineEdit_me_proxy.text())
        return music_ex

    def extract_live_bgm(self):
        def _():
            self.set_start_btn_stat_signal.emit(False)
            try:
                ex = self.get_live_extractor()
                music_id = self.ui.lineEdit_music_id.text().strip()
                if music_id:
                    save_name = ex.extract_live_music_bgm(music_id)
                    print(f"Extract success: {save_name}")
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def extract_live_chara_sound_full(self):
        def _():
            self.set_start_btn_stat_signal.emit(False)
            try:
                ex = self.get_live_extractor()
                music_id = self.ui.lineEdit_music_id.text().strip()
                chara_id = self.ui.lineEdit_chara_id.text().strip()
                if not all([music_id, chara_id]):
                    return
                save_names = ex.extract_live_chara_sound(music_id, chara_id, None)
                save_names_str = "\n".join(save_names)
                print(f"Extract success:\n{save_names_str}")
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def extract_live_chara_sound_by_lrc(self):
        def _():
            self.set_start_btn_stat_signal.emit(False)
            try:
                ex = self.get_live_extractor()
                music_id = self.ui.lineEdit_music_id.text().strip()
                chara_id = self.ui.lineEdit_chara_id.text().strip()
                if not all([music_id, chara_id]):
                    return
                save_name = ex.cut_live_chara_song_by_lrc(
                    int(music_id), int(chara_id), remove_audio_silence=self.ui.checkBox_remove_silence.isChecked()
                )
                print(f"Extract success. See {save_name}")
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def delete_select_pos(self):
        current_index = self.ui.tabWidget_parts.currentIndex()
        widget: QListWidget = getattr(self.ui, f"listWidget_mx_{current_index + 1}")
        widget.takeItem(widget.currentIndex().row())

    def clear_all_pos(self):
        for i in range(8)[1:]:
            getattr(self.ui, f"listWidget_mx_{i}").clear()

    def live_start_mix(self):
        def _():
            def get_widget_all_items(wid: QListWidget):
                ret = []
                for _i in range(wid.count()):
                    ret.append(wid.item(_i))
                return ret

            self.set_start_btn_stat_signal.emit(False)
            try:
                music_id = self.ui.lineEdit_music_id.text().strip()
                if self.ui.checkBox_all_singing.isChecked():
                    args0 = []
                    for i in range(8)[1:]:
                        widget: QListWidget = getattr(self.ui, f"listWidget_mx_{i}")
                        args0 += [int(i.text()) for i in get_widget_all_items(widget)]
                    ex = self.get_live_extractor()
                    save_name = ex.mix_live_song_all_sing(music_id, list(set(args0)))
                    print(f"Extract success: {save_name}")
                else:
                    args = []
                    for i in range(8)[1:]:
                        widget: QListWidget = getattr(self.ui, f"listWidget_mx_{i}")
                        args.append([int(i.text()) for i in get_widget_all_items(widget)])
                    ex = self.get_live_extractor()
                    save_name = ex.mix_live_song_by_parts(music_id, *args)
                    print(f"Extract success: {save_name}")
            finally:
                self.set_start_btn_stat_signal.emit(True)
        Thread(target=_).start()

    def show_main_window(self):
        self.window.show()
        self.init_main_window()


    def ui_run_main(self):
        self.show_main_window()
        exit_code = self.app.exec_()
        sys.exit(exit_code)
        # os._exit(self.app.exec_())
