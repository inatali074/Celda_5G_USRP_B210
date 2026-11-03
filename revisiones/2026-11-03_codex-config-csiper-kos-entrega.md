Creado `config/gnb/gnb_b210_00101_csiper_ppm0_kos.yml`. YAML válido, una sola clave `cell_cfg.pucch` y único cambio funcional verificado. Ningún otro archivo modificado.

Diff contra el original:

```diff
-# Variante con CSI periodico por defecto de OCUDU.
+# Variante csiper_ppm0 con pucch.max_consecutive_kos alto.
```

```diff
   # CSI por defecto de OCUDU: CSI-RS (incluye TRS) y reportes periodicos por PUCCH formato 2.
+  # Prueba 2026-11-03: el Redmi no envia CSI por PUCCH F2; umbral alto para que el CSI faltante no dispare RLF (OCUDU: configure_cli11_pucch_args).
+  pucch:
+    max_consecutive_kos: 100000
   pusch:
```
