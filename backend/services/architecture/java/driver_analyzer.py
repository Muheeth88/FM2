class DriverAnalyzer:

    def analyze(self, ast_index):
        driver_model = None
        driver_init_location = None
        driver_teardown_location = None
        driver_lifecycle_binding = None
        driver_scope = None

        # 1. Field-level detection
        for class_name, fields in ast_index.fields.items():
            for field in fields:
                text = ast_index.classes[class_name]["src"][field.start_byte:field.end_byte]
                if "ThreadLocal<WebDriver>" in text:
                    driver_model = "thread_local"
                elif "static WebDriver" in text:
                    driver_model = "singleton"
        
        # Heuristic: if WebDriver is used but no specific model found, stay None or use per_test?
        # User said: "Never use default values". So if not found, it's None.

        # 2. Method-level lifecycle detection
        for class_name, methods in ast_index.methods.items():
            src = ast_index.classes[class_name]["src"]
            for method in methods:
                m_name_node = method.child_by_field_name("name")
                if not m_name_node: continue
                m_name = src[m_name_node.start_byte:m_name_node.end_byte]
                
                body = method.child_by_field_name("body")
                if not body: continue
                body_text = src[body.start_byte:body.end_byte]

                # Detection: Initialization
                if "new ChromeDriver" in body_text or "WebDriverManager" in body_text or ".set(driver)" in body_text:
                    if driver_model is None: driver_model = "per_test" # If we see init but no field, assume per_test
                    
                    annotations = ast_index.annotations.get(f"{class_name}.{m_name}", [])
                    driver_init_location = {
                        "class": class_name,
                        "method": m_name,
                        "annotation": annotations[0] if annotations else None
                    }
                    # Heuristic for scope
                    driver_scope = self._resolve_scope(annotations, driver_scope)

                # Detection: Teardown
                if ".quit()" in body_text:
                    annotations = ast_index.annotations.get(f"{class_name}.{m_name}", [])
                    driver_teardown_location = {
                        "class": class_name,
                        "method": m_name,
                        "annotation": annotations[0] if annotations else None
                    }

        # 3. Lifecycle Binding Tracing (who calls the init method)
        if driver_init_location:
            init_method_name = driver_init_location["method"]
            for key, calls in ast_index.method_calls.items():
                if any(init_method_name in c for c in calls):
                    annotations = ast_index.annotations.get(key, [])
                    if annotations:
                        c_class, c_method = key.split(".")
                        b_scope = self._resolve_scope(annotations, None)
                        
                        driver_lifecycle_binding = {
                            "called_from_class": c_class,
                            "called_from_method": c_method,
                            "annotation": annotations[0],
                            "scope": b_scope
                        }
                        driver_scope = self._resolve_scope(annotations, driver_scope)
                        break

        # Refine scope for ThreadLocal
        if driver_model == "thread_local" and driver_scope is None:
            driver_scope = "thread"

        return {
            "model": driver_model,
            "scope": driver_scope,
            "init_location": driver_init_location,
            "teardown_location": driver_teardown_location,
            "lifecycle_binding": driver_lifecycle_binding
        }

    def _resolve_scope(self, annotations, current_scope):
        if "@BeforeMethod" in annotations or "@BeforeTest" in annotations:
            return "test"
        elif "@BeforeClass" in annotations:
            return "class"
        elif "@BeforeSuite" in annotations:
            return "suite"
        return current_scope
