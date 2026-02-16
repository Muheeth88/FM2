class DependencyResolver:

    def __init__(self, graph):
        self.graph = graph

    def resolve_closure(self, start_file: str):
        visited = set()
        stack = [start_file]

        while stack:
            current = stack.pop()

            for dep in self.graph.get(current, []):
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)

        return visited
