# Preparación recomendada en REAPER antes de DoomForge

La meta no es “masterizar dos veces”. En REAPER haz **restauración y edición**, dejando a DoomForge la tonalidad global, compresión de glue, loudness y true-peak.

## Flujo recomendado para una toma de concierto hecha con teléfono

1. **Duplica y conserva el original.** Trabaja en un proyecto a 48 kHz y, si puedes, exporta el premaster como WAV 32-bit float.
2. **No normalices a 0 dBFS.** Ajusta item/track gain para que los picos difíciles queden aproximadamente entre -6 y -3 dBFS. Si el teléfono ya clippeó, bajar gain evita nuevos clips pero no recupera la forma de onda perdida.
3. **Limpia golpes y viento con ReaEQ.** Empieza con high-pass de 25–35 Hz. En doom/stoner evita 50–80 Hz salvo que el subgrave sea realmente ruido: puedes quitar el peso del bajo y bombo.
4. **Corrige problemas, no “sonido bonito” todavía.** Busca resonancias muy obvias: 150–350 Hz puede embarrar; 2.5–4.5 kHz puede doler si el micrófono del teléfono saturó. Prefiere cortes de 1–3 dB antes que boosts grandes.
5. **Denoise sólo si hay un ruido estable.** Con ReaFIR en modo subtract, toma una muestra de ruido/ambiente sin música y reduce poco. Si aparecen sonidos acuosos/metálicos, retrocede. El público y la reverberación del recinto son parte del concierto, no “ruido” automáticamente.
6. **Automatiza picos puntuales.** Un grito al lado del teléfono o golpe aislado se arregla mejor con item gain/automation que aplastando toda la canción con un compresor.
7. **Revisa fase/estéreo.** Si al pasar a mono desaparecen guitarras o bajo, no ensanches más. Corrige primero el problema de fase.
8. **No pongas limiter final en REAPER.** Si necesitas uno sólo para escuchar, desactívalo antes de exportar el premaster.
9. **Exporta sin pérdida.** WAV 32-bit float (ideal para seguir procesando) o 24-bit. Mantén el sample rate original cuando sea razonable; no conviertas repetidamente.
10. **Usa una referencia justa.** Para una toma de público, una buena grabación live del mismo estilo suele ser mejor brújula que un álbum de estudio hiperproducido.

## Señales de que debes volver a REAPER

- Hay clips/chasquidos puntuales que puedes editar manualmente.
- El volumen cambia muchísimo entre secciones por distancia del teléfono.
- Hay una resonancia fija del recinto muy marcada.
- Un lado está claramente más alto o con fallas.
- Hay silencios/ruidos al inicio o final que no quieres conservar.
