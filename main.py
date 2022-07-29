import os
import glfw
import imgui
import OpenGL.GL as gl
import easygui
from imgui.integrations.glfw import GlfwRenderer
from components.util import LogLevel, Logger
from settings import Settings

from components.launcher import Launcher
from components.installer import Installer
from components.data_manager import DataManager
class GUI(object):
    logger = Logger("Main", LogLevel.DEBUG, "latest.log")
    logger.info("Initializing Phase 1")

    settings = Settings("settings.properties")
    with open("latest.log", "w") as fi:
        fi.write("")

    if not settings.has("root"):
        settings.set("root", easygui.diropenbox("Please select your mindustry save directory", "Select installation directory").replace("\\", "/"))
    ROOT = settings.get("root", "")

    if not os.path.exists(ROOT + "/profiles"):
        os.mkdir(ROOT + "/profiles")

    def __init__(self) -> None:
        self.logger.info("Initializing Phase 2")
        super().__init__()
        self.backgroundColor = (0, 0, 0, .5)

        self.is_open = True
        self.is_closed = False

        self.launcher = Launcher(self)
        self.installer = Installer(self)
        self.data_manager = DataManager(self)

        self.logger.info("Done, opening window")

        while not self.is_closed:
            if self.is_open:
                self.is_open = False

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
        self.close = False
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()

            self.launcher.render()

            self.installer.render()

            self.data_manager.render()

            imgui.render()
            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

            if self.close: break

        if glfw.window_should_close(self.window):
            self.save_settings()
            self.is_closed = True

        self.impl.shutdown()
        glfw.terminate()

    def save_settings(self):
        self.logger.info("Saving settings")
        self.launcher.save_settings()
        self.installer.save_settings()
        self.data_manager.save_settings()
        self.settings.set("root", self.ROOT)

if __name__ == "__main__":
    gui = GUI()


"""
✔ Launching the game
✔ Launching old versions using java
✔ Select from multiple installed versions
✔ Automatically setup all directories
✔ Installing new version from different sources
✔ Don't show installer if not connected to the internet
✔ Don't show launcher if no versions are available
✔ Save configuration to config file
✔ Relaunch window
✔ Delete profiles
✔ Multiple save directories
✔ Save directory (partial) backups
✔ Manually add new sources
[ ] Load backups
✔ Enter github access token
✔ Enter root directory
✔ Automatically refresh on source change
✔ Test on windows
[ ] Test on linux
✔ Start without console
✔ Close launcher on game launch setting
✔ Game running warning
[ ] Save settings.properties | latest.log | imgui.ini to appdata or linux eq.
✔ Access token per source?

Later
[ ] External mod manager
[ ] External mod installer
[ ] Reenter token in launcher
[ ] Token instructions

TODO Windows exe

TODO Linux exe
- Make executable
"""