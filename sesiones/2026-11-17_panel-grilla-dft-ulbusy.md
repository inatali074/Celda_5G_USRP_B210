# Sesiones 2026-11-13 y 2026-11-17: grilla en el panel, revisión del diagrama DFT-s-OFDM y causa de "UL processor is busy"

Celda en tachoPC con la opción 1 del menú (`gnb_b210_00101_n78_cpofdm.yml`). El 13/11 hubo dos corridas: una se trabó a las 12:35:50 UTC y la otra fue de 13:04 a 16:09 UTC. El 17/11 la red estuvo apagada: solo hubo análisis y documentación.

## Panel
- **Ping como consola** (commit `fa23bcd`): una línea por paquete, igual que en la terminal.
- **iperf3 como consola** (`319a48e`): salida de texto en vivo, con `--forceflush`, con la hora local en cada línea y la marca de si viene del servidor o del cliente. La caja de ping volvió a su tamaño original.
  - **Error de proceso:** la primera vez se reconstruyó la imagen sin recrear el contenedor, y el panel seguía mostrando la versión vieja. Desde ese día, cada cambio se verifica en el panel real antes de darlo por terminado.
- **Grilla de recursos, PRB por teléfono y FFT** (`a05e910`):
  - se leen las líneas `Slot decisions` del scheduler del gNB;
  - se dibujan los últimos 400 slots, con fondo según el patrón TDD, la subida rayada y las retransmisiones semitransparentes;
  - la tabla de conexiones suma las columnas PRB↓ y PRB↑;
  - la tarjeta de la celda muestra la frecuencia de muestreo y la FFT (768 puntos, 612 usados y 156 de guarda en n78), además del CP.
  - Se verificó reproduciendo líneas reales del scheduler: con un teléfono, ~8,5 Mbit/s de bajada asignados ocupan el 32 % de la grilla.
- **Corrección del CP del primer símbolo** (`e7a5536`): el extra de 16κ también escala con la FFT. Da 66 muestras en n78, no 60.

## Preguntas respondidas
- **Por qué hay 51 PRB y no 106:** 106 corresponde a 15 kHz. Con 30 kHz entran 51 en 20 MHz, y la cantidad de RE por ms es casi la misma (17 136 contra 17 808).
- **De dónde sale el CP:** TS 38.211 §5.3.1. El CP normal es 144κ·2^−μ·T_c, y suma 16κ en los símbolos l = 0 y l = 7·2^μ.
  - n78: 54 muestras (2,34 µs) y 66 en el primer símbolo.
  - n3: 108 muestras (4,69 µs).
  - Los valores son chicos porque el CP es ~7 % del símbolo, no 1/4.
- **Norma:** se bajó la **TS 38.211 V15.10.0 (Rel-15)**, que es la que fija la consigna, y se guardó en `referencias/` (excluida de git por `*.docx`). Se borró la Rel-18 que se había bajado antes. Las fórmulas de §4.1 y §5.3.1 son iguales en las dos versiones.

## Revisión del diagrama de un compañero (commit `cd9a584`)
- Original: `Diagrama_Visual_DFT_Mapeo_IFFT1536.html`, que no se modificó.
- Corregido: `Diagrama_Visual_DFT_Mapeo_IFFT_corregido.html`.
- Detalle de los errores, con su fuente: `Correcciones_Diagrama_DFT_IFFT.md`. Incluye un glosario de variables y siglas.
- **Errores principales:**
  - usaba un CP de 1/4 del símbolo, que es el CP extendido y en NR solo se permite con μ = 2;
  - usaba una FFT de 1536 a 30,72 MHz, que da 20 kHz y no 15;
  - el símbolo valía 1/SCS sin sumar el CP;
  - los slots de 0,933 y 0,467 ms deberían ser de 1 y 0,5 ms;
  - asignaba 106 PRB con DFT-s-OFDM, cuando TS 38.211 §6.3.1.4 pide 2^α2·3^α3·5^α5: el máximo es 100 en n3 y 50 en n78.
- **Sin verificar:** TS 38.214 §6.1.2.2 (asignación contigua de PRB) y los valores de PAPR, que se citan como típicos.

## "UL processor is busy" (P-004), evidencia `evidencia/09_ul_busy/` (commit `f9bf165`)
- **Las trabas:**
  - **12:35:50 UTC del 13/11:** se trabó el gNB y se perdió el plano de datos. No quedó en el log, porque el reinicio de las 13:04 lo pisó.
  - **Corrida de 13:04 a 16:09:** 329 440 fallas. Empiezan 36 s después del arranque, no se van más, y la tasa sube por escalones, de ~700 a ~5800 por minuto. El 49 % cae en el slot 19.
- **El volcado IQ no es la causa directa:** hubo minutos con 10 PUSCH y aun así ~740 fallas, y el volcado escribe en su propio hilo.
- **Causa encontrada en el código de OCUDU (commit e0db566, clon parcial de 13 MB en el scratchpad):**
  - hay 20 procesadores de subida, que se asignan por turno;
  - si un slot no recibe sus 14 símbolos (por ejemplo, porque la PHY inferior se realinea después de perder muestras), su procesador queda en "recibiendo" para siempre, porque no hay tiempo límite;
  - cada procesador trabado descarta 1 de cada 20 pedidos de subida.

  Eso explica que la falla persista, que al principio aparezca cada 100 ms (con ~2 pedidos por trama) y que crezca por escalones. **Descarta la hipótesis del PRACH pesado** (`zero_correlation_zone`): el slot 19 es simplemente el que tiene más pedidos.
- **`main_pool` tiene 1 solo hilo en tachoPC:** la cuenta da 5, pero el gNB deja 3 de las 4 CPU libres.
- **Se borró el volcado IQ** (5,2 GB) con la red apagada. Quedan 49 GB libres.

## Para retomar
- **Descartado por el usuario:** una configuración del gNB sin volcado IQ y con el log en `warning`. Se sigue usando la opción 1 del menú tal como está.
- **Prueba A/B/A en tachoPC con `expert_execution: threads: main_pool: nof_threads: 2`.**
- **Si aparece "UL processor is busy", reiniciar el gNB antes de medir:** no se recupera solo.
- **Descartado por el usuario:** informarle la falla a OCUDU.
- Revisión de Codex de `Correcciones_Diagrama_DFT_IFFT.md` y del HTML corregido.
- Verificar TS 38.214 §6.1.2.2. Siguen pendientes de antes la cita de E.212 y la tabla EDGE/LTE.
- Sigue lo pendiente del 12/11: calidad de la llamada SIP, VoNR etapa 2 y las opciones 2–4 del menú (postergadas).
