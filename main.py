from datetime import date
import shutil
import threading
import os
import subprocess
import time
import glfw
import imgui
import ctypes
import OpenGL.GL as gl
import easygui
from imgui.integrations.glfw import GlfwRenderer
from installer import getVersions, save_file
import http.client as httplib
from settings import Settings
import psutil
import zipfile

def internet_available():
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()

class GUI(object):
    settings = Settings("settings.properties")

    profile = settings.get("profile", 0)
    if not settings.has("root"):
        settings.set("root", easygui.diropenbox("Please select your mindustry save directory", "Select installation directory").replace("\\", "/"))
    ROOT = settings.get("root", "")
    install_version = settings.get("install_version", 0)
    install_source = settings.get("install_source", 0)
    use_java = settings.get("use_java", False)
    token = settings.get("token", "")
    close_on_launch = settings.get("close_on_launch", True)
    data_saves = settings.get("data_saves", ["Default"])
    current_data_save = settings.get("data_save", 0)
    sources = settings.get("sources", ["Anuken/Mindustry", "Anuken/MindustryBuilds", "GaviTSRA/TSR-Foo-Client"])

    new_save_name = ""
    download_progress = 0
    internet = internet_available()
    backup_folders = {"files": False}
    new_source = ""
    chosen_backup = 0

    if not os.path.exists(ROOT + "/profiles"):
        os.mkdir(ROOT + "/profiles")

    def __init__(self) -> None:
        super().__init__()
        self.backgroundColor = (0, 0, 0, .5)

    def open(self):
        self.load_profiles()
        if self.internet and self.token != "":
            self.load_installer()
        self.window = self.impl_glfw_init()
        gl.glClearColor(*self.backgroundColor)
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)
        self.loop()

    def impl_glfw_init(self, window_name="Mindustry Launcher", width=1000, height=600):
        if not glfw.init():
            print("Error init lol")
            exit(1)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_ANY_PROFILE)

        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

        window = glfw.create_window(int(width), int(height), window_name, None, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            print("Yay error window")
            exit(1)

        return window

    def loop(self):
        global is_closed

        close = False
        while not glfw.window_should_close(self.window):

            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()

            imgui.begin("Launcher", True)
            if len(self.profiles) > 0:
                _, self.profile = imgui.combo("Profile", self.profile, self.profiles)
                _, self.use_java = imgui.checkbox("Use java to launch", self.use_java)
                _, self.close_on_launch = imgui.checkbox("Close on launch", self.close_on_launch)
                if imgui.button("Launch game"):
                    self.load_profile(self.profiles[self.profile])
                    if self.close_on_launch:
                        close = True
                imgui.same_line()
                if imgui.button("Delete profile"):
                    if ctypes.windll.user32.MessageBoxW(0, f"Delete {self.profiles[self.profile]}", "Confirm profile deletion", 4) == 6:
                        os.remove(self.ROOT + "/profiles/" + self.profiles[self.profile])
                        self.load_profiles()
            else:
                imgui.text("No profiles installed")
            imgui.end()

            imgui.begin("Installer", True)
            if self.internet and self.token != "":
                imgui.text("New source")
                _, self.new_source = imgui.input_text("New source", self.new_source, 255)
                if imgui.button("Add source"):
                    self.sources.append(self.new_source)
                    self.install_source = len(self.sources) - 1
                    try:
                        self.load_installer()
                    except:
                        easygui.msgbox("The entered source is invalid and has been removed", "Invalid source")
                        self.sources.remove(self.sources[self.install_source])
                        self.install_source = 0
                        self.load_installer()
                imgui.same_line()
                if imgui.button("Delete current source"):
                    if ctypes.windll.user32.MessageBoxW(0, f"Delete {self.sources[self.install_source]}", "Confirm source deletion", 4) == 6:
                        self.sources.remove(self.sources[self.install_source])
                        self.install_source = 0
                        self.load_installer()
                imgui.text("Install version")
                update, self.install_source = imgui.combo("Source", self.install_source, self.sources)
                if update: self.load_installer()
                _, self.install_version = imgui.combo("Version", self.install_version, self.tags)
                imgui.progress_bar(self.download_progress, (200, 15), f"{int(self.download_progress*100)}%")
                if imgui.button("Install version"):
                    download_url, file_size = self.builds[self.tags[self.install_version]]
                    threading.Thread(target=lambda:self.install(self.tags[self.install_version], download_url, file_size)).start()
                imgui.same_line()
            elif self.token != "":
                imgui.text("You are offline")
                if imgui.button("Retry"):
                    self.internet = internet_available()
                    if self.internet:
                        self.load_installer()
            else:
                imgui.text(f"Enter github access token.\nThis will grant you access to private installation sources.\nIf you don't need this, enter something random.\nThe token can be changed while the launcher is closed\nin {self.ROOT}/settings.properties")
                changed, t = imgui.input_text("Token", self.token, 255)
                self.token = t
                if changed: 
                    self.load_installer()
            imgui.end()

            imgui.begin("Data manager")
            imgui.text("Data folders")
            if imgui.button("Create data folder"):
                self.data_saves.append(easygui.diropenbox("Select new save folder"))
            if self.data_saves[self.current_data_save] != "Default":
                imgui.same_line()
                if imgui.button("Delete data folder"):
                    res = easygui.buttonbox(f"Are you sure you want to delete this save data directory ({self.data_saves[self.current_data_save]})? You can also just remove it from the list, and re-add it later using the 'Create' button.", "Delete save data directory", ("Delete", "Remove", "Cancel"))
                    if res != "Cancel":
                        if res == "Delete":
                            shutil.rmtree(self.data_saves[self.current_data_save])
                        self.data_saves.remove(self.data_saves[self.current_data_save])
                        self.current_data_save = 0
            _, self.current_data_save = imgui.combo("Current data folder", self.current_data_save, self.data_saves)
            imgui.text("Data backups")
            show, _ = imgui.collapsing_header("Create a backup")
            if show:
                dir = self.get_save_dir()
                for folder in os.listdir(dir):
                    if os.path.isdir(f"{dir}\\{folder}"):
                        if not folder in self.backup_folders.keys():
                            self.backup_folders[folder] = False
                        _, self.backup_folders[folder] = imgui.checkbox(folder, self.backup_folders[folder])
                _, self.backup_folders["files"] = imgui.checkbox("Files", self.backup_folders["files"])
                if imgui.button("Create backup"):
                    t = time.asctime().replace(":", ".")
                    if not os.path.exists(f"backups"):
                        os.makedirs("backups")
                    with zipfile.ZipFile(f"backups/{t}.zip", mode='w') as zip_file:
                        save_dir = self.get_save_dir()
                        len_dir_path = len(save_dir)
                        for file in os.listdir(save_dir):
                            if os.path.isdir(f"{save_dir}/{file}") and self.backup_folders[file]:
                                self.zip_dir(f"{save_dir}/{file}", zip_file, len_dir_path)
                            if self.backup_folders["files"] and not os.path.isdir(f"{save_dir}/{file}"):
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
                    if ctypes.windll.user32.MessageBoxW(0, f"Delete {backups[self.chosen_backup]}", "Confirm backup deletion", 4) == 6:
                        os.remove(f"backups/{backups[self.chosen_backup]}")
                        self.chosen_backup = 0
            imgui.end()

            imgui.render()
            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

            if close: break

        if glfw.window_should_close(self.window):
            self.save_settings()
            is_closed = True

        self.impl.shutdown()
        glfw.terminate()

    def load_profiles(self):
        self.profiles = []
        for _profile in os.listdir(self.ROOT+"/profiles"):
            self.profiles.append(_profile)

    def install(self, tag, download_url, file_size):
        print(download_url)
        for update in save_file(download_url, f"{self.ROOT}/profiles/{tag}.jar", file_size, self.token):
           self.download_progress = update
        self.load_profiles()

    def load_profile(self, name):
        with open(self.ROOT+"/config.json", "w") as fi:
            fi.write('{"classPath": ["profiles/'+name+'"],"mainClass": "mindustry.desktop.DesktopLauncher"}')
        threading.Thread(target=self.run).start()

    def run(self):
        global is_open
        global is_closed
        is_open = False

        env = os.environ.copy()
        if self.data_saves[self.current_data_save] != "Default":
            env["MINDUSTRY_DATA_DIR"] = self.get_save_dir()

        if "Mindustry.exe" in (p.name() for p in psutil.process_iter()):
            if not easygui.ynbox("Mindustry is already running.", "Game already running", ("Start anyway", "Cancel"), default_choice="Cancel", cancel_choice="Cancel"):
                is_open = True
                return 

        if self.use_java:
            res = subprocess.call(["java", "-jar", f"{self.ROOT}/profiles/{self.profiles[self.profile]}"], env=env)
        else:
            res = subprocess.call(self.ROOT+"/Mindustry.exe", env=env)
        if res != 0:
            res = easygui.buttonbox("Mindustry has crashed. If it didn't even open, try running it using Java.", "Ohno", ("Relaunch", "Relaunch (Java)", "Open launcher", "Close"))
            if res == None: is_closed = True
            elif res.startswith("Relaunch"):
                if res.endswith("(Java)"):
                    self.use_java = True
                self.run()
            elif res == "Open launcher":
                is_open = True
            elif res == "Close":
                self.save_settings()
                is_closed = True
        else:
            self.save_settings()
            is_closed = True

    def load_installer(self):
        self.builds = getVersions(self.sources[self.install_source], 200, self.token)
        self.tags = []
        for build in self.builds:
            self.tags.append(build)

    def save_settings(self):
        self.settings.set("profile", self.profile)
        self.settings.set("root", self.ROOT)
        self.settings.set("install_version", self.install_version)
        self.settings.set("install_source", self.install_source)
        self.settings.set("use_java", self.use_java)
        self.settings.set("token", self.token)
        self.settings.set("close_on_launch", self.close_on_launch)
        self.settings.set("data_saves", self.data_saves)
        self.settings.set("data_save", self.current_data_save)
        self.settings.set("sources", self.sources)

    def get_save_dir(self):
        dir = self.data_saves[self.current_data_save]
        if dir == "Default":
            dir = "C:\\Users\\gavin\\AppData\\Roaming\\Mindustry" #TODO Manage default
        return dir

    def zip_dir(self, path, zip_file, len_dir_path):
        for file in os.listdir(path):
            zip_file.write(path+"/"+file, path[len_dir_path:]+"/"+file)

is_open = True
is_closed = False

if __name__ == "__main__":
    gui = GUI()
    gui.open()
    while not is_closed:
        if is_open:
           gui.open()
           is_open = False


"""
TODO
[x] Launching the game
[x] Launching old versions using java
[x] Select from multiple installed versions
[x] Automatically setup all directories
[x] Installing new version from different sources
[x] Don't show installer if not connected to the internet
[x] Don't show launcher if no versions are available
[x] Save configuration to config file
[x] Relaunch window
[x] Delete profiles
[x] Multiple save directories
[x] Save directory (partial) backups
[x] Manually add new sources
[ ] Load backups
[x] Enter github access token
[x] Enter root directory
[x] Automatically refresh on source change
[ ] Test on windows
[ ] Test on linux
[ ] Start without console
[x] Close launcher on game launch setting
[x] Game running warning

Later
[ ] External mod manager
[ ] External mod installer
[ ] Access token per source?
[ ] Reenter token in launcher
[ ] Token instructions
"""