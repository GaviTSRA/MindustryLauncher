import imgui
import easygui
import threading
import requests

from settings import Settings

from .util import LogLevel, Logger, internet_available

class Installer:
    logger = Logger("Installer", LogLevel.DEBUG, "latest.log")

    logger.debug("Loading settings")
    settings = Settings("settings.properties")
    sources = settings.get("sources", ["Anuken/Mindustry", "Anuken/MindustryBuilds", "GaviTSRA/TSR-Foo-Client"])
    token = settings.get("token", "")
    install_version = settings.get("install_version", 0)
    install_source = settings.get("install_source", 0)

    new_source = ""
    internet = internet_available()
    download_progress = 0

    def __init__(self, parent) -> None:
        self.logger.info("Loading installer")
        self.parent = parent
        if self.internet and self.token != "":
            self.load_installer()
        self.logger.info("Loaded")
        self.logger.debug(f"Internet: {self.internet}")

    def render(self):
        imgui.begin("Installer", True)
        if self.internet and self.token != "":
            imgui.text("New source")
            _, self.new_source = imgui.input_text("New source", self.new_source, 255)
            if imgui.button("Add source"):
                self.logger.info("Adding source " + self.new_source)
                self.sources.append(self.new_source)
                self.install_source = len(self.sources) - 1
                try:
                    self.load_installer()
                except:
                    self.logger.warn("Invalid source detected (see previous error). Removing")
                    easygui.msgbox("The entered source is invalid and has been removed", "Invalid source")
                    self.sources.remove(self.sources[self.install_source])
                    self.install_source = 0
                    self.load_installer()
            imgui.same_line()
            if imgui.button("Delete current source"):
                self.logger.info("Delete current source?")
                if easygui.ynbox(f"Do you want to delete {self.sources[self.install_source]}?", "Delete source", default_choice="[<F2>]No"):
                    self.logger.info("Deleting")
                    self.sources.remove(self.sources[self.install_source])
                    self.install_source = 0
                    self.load_installer()
                    self.logger.info("Done")
            imgui.text("Install version")
            update, self.install_source = imgui.combo("Source", self.install_source, self.sources)
            if update: self.load_installer()
            _, self.install_version = imgui.combo("Version", self.install_version, self.tags)
            imgui.progress_bar(self.download_progress, (200, 15), f"{int(self.download_progress*100)}%")
            if imgui.button("Install version"):
                self.logger.info("Starting installer thread")
                download_url, file_size = self.builds[self.tags[self.install_version]]
                threading.Thread(target=lambda:self.install(self.tags[self.install_version], download_url, file_size)).start()
            imgui.same_line()
        elif self.token != "":
            imgui.text("You are offline")
            if imgui.button("Retry"):
                self.logger.info("Rechecking for internet")
                self.internet = internet_available()
                if self.internet:
                    self.load_installer()
                self.logger.debug("Internet: " + self.internet)
        else:
            imgui.text(f"Enter github access token.\nThis will grant you access to private installation sources.\nIf you don't need this, enter something random.\nThe token can be changed while the launcher is closed\nin {self.parent.ROOT}/settings.properties") # TODO path is wrong
            changed, self.token = imgui.input_text("Token", self.token, 255)
            if changed: 
                self.load_installer()
        imgui.end()

    def install(self, tag, download_url, file_size):
        self.logger.info(f"Installing tag {tag} from url {download_url} with a filesize of {file_size}")
        try:
            for update in self.save_file(download_url, f"{self.parent.ROOT}/profiles/{tag}.jar", file_size, self.token):
                self.download_progress = update
            self.parent.launcher.load_profiles()
        except Exception as err:
            self.logger.error("Error installing: " + str(err))
            raise err

    def getVersions(self, repo, amount, token):
        self.logger.info(f"Getting {amount} versions from {repo}")
        try:
            self.logger.debug(f"Full url: https://api.github.com/repos/{repo}/releases?per_page={amount}")
            res = requests.get(f"https://api.github.com/repos/{repo}/releases?per_page={amount}", headers={"Authorization": "token " + token}).json()
            builds = {}

            self.logger.debug("Result: ")
            self.logger.debug(res)

            for build in res:
                download_url = ""
                tag = build["tag_name"]

                for file in build["assets"]:
                    if not "server" in file["name"].lower() and not "android" in file["name"].lower():
                        file_size = file["size"]
                        asset_id = file["id"]
                        name = file["name"]
                        self.logger.debug(f"Found version {name} for tag {tag}")
                download_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
                builds[tag] = (download_url, file_size)
            return builds

        except Exception as err:
            self.logger.error("Error getting versions: " + str(err))
            raise err

    def save_file(self, url, path, file_size, token):
        self.logger.info(f"Saving {url} to {path}")
        try:
            downloaded = 0
            data = requests.get(url, headers={"Authorization": "token " + token, "Accept": "application/octet-stream"}, stream=True)
            with open(path, "wb") as fi:
                for chunk in data.iter_content(chunk_size=1024): 
                    if chunk: # filter out keep-alive new chunks
                        downloaded += len(chunk)
                        fi.write(chunk)                
                        yield downloaded / file_size
        except Exception as err:
            self.logger.error("Error downloading file: " + str(err))
            raise err

    def load_installer(self):
        self.logger.info("Loading installer")
        try:
            self.builds = self.getVersions(self.sources[self.install_source], 200, self.token)
            self.tags = []
            for build in self.builds:
                self.tags.append(build)
        except Exception as err:
            self.logger.error("Error loading installer: " + str(err))
            raise err

    def save_settings(self):
        self.logger.info("Saving settings")
        try:
            self.settings.set("install_version", self.install_version)
            self.settings.set("install_source", self.install_source)
            self.settings.set("token", self.token)
            self.settings.set("sources", self.sources)
        except Exception as err:
            self.logger.error("Error saving settings: " + str(err))
            raise err