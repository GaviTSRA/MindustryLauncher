from sys import platform
import imgui
import easygui
import os
import threading
import subprocess
import psutil
from components.util import LogLevel, Logger

from settings import Settings

class Launcher:
    logger = Logger("Launcher", LogLevel.DEBUG, "latest.log")

    logger.debug("Loading settings")
    settings = Settings("settings.properties")
    profile = settings.get("profile", 0)
    use_java = settings.get("use_java", False)
    close_on_launch = settings.get("close_on_launch", True)

    def __init__(self, parent) -> None:
        self.logger.info("Loading launcher")
        self.parent = parent
        self.load_profiles()
        self.logger.info("Loaded")

    def render(self):
        imgui.begin("Launcher", True)
        if len(self.profiles) > 0:
            _, self.profile = imgui.combo("Profile", self.profile, self.profiles)
            _, self.use_java = imgui.checkbox("Use java to launch", self.use_java)
            _, self.close_on_launch = imgui.checkbox("Close on launch", self.close_on_launch)
            if imgui.button("Launch game"):
                try:
                    self.logger.info(f"Loading game with profile {self.profiles[self.profile]}")
                    self.logger.debug(f"Close on launch: {self.close_on_launch}")
                    self.load_profile(self.profiles[self.profile])
                    if self.close_on_launch:
                        self.parent.close = True
                except Exception as err:
                    self.logger.error("Error during game launch: " + str(err))
                    raise err
            imgui.same_line()
            if imgui.button("Delete profile"):
                self.logger.info(f"Delete profile {self.profiles[self.profile]}?")
                if easygui.ynbox(f"Delete {self.profiles[self.profile]}?", "Confirm profile deletion"):
                    try:
                        self.logger.info("Deleting")
                        os.remove(self.parent.ROOT + "/profiles/" + self.profiles[self.profile])
                        self.load_profiles()
                        self.profile = 0
                        self.logger.info("Deleted")
                    except Exception as err:
                        self.logger.error("Error during profile deletion: " + str(err))
                        raise err
        else:
            imgui.text("No profiles installed")
        imgui.end()

    def load_profiles(self):
        self.logger.info("Loading profiles")
        try:
            self.profiles = []
            for _profile in os.listdir(self.parent.ROOT+"/profiles"):
                self.profiles.append(_profile)
        except Exception as err:
            self.logger.error("Error loading profiles: " + str(err))
            raise err

    def load_profile(self, name):
        self.logger.info(f"Loading profile {name}")
        try:
            with open(self.parent.ROOT+"/config.json", "w") as fi:
                fi.write('{"classPath": ["profiles/'+name+'"],"mainClass": "mindustry.desktop.DesktopLauncher"}')
            threading.Thread(target=self.run).start()
        except Exception as err:
            self.logger.error(f"Error loading profile {name}: {str(err)}")
            raise err

    def run(self):
        self.logger.info("Starting game")
        try: 
            self.is_open = False

            self.logger.debug("Loading env")
            env = os.environ.copy()
            if self.parent.data_manager.data_saves[self.parent.data_manager.current_data_save] != "Default":
                env["MINDUSTRY_DATA_DIR"] = self.parent.data_manager.get_save_dir()

            self.logger.debug("Checking for processes")
            if "Mindustry.exe" in (p.name() for p in psutil.process_iter()) or "Mindustry" in (p.name() for p in psutil.process_iter()) or "Mindustry.bin" in (p.name() for p in psutil.process_iter()):
                if not easygui.ynbox("Mindustry is already running.", "Game already running", ("Start anyway", "Cancel"), default_choice="Cancel", cancel_choice="Cancel"):
                    self.parent.is_open = True
                    return 

            if self.use_java:
                self.logger.debug("Launching with java")
                res = subprocess.call(["java", "-jar", f"{self.parent.ROOT}/profiles/{self.profiles[self.profile]}"], env=env)
            else:
                self.logger.debug("Launching")
                if platform == "linux" or platform == "linux2":
                    res = subprocess.call(self.parent.ROOT+"/Mindustry", env=env)
                elif platform == "win32":
                    res = subprocess.call(self.parent.ROOT+"/Mindustry.exe", env=env)
                else:
                    self.logger.error("Invalid os or could not get os info")
                    raise AssertionError("Invalid os")

            if res != 0:
                self.logger.info("Opening crash menu")
                res = easygui.buttonbox("Mindustry has crashed. If it didn't even open, try running it using Java.", "Ohno", ("Relaunch", "Relaunch (Java)", "Open launcher", "Close"))
                if res == None: self.parent.is_closed = True
                elif res.startswith("Relaunch"):
                    self.logger.debug("Relaunching")
                    if res.endswith("(Java)"):
                        self.logger.debug("(with java)")
                        self.use_java = True
                    self.run()
                elif res == "Open launcher":
                    self.logger.debug("Reopening launcher")
                    self.parent.is_open = True
                elif res == "Close":
                    self.logger.debug("Closing")
                    self.parent.save_settings()
                    self.parent.is_closed = True
            else:
                self.parent.save_settings()
                self.parent.is_closed = True
        except Exception as err:
            self.logger.error("Error running game: " + str(err))
            raise err

    def save_settings(self):
        self.logger.info("Saving settings")
        try:
            self.settings.set("profile", self.profile)
            self.settings.set("use_java", self.use_java)
            self.settings.set("close_on_launch", self.close_on_launch)
        except Exception as err:
            self.logger.error("Error saving settings: " + str(err))
            raise err