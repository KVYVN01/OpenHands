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

# This is a namespace package - extend the path to include installed packages
# (We need to do this to support dependencies openhands-sdk, openhands-tools and openhands-agent-server
# which all have a top level `openhands`` package.)
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Import version information for backward compatibility
from openhands.app_server.version import __version__, get_version

__all__ = ['__version__', 'get_version']
