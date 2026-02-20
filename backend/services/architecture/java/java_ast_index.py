from tree_sitter import Parser
from tree_sitter_languages import get_language
import os


class JavaASTIndex:

    def __init__(self):
        self.parser = Parser()
        self.parser.set_language(get_language("java"))

        self.classes = {}              # class_name -> {node, file}
        self.class_parents = {}        # child -> parent
        self.fields = {}               # class_name -> list of fields
        self.methods = {}              # class_name -> list of methods
        self.annotations = {}          # class_name.method_name -> list of annotations
        self.method_calls = {}         # class_name.method_name -> list of called method names

    def build(self, java_files):
        for path in java_files:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()

            tree = self.parser.parse(bytes(src, "utf-8"))
            root = tree.root_node

            self._index_file(path, src, root)

    def _index_file(self, path, src, root):
        for node in root.children:
            if node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if not name_node:
                    continue

                class_name = src[name_node.start_byte:name_node.end_byte]

                self.classes[class_name] = {
                    "node": node,
                    "file": path,
                    "src": src
                }

                # inheritance
                superclass = node.child_by_field_name("superclass")
                if superclass:
                    parent = src[superclass.start_byte:superclass.end_byte]
                    parent = parent.replace("extends", "").strip()
                    self.class_parents[class_name] = parent

                self.fields[class_name] = []
                self.methods[class_name] = []

                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "field_declaration":
                            self.fields[class_name].append(child)
                        if child.type == "method_declaration":
                            self.methods[class_name].append(child)
                            
                            # Index annotations and calls for methods
                            m_name_node = child.child_by_field_name("name")
                            if m_name_node:
                                m_name = src[m_name_node.start_byte:m_name_node.end_byte]
                                key = f"{class_name}.{m_name}"
                                self.annotations[key] = self._get_annotations(child, src)
                                self.method_calls[key] = self._get_method_calls(child, src)

    def _get_method_calls(self, node, src):
        calls = []
        
        def walk(n):
            if n.type == "method_invocation":
                name_node = n.child_by_field_name("name")
                if name_node:
                    calls.append(src[name_node.start_byte:name_node.end_byte])
            for child in n.children:
                walk(child)
        
        walk(node)
        return calls

    def _get_annotations(self, node, src):
        annotations = []
        # tree-sitter method_declaration usually has modifiers child which contains annotations
        modifiers = node.child_by_field_name("modifiers")
        if modifiers:
            for mod in modifiers.children:
                if mod.type == "marker_annotation":
                    # e.g. @Test, @BeforeMethod
                    ann_name_node = mod.child_by_field_name("name")
                    if ann_name_node:
                        ann_name = src[ann_name_node.start_byte:ann_name_node.end_byte]
                        annotations.append(ann_name)
                elif mod.type == "annotation":
                    # e.g. @Test(groups = "...")
                    ann_name_node = mod.child_by_field_name("name")
                    if ann_name_node:
                        ann_name = src[ann_name_node.start_byte:ann_name_node.end_byte]
                        annotations.append(ann_name)
        return annotations