"""Import easyeditor without its multimodal, trainer and evaluation extras (engine v2).

``easyeditor/__init__.py`` imports every editor, trainer and multimodal model at import time, which
drags in timm, torchvision, fairscale, iopath, OpenCV, PyAV, qwen-vl-utils, sentence-transformers,
LLM-API clients and metric libraries.  ROME, MEMIT and AlphaEdit use none of them, and on an NGC
image installing the torchvision-based ones can make pip replace the image's CUDA build of torch.

``apply()`` registers a stand-in module for each optional dependency that is not installed.  A
stand-in satisfies import-time use (attribute access, subclassing, type annotations, ``X[...]``,
``X | Y``) but raises as soon as anything calls or instantiates it, so an edit path that really
needed one fails loudly instead of running a no-op.  Installed packages are never shadowed.
transformers is imported first so its package-availability flags reflect the real environment.
``stubbed()`` lists what was replaced; rt.deltas records it in every delta's provenance.
"""
import importlib.machinery
import importlib.util
import sys
import types

OPTIONAL = ("timm", "torchvision", "iopath", "fairscale", "cv2", "av", "qwen_vl_utils",
            "sentence_transformers", "higher", "omegaconf", "hydra", "zhipuai", "openai", "rouge",
            "nltk", "matplotlib", "peft", "einops", "PIL", "sklearn", "scipy", "pandas")
_STUBBED = []


class StubUsed(RuntimeError):
    """A stand-in for an uninstalled optional dependency was called."""


class _Meta(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _stand_in(f"{cls.__qualname__}.{name}")

    def __getitem__(cls, item):
        return cls

    def __or__(cls, other):
        return cls

    __ror__ = __or__

    def __iter__(cls):
        return iter(())

    def __call__(cls, *args, **kwargs):
        raise StubUsed(f"{cls.__qualname__} belongs to an optional dependency that is not installed "
                       "(vendor_patches.easyedit_lean_import); install it if this code path is needed")


_CLASSES = {}


def _stand_in(qualname):
    """One stand-in class per dotted name, so identity checks see the same object every time."""
    if qualname not in _CLASSES:
        _CLASSES[qualname] = _Meta(qualname.rsplit(".", 1)[-1], (),
                                   {"__qualname__": qualname, "__module__": "stub"})
    return _CLASSES[qualname]


class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        full = f"{self.__name__}.{name}"
        if full in sys.modules:
            return sys.modules[full]
        return _stand_in(full)


class _Finder:
    """Serves submodules of stubbed packages (``import timm.models.hub``)."""

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in _STUBBED and fullname not in sys.modules:
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None

    def create_module(self, spec):
        return _make_module(spec.name)

    def exec_module(self, module):
        return None


def _make_module(name):
    mod = _StubModule(name)
    mod.__path__ = []
    mod.__spec__ = importlib.machinery.ModuleSpec(name, None, is_package=True)
    mod.__file__ = None
    return mod


def _installed(name):
    if name in sys.modules:
        return sys.modules[name] is not None and not isinstance(sys.modules[name], _StubModule)
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def apply(names=OPTIONAL):
    """Stand in for every name in ``names`` that is not installed; returns the stubbed names."""
    import transformers  # noqa: F401  (freeze transformers' availability flags first)
    for name in names:
        if name not in _STUBBED and not _installed(name):
            sys.modules[name] = _make_module(name)
            _STUBBED.append(name)
    if _STUBBED and not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())
    return list(_STUBBED)


def stubbed():
    return list(_STUBBED)
