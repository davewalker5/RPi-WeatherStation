import json
from pathlib import Path

class AppSettings:
    def __init__(self, settings_file):
        # Load the device list and settings from the specified file
        with open(settings_file, "r") as json_f:
            self.application_settings = json.load(json_f)

    @property
    def settings(self):
        return { key: value for key, value in self.application_settings.items() if key != "devices" }

    @property
    def devices(self):
        return self.application_settings["devices"]

    @staticmethod
    def default_settings_file():
        project_folder = Path(__file__).resolve().parent.parent.parent
        settings_file_path = project_folder / "data" / "appsettings.json"
        return settings_file_path.absolute()
