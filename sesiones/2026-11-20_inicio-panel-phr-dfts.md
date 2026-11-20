# Sesión 2026-11-20: inicio de la celda desde el panel y PHR con DFT-s-OFDM

## Inicio desde el panel (D-022)
- Pedido del profesor: iniciar y cambiar la configuración sin la terminal.
- Ícono "Celda 5G" (`scripts/instalar_lanzador.sh`) → `scripts/lanzador.sh` (governor, núcleo y panel sin radio) → `scripts/control_red.py` en el host, solo en 127.0.0.1:8090, con 4 opciones fijas o frenar.
- Revisión de Codex (`revisiones/2026-11-20_codex-inicio-desde-panel.md`): 2 críticos y 7 altos, todos aplicados salvo la credencial por sesión (riesgo aceptado).
- Prueba real: reinicio de opción 1 a 2, frenar y cierre del lanzador con Ctrl-C. Al cerrar, Open5GS salió con 139 y Compose dejó MongoDB andando: `stop.sh` ahora detiene los servicios de a uno.
- Guía de la consola del gNB en el `README`.

## PHR con DFT-s-OFDM
- Primer intento (13:50 UTC) con el gNB degradado: ~93 UL busy por segundo, subida de 0,2–3 Mbit/s, buffer del teléfono casi vacío. Descartado.
- Segundo intento con el gNB recién reiniciado desde el panel (13:54:36–13:54:58 UTC): buffer lleno, PHR negativo en todas las filas (mediana −7 dB), SINR 24,3 dB, MCS 23, 11,8 Mbit/s, BLER 40 %, ~21 UL busy por segundo.
- Contra CP-OFDM del 17/11 (mismo criterio): SINR 21,9 dB, 13,1 Mbit/s, BLER 32 %, PHR mediana 1 dB.
- Conclusión: el UE queda en P_CMAX con las dos formas de onda; la SINR algo mayor con DFT-s-OFDM va en el sentido de la MPR (TS 38.101-1 tabla 6.2.2-1) pero está dentro de la variabilidad, y la tasa no mejora. Informe §9.5, párrafo 28 y conclusiones actualizados (49 páginas).
- Evidencia: `evidencia/06_mediciones/2026-11-20_iperf_ul_phr_dfts.txt`.
