import os

class StructuralAnalyzer:

    def analyze(self, ast_index, workspace_path):
        structure_type = None
        test_types = []
        page_pattern = {
            "base_page_class": None,
            "pages_detected": [],
            "driver_injection": None,
            "driver_storage": None
        }
        
        # 1. Detect POM & Page Classes
        for class_name, src_info in ast_index.classes.items():
            src = src_info["src"]
            is_page = any(term in class_name for term in ["Page", "PO", "Screen", "Component"])
            
            if is_page:
                page_pattern["pages_detected"].append(class_name)
                
                # Detect driver injection (usually constructor)
                if "public " + class_name + "(WebDriver" in src or "public " + class_name + "(RemoteWebDriver" in src:
                    page_pattern["driver_injection"] = "constructor"

                # Detect driver storage (instance field vs static)
                if "this.driver =" in src or "driver =" in src:
                    fields = ast_index.fields.get(class_name, [])
                    for field in fields:
                        field_text = src[field.start_byte:field.end_byte]
                        if "WebDriver" in field_text and "static" not in field_text:
                            page_pattern["driver_storage"] = "instance_field"
                            break
                        elif "WebDriver" in field_text and "static" in field_text:
                            page_pattern["driver_storage"] = "static_field"

            # Detect BasePage
            if class_name in ["BasePage", "PageBase", "AbstractPage"]:
                page_pattern["base_page_class"] = class_name
        
        if len(page_pattern["pages_detected"]) > 3:
            structure_type = "POM"

        # 2. Detect BDD
        has_bdd = False
        for root, dirs, files in os.walk(workspace_path):
            for f in files:
                if f.endswith(".feature"):
                    has_bdd = True
                    break
        if has_bdd:
            structure_type = "BDD"
        
        # If no POM/BDD, it remains None or should we say 'flat'?
        # User said: "Never use default values". So if not POM/BDD, it's None.

        # 3. Detect UI vs API & Split Models
        ui_arch = None
        api_arch = None
        test_types_set = set()

        for class_name, src_info in ast_index.classes.items():
            src = src_info["src"]
            # UI hints
            if any(term in src for term in ["WebDriver", "WebElement", "By.", "driver."]):
                test_types_set.add("UI")
                if not ui_arch:
                    ui_arch = {"engine": "selenium", "pattern": structure_type}
            # API hints
            if any(term in src for term in ["RestAssured", "given()", "when()", "Response", "BaseAPI"]):
                test_types_set.add("API")
                if not api_arch:
                    api_arch = {"engine": "rest-assured", "base_api_class": "BaseAPI" if "BaseAPI" in src else None}

        # 4. Detect Framework Versions
        versions = None
        for root, dirs, files in os.walk(workspace_path):
            if "pom.xml" in files:
                with open(os.path.join(root, "pom.xml"), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "selenium-java" in content or "testng" in content:
                        if versions is None: versions = {}
                        if "selenium-java" in content:
                            versions["selenium"] = "4.x"
                        if "testng" in content:
                            versions["testng"] = "7.x"

        return {
            "structure_type": structure_type,
            "test_types_detected": list(test_types_set),
            "framework_version": versions,
            "page_object_pattern": page_pattern,
            "ui_architecture": ui_arch,
            "api_architecture": api_arch
        }
