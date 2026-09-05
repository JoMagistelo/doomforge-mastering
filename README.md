# DoomForge Mastering Studio

Mastering desktop **open-source** para grabaciones difíciles —especialmente conciertos capturados con teléfono— con interfaz Flet oscura/morada, preview A/B, referencia tonal, medición LUFS y control true-peak.

> DoomForge puede mejorar balance, nivel, ruido moderado y dinámica. No puede reconstruir perfectamente información destruida por clipping del micrófono, sobrecarga analógica, viento severo o compresión con pérdida extrema.

## Qué incluye

- Importación: WAV, FLAC, MP3, OGG, AIFF y, vía FFmpeg empaquetado por `imageio-ffmpeg`, M4A/AAC/WMA/OPUS/AC3/MP4 cuando el codec lo permite.
- Referencia: analiza loudness y 5 bandas espectrales y propone un match **limitado** (±3 dB por banda; -16 a -9 LUFS).
- Recovery: denoise espectral no estacionario + high-pass.
- Mastering: EQ musical de 5 zonas, compresor, saturación suave, width Mid/Side, normalización LUFS y limiter.
- Safety: medición de sample peak, true-peak 4x aproximado, crest factor y porcentaje de muestras al borde de clipping.
- Preview: genera un fragmento Original/Master y permite A/B antes del render completo.
- Exportación: WAV, FLAC, MP3, OGG, M4A y AAC.
- Presets: Phone Rescue / Live, Streaming Balanced, Doom / Heavy y Dynamic Archive.
- Tooltips discretos con icono de información junto a los parámetros.
- Tests y GitHub Actions.

## Stack abierto

- Flet: UI desktop.
- Spotify `pedalboard`: filtros, compresor y limiter (GPLv3).
- `pyloudnorm`: medición ITU-R BS.1770 (MIT).
- `noisereduce`: spectral gating (MIT).
- NumPy/SciPy para análisis y true-peak aproximado.

El proyecto se distribuye como **GPL-3.0-or-later** para mantener compatibilidad con `pedalboard`.

## Instalación rápida · Windows / VS Code

Recomendado: Python 3.12 o 3.13.

```powershell
git clone https://github.com/JoMagistelo/doomforge-mastering.git
cd doomforge-mastering
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python main.py
```

Si PowerShell bloquea la activación de la venv en tu sesión:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

También puedes ejecutar el entrypoint instalado:

```powershell
doomforge
```

## Si recibiste el ZIP

También puedes ejecutar `scripts\setup_windows.ps1` después de descomprimir.


```powershell
Expand-Archive .\doomforge-mastering.zip .\
cd .\doomforge-mastering
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .
python main.py
```

## Uso recomendado

1. Carga la pista.
2. Mira LUFS, true-peak, crest y clipping detectado.
3. Elige un preset conservador.
4. Carga una referencia parecida si quieres una brújula tonal.
5. Pulsa **Aplicar sugerencia** sólo si la referencia tiene sentido.
6. Ajusta parámetros con los tooltips de información.
7. Genera preview y compara **Original / Master / Ref**.
8. Si el A/B mejora sin perder pegada, renderiza WAV/FLAC para archivo o MP3/AAC para distribución.

## Targets orientativos

No son leyes:

- Archivo dinámico / live natural: -16 a -14 LUFS-I, -1.5 a -1 dBTP.
- Streaming equilibrado: alrededor de -14 a -12 LUFS-I, -1 dBTP.
- Rock/doom denso: -12 a -10 LUFS-I puede funcionar si el mix aguanta.
- Evita perseguir -8/-6 LUFS sólo porque una referencia comercial está muy limitada.

## Antes de DoomForge: REAPER

Lee [`docs/REAPER_PREP.md`](docs/REAPER_PREP.md). La idea es editar/restaurar en REAPER y dejar el mastering final a DoomForge.

## Publicarlo en tu GitHub

Consulta [`PUBLISH_TO_GITHUB.md`](PUBLISH_TO_GITHUB.md). Incluye los comandos con `gh repo create` y el clone posterior desde VS Code.

## Tests

```powershell
pip install -e ".[dev]"
pytest -q
```

## Notas de rendimiento

El denoise es la etapa más costosa. Para conciertos largos, úsalo sólo si hace una diferencia audible. El preview procesa sólo el fragmento elegido.

## Licencia

GPL-3.0-or-later. Consulta `LICENSE`.
