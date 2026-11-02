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
