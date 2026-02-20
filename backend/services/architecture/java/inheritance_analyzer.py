class InheritanceAnalyzer:

    def analyze(self, ast_index):

        tree = ast_index.class_parents
        base_test = None

        for child, parent in tree.items():
            if "Base" in parent:
                base_test = parent

        return {
            "tree": tree,
            "base_test": base_test
        }