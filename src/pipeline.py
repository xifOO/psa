from pathlib import Path
from typing import Any, Dict, List
from config.rules import Config
from index.extractor import Extractor
from index.maps import Index
from entity import CodeEntity
from index.collector import EntityCollector
from metrics.base import Analyzer
from node import ASTVisitor, CallVisitor


class Pipeline:
    def __init__(self, config: Config, root_path: Path) -> None:
        self.config = config

        self._extractor = Extractor(root_path)

    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        tree, module_name = self._extractor.extract_file(file_path)
        index = self._build_index(tree, module_name)

        entities = self._build_entities(index)
        results = self._run_analyzers(index, entities)
        for result in results:
            result["file_path"] = str(file_path)
            result["module"] = module_name

        return results

    def _build_index(self, tree, module_name: str) -> Index:
        index = Index()

        ast_builder = ASTVisitor(index)
        module_scope = ast_builder.build_module(tree, module_name)

        call_builder = CallVisitor(index, module_scope)
        call_builder.visit(tree)

        return index

    def _build_entities(self, index: Index) -> List[CodeEntity]:
        collector = EntityCollector(index)
        return collector.collect()

    def _run_analyzers(
        self, index: Index, entities: List[CodeEntity]
    ) -> List[Dict[str, Any]]:
        results = []
        for entity in entities:
            for analyzer in Analyzer.for_entity(entity):
                value, context = analyzer.analyze(index, entity)

                results.append(
                    {
                        "analyzer": analyzer.__class__.__name__,
                        "entity": entity.name,
                        "entity_type": entity.__class__.__name__,
                        "node_id": entity.node_id,
                        "value": value,
                        "context": context,
                    }
                )

        return results
