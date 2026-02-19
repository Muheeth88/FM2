import os
import ast
import json
import glob
import hashlib
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from openai import OpenAI

from database.db import Database
from services.llm_enrichment_service import LLMEnrichmentService


# ===============================
# CONFIG
# ===============================

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY = ""
MODEL = "gpt-4o-mini"  # Small deterministic model
USE_LLM = True         # LLM enrichment enabled

VOLATILE_FIELDS = {
    "extraction_version",
    "generated_at",
    "debug_info",
    "llm_metadata"
}


# ===============================
# INTENT HASHING
# ===============================

def remove_volatile_fields(obj):
    """Recursively strip volatile/non-deterministic fields before hashing."""
    if isinstance(obj, dict):
        return {
            k: remove_volatile_fields(v)
            for k, v in sorted(obj.items())
            if k not in VOLATILE_FIELDS
        }
    elif isinstance(obj, list):
        return [remove_volatile_fields(item) for item in obj]
    else:
        return obj


def generate_intent_hash(normalized_model: Dict[str, Any]) -> str:
    """Produce a stable SHA-256 hash of the canonical intent model."""
    cleaned = remove_volatile_fields(normalized_model)

    canonical_json = json.dumps(
        cleaned,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


from tree_sitter import Parser
from tree_sitter_languages import get_language

import logging
logger = logging.getLogger(__name__)

# ===============================
# SELENIUM API PATTERNS
# ===============================

# Methods on WebDriver / WebElement that represent real browser actions
SELENIUM_ACTION_METHODS = {
    'click': 'click',
    'sendKeys': 'type',
    'send_keys': 'type',
    'clear': 'clear',
    'submit': 'submit',
    'getText': 'get_text',
    'getAttribute': 'get_attribute',
    'isDisplayed': 'is_displayed',
    'isEnabled': 'is_enabled',
    'isSelected': 'is_selected',
}

# Methods that are navigation
SELENIUM_NAVIGATE_METHODS = {
    'get': 'navigate',
    'navigate().to': 'navigate',
    'navigate().back': 'navigate_back',
    'navigate().forward': 'navigate_forward',
    'navigate().refresh': 'refresh',
}

# Wrapper methods that map to real Selenium actions (from BasePage/WebUtil patterns)
WRAPPER_ACTION_METHODS = {
    'clickElement': 'click',
    'clickAndWaitElement': 'click',
    'waitTillClickableAndClick': 'click',
    'inputText': 'type',
    'enterText': 'type',
    'setText': 'type',
    'getText': 'get_text',
    'waitUntilElementIsVisible': 'wait',
    'waitUntilElementIsClickable': 'wait',
    'isElementVisible': 'wait',
    'waitForFrameAndSwitch': 'switch_frame',
    'refresh': 'refresh',
    'click': 'click',
    'type': 'type',
    'wait': 'wait',
    'clear': 'clear',
}

# By strategy methods
BY_STRATEGIES = {
    'xpath': 'xpath',
    'id': 'id',
    'cssSelector': 'css',
    'css': 'css',
    'className': 'class_name',
    'name': 'name',
    'tagName': 'tag_name',
    'linkText': 'link_text',
    'partialLinkText': 'partial_link_text',
}

# Assertion methods
ASSERTION_METHODS = {
    'assertEquals': 'equals',
    'assertNotEquals': 'not_equals',
    'assertTrue': 'true',
    'assertFalse': 'false',
    'assertNull': 'null',
    'assertNotNull': 'not_null',
    'fail': 'fail',
    'assertThat': 'that',
    'expect': 'that',
    'verify': 'that',
    'verifyTrue': 'true',
    'verifyFalse': 'false',
    'verifyEquals': 'equals',
    'verifyNotEquals': 'not_equals',
    'verifyElementPresent': 'present',
    'verifyElementNotPresent': 'not_present',
}

# API / RestAssured patterns
REST_ASSURED_METHODS = {
    'get': 'GET',
    'post': 'POST',
    'put': 'PUT',
    'delete': 'DELETE',
    'patch': 'PATCH',
    'head': 'HEAD',
    'options': 'OPTIONS',
}

# API Utility wrapper methods (common in this codebase)
API_UTIL_METHODS = {
    'sendGet': 'GET',
    'sendPost': 'POST',
    'sendPut': 'PUT',
    'sendDELETE': 'DELETE',
    'sendDelete': 'DELETE',
    'sendPATCH': 'PATCH',
    'getRequest': 'GET',
    'postRequest': 'POST',
    'putRequest': 'PUT',
    'deleteRequest': 'DELETE',
}

# TestNG/JUnit lifecycle annotations
LIFECYCLE_ANNOTATIONS = {
    '@BeforeSuite': 'beforeAll',
    '@AfterSuite': 'afterAll',
    '@BeforeClass': 'beforeClass',
    '@AfterClass': 'afterClass',
    '@BeforeMethod': 'beforeEach',
    '@AfterMethod': 'afterEach',
    '@BeforeTest': 'beforeTest',
    '@AfterTest': 'afterTest',
    '@Before': 'beforeEach',
    '@After': 'afterEach',
    '@BeforeAll': 'beforeAll',
    '@AfterAll': 'afterAll',
    '@BeforeEach': 'beforeEach',
    '@AfterEach': 'afterEach',
}

# Lifecycle action mapping (Phase 3 improvements)
LIFECYCLE_ORDER = ['beforeAll', 'beforeClass', 'beforeEach', 'test', 'afterEach', 'afterClass', 'afterAll']



# ===============================
# LAYER 1 — AST EXTRACTION
# ===============================

class WorkspaceIndex:
    """Index of all classes, fields, and methods in the workspace for cross-file resolution."""

    def __init__(self):
        # class_name -> file_path
        self.class_to_file: Dict[str, str] = {}
        # class_name -> {field_name -> {strategy, value}}
        self.class_locators: Dict[str, Dict[str, Dict[str, str]]] = {}
        # class_name -> {method_name -> tree-sitter node}
        self.class_methods: Dict[str, Dict[str, Any]] = {}
        # class_name -> source code bytes
        self.class_sources: Dict[str, bytes] = {}
        # class_name -> parent_class_name
        self.class_parents: Dict[str, str] = {}


class ASTExtractor:
    """Deterministic AST extraction for Python and Java with deep Selenium analysis."""

    def __init__(self):
        self._java_parser = None
        self._java_lang = None
        self._workspace_index: Optional[WorkspaceIndex] = None

    def _init_java_parser(self):
        if not self._java_parser:
            try:
                self._java_lang = get_language("java")
                self._java_parser = Parser()
                self._java_parser.set_language(self._java_lang)
            except Exception as e:
                logger.error(f"Failed to initialize Java parser: {e}")

    # ----------------------------------------------------------
    # Workspace Index — cross-file resolution
    # ----------------------------------------------------------

    def build_workspace_index(self, workspace_files: List[str]):
        """Build an index of all classes, locator fields, and methods in the workspace."""
        self._init_java_parser()
        if not self._java_parser:
            return

        self._workspace_index = WorkspaceIndex()

        for file_path in workspace_files:
            if not file_path.endswith('.java'):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    src = f.read()
            except Exception:
                continue

            src_bytes = src.encode('utf-8')
            tree = self._java_parser.parse(src_bytes)
            root = tree.root_node

            self._index_java_file(file_path, src, src_bytes, root)

    def _index_java_file(self, file_path: str, src: str, src_bytes: bytes, root):
        """Index a single Java file for classes, locator fields, and methods."""
        for node in self._walk_nodes(root):
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if not name_node:
                    continue
                class_name = src[name_node.start_byte:name_node.end_byte]

                self._workspace_index.class_to_file[class_name] = file_path
                self._workspace_index.class_sources[class_name] = src_bytes
                self._workspace_index.class_locators.setdefault(class_name, {})
                self._workspace_index.class_methods.setdefault(class_name, {})

                # Check for superclass
                superclass_node = node.child_by_field_name('superclass')
                if superclass_node:
                    # superclass is a "type_identifier" or "superclass" node
                    super_text = src[superclass_node.start_byte:superclass_node.end_byte]
                    # Remove "extends " prefix if present
                    if super_text.startswith('extends '):
                        super_text = super_text[8:].strip()
                    # Handle generic types like "extends BasePage"
                    if '<' in super_text:
                        super_text = super_text[:super_text.index('<')]
                    self._workspace_index.class_parents[class_name] = super_text.strip()

                # Index fields and methods within the class body
                body_node = node.child_by_field_name('body')
                if body_node:
                    self._index_class_body(class_name, src, src_bytes, body_node)

    def _index_class_body(self, class_name: str, src: str, src_bytes: bytes, body_node):
        """Index fields and methods within a class body."""
        for child in body_node.children:
            # Index field declarations with By.xxx(...) locators
            if child.type == 'field_declaration':
                self._index_locator_field(class_name, src, child)

            # Index method declarations
            if child.type == 'method_declaration':
                name_node = child.child_by_field_name('name')
                if name_node:
                    method_name = src[name_node.start_byte:name_node.end_byte]
                    self._workspace_index.class_methods[class_name][method_name] = {
                        'node': child,
                        'src': src,
                        'src_bytes': src_bytes,
                    }

    def _index_locator_field(self, class_name: str, src: str, field_node):
        """Extract By.xpath/id/css locator from a field declaration."""
        # Look for pattern: By.xpath("...") or By.id("..."), etc.
        declarators = [c for c in field_node.children if c.type == 'variable_declarator']
        for decl in declarators:
            name_node = decl.child_by_field_name('name')
            value_node = decl.child_by_field_name('value')
            if not name_node or not value_node:
                continue

            field_name = src[name_node.start_byte:name_node.end_byte]
            locator = self._extract_by_locator(src, value_node)
            if locator:
                self._workspace_index.class_locators[class_name][field_name] = locator

    def _extract_by_locator(self, src: str, node) -> Optional[Dict[str, str]]:
        """Extract a By.xxx("value") locator from an expression node."""
        # Look for method_invocation like By.xpath("...")
        if node.type == 'method_invocation':
            obj_node = node.child_by_field_name('object')
            name_node = node.child_by_field_name('name')
            args_node = node.child_by_field_name('arguments')

            if obj_node and name_node:
                obj_text = src[obj_node.start_byte:obj_node.end_byte]
                method_text = src[name_node.start_byte:name_node.end_byte]

                if obj_text == 'By' and method_text in BY_STRATEGIES:
                    strategy = BY_STRATEGIES[method_text]
                    value = self._extract_first_string_arg(src, args_node)
                    if value is not None:
                        return {'strategy': strategy, 'value': value}

        # Recurse into children
        for child in node.children:
            result = self._extract_by_locator(src, child)
            if result:
                return result

        return None

    def _extract_first_string_arg(self, src: str, args_node) -> Optional[str]:
        """Extract the first string literal argument from an argument list."""
        if not args_node:
            return None
        for child in args_node.children:
            if child.type == 'string_literal':
                raw = src[child.start_byte:child.end_byte]
                return raw.strip('"').strip("'")
            # Handle String.format(...) — extract the template
            if child.type == 'method_invocation':
                obj = child.child_by_field_name('object')
                name = child.child_by_field_name('name')
                if obj and name:
                    o = src[obj.start_byte:obj.end_byte]
                    n = src[name.start_byte:name.end_byte]
                    if o == 'String' and n == 'format':
                        inner_args = child.child_by_field_name('arguments')
                        return self._extract_first_string_arg(src, inner_args)
        return None

    def _walk_nodes(self, node):
        """Generator to walk all nodes in a tree-sitter tree."""
        yield node
        for child in node.children:
            yield from self._walk_nodes(child)

    # ----------------------------------------------------------
    # Main entry point
    # ----------------------------------------------------------

    def parse_files(self, file_paths):
        raw_model = {
            'raw_steps': [],
            'assertions': [],
            'locators': [],
            'lifecycle_hooks': [],
            'control_flow': [],
            'referenced_locators': set(),  # Phase 2: Track used locators
            'api_context': {},             # Phase 3: Context for fluent API builders
        }

        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    src = f.read()
            except Exception:
                continue

            if path.endswith('.py'):
                self._parse_python(path, src, raw_model)
            elif path.endswith('.java'):
                self._parse_java(path, src, raw_model)

        # Phase 2: Only include locators that were actually referenced in steps
        if self._workspace_index:
            referenced = raw_model.get('referenced_locators', set())
            for class_name, field_name in referenced:
                locs = self._workspace_index.class_locators.get(class_name, {})
                locator = locs.get(field_name)
                if locator:
                    res_loc = {
                        'field_name': field_name,
                        'strategy': locator['strategy'],
                        'value': locator['value'],
                        'class': class_name,
                        'file': self._workspace_index.class_to_file.get(class_name, 'unknown')
                    }
                    if res_loc not in raw_model['locators']:
                        raw_model['locators'].append(res_loc)

        # Phase 2: Convert set to list for JSON serialization compatibility
        if 'referenced_locators' in raw_model:
            raw_model['referenced_locators'] = list(raw_model['referenced_locators'])

        return raw_model

    # ----------------------------------------------------------
    # Python parsing (kept as-is)
    # ----------------------------------------------------------

    def _parse_python(self, path, src, result):
        try:
            tree = ast.parse(src, filename=path)
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        func_name = self._get_python_call_name(sub.func)
                        args = []
                        for a in sub.args:
                            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                                args.append(a.value)
                            else:
                                args.append(ast.dump(a))

                        # Heuristics
                        lower_name = str(func_name).lower()
                        if 'click' in lower_name:
                            result['raw_steps'].append({'type': 'action', 'action': 'click', 'detail': {'fn': func_name, 'args': args, 'file': path}})
                        elif any(k in lower_name for k in ['send_keys', 'type', 'login', 'settext', 'input']):
                            result['raw_steps'].append({'type': 'action', 'action': 'type', 'detail': {'fn': func_name, 'args': args, 'file': path}})
                        elif 'find' in lower_name:
                            result['locators'].append({'fn': func_name, 'args': args, 'file': path})
                        elif any(k in lower_name for k in ['assert', 'should', 'verify', 'check']):
                            result['assertions'].append({'type': 'assertion', 'detail': {'fn': func_name, 'args': args, 'file': path}})

                    if isinstance(sub, ast.Assert):
                        result['assertions'].append({'type': 'assertion', 'detail': {'assert': ast.dump(sub), 'file': path}})

                    if isinstance(sub, (ast.If, ast.For, ast.While, ast.Try)):
                        result['control_flow'].append({'type': type(sub).__name__, 'lineno': getattr(sub, 'lineno', None)})

            # detect lifecycle hooks
            if isinstance(node, ast.FunctionDef) and node.name in ('setUp', 'tearDown', 'setup_method', 'teardown_method'):
                result['lifecycle_hooks'].append({'name': node.name, 'file': path, 'lineno': getattr(node, 'lineno', None)})

    def _get_python_call_name(self, node):
        if isinstance(node, ast.Attribute):
            return self._get_python_call_name(node.value) + '.' + node.attr
        if isinstance(node, ast.Name):
            return node.id
        return ast.dump(node)

    # ----------------------------------------------------------
    # Java parsing — Deep Selenium-aware extraction
    # ----------------------------------------------------------

    def _parse_java(self, path, src, result):
        self._init_java_parser()
        if not self._java_parser:
            return

        src_bytes = src.encode('utf-8')
        tree = self._java_parser.parse(src_bytes)
        root = tree.root_node

        # Find the class in this file
        current_class = None
        for node in self._walk_nodes(root):
            if node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    current_class = src[name_node.start_byte:name_node.end_byte]
                break

        # Collect lifecycle hooks from annotations
        self._extract_lifecycle_hooks_from_tree(path, src, root, result)

        # Phase 2: No workspace-wide filtering here anymore.
        # It's moved to parse_files to ensure all references are collected.
        if not self._workspace_index:
            # Fallback: collect locators from this file's fields if no workspace index
            self._extract_locator_fields_from_tree(path, src, root, result)

        # If this file extends BaseTest or similar, also extract lifecycle from parent
        if self._workspace_index and current_class:
            parent = self._workspace_index.class_parents.get(current_class)
            if parent and parent in self._workspace_index.class_methods:
                parent_file = self._workspace_index.class_to_file.get(parent, '')
                parent_src = self._workspace_index.class_sources.get(parent, b'').decode('utf-8', errors='replace')
                # Parse parent for lifecycle hooks
                parent_tree = self._java_parser.parse(self._workspace_index.class_sources.get(parent, b''))
                self._extract_lifecycle_hooks_from_tree(parent_file, parent_src, parent_tree.root_node, result)

        # Find @Test methods and extract their bodies
        self._extract_test_methods(path, src, src_bytes, root, result, current_class)

    def _extract_locator_fields_from_tree(self, path: str, src: str, root, result):
        """Extract By.xxx(...) locator field declarations from the file."""
        for node in self._walk_nodes(root):
            if node.type == 'field_declaration':
                declarators = [c for c in node.children if c.type == 'variable_declarator']
                for decl in declarators:
                    name_node = decl.child_by_field_name('name')
                    value_node = decl.child_by_field_name('value')
                    if not name_node or not value_node:
                        continue

                    field_name = src[name_node.start_byte:name_node.end_byte]
                    locator = self._extract_by_locator(src, value_node)
                    if locator:
                        result['locators'].append({
                            'field_name': field_name,
                            'strategy': locator['strategy'],
                            'value': locator['value'],
                            'file': path,
                        })

    def _extract_lifecycle_hooks_from_tree(self, path: str, src: str, root, result):
        """Extract lifecycle hooks by finding annotated methods."""
        for node in self._walk_nodes(root):
            if node.type == 'method_declaration':
                # Check annotations above this method
                annotations = self._get_method_annotations(src, node)
                for annot_text in annotations:
                    # Normalize: strip parameters like @BeforeSuite(alwaysRun = true)
                    annot_base = annot_text.split('(')[0].strip()
                    if annot_base in LIFECYCLE_ANNOTATIONS:
                        hook_type = LIFECYCLE_ANNOTATIONS[annot_base]
                        method_name_node = node.child_by_field_name('name')
                        method_name = src[method_name_node.start_byte:method_name_node.end_byte] if method_name_node else 'unknown'

                        # Infer what the hook does from method body
                        hook_action = self._infer_lifecycle_action(src, node, method_name, hook_type)

                        # Avoid duplicate hooks (compound key)
                        hook_key = (hook_type, method_name, hook_action)
                        if any((h['type'], h['method'], h['action']) == hook_key for h in result['lifecycle_hooks']):
                            continue

                        hook_entry = {
                            'type': hook_type,
                            'method': method_name,
                            'action': hook_action,
                            'file': path,
                        }
                        result['lifecycle_hooks'].append(hook_entry)

    def _get_method_annotations(self, src: str, method_node) -> List[str]:
        """Get annotation strings for a method declaration."""
        annotations = []
        # In tree-sitter-java, annotations may be modifiers children
        for child in method_node.children:
            if child.type == 'modifiers':
                for mod_child in child.children:
                    if mod_child.type in ('marker_annotation', 'annotation'):
                        annot_text = src[mod_child.start_byte:mod_child.end_byte]
                        annotations.append(annot_text)
        # Also check parent (some tree-sitter versions put annotations as siblings)
        if method_node.parent:
            prev = method_node.prev_sibling
            while prev and prev.type in ('marker_annotation', 'annotation'):
                annotations.append(src[prev.start_byte:prev.end_byte])
                prev = prev.prev_sibling
        return annotations

    def _infer_lifecycle_action(self, src: str, node, method_name: str, hook_type: str) -> str:
        """Infer what a lifecycle hook does based on its body and the hook type (before/after)."""
        body_text = src[node.start_byte:node.end_byte].lower()
        
        # Heuristics based on hook type (setup vs teardown)
        is_setup = 'before' in hook_type.lower()
        is_teardown = 'after' in hook_type.lower()
        
        if is_setup:
            if any(k in body_text for k in ['startsession', 'getdriver', 'newdriver', 'chromedriver', 'firefoxdriver', 'browserdriver', 'init', 'setup']):
                return 'driver_init'
        if is_teardown:
            if any(k in body_text for k in ['closesession', 'quit', 'close', 'teardown', 'stop']):
                return 'browser_close'
                
        if any(k in body_text for k in ['report', 'extent', 'allure']):
            return 'report_setup' if is_setup else 'report_teardown'
        if any(k in body_text for k in ['log', 'logger']):
            return 'logging_setup' if is_setup else 'logging_teardown'
            
        return method_name

    def _extract_test_methods(self, path: str, src: str, src_bytes: bytes, root, result, current_class: str):
        """Find @Test methods and deeply extract their actions."""
        for node in self._walk_nodes(root):
            if node.type == 'method_declaration':
                annotations = self._get_method_annotations(src, node)
                is_test = any('@Test' in a for a in annotations)
                if not is_test:
                    continue

                # Extract all actions from this test method body
                body = node.child_by_field_name('body')
                if body:
                    self._extract_actions_from_body(
                        path, src, body, result,
                        current_class=current_class,
                        depth=0
                    )

    def _extract_actions_from_body(self, path: str, src: str, body_node,
                                    result, current_class: str = None,
                                    depth: int = 0, source_method: str = None):
        """
        Extract real Selenium and API actions from a method body.
        Phase 3: Deep expansion depth increased to 5.
        Now preserves execution order by visiting objects before parents.
        """
        if not body_node or depth > 5:  # prevent infinite recursion or null
            return

        # Use a list of statements/nodes to process in order
        # We don't use _walk_nodes flat here because we want to control the recursion order
        # to preserve AST execution order (e.g. for fluent APIs and sequential statements)
        
        for node in body_node.children:
            # Skip noise nodes
            if node.type in ('(', ')', '{', '}', ';', ','):
                continue

            # ----- Control Flow Detection (Phase 3: Structured & Scoped) -----
            if node.type in ('if_statement', 'for_statement', 'while_statement', 'try_statement', 'enhanced_for_statement'):
                if depth == 0:
                    condition = ""
                    if node.type == 'if_statement':
                        cond_node = node.child_by_field_name('condition')
                        if cond_node:
                            condition = src[cond_node.start_byte:cond_node.end_byte].strip('()').strip()
                    elif node.type in ('for_statement', 'enhanced_for_statement', 'while_statement'):
                        # Find the header before the block
                        header = src[node.start_byte:node.end_byte].split('{')[0].strip()
                        condition = header
                    
                    result['control_flow'].append({
                        'type': 'control',
                        'action': node.type.replace('_statement', '').replace('enhanced_', ''),
                        'condition': condition,
                        'scope': 'test',
                        'file': path,
                        'line': node.start_point[0] + 1
                    })
                
                # Recurse into blocks/consequents of control flow
                for child in node.children:
                    if child.type in ('block', 'if_statement', 'else'):
                         self._extract_actions_from_body(path, src, child, result, current_class, depth, source_method)
                continue

            # ----- Statement Level Processing -----
            if node.type == 'expression_statement':
                # Process the inner expression
                for child in node.children:
                    self._extract_actions_from_inner(path, src, child, result, body_node, current_class, depth, source_method)
                continue
            
            # For other node types (variable declarations, etc), look for nested expressions
            self._extract_actions_from_inner(path, src, node, result, body_node, current_class, depth, source_method)

    def _extract_actions_from_inner(self, path: str, src: str, node,
                                    result, body_node, current_class: str = None,
                                    depth: int = 0, source_method: str = None):
        """Sub-routine to handle nested expressions inside statements while maintaining order."""
        if not node:
            return
        
        # 1. Recurse into "object" of method invocation FIRST (Execution Order)
        if node.type == 'method_invocation':
            obj_node = node.child_by_field_name('object')
            if obj_node:
                self._extract_actions_from_inner(path, src, obj_node, result, body_node, current_class, depth, source_method)
            
            # Now process this actual call
            self._process_single_method_call(path, src, node, result, body_node, current_class, depth, source_method)
            
            # Visit arguments
            args_node = node.child_by_field_name('arguments')
            if args_node:
                for arg in args_node.children:
                    if arg.type not in ('(', ')', ','):
                        self._extract_actions_from_inner(path, src, arg, result, body_node, current_class, depth, source_method)
            return

        # 2. Variable declarations (int x = call())
        if node.type == 'variable_declarator':
            value_node = node.child_by_field_name('value')
            if value_node:
                self._extract_actions_from_inner(path, src, value_node, result, body_node, current_class, depth, source_method)
            return

        # 3. Handle other containers
        for child in node.children:
            if child.type not in ('(', ')', '{', '}', ';', ','):
                self._extract_actions_from_inner(path, src, child, result, body_node, current_class, depth, source_method)

    def _process_single_method_call(self, path: str, src: str, node,
                                    result, body_node, current_class: str = None,
                                    depth: int = 0, source_method: str = None):
        """Process a single method_invocation node."""
        name_node = node.child_by_field_name('name')
        obj_node = node.child_by_field_name('object')
        args_node = node.child_by_field_name('arguments')

        if not name_node:
            return

        method_name = src[name_node.start_byte:name_node.end_byte]
        obj_text = src[obj_node.start_byte:obj_node.end_byte] if obj_node else ''

        # ----- 1. driver.get(url) — Navigation -----
        if method_name == 'get' and 'driver' in obj_text.lower():
            url = self._extract_first_string_arg(src, args_node)
            result['raw_steps'].append({
                'type': 'action',
                'action': 'navigate',
                'url': url or 'dynamic',
                'detail': {
                    'fn': f'{obj_text}.get',
                    'args': [url] if url else [],
                    'file': path,
                },
                'source_method': source_method,
            })
            return

        # ----- 2. driver.findElement(By.xxx(...)).click/sendKeys -----
        if method_name in SELENIUM_ACTION_METHODS and obj_node:
            # Check if the object is a findElement call
            locator = self._extract_chained_locator(src, obj_node, result, current_class)
            if locator:
                action = SELENIUM_ACTION_METHODS[method_name]
                step = {
                    'type': 'action',
                    'action': action,
                    'locator': locator,
                    'detail': {
                        'fn': f'findElement(...).{method_name}',
                        'file': path,
                    },
                    'source_method': source_method,
                }
                # For sendKeys, extract the value
                if action == 'type':
                    value = self._extract_first_string_arg(src, args_node)
                    if value:
                        step['value'] = value
                    else:
                        value_text = self._extract_arg_text(src, args_node)
                        step['value'] = 'dynamic'
                        step['value_ref'] = value_text
                result['raw_steps'].append(step)
                return

        # ----- 3. scriptAction.xxx(locatorField, ...) — Wrapper methods -----
        if method_name in WRAPPER_ACTION_METHODS:
            action = WRAPPER_ACTION_METHODS[method_name]
            locator = self._resolve_locator_from_args(src, args_node, result, current_class)
            step = {
                'type': 'action',
                'action': action,
                'locator': locator,
                'detail': {
                    'fn': f'{obj_text}.{method_name}' if obj_text else method_name,
                    'file': path,
                },
                'source_method': source_method,
            }

            # For inputText / type, extract the value (second arg usually but can vary)
            if action == 'type':
                # Heuristic: try second arg first, then look for any string arg
                value = self._extract_nth_string_arg(src, args_node, 1) or self._extract_first_string_arg(src, args_node)
                if value:
                    step['value'] = value
                else:
                    value_ref = self._extract_nth_arg_text(src, args_node, 1) or self._extract_arg_text(src, args_node)
                    step['value'] = 'dynamic'
                    if value_ref:
                        step['value_ref'] = value_ref

            result['raw_steps'].append(step)
            return

        # ----- 4. Assert.xxx(...) — Assertions (Fix: support static imports) -----
        is_assertion = (
            method_name in ASSERTION_METHODS and 
            (not obj_text or 'Assert' in obj_text or 'assert' in obj_text or 'expect' in obj_text or 'verify' in obj_text)
        )
        if is_assertion:
            operator = ASSERTION_METHODS[method_name]
            assertion = {
                'type': 'assertion',
                'operator': operator,
                'detail': {
                    'fn': f'{obj_text}.{method_name}' if obj_text else method_name,
                    'file': path,
                },
                'source_method': source_method,
            }

            # Extract left/right/condition
            if operator in ('equals', 'not_equals'):
                # Handle Assert.assertEquals(actual, expected) or (expected, actual, delta) etc.
                assertion['left'] = self._extract_nth_arg_text(src, args_node, 0) or 'unknown'
                assertion['right'] = self._extract_nth_arg_text(src, args_node, 1) or 'unknown'
            elif operator in ('true', 'false', 'present', 'not_present'):
                assertion['condition'] = self._extract_nth_arg_text(src, args_node, 0) or 'unknown'
            elif operator == 'fail':
                assertion['message'] = self._extract_first_string_arg(src, args_node) or 'unknown'
            
            result['assertions'].append(assertion)
            return

        # ----- 5. API / RestAssured Modelling -----
        is_api_obj = any(k in obj_text.lower() for k in ('restassured', 'given', 'when', 'request', 'apiutil', 'spec', 'response'))
        api_method = None
        endpoint_idx = 0
        
        if method_name in REST_ASSURED_METHODS:
            if is_api_obj or not obj_text:
                api_method = REST_ASSURED_METHODS[method_name]
                endpoint_idx = 0
        elif method_name in API_UTIL_METHODS:
            if is_api_obj or not obj_text:
                api_method = API_UTIL_METHODS[method_name]
                # sendPost(url, body) or sendPost(body, url)? Usually url first or payload first.
                endpoint_idx = 1 if api_method in ('POST', 'PUT', 'PATCH') and len(args_node.children) > 3 else 0

        # API fluent handlers: .body(), .header(), .param()
        if method_name == 'body':
            result['api_context']['payload'] = self._extract_arg_text(src, args_node)
        elif method_name in ('header', 'headers'):
            result['api_context'].setdefault('headers', []).append(self._extract_arg_text(src, args_node))
        elif method_name in ('param', 'params', 'queryParam'):
             result['api_context'].setdefault('params', []).append(self._extract_arg_text(src, args_node))

        if api_method:
            endpoint = self._extract_nth_string_arg(src, args_node, endpoint_idx) or self._extract_nth_arg_text(src, args_node, endpoint_idx) or 'dynamic'
            step = {
                'type': 'action',
                'action': 'http_request',
                'method': api_method,
                'endpoint': endpoint,
                'detail': {
                    'fn': f'{obj_text}.{method_name}' if obj_text else method_name,
                    'file': path,
                },
                'source_method': source_method,
            }
            # Consume context
            if 'payload' in result['api_context']:
                step['payload'] = result['api_context'].pop('payload')
            if 'headers' in result['api_context']:
                step['headers'] = result['api_context'].pop('headers')
            if 'params' in result['api_context']:
                step['params'] = result['api_context'].pop('params')

            result['raw_steps'].append(step)
            return

        # ----- 6. Page Object expansion (Phase 3+) -----
        if self._workspace_index and depth < 5:
            resolved_class = None
            if obj_node:
                resolved_class = self._resolve_object_class(src, obj_node, body_node, current_class)
            else:
                if current_class and method_name in self._workspace_index.class_methods.get(current_class, {}):
                    resolved_class = current_class
            
            if resolved_class and resolved_class in self._workspace_index.class_methods:
                method_info = self._workspace_index.class_methods[resolved_class].get(method_name)
                if method_info:
                    po_src = method_info['src']
                    po_node = method_info['node']
                    po_body = po_node.child_by_field_name('body')
                    po_file = self._workspace_index.class_to_file.get(resolved_class, path)
                    if po_body:
                        self._extract_actions_from_body(
                            po_file, po_src, po_body, result,
                            current_class=resolved_class,
                            depth=depth + 1,
                            source_method=f'{resolved_class}.{method_name}'
                        )
                    return

                # Also check parent class methods
                parent_class = self._workspace_index.class_parents.get(resolved_class)
                if parent_class and parent_class in self._workspace_index.class_methods:
                    method_info = self._workspace_index.class_methods[parent_class].get(method_name)
                    if method_info:
                        po_src = method_info['src']
                        po_node = method_info['node']
                        po_body = po_node.child_by_field_name('body')
                        po_file = self._workspace_index.class_to_file.get(parent_class, path)
                        if po_body:
                            self._extract_actions_from_body(
                                po_file, po_src, po_body, result,
                                current_class=parent_class,
                                depth=depth + 1,
                                source_method=f'{parent_class}.{method_name}'
                            )
                        return

    def _extract_chained_locator(self, src: str, obj_node, result, current_class: str = None) -> Optional[Dict[str, str]]:
        """
        Check if obj_node is a findElement(By.xxx("...")) call and extract the locator.
        Handles: driver.findElement(By.xpath("//input")) → {strategy: "xpath", value: "//input"}
        Also handles field references: driver.findElement(txtUser)
        """
        if obj_node.type != 'method_invocation':
            return None

        name_node = obj_node.child_by_field_name('name')
        if not name_node:
            return None

        name = src[name_node.start_byte:name_node.end_byte]
        if name not in ('findElement', 'findElements'):
            return None

        args_node = obj_node.child_by_field_name('arguments')
        if not args_node:
            return None
 
        return self._resolve_locator_from_args(src, args_node, result, current_class)

    def _resolve_locator_from_args(self, src: str, args_node, result, current_class: str = None) -> Optional[Dict[str, str]]:
        """
        Resolve the locator from the first argument of a wrapper method.
        The argument might be:
        - A By.xxx("...") inline call
        - A field reference like txtUserEmailID
        - A By.xpath(String.format(template, value)) call
        """
        if not args_node:
            return None

        for child in args_node.children:
            if child.type in ('(', ')', ','):
                continue

            # Try direct By.xxx(...) inline
            locator = self._extract_by_locator(src, child)
            if locator:
                return locator

            # Try field reference
            if child.type == 'identifier':
                field_name = src[child.start_byte:child.end_byte]
                # Phase 2: Mark as referenced
                if current_class:
                    result['referenced_locators'].add((current_class, field_name))
                return self._lookup_field_locator(field_name, current_class)

            break  # Only check first real argument

        return None

    def _lookup_field_locator(self, field_name: str, current_class: str = None) -> Optional[Dict[str, str]]:
        """Look up a field name in the workspace index to find its locator."""
        if not self._workspace_index or not current_class:
            return None

        # Check current class
        locators = self._workspace_index.class_locators.get(current_class, {})
        if field_name in locators:
            return locators[field_name]

        # Check parent class
        parent = self._workspace_index.class_parents.get(current_class)
        if parent:
            parent_locators = self._workspace_index.class_locators.get(parent, {})
            if field_name in parent_locators:
                return parent_locators[field_name]

        return None

    def _resolve_object_class(self, src: str, obj_node, body_node, current_class: str = None) -> Optional[str]:
        """
        Resolve the class of an object reference.
        For example, in `loginPage.loginToApplication(...)`, resolve loginPage → LoginPage.

        Strategy:
        1. Look for local variable declarations like `LoginPage loginPage = new LoginPage(...)`
        2. Check if the variable name matches a known class (case-insensitive)
        """
        if not self._workspace_index:
            return None

        if obj_node.type == 'method_invocation':
            # Fluent API / Method chaining: resolve the object of the inner call
            inner_obj = obj_node.child_by_field_name('object')
            if inner_obj:
                return self._resolve_object_class(src, inner_obj, body_node, current_class)
            else:
                # Implicit 'this' in the inner call
                return current_class

        if obj_node.type == 'super':
            return self._workspace_index.class_parents.get(current_class)

        obj_text = src[obj_node.start_byte:obj_node.end_byte]
        # Remove method chains — just get the base variable name
        if '.' in obj_text:
            obj_text = obj_text.split('.')[0]

        # Search for a local variable declaration with this name
        for node in self._walk_nodes(body_node):
            if node.type == 'local_variable_declaration':
                for child in node.children:
                    if child.type == 'variable_declarator':
                        var_name_node = child.child_by_field_name('name')
                        if var_name_node:
                            var_name = src[var_name_node.start_byte:var_name_node.end_byte]
                            if var_name == obj_text:
                                # Get the type
                                type_node = None
                                # Check siblings in parent node (local_variable_declaration)
                                for sibling in child.parent.children:
                                    if sibling.type in ('type_identifier', 'generic_type', 'scoped_type_identifier'):
                                        type_node = sibling
                                        break
                                if type_node:
                                    type_text = src[type_node.start_byte:type_node.end_byte]
                                    if type_text in self._workspace_index.class_to_file:
                                        return type_text

        # Fallback: try matching variable name to known classes case-insensitively
        for class_name in self._workspace_index.class_to_file:
            if class_name.lower() == obj_text.lower():
                return class_name

        return None

    def _extract_arg_text(self, src: str, args_node) -> Optional[str]:
        """Extract full text of the first argument."""
        if not args_node:
            return None
        for child in args_node.children:
            if child.type in ('(', ')', ','):
                continue
            return src[child.start_byte:child.end_byte]
        return None

    def _extract_nth_arg_text(self, src: str, args_node, n: int) -> Optional[str]:
        """Extract text of the nth argument (0-indexed)."""
        if not args_node:
            return None
        idx = 0
        for child in args_node.children:
            if child.type in ('(', ')', ','):
                continue
            if idx == n:
                return src[child.start_byte:child.end_byte]
            idx += 1
        return None

    def _extract_nth_string_arg(self, src: str, args_node, n: int) -> Optional[str]:
        """Extract the nth string literal argument (0-indexed)."""
        if not args_node:
            return None
        idx = 0
        for child in args_node.children:
            if child.type in ('(', ')', ','):
                continue
            if idx == n:
                if child.type == 'string_literal':
                    raw = src[child.start_byte:child.end_byte]
                    return raw.strip('"').strip("'")
                return None
            idx += 1
        return None


# ===============================
# LAYER 2 — NORMALIZATION
# ===============================

class IntentNormalizer:
    """Convert raw AST model into framework-agnostic canonical schema."""

    def normalize(self, raw_model):
        steps = []
        assertions = []
        locators = []

        for s in raw_model.get('raw_steps', []):
            if s.get('type') == 'action':
                action = s.get('action')
                step = {
                    'type': 'action',
                    'action': action,
                }

                # Add locator if present
                locator = s.get('locator')
                if locator and isinstance(locator, dict) and locator.get('strategy'):
                    step['locator'] = {
                        'strategy': locator['strategy'],
                        'value': locator['value'],
                    }

                # Add URL for navigate actions
                if action == 'navigate' and s.get('url'):
                    step['url'] = s['url']

                # Add value for type actions
                if action == 'type':
                    step['value'] = s.get('value', 'dynamic')
                    if s.get('value_ref'):
                        step['value_ref'] = s['value_ref']

                # Add API action metadata (Phase 3)
                if action == 'http_request':
                    step['method'] = s.get('method')
                    step['endpoint'] = s.get('endpoint')
                    if s.get('payload'):
                        step['payload'] = s['payload']
                    if s.get('headers'):
                        step['headers'] = s['headers']
                    if s.get('params'):
                        step['params'] = s['params']

                # Add source method tracing as metadata (Phase 6: Clean Canonical Core)
                if s.get('source_method'):
                    step['metadata'] = {'source_method': s['source_method']}

                steps.append(step)

        for a in raw_model.get('assertions', []):
            assertion = {'type': 'assertion'}
            if a.get('operator'):
                assertion['operator'] = a['operator']
            if a.get('left'):
                assertion['left'] = a['left']
            if a.get('right'):
                assertion['right'] = a['right']
            if a.get('condition'):
                assertion['condition'] = a['condition']
            if a.get('message'):
                assertion['message'] = a['message']
            if a.get('source_method'):
                assertion['metadata'] = {'source_method': a['source_method']}
            # Fallback for old format
            if not assertion.get('operator') and a.get('detail'):
                assertion['detail'] = a['detail']
            assertions.append(assertion)

        for l in raw_model.get('locators', []):
            locators.append({
                'field_name': l.get('field_name', l.get('fn', 'unknown')),
                'strategy': l.get('strategy', 'unknown'),
                'value': l.get('value'),
            })

        # Normalize and Deduplicate lifecycle hooks (Phase 6)
        lifecycle_hooks = []
        seen_hooks = set()
        for h in raw_model.get('lifecycle_hooks', []):
            htype = h.get('type', 'unknown')
            # Normalize action name: lower, strip 'Test' suffix
            action = h.get('action', h.get('name', 'unknown')).lower().replace('test', '').strip('_')
            
            # Semantic normalization: teardown -> logical 'teardown'
            if any(k in action for k in ('teardown', 'close', 'quit', 'exit', 'stop', 'after', 'cleanup')):
                action = 'teardown'
            if any(k in action for k in ('setup', 'init', 'start', 'entry', 'before', 'prepare')):
                action = 'setup'

            hook_key = (htype, action)
            if hook_key in seen_hooks:
                continue
            seen_hooks.add(hook_key)

            hook = {
                'type': htype,
                'action': action,
            }
            if h.get('method'):
                hook['method'] = h['method']
            lifecycle_hooks.append(hook)

        # Filter Control Flow: Only keep 'test' scope (Phase 6)
        filtered_control_flow = [
            cf for cf in raw_model.get('control_flow', [])
            if cf.get('scope') == 'test'
        ]

        normalized = {
            'steps': steps,
            'assertions': assertions,
            'locators': locators,
            'lifecycle_hooks': lifecycle_hooks,
            'control_flow': filtered_control_flow,
            'validation_warnings': [],
            'semantic_flags': [],
        }

        # ----- 1. Deterministic Validation Warnings -----
        
        # NO_ASSERTION_PRESENT
        if not assertions:
            normalized['validation_warnings'].append("NO_ASSERTION_PRESENT")
            normalized['semantic_flags'].append("WEAK_TEST_STRUCTURE")

        # DUPLICATE_WAIT
        last_wait_locator = None
        for s in steps:
            if s.get('action') == 'wait':
                loc = s.get('locator')
                if loc and loc == last_wait_locator:
                    normalized['validation_warnings'].append("DUPLICATE_WAIT")
                last_wait_locator = loc
            else:
                last_wait_locator = None

        # DYNAMIC_URL
        for s in steps:
            if s.get('action') == 'navigate' and s.get('url') == 'dynamic':
                normalized['validation_warnings'].append("DYNAMIC_URL")

        # MISSING_POST_ACTION_VALIDATION
        # If the last step is an action without a following assertion
        if steps and not assertions:
             normalized['validation_warnings'].append("MISSING_POST_ACTION_VALIDATION")

        # ----- 2. Step Ordering Check (Deterministic heuristic) -----
        # Check for suspicious ordering: typing password before email
        # This is a bit specific but the user requested it.
        email_step_idx = -1
        password_step_idx = -1
        for i, s in enumerate(steps):
            if s.get('action') == 'type':
                val = str(s.get('value', '')).lower()
                ref = str(s.get('value_ref', '')).lower()
                if 'email' in val or 'email' in ref:
                    email_step_idx = i
                if 'password' in val or 'pass' in ref:
                    password_step_idx = i
        
        if password_step_idx != -1 and email_step_idx != -1 and password_step_idx < email_step_idx:
            normalized['validation_warnings'].append("SUSPICIOUS_STEP_ORDERING")

        return normalized

    def _extract_target_from_args(self, args):
        # Very small heuristic: first string arg is treated as locator value
        if not args:
            return None
        val = args[0]
        strategy = 'unknown'
        if isinstance(val, str):
            if val.startswith('#'):
                strategy = 'css'#id
            elif val.startswith('.'):
                strategy = 'css'
            elif '//' in val or '/' in val:
                strategy = 'xpath'
            else:
                strategy = 'text_or_id'
        return {'strategy': strategy, 'value': val}

    def _normalize_locator(self, l):
        args = l.get('args', [])
        val = args[0] if args else None
        return {'fn': l.get('fn'), 'value': val}


# Backward compatibility alias
Normalizer = IntentNormalizer



# ===============================
# LAYER 4 — VALIDATION
# ===============================

class IntentValidator:
    """Validate LLM enriched output against normalized model per guardrails."""

    def validate(self, normalized, enriched):
        result = {'valid': True, 'reasons': []}
        if not isinstance(enriched, dict):
            result['valid'] = False
            result['reasons'].append('enriched_not_dict')
            return result

        # Step count
        n_steps = len(normalized.get('steps', []))
        e_steps = 0
        if 'step_groups' in enriched:
            for g in enriched.get('step_groups', []):
                e_steps += len(g.get('steps', []))

        if e_steps and e_steps != n_steps:
            result['valid'] = False
            result['reasons'].append('step_count_mismatch')

        # Assertion count
        n_asserts = len(normalized.get('assertions', []))
        e_asserts = enriched.get('assertion_count', None)
        if e_asserts is not None and e_asserts != n_asserts:
            result['valid'] = False
            result['reasons'].append('assertion_count_mismatch')

        # Locator integrity: ensure values not changed if provided
        n_loc_vals = [l.get('value') for l in normalized.get('locators', [])]
        e_loc_vals = enriched.get('locators', None)
        if e_loc_vals is not None and set(map(str, e_loc_vals)) != set(map(str, n_loc_vals)):
            result['valid'] = False
            result['reasons'].append('locator_mismatch')

        return result


# ===============================
# MAIN SERVICE
# ===============================

class IntentExtractorService:
    def __init__(self, db_path=None, extraction_version='v1'):
        self.db = Database(db_path) if db_path else Database()
        self.db.init_schema()
        self.ast_extractor = ASTExtractor()
        self.normalizer = IntentNormalizer()
        self.llm_service = LLMEnrichmentService()
        self.validator = IntentValidator()
        self.extraction_version = extraction_version

    # ----------------------------------------------------------
    # Step 9 Pipeline — process_feature
    # ----------------------------------------------------------

    def process_feature(self, session_id: str, feature_id: str, file_paths: List[str],
                        workspace_files: List[str] = None):
        """
        Full Step 9 pipeline:
          0. Build workspace index  (cross-file resolution)
          1. AST Extraction         (deterministic, deep Selenium analysis)
          2. Normalization           (canonical schema)
          3. Intent Hashing          (SHA-256)
          4. Optional LLM enrichment + guardrails
          5. Persist to SQLite
        """

        # STEP 0 — Build workspace index for cross-file resolution
        if workspace_files:
            self.ast_extractor.build_workspace_index(workspace_files)

        # STEP 1 — AST Extraction
        raw_model = self.ast_extractor.parse_files(file_paths)

        # STEP 2 — Normalize
        normalized_model = self.normalizer.normalize(raw_model)

        # STEP 3 — Pruning (Phase 3)
        # If no steps and no assertions, skip this feature to prevent "phantom" migration
        if not normalized_model.get('steps') and not normalized_model.get('assertions'):
            logger.info(f"Skipping feature {feature_id} - no executable steps or assertions found.")
            return {
                "feature_id": feature_id,
                "status": "SKIPPED",
                "reason": "EMPTY_FEATURE"
            }

        # STEP 4 — Intent Hash
        intent_hash = generate_intent_hash(normalized_model)

        # STEP 4 — Optional LLM enrichment
        enriched_model = None
        enrichment_status = "SKIPPED"

        # Skip Logic
        should_enrich = (
            len(normalized_model.get('steps', [])) >= 1 and
            USE_LLM
        )

        if should_enrich:
            # Check if already enriched with this hash
            existing = self.db.fetchone(
                "SELECT enriched_model, enrichment_status FROM feature_intent WHERE intent_hash = ? AND enrichment_status = 'SUCCESS'",
                (intent_hash,)
            )
            if existing:
                logger.info(f"Feature {feature_id} already enriched for hash {intent_hash}. Skipping LLM call.")
                try:
                    enriched_model = json.loads(existing['enriched_model'])
                    enrichment_status = existing['enrichment_status']
                except:
                    enriched_model = None
            
            if enriched_model is None:
                enriched_model = self.llm_service.enrich(normalized_model)
                if enriched_model:
                    enrichment_status = enriched_model.get("enrichment_status", "UNKNOWN")

        # STEP 5 — Save to DB
        self._save_to_db(
            session_id,
            feature_id,
            raw_model,
            normalized_model,
            enriched_model,
            intent_hash,
            enrichment_status
        )

        return {
            "feature_id": feature_id,
            "intent_hash": intent_hash,
            "normalized_model": normalized_model,
            "enriched_model": enriched_model
        }

    # ----------------------------------------------------------
    # Legacy extract() — kept for backward compatibility
    # ----------------------------------------------------------

    def extract(self, feature_id, file_paths, language='python', framework=None, use_llm=True, llm_goal=None):
        # Resume support: check DB
        row = self.db.fetchone('SELECT * FROM feature_intent WHERE feature_id = ?', (feature_id,))

        if row and row.get('raw_model'):
            raw_model = json.loads(row.get('raw_model'))
        else:
            raw_model = self.ast_extractor.parse_files(file_paths)
            self.db.execute('INSERT OR REPLACE INTO feature_intent (feature_id, raw_model, extraction_version, llm_used, validation_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)',
                            (feature_id, json.dumps(raw_model), self.extraction_version, 0, 'raw_extracted', datetime.utcnow(), datetime.utcnow()))

        if row and row.get('normalized_model'):
            normalized = json.loads(row.get('normalized_model'))
        else:
            normalized = self.normalizer.normalize(raw_model)
            self.db.execute('UPDATE feature_intent SET normalized_model = ?, updated_at = ? WHERE feature_id = ?',
                            (json.dumps(normalized), datetime.utcnow(), feature_id))

        enriched = None
        validation_status = 'normalized'

        if use_llm:
            if row and row.get('enriched_model'):
                enriched = json.loads(row.get('enriched_model'))
                validation_status = row.get('validation_status') or 'enriched_from_db'
            else:
                enriched = self.llm_service.enrich(normalized)
                validation = self.validator.validate(normalized, enriched)
                if not validation.get('valid'):
                    validation_status = 'LLM_CONFLICT'
                    # do not overwrite normalized with enriched
                    self.db.execute('UPDATE feature_intent SET enriched_model = ?, llm_used = ?, validation_status = ?, updated_at = ? WHERE feature_id = ?',
                                    (json.dumps(enriched), 1, validation_status, datetime.utcnow(), feature_id))
                else:
                    validation_status = 'validated'
                    self.db.execute('UPDATE feature_intent SET enriched_model = ?, llm_used = ?, validation_status = ?, updated_at = ? WHERE feature_id = ?',
                                    (json.dumps(enriched), 1, validation_status, datetime.utcnow(), feature_id))

        return {'feature_id': feature_id, 'raw_model': raw_model, 'normalized_model': normalized, 'enriched_model': enriched, 'validation_status': validation_status}

    # ----------------------------------------------------------
    # DB Persistence
    # ----------------------------------------------------------

    def _save_to_db(
        self,
        session_id: str,
        feature_id: str,
        raw_model: Dict,
        normalized_model: Dict,
        enriched_model: Dict,
        intent_hash: str,
        enrichment_status: str
    ):
        llm_used = 1 if enrichment_status == "SUCCESS" else 0
        validation_status = enrichment_status if enrichment_status in ("LLM_CONFLICT", "LLM_ERROR") else "validated"
        
        self.db.execute("""
            INSERT OR REPLACE INTO feature_intent
            (feature_id, raw_model, normalized_model,
             enriched_model, intent_hash, extraction_version,
             llm_used, validation_status, enrichment_status, 
             enrichment_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feature_id,
            json.dumps(raw_model),
            json.dumps(normalized_model),
            json.dumps(enriched_model) if enriched_model else None,
            intent_hash,
            self.extraction_version,
            llm_used,
            validation_status,
            enrichment_status,
            "v1", # Enrichment version
            datetime.utcnow(),
            datetime.utcnow()
        ))
