import ast
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ASTCodeSlicer:
    """
    Code slicer using Python AST (and Tree-sitter abstraction) to extract minimal,
    standalone reference code slices including necessary imports and classes.
    """
    def __init__(self):
        pass

    def extract_slice_by_symbol(self, source_code: str, target_symbol: str) -> Optional[str]:
        """
        Parses source code, extracts relevant imports and the target function/class.
        """
        try:
            tree = ast.parse(source_code)
        except Exception as e:
            logger.error(f"Failed to parse source code AST: {e}")
            return None

        imports = []
        target_node = None

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == target_symbol:
                    target_node = node

        if not target_node:
            logger.warning(f"Symbol '{target_symbol}' not found in source AST.")
            return None

        slice_code = "\n".join(imports) + "\n\n" + ast.unparse(target_node)
        return slice_code

    def extract_exported_symbols(self, source_code: str) -> List[Dict[str, Any]]:
        """Returns all top-level functions and classes in source code."""
        try:
            tree = ast.parse(source_code)
        except Exception as e:
            logger.error(f"AST parsing error: {e}")
            return []

        symbols = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append({
                    "name": node.name,
                    "type": "function",
                    "docstring": ast.get_docstring(node),
                    "code": ast.unparse(node)
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "docstring": ast.get_docstring(node),
                    "code": ast.unparse(node)
                })
        return symbols
