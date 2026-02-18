import tree_sitter_typescript as ts_ts
from tree_sitter import Language

with open("debug_results.txt", "w") as f:
    f.write(f"type: {type(ts_ts.language_typescript())}\n")
    f.write(f"value: {ts_ts.language_typescript()}\n")

    try:
        lang = Language(ts_ts.language_typescript(), "typescript")
        f.write("Language(ptr, name) success\n")
    except Exception as e:
        f.write(f"Language(ptr, name) failed: {e}\n")

    try:
        lang = Language(ts_ts.language_typescript())
        f.write("Language(ptr) success\n")
    except Exception as e:
        f.write(f"Language(ptr) failed: {e}\n")
