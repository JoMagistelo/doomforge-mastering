from __future__ import annotations

import gc
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from pedalboard.io import AudioFile

NATIVE_READ = {'.wav', '.wave', '.flac', '.mp3', '.ogg', '.aif', '.aiff'}
NATIVE_WRITE = {'.wav', '.flac', '.mp3', '.ogg', '.aif', '.aiff'}
SUPPORTED_IMPORT = sorted(NATIVE_READ | {'.m4a', '.aac', '.wma', '.opus', '.ac3', '.mp4'})
SUPPORTED_EXPORT = ['.wav', '.flac', '.mp3', '.ogg', '.m4a', '.aac']


def ffmpeg_executable() -> str:
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        system = shutil.which('ffmpeg')
        if system:
            return system
        raise RuntimeError('No se encontró FFmpeg ni el binario de imageio-ffmpeg.')


def _temp_output_path(prefix: str, suffix: str = '.wav') -> Path:
    """Return a unique non-existent path inside a private temp directory.

    On Windows, pre-creating the destination with NamedTemporaryFile/mkstemp can
    race with AV/indexers or native audio libraries and lead to WinError 32.
    FFmpeg is happiest when it creates the output file itself.
    """
    directory = Path(tempfile.mkdtemp(prefix=f'{prefix}dir_'))
    return directory / f'{prefix}{suffix}'


def _cleanup_temp(path: Path, retries: int = 8, delay_s: float = 0.08) -> None:
    """Best-effort cleanup that tolerates delayed native handle release on Windows."""
    parent = path.parent
    for attempt in range(retries):
        try:
            if path.exists():
                path.unlink()
            if parent.exists() and parent.name.startswith(('doomforge_decode_dir_', 'doomforge_encode_dir_')):
                parent.rmdir()
            return
        except (PermissionError, OSError):
            gc.collect()
            if attempt < retries - 1:
                time.sleep(delay_s * (attempt + 1))
    # Temp cleanup must never turn a successful decode/render into an app error.


def _run_ffmpeg(cmd: list[str], *, operation: str) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or '').strip()
        if detail:
            raise RuntimeError(f'FFmpeg no pudo {operation}: {detail}') from exc
        raise RuntimeError(f'FFmpeg no pudo {operation} (código {exc.returncode}).') from exc


def _decode_with_ffmpeg(path: Path) -> Path:
    temp = _temp_output_path('doomforge_decode_')
    cmd = [
        ffmpeg_executable(), '-y', '-hide_banner', '-loglevel', 'error',
        '-i', str(path), '-vn', '-c:a', 'pcm_f32le', str(temp),
    ]
    try:
        _run_ffmpeg(cmd, operation=f'decodificar {path.name}')
        return temp
    except Exception:
        _cleanup_temp(temp)
        raise


def _read_from_audiofile(
    decode_path: Path,
    *,
    start_s: float | None,
    duration_s: float | None,
) -> tuple[np.ndarray, int]:
    with AudioFile(str(decode_path)) as f:
        sr = int(f.samplerate)
        if start_s:
            f.seek(int(max(0.0, start_s) * sr))
        frames = f.frames - f.tell()
        if duration_s is not None:
            frames = min(frames, int(max(0.0, duration_s) * sr))
        audio = f.read(max(0, frames))
    return np.array(audio, dtype=np.float32, copy=True), sr


def read_audio(
    path: str | Path,
    *,
    start_s: float | None = None,
    duration_s: float | None = None,
) -> tuple[np.ndarray, int]:
    path = Path(path)
    temp: Path | None = None
    try:
        decode_path = path
        if path.suffix.lower() not in NATIVE_READ:
            temp = _decode_with_ffmpeg(path)
            decode_path = temp
        try:
            audio, sr = _read_from_audiofile(decode_path, start_s=start_s, duration_s=duration_s)
        except Exception:
            if temp is not None:
                raise
            temp = _decode_with_ffmpeg(path)
            audio, sr = _read_from_audiofile(temp, start_s=start_s, duration_s=duration_s)
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        return audio, sr
    finally:
        if temp is not None:
            _cleanup_temp(temp)


def audio_info(path: str | Path) -> tuple[int, int, float]:
    path = Path(path)
    temp: Path | None = None
    try:
        decode_path = path
        if path.suffix.lower() not in NATIVE_READ:
            temp = _decode_with_ffmpeg(path)
            decode_path = temp
        with AudioFile(str(decode_path)) as f:
            sr = int(f.samplerate)
            channels = int(f.num_channels)
            frames = int(f.frames)
        return sr, channels, float(frames) / sr if sr else 0.0
    finally:
        if temp is not None:
            _cleanup_temp(temp)


def _write_native(path: Path, audio: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with AudioFile(str(path), 'w', sr, audio.shape[0]) as f:
        f.write(np.asarray(audio, dtype=np.float32))


def write_audio(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXPORT:
        raise ValueError(f'Formato de exportación no soportado: {ext}')
    if ext in NATIVE_WRITE:
        _write_native(path, audio, sr)
        return path

    temp_wav = _temp_output_path('doomforge_encode_')
    try:
        _write_native(temp_wav, audio, sr)
        codec_args = {
            '.m4a': ['-c:a', 'aac', '-b:a', '256k'],
            '.aac': ['-c:a', 'aac', '-b:a', '256k'],
        }[ext]
        _run_ffmpeg([
            ffmpeg_executable(), '-y', '-hide_banner', '-loglevel', 'error',
            '-i', str(temp_wav), *codec_args, str(path),
        ], operation=f'codificar {path.name}')
        return path
    finally:
        _cleanup_temp(temp_wav)


def write_preview_wav(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    path = Path(path)
    if path.suffix.lower() != '.wav':
        path = path.with_suffix('.wav')
    _write_native(path, audio, sr)
    return path
