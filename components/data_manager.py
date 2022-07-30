from sys import platform
import imgui
import easygui
import shutil
import os
import zipfile
import time
from components.util import LogLevel, Logger

from settings import Settings

class DataManager:
    logger = Logger("DataManager", LogLevel.DEBUG, "latest.log")
    logger.info("Loading settings")

    settings = Settings("settings.properties")
    data_saves = settings.get("data_saves", ["Default"])
    current_data_save = settings.get("data_save", 0)

    backup_folders = {"files": False}
    chosen_backup = 0
    save_dir = ""

    def __init__(self, parent) -> None:
        self.logger.info("Loading data manager")
        self.parent = parent
        self.save_dir = self.get_save_dir()
        self.logger.info("Done")
        if not os.path.exists("backups"):
            os.mkdir("backups")

    def render(self):
        imgui.begin("Data manager")
        imgui.text("Data folders")
        if imgui.button("Create data folder"):
            self.data_saves.append(easygui.diropenbox("Select new save folder"))
        if self.data_saves[self.current_data_save] != "Default":
            imgui.same_line()
            if imgui.button("Delete data folder"):
                self.logger.info("Delete data folder?")
                res = easygui.buttonbox(f"Are you sure you want to delete this save data directory ({self.data_saves[self.current_data_save]})? You can also just remove it from the list, and re-add it later using the 'Create' button.", "Delete save data directory", ("Delete", "Remove", "Cancel"))
                if res != "Cancel":
                    self.logger.info("Yes")
                    if res == "Delete":
                        self.logger.debug("Deleting")
                        shutil.rmtree(self.data_saves[self.current_data_save])
                    self.data_saves.remove(self.data_saves[self.current_data_save])
                    self.current_data_save = 0
                    self.save_dir = self.get_save_dir()
        c, self.current_data_save = imgui.combo("Current data folder", self.current_data_save, self.data_saves)
        if c:
            self.save_dir = self.get_save_dir()
        imgui.text("Data backups")
        show, _ = imgui.collapsing_header("Create a backup")
        if show:
            dir = self.save_dir
            for folder in os.listdir(dir):
                if os.path.isdir(f"{dir}/{folder}"):
                    if not folder in self.backup_folders.keys():
                        self.backup_folders[folder] = False
                    _, self.backup_folders[folder] = imgui.checkbox(folder, self.backup_folders[folder])
            _, self.backup_folders["files"] = imgui.checkbox("Files", self.backup_folders["files"])
            if imgui.button("Create backup"):
                self.logger.info("Creating backup")
                t = time.asctime().replace(":", ".")
                if not os.path.exists(f"backups"):
                    os.makedirs("backups")
                with zipfile.ZipFile(f"backups/{t}.zip", mode='w') as zip_file:
                    save_dir = self.get_save_dir()
                    len_dir_path = len(save_dir)
                    for file in os.listdir(save_dir):
                        if os.path.isdir(f"{save_dir}/{file}") and self.backup_folders[file]:
                            self.logger.debug(f"Backup dir : {save_dir}/{file}")
                            self.zip_dir(f"{save_dir}/{file}", zip_file, len_dir_path)
                        if self.backup_folders["files"] and not os.path.isdir(f"{save_dir}/{file}"):
                            self.logger.debug(f"Backup file: {save_dir}/{file}")
                            file_path = os.path.join(save_dir, file)
                            zip_file.write(file_path, file_path[len_dir_path:])

        show, _ = imgui.collapsing_header("Backups")
        if show: 
            backups = []
            for file in os.listdir("backups"):
                backups.append(file)
            _, self.chosen_backup = imgui.combo("Backup", self.chosen_backup, backups)
            #if imgui.button("Load backup"):
                # TODO load
            #imgui.same_line()
            if imgui.button("Delete backup"):
                self.logger.info("Delete backup?")
                if easygui.ynbox(f"Delete {backups[self.chosen_backup]}", "Confirm backup deletion"):
                    self.logger.info("Yes")
                    os.remove(f"backups/{backups[self.chosen_backup]}")
                    self.chosen_backup = 0
        imgui.end()

    def zip_dir(self, path, zip_file, len_dir_path):
        self.logger.info(f"Zipping {path} to {zip_file.filename}")
        try:
            for file in os.listdir(path):
                zip_file.write(path+"/"+file, path[len_dir_path:]+"/"+file)
        except Exception as err:
            self.logger.error("Error while zipping dir: " + str(err))
            raise err

    def get_save_dir(self):
        self.logger.info("Getting save dir")
        dir = self.data_saves[self.current_data_save]
        try:
            if dir == "Default":
                self.logger.debug("Getting default dir")
                if platform == "linux" or platform == "linux2":
                    self.logger.debug("Detected linux")
                    if os.getenv("XDG_DATA_HOME") != None:
                        dir = os.getenv("XDG_DATA_HOME")
                        if not dir.endsWith("/"): dir += "/"
                        dir = dir + "Mindustry/"
                    else:
                        dir = os.path.expanduser("~") + "/.local/share/Mindustry/"
                elif platform == "win32":
                    self.logger.debug("Detected windows")
                    dir = os.getenv("AppData") + "/Mindustry"
            self.logger.info(f"Got dir: {dir}")
            return dir
        except Exception as err:
            self.logger.error("Error getting save dir: " + str(err))
            raise err

    def save_settings(self):
        self.logger.info("Saving settings")
        try:
            self.settings.set("data_saves", self.data_saves)
            self.settings.set("data_save", self.current_data_save)
        except Exception as err:
            self.logger.error("Error saving settings: " + str(err))
            raise err