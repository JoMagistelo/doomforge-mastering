from doomforge.audio.io import _new_temp_wav


def test_temp_wav_handle_is_closed_and_path_is_reusable():
    path = _new_temp_wav("doomforge_test_")
    try:
        # This specifically catches the Windows failure mode where mkstemp's
        # descriptor remained open and external processes could not reopen it.
        path.write_bytes(b"RIFF")
        assert path.read_bytes() == b"RIFF"
    finally:
        path.unlink(missing_ok=True)
    assert not path.exists()
