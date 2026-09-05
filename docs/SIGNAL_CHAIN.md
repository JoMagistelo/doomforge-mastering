# Cadena DSP de DoomForge

1. Input gain
2. Denoise espectral no estacionario (opcional)
3. High-pass
4. EQ de 5 zonas: low shelf / low-mid / mid / presence / air shelf
5. Compresor broadband de glue
6. Saturación suave en paralelo
7. Ajuste Mid/Side de stereo width
8. Normalización hacia target LUFS (con límite de ganancia)
9. Limiter
10. Medición oversampled de true-peak y safety trim final

## Filosofía

- No intenta inventar detalle que nunca fue capturado por el micrófono.
- El modo Reference Match limita cambios para evitar copiar mastering agresivo o diferencias de arreglo.
- True-peak tiene prioridad sobre perseguir exactamente el LUFS objetivo.
- Los presets son puntos de partida, no recetas universales.
