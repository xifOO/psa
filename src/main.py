from pathlib import Path
from config.rules import Config
from runner import Runner


config = Config.from_yaml("settings.yaml")

runner = Runner(config, Path("./src"), [])
