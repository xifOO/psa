from pathlib import Path
from typing import Iterable, List, Tuple

from config.rules import Config
from reporters.base import BaseReporter
from pipeline import Pipeline


DiffResult = Tuple[str, object, dict]


class Runner:
    def __init__(
        self, config: Config, root: Path, reporters: List[BaseReporter]
    ) -> None:
        self.config = config
        self.reporters = reporters
        self.root = root
        self.pipeline = Pipeline(config, root)

    def iter_python_files(self) -> Iterable[Path]:
        for path in self.root.rglob("*.py"):
            yield path

    def run(self) -> None:
        results = []

        for file_path in self.iter_python_files():
            try:
                results = self.pipeline.process_file(file_path)
                results.extend(results)
            except Exception as e:
                results.append(
                    {
                        "file_path": str(file_path),
                        "error": str(e),
                    }
                )
