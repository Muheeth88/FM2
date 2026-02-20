LIFECYCLE_MAP = {
    "@BeforeSuite": "global",
    "@BeforeClass": "class",
    "@BeforeMethod": "per_test",
    "@AfterMethod": "teardown",
    "@AfterSuite": "teardown"
}


class LifecycleAnalyzer:

    def analyze(self, ast_index):

        global_setup = None
        per_test = None
        teardown = None

        for class_name, methods in ast_index.methods.items():
            src = ast_index.classes[class_name]["src"]

            for method in methods:
                # check modifiers for annotations
                for child in method.children:
                    if child.type == "modifiers":
                        for mod in child.children:
                            if mod.type in ("marker_annotation", "annotation"):
                                annot = src[mod.start_byte:mod.end_byte]

                                if annot.startswith("@BeforeSuite"):
                                    global_setup = True
                                if annot.startswith("@BeforeMethod"):
                                    per_test = True
                                if annot.startswith("@After"):
                                    teardown = True

        # If we scanned everything and didn't find them, should we say False or None?
        # If we follow "never assume", and we didn't find them, we can't be 100% sure they aren't there 
        # (e.g. inheritance from external lib).
        # But if we strictly want "no defaults", we'll keep them as None if not found.

        return {
            "global": global_setup,
            "per_test": per_test,
            "teardown": teardown
        }