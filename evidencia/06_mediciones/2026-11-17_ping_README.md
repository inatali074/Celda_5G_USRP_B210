# Ping al Redmi (2026-11-17)

Celda n78 TDD, opción 1 del menú, recién arrancada. El Redmi estaba en "NR only", con IP 10.45.0.2. El ping se hizo desde el contenedor `dashboard`, que usa la red de `open5gs`: 60 paquetes cada 0,5 s, con `-W 2`. Los archivos `..._corrida{1,2,3}.txt` tienen la salida original y el contador de "UL processor is busy" del gNB antes y después de cada corrida.

| Corrida | Pérdida | Mín. | Mediana | p90 | Máx. | Jitter* |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 % | 9,7 ms | 25,1 ms | 34,8 ms | 121 ms | 13,9 ms |
| 2 | 0 % | 7,7 ms | 21,6 ms | 121 ms | 1297 ms | 62,3 ms |
| 3 | 25 % | 10,0 ms | 27,9 ms | 131 ms | 725 ms | 49,8 ms |

\* El jitter es la media de las diferencias entre RTT sucesivos.

- **"UL processor is busy"** se mantuvo en ~7 fallas por segundo durante las tres corridas: un procesador trabado desde el primer acceso (ver `evidencia/09_ul_busy/`).
- **Corrida 3:** perdió los paquetes 26 a 40, unos 7 s seguidos. Entre 18:49:11,7 y 18:49:17,4 UTC el gNB no recibió ningún PUSCH y casi no programó PDSCH. Los PUCCH llegaron con `sr=no`. No hubo RLF ni otros avisos, y la causa no se identificó.
