from pathlib import Path

from doomforge.audio.io import _cleanup_temp, _temp_output_path


def test_temp_output_path_is_not_precreated():
    path = _temp_output_path('doomforge_decode_')
    try:
        assert isinstance(path, Path)
        assert not path.exists()
        assert path.parent.exists()
    finally:
        _cleanup_temp(path)


def test_cleanup_does_not_raise_when_file_is_already_gone():
    path = _temp_output_path('doomforge_encode_')
    _cleanup_temp(path)
    _cleanup_temp(path)
