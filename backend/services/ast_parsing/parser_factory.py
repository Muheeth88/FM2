from .python_ast_parser import PythonASTParser
from .ts_ast_parser import TypeScriptASTParser
from .java_ast_parser import JavaASTParser


class ASTParserFactory:

    @staticmethod
    def get_parser(language: str, repo_root: str):
        if language.lower() == "python":
            return PythonASTParser(repo_root)
        if language.lower() in ["typescript", "javascript"]:
            return TypeScriptASTParser(repo_root)
        if language.lower() == "java":
            return JavaASTParser(repo_root)

        raise ValueError(f"Unsupported language: {language}")
