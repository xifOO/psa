import ast
from pathlib import Path
from typing import Optional, Tuple


class Extractor:
    def __init__(self, root_path: Optional[Path] = None) -> None:
        self.root_path = root_path

    def extract_file(self, path: Path) -> Tuple[ast.Module, str]:
        tree = ast.parse(path.read_text(), filename=str(path))
        module_name = path.stem
        return tree, module_name

    def extract_dir(self, path: Path):
        modules = []
        for py_file in path.rglob("*.py"):
            module = self.extract_file(py_file)
            modules.append(module)
        return modules
