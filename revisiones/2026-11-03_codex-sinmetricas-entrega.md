Creados en `config/gnb/`:

- `gnb_b210_00101_csiper_ppm0_kos_sinmetricas.yml`
- `gnb_b210_00101_n3_ppm0_kos_sinmetricas.yml`

Ambos incluyen el comentario pedido y eliminan los bloques completos `remote_control` y `metrics`. YAML parseado correctamente con PyYAML.

Comparados mediante `git show 981c456:...`: ignorando el comentario nuevo, solo difieren por una línea vacía y el comentario preexistente `# Monitoreo interno de la red ran; no publica el control remoto al host.`, conservados para respetar el resto del original. La configuración coincide.

No modifiqué otros archivos ni ejecuté Docker o transmisiones.
