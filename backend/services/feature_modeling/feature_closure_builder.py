from typing import Dict, Set


class FeatureClosureBuilder:

    def __init__(self, graph: Dict[str, Set[str]]):
        self.graph = graph

    def build_closure(self, test_file: str) -> Set[str]:
        visited = set()
        stack = [test_file]

        while stack:
            current = stack.pop()

            for dep in self.graph.get(current, []):
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)

        return visited
