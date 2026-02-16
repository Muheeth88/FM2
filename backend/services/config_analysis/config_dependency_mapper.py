class ConfigDependencyMapper:

    def __init__(self, graph, config_files):
        self.graph = graph
        self.config_files = config_files

    def map_config_to_features(self, feature_files):
        mapping = {}

        for feature, files in feature_files.items():
            related = set()

            for f in files:
                for config in self.config_files:
                    if config in self.graph.get(f, []):
                        related.add(config)

            mapping[feature] = list(related)

        return mapping
