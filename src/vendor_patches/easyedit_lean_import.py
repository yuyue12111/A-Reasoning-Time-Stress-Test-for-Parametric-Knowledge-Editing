"""Import easyeditor without its multimodal, trainer and evaluation extras (engine v2).

``easyeditor/__init__.py`` imports every editor, trainer and multimodal model at import time, which
drags in timm, torchvision, fairscale, iopath, OpenCV, PyAV, qwen-vl-utils, sentence-transformers,
LLM-API clients and metric libraries.  ROME, MEMIT and AlphaEdit use none of them, and on an NGC
image installing the torchvision-based ones can make pip replace the image's CUDA build of torch.

``apply()`` imports easyeditor and stands in only for optional packages that its import chain
actually fails on.  Before any stand-in exists, transformers and (when installed) torchvision are
imported, and transformers' processor module is touched, so every installed package runs its own
optional-dependency probes against the real environment.  (A stand-in created first would make
``import av`` succeed inside torchvision, whose next call then hits the stand-in: that is how the
2026-09-28 platform check failed with "Could not import module 'AutoProcessor'".)

A stand-in satisfies import-time use (attribute access, subclassing, type annotations, ``X[...]``,
``X | Y``) but raises as soon as anything calls or instantiates it, so an edit path that really
needed one fails loudly instead of running a no-op.  Installed packages are never shadowed.
``stubbed()`` lists what was replaced; rt.deltas records it in every delta log header.
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


def _stub(name):
    sys.modules[name] = _make_module(name)
    _STUBBED.append(name)
    if not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.insert(0, _Finder())


def _prime():
    """Let installed packages run their optional-dependency probes before any stand-in exists."""
    import transformers
    for mod in ("torchvision",):
        if _installed(mod):
            try:
                importlib.import_module(mod)
            except Exception:  # noqa: BLE001 - a broken optional package is easyeditor's problem, not ours
                pass
    try:
        getattr(transformers, "AutoProcessor")
    except Exception:  # noqa: BLE001
        pass


def apply(names=OPTIONAL, target="easyeditor", max_rounds=64):
    """Import ``target``, standing in only for members of ``names`` its import fails on.

    Returns the stubbed names.  With ``target=None`` every missing name is stubbed eagerly (tests).
    Any other import failure is raised unchanged.
    """
    if target is None:
        for name in names:
            if name not in _STUBBED and not _installed(name):
                _stub(name)
        return list(_STUBBED)
    _prime()
    for _ in range(max_rounds):
        try:
            importlib.import_module(target)
            return list(_STUBBED)
        except ModuleNotFoundError as e:
            root = (e.name or "").split(".")[0]
            if root not in names or root in _STUBBED or _installed(root):
                raise
            _stub(root)
            for key in [k for k in sys.modules if k == target or k.startswith(target + ".")]:
                del sys.modules[key]
    raise RuntimeError(f"{target} still fails to import after {max_rounds} stand-ins")


def stubbed():
    return list(_STUBBED)
