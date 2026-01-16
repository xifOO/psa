from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from psa.config.rules import Config
from psa.reporters.base import BaseReporter
from psa.pipeline import Pipeline


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

    def run(self) -> List[Dict[str, Any]]:
        results = []

        for file_path in self.iter_python_files():
            try:
                file_results = self.pipeline.process_file(file_path)
                results.extend(file_results)
            except Exception as e:
                results.append(
                    {
                        "file_path": str(file_path),
                        "error": str(e),
                    }
                )

        return results
