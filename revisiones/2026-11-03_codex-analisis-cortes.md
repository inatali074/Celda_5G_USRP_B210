El análisis encuentra asociaciones útiles, pero **no demuestra todavía las causas de los cortes**. No encontré hallazgos bloqueantes; sí estos importantes. Las líneas citadas corresponden al análisis de Claude; las de logs, al archivo descomprimido.

1. **Importante — L5 y L21–25: “PUSCH vacío” y “el Redmi lo descarta” exceden la evidencia.**  
   **Verificado:** hay una asociación muy fuerte entre CSI aperiódico y CRC fallido con SINR negativa. **Inferido:** que el UE no transmitió. También podrían fallar la recepción del grant, la temporización, los DM-RS o el estimador. Incluso aparecen `crc=OK` con SINR negativa (`160139_gnb`, líneas 2319, 3321–3359). Corregir por “PUSCH no decodificado, con SINR estimada negativa”. `ack=2` es compatible con DTX, pero no pude verificar su codificación contra el tag: GitLab y el espejo no entregaron los archivos. DTX tampoco prueba ausencia física de transmisión.

2. **Importante — L8–19: la asociación con `clock_ppm` existe; el mecanismo físico queda abierto.**  
   Reproduje las tasas usando **Σ(`ta_cmd−31`) / segundos con algún PUSCH CRC OK**: `729/190=3,84`, `679/246=2,76`, `161/57=2,82` y `−6/50=−0,12`. El paso a μ=1 es correcto: **16·64·Tc/2 = 0,260417 µs**; equivalen a **+1,00; +0,719; +0,736 y −0,031 µs/s**. [TS 38.213 §4.2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/15.02.00_60/ts_138213v150200p.pdf).  
   Pero son comandos enviados, no ajustes confirmados, y el denominador excluye segundos sin éxito. Tampoco separa teléfonos. Corregir la presentación como *tasa de TA solicitado*. Que corregir solamente la portadora pueda producir desacople es plausible; que el UE derive necesariamente su temporización de esa corrección no está demostrado. Una deriva libre de 1,87 ppm sería 1,87 µs/s, distinta de estas tasas. La implementación de `clock_ppm` quedó sin verificar por falta de acceso al código.

3. **Importante — L22–24: falta definir el filtro de las cuentas.**  
   Con `zcat …160139_gnb.log.gz`, clasificando líneas `PUSCH:` por presencia de `csi1=`, CRC y signo de SINR, el archivo completo da:

   | | CRC OK | KO, SINR ≥0 | KO, SINR <0 |
   |---|---:|---:|---:|
   | Con CSI | 3 | 0 | 7136 |
   | Sin CSI | 4993 | 832 | 5317 |

   Los valores publicados requieren una ventana y una definición reproducible de “UE activo”. **Sí verifiqué** `0x4602 → ue=1 → ran_ue=1 → IMSI …004`: gNB `164854`, líneas 2462–2474; núcleo homónimo, 5290–5323. Sus **384 OK y 50 KO con SINR no negativa** coinciden, pero además hay **16 KO con SINR negativa**. La asociación SIM–modelo proviene del inventario, no del AMF.

4. **Importante — L12–17 y L31–32: se cuentan avisos repetidos como RLF independientes.**  
   Reproduje **38+14 avisos MAC**, con **5+7** eventos precedidos por fallos de tiempo real en ≤3 s. Sin embargo, contando `DU-MNG … RLF detected … Timer`, son **31+9 liberaciones iniciadas**, con **1+5** coincidencias. Corregir **12/52** por una métrica que identifique qué cuenta. La escasa coincidencia inmediata no permite concluir que el tiempo real sea “de segundo orden”: faltan ventanas respecto del inicio de la degradación y comparación contra períodos sin corte.

5. **Importante — L27–29: el disparo y la liberación están verificados; la explicación temporal necesita precisión.**  
   En `164854_gnb`, línea 36936, se declaran 100 HARQ-ACK KOs a **19:45:55,744922**; vuelve `ack=1` a **55,755282** y se pide liberar a **59,744845** (líneas 37018 y 73050). No hay que equiparar 100 KOs con 100 slots: un reporte puede llevar varios bits HARQ, y KO incluye NACK/DTX. Los tres parámetros están documentados, pero `pucch.max_consecutive_kos` corresponde a **CSI no decodificado en formato 2**. [Referencia srsRAN](https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html). Falta confirmar implementación y recuperación del contador en este tag.

6. **Importante — L19, L25 y L35: faltan controles y alternativas.**  
   Las corridas cambian duración, tráfico, cantidad de teléfonos y `tx_gain` —70/80/60/80 en las configuraciones embebidas—. Con ppm=0 todavía hay **250 PUSCH con CSI, CRC KO y SINR negativa**, ninguno OK: la anomalía CSI persiste. Además de incompatibilidad del Redmi, considerar grants perdidos por PDCCH, configuración UCI/DM-RS, potencia UL, saturación y errores de estimación. Tampoco alcanza SINR 15–25 dB para declarar “MCS demasiado alto”: hacen falta MCS, tasa de código y BLER de primeras transmisiones.

No edité archivos ni abrí secretos. La principal limitación pendiente es verificar el código exacto de `release_26_10`.
