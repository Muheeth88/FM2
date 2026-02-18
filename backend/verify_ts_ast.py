import os
import tempfile
import shutil
from services.ast_parsing.ts_ast_parser import TypeScriptASTParser

def test_ts_ast_parser():
    repo_root = tempfile.mkdtemp()
    try:
        test_file = "sample.ts"
        with open(os.path.join(repo_root, test_file), "w", encoding="utf-8") as f:
            f.write("import { x } from 'y'; class A { method() { test('a', () => {}); } }")

        parser = TypeScriptASTParser(repo_root)
        result = parser.parse_file(test_file)
        print(f"Result: {result}")
        assert result["is_test"] == True
        print("Success!")
    finally:
        shutil.rmtree(repo_root)

if __name__ == "__main__":
    test_ts_ast_parser()
