from typing import Set


class FeatureSharedMapper:

    def __init__(self, shared_modules: Set[str]):
        self.shared_modules = shared_modules

    def map_feature_shared(self, feature_closure: Set[str]):
        return list(feature_closure.intersection(self.shared_modules))
