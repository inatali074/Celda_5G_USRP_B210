# Sesión 0 (2026-10-30): configuración inicial

## Hecho
- Codex (0.166.0) y agy (1.4.8) responden "ok" en modo no interactivo con sesión iniciada.
- Entorno relevado sin modificar nada (ver `PROYECTO.md`).
- Creados `PROYECTO.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.gitignore`, las carpetas y el repo git local.
- El `CLAUDE.md` anterior se conservó completo como `CONTEXTO_ANTECEDENTES.local.md`, fuera de git porque contiene claves de SIM.

- Codex revisó la configuración (`revisiones/2026-10-30_configuracion-inicial.md`) y marcó tres incoherencias, ya corregidas: comprobación de claves, alcance de D-001 y política sobre `~/red5g`.

## Hallazgos
- `~/red5g` no existe en esta PC. El único antecedente disponible es el docx.
- La B210 no estaba conectada.

## Plan propuesto para la sesión 1 (sin transmitir)
1. El usuario define entorno de RF, celulares y entregable.
2. Gemini, consulta puntual: ¿una USIM sin DF_5GS ni servicios 5G impide 5G SA según TS 31.102 y TS 33.501? Bandas SA de los celulares elegidos.
3. Gemini, consulta puntual: tag o commit estable de OCUDU/srsRAN, imagen base para el gNB y Open5GS v2.8.0 en Docker, y acceso USB a la B210 desde el contenedor.
4. Claude decide banda, numerología y versiones (P-001, P-002) con justificación; Codex revisa.
5. Con el ok del usuario, Codex escribe los Dockerfile, el compose y los scripts; Claude los revisa; el usuario aprueba lo que use sudo.
6. Con el ok del usuario, construir los contenedores y verificar el núcleo y el gNB con ZMQ + srsUE, sin radio. Cierre con evidencia de registro y sesión PDU.
