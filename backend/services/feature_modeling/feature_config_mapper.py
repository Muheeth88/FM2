from typing import Set, List


class FeatureConfigMapper:

    def __init__(self, global_configs: List[str]):
        self.global_configs = set(global_configs)

    def map_feature_configs(self, feature_closure: Set[str]):
        return list(feature_closure.intersection(self.global_configs))
