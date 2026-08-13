from PyQtInspect._pqi_bundle.monkey_qt.metadata import (
    PatchMark,
    SuppressPatchMark,
)


def test_patch_mark_subclass_only_defines_mark_name():
    class CustomPatchMark(PatchMark):
        _mark = '_custom_patch_mark'

    class Target:
        pass

    with CustomPatchMark.marked(Target):
        assert CustomPatchMark.is_marked(Target)
        assert not SuppressPatchMark.is_marked(Target)

    assert not CustomPatchMark.is_marked(Target)


def test_suppressed_restores_an_existing_mark():
    class Base:
        pass

    class Child(Base):
        pass

    target = Child()
    SuppressPatchMark.mark(Base)
    try:
        with SuppressPatchMark.marked(target):
            assert SuppressPatchMark.is_marked(target)

        assert SuppressPatchMark.is_marked(target)
    finally:
        SuppressPatchMark.unmark(Base)


def test_suppressed_removes_a_temporary_mark():
    class Target:
        pass

    with SuppressPatchMark.marked(Target):
        assert SuppressPatchMark.is_marked(Target)

    assert not SuppressPatchMark.is_marked(Target)
