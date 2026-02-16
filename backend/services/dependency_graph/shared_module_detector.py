class SharedModuleDetector:

    def __init__(self, reverse_graph):
        self.reverse_graph = reverse_graph

    def detect_shared_modules(self):
        shared = []

        for file, parents in self.reverse_graph.items():
            if len(parents) > 1:
                shared.append(file)

        return shared
