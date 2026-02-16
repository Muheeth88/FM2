from collections import defaultdict
from typing import Dict, Set


class DependencyGraphBuilder:

    def __init__(self, dependency_rows):
        """
        dependency_rows = [
            (from_file, to_file)
        ]
        """
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)

        for from_f, to_f in dependency_rows:
            self.graph[from_f].add(to_f)
            self.reverse_graph[to_f].add(from_f)

    def get_graph(self) -> Dict[str, Set[str]]:
        return self.graph

    def get_reverse_graph(self) -> Dict[str, Set[str]]:
        return self.reverse_graph
