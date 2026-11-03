# Etapa 4 y 5: sesión PDU y tráfico IP (2026-11-02)

**Estado: lograda, pero inestable. Sin mediciones todavía.**

## Qué confirma
- Sesión PDU por DNN `Metodos1` (S-NSSAI SST 1): `UE SUPI[imsi-001010000000003] DNN[Metodos1] IPv4[10.45.0.2]` en el log del núcleo.
- Tráfico IP real: contadores de `ogstun` con 2,29 MB de bajada y 0,48 MB de subida en la primera corrida, y la regla `MASQUERADE` con 110 paquetes. El usuario confirmó navegación.

## Qué no confirma
La conexión se corta: RLF por CRC y HARQ-ACK consecutivos, y reestablecimientos RRC. Es una prueba con PLMN 001/01, no 722/999 (ver D-008 en `PROYECTO.md`), y sin DFT-s-OFDM ni NEA2 validados por separado.

## Archivos
- `2026-11-02_*_00101_sincsi_tx70.*`: primera navegación (sin CSI, tx 70).
- `2026-11-02_*_00101_sincsi_tx80.*`: corrida con más potencia, sin CSI.
- `../03_registro/2026-11-02_*_00101_rlf_csi.log`: primer registro con 001/01, corte a los 3 s por CSI.

Los logs del gNB están comprimidos con gzip. Identificadores de terceros anonimizados en los logs del núcleo.

## 2026-11-03: corte de los 60 s y estabilidad con `NR only`
**Qué confirma:**
- **El corte de ~60 s lo inicia el teléfono, por la voz.** En `2026-11-03_redmi_logcat_radio_extracto.log`, el módem pasa a "sin servicio" (`+CIEV: 3,0`) y a RRC idle (`+CSCON: 0`) a los 60,00 ± 0,02 s de obtener servicio (`+CIEV: 3,1`). Después escanea LTE (`+EPHYCONFIG: 4,...`). En los logs del gNB y del núcleo no hay ningún mensaje en ese momento.
- **Con `NR only`** (`*_n3_nronly*` y `*_tdd_nronly*`), el Redmi quedó conectado más de 5 min en n3 y en n78.
- **n3 FDD funciona** (`*_n3_volte_*`). Ver D-015 en `PROYECTO.md` y `sesiones/2026-11-03_cortes-60s-volte.md`.

**Qué no confirma:** que el mecanismo interno sea exactamente un temporizador de registro IMS. El MDLog no se pudo decodificar, y es la explicación más consistente, no una lectura directa. Tampoco hay mediciones de throughput todavía.

**Archivos** (`2026-11-03_*`):
- `gnb_eventos_<corrida>.log` y `nucleo_<corrida>.log`: extractos (UE, RRC, RLF, registro, DNN y paging), con el conteo de PRACH y de fallas de tiempo real en la cabecera. Corridas:
  - `n3_volte_1`, `_2_logcat` y `_3_mdlog`: n3 con VoLTE;
  - `n3_sin_volte`;
  - `n3_nronly`: termina con el procesador de UL trabado;
  - `tdd_nronly`.
- `gnb_tdd_nronly_completo.log.gz`: log completo del gNB de la corrida estable en n78.
- `redmi_logcat_radio_extracto.log`: líneas AT de radio del Redmi (19:52-19:57 y 20:07-20:10 UTC). El reloj del teléfono iba ~0,9 s atrasado respecto de la PC de Santi.

Solo aparecen las SIM de laboratorio (…003 y …004).
