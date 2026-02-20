class ScopeAnalyzer:

    def analyze(self, ast_index):

        for class_name, methods in ast_index.methods.items():
            src = ast_index.classes[class_name]["src"]

            for method in methods:
                body = method.child_by_field_name("body")
                if not body:
                    continue

                body_text = src[body.start_byte:body.end_byte]

                if "new ChromeDriver" in body_text:
                    # determine annotation
                    for child in method.children:
                        if child.type == "modifiers":
                            for mod in child.children:
                                annot = src[mod.start_byte:mod.end_byte]

                                if annot.startswith("@BeforeSuite"):
                                    return {"scope": "suite"}
                                if annot.startswith("@BeforeClass"):
                                    return {"scope": "class"}
                                if annot.startswith("@BeforeMethod"):
                                    return {"scope": "test"}

        return {"scope": "unknown"}