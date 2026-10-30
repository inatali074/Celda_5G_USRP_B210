Encontré tres problemas de coherencia. No modifiqué archivos ni abrí `*.local.*` o `config/secretos/`.

1. **Importante — [AGENTS.md:7](AGENTS.md:7) y [AGENTS.md:16](AGENTS.md:16): verificación de claves imposible con el acceso permitido.** Se exige comprobar que las claves del núcleo coincidan con las de la tarjeta, pero se prohíbe leer los archivos donde deben guardarse. Codex no puede certificar esa coincidencia directamente. **Corrección:** asignar esa comprobación al usuario mediante un procedimiento local que informe únicamente coincidencia o diferencia; Codex revisa el procedimiento y su resultado sin acceder a las claves.

2. **Importante — [.gitignore:7](.gitignore:7), frente a [PROYECTO.md:44](PROYECTO.md:44): el material previo no queda completamente excluido.** `git status --short --ignored` muestra como `??` estos archivos de la raíz:
   
   - `DFT-s-OFDM_explicacion.html`
   - `Diagramas_UL_DL_Paging_5G.html`
   - `Diagramas_UL_DL_Paging_5G.md`
   - `generar_html.py`

   Un `git add .` los incorporaría, aunque D-001 dice que se versiona lo nuevo y se excluye el material previo. **Corrección:** excluirlos explícitamente o registrar cuáles se decide incorporar como excepción. **No detecté claves de SIM en ellos.**

3. **Menor — [AGENTS.md:15](AGENTS.md:15), frente a [PROYECTO.md:12](PROYECTO.md:12): distinto permiso para reutilizar antecedentes.** AGENTS permite copiar valores de `~/red5g` con justificación; PROYECTO establece que no se reutiliza nada. Si se obtiene acceso a ese directorio, justificar una copia cumpliría una regla y violaría la otra. **Corrección:** definir una única política y reflejarla en ambos archivos.

Verifiqué además:

- **Comandos:** las opciones documentadas de `codex exec` y `agy` están presentes en sus ayudas locales; no encontré errores de sintaxis demostrables. La ayuda por sí sola no acredita que las consultas funcionen ni cómo aplican todas las restricciones.
- **Secretos y Git:** `.env` y `CONTEXTO_ANTECEDENTES.local.md` aparecen como ignorados (`!!`). `git ls-files` no devuelve archivos rastreados.
- **Archivos incorporables:** no detecté literales hexadecimales de 32 caracteres ni asignaciones evidentes de Ki, OPc o ADM en los archivos no ignorados. Es una comprobación por patrones, no una garantía de ausencia de secretos con otros formatos.
- **Configuración de red:** todavía no hay configuraciones efectivas de gNB o núcleo para contrastar PLMN, TAC, slices, N2/N3 o parámetros radio. Los valores pendientes siguen sin poder validarse.
