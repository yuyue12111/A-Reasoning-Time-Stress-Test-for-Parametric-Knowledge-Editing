"""The lean import stands in only for missing optional packages, and a stand-in fails loudly when used."""
import sys


def test_stand_in_imports_but_refuses_calls():
    from vendor_patches import easyedit_lean_import as L
    name = "zz_rt_optional_pkg"
    got = L.apply(names=(name,), target=None)
    assert name in got
    import zz_rt_optional_pkg
    import zz_rt_optional_pkg.sub.deeper as deep          # submodules of a stubbed package resolve
    cls = zz_rt_optional_pkg.Model

    class Child(cls):                                       # subclassing works at import time
        pass
    assert zz_rt_optional_pkg.Model[int] is cls and (cls | None) is cls
    for thing in (cls, deep.helper, Child):
        try:
            thing()
        except L.StubUsed:
            continue
        raise AssertionError(f"{thing} must refuse to be called")


def test_installed_packages_are_never_shadowed():
    from vendor_patches import easyedit_lean_import as L
    import json
    L.apply(names=("json",), target=None)
    assert sys.modules["json"] is json and "json" not in L.stubbed()


def test_stand_ins_only_where_the_target_import_fails():
    """A missing optional module is stubbed only if the target's own import chain needs it, and an
    installed package that probes the same module first keeps seeing the real environment."""
    import os, tempfile
    from vendor_patches import easyedit_lean_import as L
    with tempfile.TemporaryDirectory() as d:
        pkg = os.path.join(d, "zz_rt_target")
        os.makedirs(pkg)
        with open(os.path.join(pkg, "__init__.py"), "w") as fh:
            fh.write("import zz_rt_needed_optional\nVALUE = 1\n")
        sys.path.insert(0, d)
        try:
            got = L.apply(names=("zz_rt_needed_optional", "zz_rt_unneeded_optional"), target="zz_rt_target")
            import zz_rt_target
            assert zz_rt_target.VALUE == 1
            assert "zz_rt_needed_optional" in got and "zz_rt_unneeded_optional" not in got
        finally:
            sys.path.remove(d)


def test_non_optional_failures_are_raised():
    import os, tempfile
    from vendor_patches import easyedit_lean_import as L
    with tempfile.TemporaryDirectory() as d:
        pkg = os.path.join(d, "zz_rt_target2")
        os.makedirs(pkg)
        with open(os.path.join(pkg, "__init__.py"), "w") as fh:
            fh.write("import zz_rt_required_dependency\n")
        sys.path.insert(0, d)
        try:
            L.apply(names=("something_else",), target="zz_rt_target2")
        except ModuleNotFoundError as e:
            assert e.name == "zz_rt_required_dependency"
            return
        finally:
            sys.path.remove(d)
    raise AssertionError("a missing required dependency must be raised, not stubbed")
