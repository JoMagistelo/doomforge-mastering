import pytest

pytest.importorskip("flet")
pytest.importorskip("flet_audio")


def test_ui_module_imports():
    import doomforge.ui.app  # noqa: F401
