# oh-pro: force ensure_ascii=False globally for JSON serialization
# This prevents Unicode escapes like \u0412\u0435\u0440... for Cyrillic text
import json as _json

_orig_dumps = _json.dumps
_orig_dump = _json.dump


def _dumps(obj, *a, ensure_ascii=False, **kw):
    return _orig_dumps(obj, *a, ensure_ascii=ensure_ascii, **kw)


def _dump(obj, fp, *a, ensure_ascii=False, **kw):
    return _orig_dump(obj, fp, *a, ensure_ascii=ensure_ascii, **kw)


_json.dumps = _dumps
_json.dump = _dump


# oh-pro: decode \uXXXX Unicode escapes in LLM tool-call arguments
# LLMs (especially Claude) sometimes escape non-ASCII characters like
# Cyrillic as \u041f\u0440\u0438\u0432\u0435\u0442 in function call arguments.
# This round-trips the raw argument string through json.loads/dumps to
# convert them to proper Unicode before storing in conversation history.
def _oh_decode_unicode_args(raw_args: str) -> str:
    """Round-trip JSON string to convert \\uXXXX to proper Unicode."""
    if not isinstance(raw_args, str) or '\\u' not in raw_args:
        return raw_args
    try:
        parsed = _json.loads(raw_args)
        return _dumps(parsed)
    except _json.JSONDecodeError:
        return raw_args


# This is a namespace package - extend the path to include installed packages
# (We need to do this to support dependencies openhands-sdk, openhands-tools and openhands-agent-server
# which all have a top level `openhands`` package.)
__path__ = __import__('pkgutil').extend_path(__path__, __name__)


# Patch MessageToolCall to decode unicode in LLM tool-call arguments.
# Must happen AFTER namespace extension so openhands.sdk is importable.
def _oh_patch_message_tool_call():
    import openhands.sdk.llm.message as _msg_module

    _orig_from_chat = _msg_module.MessageToolCall.from_chat_tool_call
    _orig_from_resp = _msg_module.MessageToolCall.from_responses_function_call

    @classmethod  # type: ignore[arg-type]
    def _patched_from_chat(cls, tool_call):
        result = _orig_from_chat.__func__(cls, tool_call)
        result.arguments = _oh_decode_unicode_args(result.arguments)
        return result

    @classmethod  # type: ignore[arg-type]
    def _patched_from_resp(cls, item):
        result = _orig_from_resp.__func__(cls, item)
        result.arguments = _oh_decode_unicode_args(result.arguments)
        return result

    _msg_module.MessageToolCall.from_chat_tool_call = _patched_from_chat
    _msg_module.MessageToolCall.from_responses_function_call = _patched_from_resp


_oh_patch_message_tool_call()
del _oh_patch_message_tool_call


# oh-pro: auto-deploy skills on first import (no setup-skills.sh needed)
def _oh_setup_skills():
    """Copy oh-pro skills from repo skills/ → ~/.agents/skills/ on first run."""
    import shutil
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parent.parent
    src = repo_root / 'skills'
    dst = _Path.home() / '.agents' / 'skills'

    if not src.is_dir():
        return  # no oh-pro skills to deploy

    # Check if already deployed (compare count of .md files)
    src_count = len(list(src.glob('*.md')))
    dst_count = len(list(dst.glob('*.md'))) if dst.is_dir() else 0

    if dst_count >= src_count:
        return  # already up to date

    try:
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob('*.md'):
            shutil.copy2(f, dst / f.name)
    except Exception:
        pass  # silent fail — skills still work from repo dir for settings page


_oh_setup_skills()
del _oh_setup_skills

# Import version information for backward compatibility
from openhands.app_server.version import __version__, get_version

__all__ = ['__version__', 'get_version']
