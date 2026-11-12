Implementado el menú, las cuatro configuraciones y el EVM medido desde IQ. No inicié radio, Docker ni servicios del host.

Archivos creados en `config/gnb/`:

- `gnb_b210_00101_n78_cpofdm.yml`
- `gnb_b210_00101_n78_dfts.yml`
- `gnb_b210_00101_n3_cpofdm.yml`
- `gnb_b210_00101_n3_dfts.yml`

Archivos modificados:

- `start.sh`, `docker-compose.yml`, `README.md`
- `docker/dashboard/{iq.py,app.py,evm.html,README.md}`
- `docs/LEVANTAR_EN_OTRA_PC.md`

Borrados los siete solicitados, con prefijo `gnb_b210_00101_`: `csiper_ppm0_kos.yml`, `csiper_ppm0_kos_sinmetricas.yml`, `csiper_ppm0_kos_sinmetricas_dfts.yml`, `csiper_ppm0_kos_evm.yml`, `csiper_ppm0_kos_evm_iq.yml`, `n3_ppm0_kos.yml` y `n3_ppm0_kos_sinmetricas.yml`.

**El paso `git rm` quedó incompleto:** `.git` está montado en solo lectura. Los archivos están borrados del árbol de trabajo, pero las bajas no quedaron preparadas en el índice. Conservé los cambios previos ajenos a esta tarea.

Los diffs entre configuraciones muestran lo siguiente. Dentro de n78:

```diff
-# n78 TDD, subida CP-OFDM.
+# n78 TDD, subida DFT-s-OFDM.
-    enable_transform_precoding: false
+    enable_transform_precoding: true
```

Dentro de n3:

```diff
-# n3 FDD, subida CP-OFDM.
+# n3 FDD, subida DFT-s-OFDM. Nunca probada en el aire.
-    enable_transform_precoding: false
+    enable_transform_precoding: true
```

Entre n78 y n3, para ambas formas de onda, cambian la cabecera y estos parámetros:

```diff
-  dl_arfcn: 635000  # 3525 MHz; n78, raster de 30 kHz.
-  band: 78
+  dl_arfcn: 368500  # DL 1842,5 MHz, UL 1747,5 MHz, n3 FDD
+  band: 3
   channel_bandwidth_MHz: 20
-  common_scs: 30
+  common_scs: 15
   plmn: '00101'
   tac: 7
   pci: 1
+  pdcch:
+    common:
+      ss0_index: 0
+      coreset0_index: 12
+  prach:
+    prach_config_index: 1
```

La comparación de YAML también confirmó igualdad completa dentro de cada par al normalizar `enable_transform_precoding`.

Salida de `python3 -I docker/dashboard/iq.py --probar`:

```text
OK: n78 CP-OFDM N_sc=612 EVM=5.72% (esperado 5.62% ±0,5 pp)
OK: n78 DFT-s-OFDM N_sc=612 EVM=5.90% (esperado 5.62% ±0,5 pp)
OK: n3 CP-OFDM N_sc=1272 EVM=5.71% (esperado 5.62% ±0,5 pp)
OK: n3 DFT-s-OFDM N_sc=1272 EVM=5.80% (esperado 5.62% ±0,5 pp)
OK: búsqueda u=17/delta=1 y validación de grillas/slots
```

`bash -n start.sh`: sin salida, código **0**.

Salida de `START_SH_SOLO_ARGS=1 ./start.sh gnb_b210_00101_n3_dfts.yml`:

```text
GNB_CONFIG=gnb_b210_00101_n3_dfts.yml
origen=argumento
confirmado=no
```

También pasaron sintaxis Python, lectura de configuraciones, contrato `/api/evm` y agregación de energías por RNTI con timestamp, usando un ejecutor reemplazado en la prueba. La prueba con el ejecutor real no terminó en este entorno; queda pendiente la integración completa.

Confirmé en OCUDU las claves YAML utilizadas, el default `post_equalization` y DMRS con `u=n_rs_id%30`, `v=0`; el recorrido revisado usa PCI. Si la coherencia falla, IQ busca `u` y delta e informa la convención elegida. No quedaron claves utilizadas sin confirmar.

Limitaciones: DMRS DFT-s-OFDM con `M_ZC<36` y pi/2-BPSK se rechazan explícitamente. Falta contrastar con capturas reales; n3 DFT-s-OFDM sigue marcada como nunca probada en el aire.
