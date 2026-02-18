import tree_sitter_typescript as ts_ts
from tree_sitter import Language

print(f"type: {type(ts_ts.language_typescript())}")
print(f"value: {ts_ts.language_typescript()}")

try:
    lang = Language(ts_ts.language_typescript(), "typescript")
    print("Language(ptr, name) success")
except Exception as e:
    print(f"Language(ptr, name) failed: {e}")

try:
    lang = Language(ts_ts.language_typescript())
    print("Language(ptr) success")
except Exception as e:
    print(f"Language(ptr) failed: {e}")
