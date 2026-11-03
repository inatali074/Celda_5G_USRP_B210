Modifiqué únicamente `start.sh`. `bash -n`, `git diff --check` y 10 pruebas del parseo aislado pasaron. Shellcheck no está instalado. No ejecuté `start.sh`, Docker ni sudo.

El diff incorpora:

```diff
-# Uso: ./start.sh
+# Uso: ./start.sh [ARCHIVO_GNB.yml] [--confirmado] (en cualquier orden).
+# Acepta también config/gnb/ARCHIVO_GNB.yml. Prioridad: argumento > GNB_CONFIG > defecto.
```

- Función `parsear_argumentos`: acepta ambos órdenes, normaliza `config/gnb/X.yml`, rechaza argumentos desconocidos y archivos múltiples, y avisa cuando el argumento reemplaza la variable.
- `START_SH_SOLO_ARGS=1`: imprime elección, origen y confirmación, y sale antes de los chequeos.
- Antes de confirmar, muestra archivo, origen, `dl_arfcn`, `tx_gain`, PLMN y `clock_ppm`.
- Inmediatamente después del arranque, compara los montajes de `docker inspect` con el archivo elegido; ante discrepancia o fallo de inspección, informa, detiene `gnb-radio` y sale con error.

La confirmación `si`, governor, espera de Open5GS y screen permanecen intactos. El diff completo está disponible con `git diff -- start.sh`.
