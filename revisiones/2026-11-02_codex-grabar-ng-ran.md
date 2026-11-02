Encontré **cuatro problemas importantes y uno menor**. No edité archivos, no abrí secretos ni `*.local.*`, y no accedí al lector. Las pruebas puras incluidas pasan; también reproduje con respuestas simuladas el fallo de `61xx` encadenados.

1. **Importante — consulta ADM sin garantía específica para LY14.** [grabar_ng_ran.py:139](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/grabar_ng_ran.py:139), llamada en línea 201.
   
   §11.1.9.1.2 define VERIFY vacío como consulta del contador **de PIN**, sin presentar una clave incorrecta. Por eso, **P3=0 no implica por sí mismo gastar un intento**. Pero esa cita no demuestra que la implementación administrativa LY14 en `0x0C` respete esa semántica. El script lo afirma incondicionalmente y lo ejecuta incluso sin `--escribir`, antes de conocer el contador.
   
   **Corrección:** exigir evidencia del fabricante o una validación previa documentada para esa referencia; hasta entonces, excluir esa consulta del modo de inspección. No afirmo que la LY14 efectivamente descuente: es una garantía pendiente. [TS 102 221, alcance y §11.1.9](https://www.etsi.org/deliver/etsi_ts/102200_102299/102221/15.01.00_60/ts_102221v150100p.pdf).

2. **Importante — manejo incompleto de `61xx`/`6Cxx`, relevante para T=0.** [grabar_ng_ran.py:105](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/grabar_ng_ran.py:105).
   
   Solo admite una corrección `6Cxx` y un GET RESPONSE. Si GET RESPONSE devuelve `6Cxx`, no lo corrige; si devuelve otro `61xx`, no continúa. Además reemplaza los datos anteriores en vez de concatenarlos. Puede abortar durante una selección o relectura, incluso después de escrituras anteriores. Es el mismo defecto que [leer_sim.py:23](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/leer_sim.py:23).
   
   **Corrección:** bucle acotado que acumule datos y corrija el Le del comando que recibió `6Cxx`. Mantener VERIFY y UPDATE fuera de reintentos automáticos. El encadenamiento está contemplado expresamente para T=0 en anexo C.1.6. [TS 102 221](https://www.etsi.org/deliver/etsi_ts/102200_102299/102221/15.01.00_60/ts_102221v150100p.pdf).

3. **Importante — continúa escribiendo después de verificar una discrepancia.** [grabar_ng_ran.py:228](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/grabar_ng_ran.py:228).
   
   Una relectura incorrecta solo incrementa `fallas`; continúa con los otros archivos y puede limpiar estados aunque las listas hayan quedado mal. Contradice “un fallo corta la ejecución”.
   
   **Corrección:** cortar inmediatamente ante la primera discrepancia, informar qué escrituras ya se realizaron y conservar la copia. Evitar restauraciones automáticas sin diagnóstico.

4. **Importante — controles de seguridad implementados con `assert`.** [grabar_ng_ran.py:149](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/grabar_ng_ran.py:149), también líneas 85–88, 101 y 126–135.
   
   Con `python -O` desaparece el control del SELECT previo al UPDATE: si falla la selección, puede escribirse sobre el EF que siga seleccionado. Además desaparecen directamente las llamadas de inicialización contenidas en `assert`. `-I` no impide agregar `-O`.
   
   **Corrección:** llamadas y comprobaciones explícitas con excepciones; ninguna precondición de escritura debe depender de `assert`.

5. **Menor — referencia normativa incompleta.** [grabar_ng_ran.py:11](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/grabar_ng_ran.py:11).
   
   `§4.2.5x` no identifica una sección. Debe decir **§4.2.53** para OPLMNwAcT; §4.2.5 y §4.2.54 corresponden a PLMNwAcT y HPLMNwAcT. Para los estados conviene agregar §4.2.17, §4.2.23 y §4.2.91. [TS 31.102 v15.7.0](https://www.etsi.org/deliver/etsi_ts/131100_131199/131102/15.07.00_60/ts_131102v150700p.pdf).

**Verificado sin errores:** `279299` representa 722/999; las entradas son de cinco bytes; `i+3` apunta al primer byte AcT y `40→48` agrega b4 conservando E-UTRAN. Los FID y offsets cero-based **10, 13 y 17** son correctos; `01` representa “not updated”. UPDATE usa `Lc=1` y direccionamiento por offset correcto. [TS 31.102 v15.7.0](https://www.etsi.org/deliver/etsi_ts/131100_131199/131102/15.07.00_60/ts_131102v150700p.pdf).

El código presenta la clave una sola vez en `0x0C`, sin reintentar, y nunca usa `0x0A` como referencia VERIFY. Los **10 intentos iniciales** son un dato aportado por vos; no están comprobados por esta revisión. Las transformaciones de estados son deliberadamente condicionales: únicamente `03→01`, `03→01` y `02→01`, respectivamente.
