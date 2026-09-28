"""The lean import stands in only for missing optional packages, and a stand-in fails loudly when used."""
import sys


def test_stand_in_imports_but_refuses_calls():
    from vendor_patches import easyedit_lean_import as L
    name = "zz_rt_optional_pkg"
    got = L.apply(names=(name,))
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
    L.apply(names=("json",))
    assert sys.modules["json"] is json and "json" not in L.stubbed()
