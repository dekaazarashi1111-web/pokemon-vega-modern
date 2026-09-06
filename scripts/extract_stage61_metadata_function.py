"""Stage61の既存metadata式を意味不変で共有関数へ移す編集補助。"""
from __future__ import annotations
import ast


NAME = '_persistent_state_compatibility_metadata'
ANCHOR = 'def _critical_release_persistent_state_contract()'


def transform(source: str) -> str:
    tree = ast.parse(source)
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == NAME
           for node in ast.walk(tree)):
        raise ValueError('metadata function already exists')
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'persistent_state_compatibility' \
                        and isinstance(value, ast.Dict):
                    candidates.append(value)
    if len(candidates) != 1 or source.count(ANCHOR) != 1:
        raise ValueError('metadata extraction source is not unique')
    literal = ast.get_source_segment(source, candidates[0])
    if not isinstance(literal, str):
        raise ValueError('metadata expression unavailable')
    old = '        "persistent_state_compatibility": ' + literal
    if source.count(old) != 1:
        raise ValueError('metadata declaration indentation differs')
    lines = literal.splitlines()
    dedented = lines[0] + '\n' + '\n'.join(
        line[8:] if line.startswith('        ') else line for line in lines[1:])
    definition = ('def ' + NAME + '() -> dict[str, Any]:\n'
                  '    """strict生成物と状態unit候補が共有する完全なsave契約。"""\n'
                  '    return ' + dedented + '\n\n\n')
    result = source.replace(old, '        "persistent_state_compatibility": ' + NAME + '()', 1)
    result = result.replace(ANCHOR, definition + ANCHOR, 1)
    updated = ast.parse(result)
    function = next(node for node in updated.body if isinstance(node, ast.FunctionDef) and node.name == NAME)
    returns = [node for node in function.body if isinstance(node, ast.Return)]
    if len(returns) != 1 or ast.dump(returns[0].value) != ast.dump(candidates[0]):
        raise ValueError('metadata AST changed during extraction')
    return result
