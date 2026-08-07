from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import ryml


def ryml_parse(data: str) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Parse a YAML string into a Python dictionary.
    Around ~40x faster than `ruamel.yaml`, but does not preserve comments.

    Allows for multiple documents to be included in a single stream, in which
    case the result will be a list of YAML documents. This isn't distinguished
    from a single document containing a single YAML list.
    """
    import ryml

    with capture_stderr_as_exception(ValueError):
        tree: ryml.Tree = ryml.parse_in_arena(data)
    return ryml_tree_to_dict(tree)


def ryml_tree_to_dict(tree: ryml.Tree) -> dict[str, Any]:
    import ryml

    def _convert_node(node: Any) -> Any:
        if tree.is_val(node):
            return parse_val_node(tree, node)

        if tree.is_seq(node):
            result_seq: list[Any] = []
            for child in ryml.children(tree, node):
                result_seq.append(_convert_node(child))
            return result_seq

        if tree.is_map(node):
            result_map: dict[str, Any] = {}
            for child in ryml.children(tree, node):
                key = memoryview_to_str(cast(memoryview, tree.key(child)))
                value = _convert_node(child)
                result_map[key] = value
            return result_map

        return parse_val_node(tree, node)

    root_id = tree.root_id()
    return cast(dict[str, Any], _convert_node(root_id))


def parse_val_node(tree: ryml.Tree, node: Any) -> Any:
    val_str = memoryview_to_str(cast(memoryview, tree.val(node)))
    if tree.is_val_quoted(node):
        return val_str
    else:
        return parse_scalar(val_str)


NONE_VALUES = frozenset({"null", "Null", "NULL", "~", ""})
TRUE_VALUES = frozenset({"true", "True", "TRUE"})
FALSE_VALUES = frozenset({"false", "False", "FALSE"})
INF_VALUES = frozenset({".inf", ".Inf", ".INF", "+.inf", "+.Inf", "+.INF"})
NEG_INF_VALUES = frozenset({"-.inf", "-.Inf", "-.INF"})
NAN_VALUES = frozenset({".nan", ".NaN", ".NAN"})


def parse_scalar(val: str) -> Any:
    if val in NONE_VALUES:
        return None
    elif val in TRUE_VALUES:
        return True
    elif val in FALSE_VALUES:
        return False
    elif val in INF_VALUES:
        return float("inf")
    elif val in NEG_INF_VALUES:
        return float("-inf")
    elif val in NAN_VALUES:
        return float("nan")

    if val.startswith(("0x", "0X")):
        try:
            return int(val, 16)
        except ValueError:
            pass
    elif val.startswith(("0o", "0O")):
        try:
            return int(val, 8)
        except ValueError:
            pass
    elif val.startswith(("0b", "0B")):
        try:
            return int(val, 2)
        except ValueError:
            pass
    else:
        try:
            if "." not in val and "e" not in val.lower():
                return int(val)
        except ValueError:
            pass
    try:
        return float(val)
    except ValueError:
        pass

    return str(val)


def memoryview_to_str(mv: memoryview) -> str:
    if not mv:
        return ""
    return mv.tobytes().decode("utf-8")


@contextmanager
def capture_stderr_as_exception(
    exception_type: type[BaseException],
) -> Generator[None, None, None]:
    """
    Capture stderr as an exception. `ryml` prints errors directly to stderr,
    without a clear way (in Python at least) to capture them. This overrides
    the stderr file descriptor to a temporary file, and raises an exception
    with the captured contents. This override is more aggressive than the
    built-in `redirect_stderr` context manager because it needs to work down
    to the C level.
    """
    original_stderr_fd = os.dup(2)  # 2 is stderr
    temp_std_err_file = tempfile.TemporaryFile(mode="w+b")  # noqa: SIM115
    _ = os.dup2(temp_std_err_file.fileno(), 2)
    try:
        yield
    except Exception as e:
        _ = temp_std_err_file.seek(0)
        std_err_msg = temp_std_err_file.read().decode("utf-8").strip()
        raise exception_type(std_err_msg) from e
    finally:
        _ = os.dup2(original_stderr_fd, 2)
        os.close(original_stderr_fd)
        temp_std_err_file.close()
