from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from pedalboard.io import AudioFile


NATIVE_READ = {".wav", ".wave", ".flac", ".mp3", ".ogg", ".aif", ".aiff"}
NATIVE_WRITE = {".wav", ".flac", ".mp3", ".ogg", ".aif", ".aiff"}
SUPPORTED_IMPORT = sorted(NATIVE_READ | {".m4a", ".aac", ".wma", ".opus", ".ac3", ".mp4"})
SUPPORTED_EXPORT = [".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"]


def ffmpeg_executable() -> str:
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        system = shutil.which("ffmpeg")
        if system:
            return system
        raise RuntimeError("No se encontró FFmpeg ni el binario de imageio-ffmpeg.")


def _decode_with_ffmpeg(path: Path) -> Path:
    temp = Path(tempfile.mkstemp(prefix="doomforge_decode_", suffix=".wav")[1])
    cmd = [
        ffmpeg_executable(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(path), "-vn", "-c:a", "pcm_f32le", str(temp),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return temp


def read_audio(path: str | Path, *, start_s: float | None = None, duration_s: float | None = None) -> tuple[np.ndarray, int]:
    path = Path(path)
    decode_path = path
    temp: Path | None = None
    try:
        if path.suffix.lower() not in NATIVE_READ:
            temp = _decode_with_ffmpeg(path)
            decode_path = temp
        try:
            with AudioFile(str(decode_path)) as f:
                sr = int(f.samplerate)
                if start_s:
                    f.seek(int(max(0.0, start_s) * sr))
                frames = f.frames - f.tell()
                if duration_s is not None:
                    frames = min(frames, int(max(0.0, duration_s) * sr))
                audio = f.read(max(0, frames))
        except Exception:
            if temp is None:
                temp = _decode_with_ffmpeg(path)
                with AudioFile(str(temp)) as f:
                    sr = int(f.samplerate)
                    if start_s:
                        f.seek(int(max(0.0, start_s) * sr))
                    frames = f.frames - f.tell()
                    if duration_s is not None:
                        frames = min(frames, int(max(0.0, duration_s) * sr))
                    audio = f.read(max(0, frames))
            else:
                raise
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        return audio, sr
    finally:
        if temp and temp.exists():
            temp.unlink(missing_ok=True)


def audio_info(path: str | Path) -> tuple[int, int, float]:
    path = Path(path)
    decode_path = path
    temp: Path | None = None
    try:
        if path.suffix.lower() not in NATIVE_READ:
            temp = _decode_with_ffmpeg(path)
            decode_path = temp
        with AudioFile(str(decode_path)) as f:
            sr = int(f.samplerate)
            channels = int(f.num_channels)
            duration = float(f.frames) / sr if sr else 0.0
        return sr, channels, duration
    finally:
        if temp and temp.exists():
            temp.unlink(missing_ok=True)


def _write_native(path: Path, audio: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with AudioFile(str(path), "w", sr, audio.shape[0]) as f:
        f.write(np.asarray(audio, dtype=np.float32))


def write_audio(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXPORT:
        raise ValueError(f"Formato de exportación no soportado: {ext}")
    if ext in NATIVE_WRITE:
        _write_native(path, audio, sr)
        return path

    temp_wav = Path(tempfile.mkstemp(prefix="doomforge_encode_", suffix=".wav")[1])
    try:
        _write_native(temp_wav, audio, sr)
        codec_args = {
            ".m4a": ["-c:a", "aac", "-b:a", "256k"],
            ".aac": ["-c:a", "aac", "-b:a", "256k"],
        }[ext]
        cmd = [
            ffmpeg_executable(), "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(temp_wav), *codec_args, str(path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return path
    finally:
        temp_wav.unlink(missing_ok=True)


def write_preview_wav(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    path = Path(path)
    if path.suffix.lower() != ".wav":
        path = path.with_suffix(".wav")
    _write_native(path, audio, sr)
    return path
