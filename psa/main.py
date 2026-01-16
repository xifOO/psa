from pathlib import Path
from psa.config.rules import Config
from psa.runner import Runner


config = Config.from_yaml("settings.yaml")

runner = Runner(config, Path("./psa/config"), [])

a = runner.run()