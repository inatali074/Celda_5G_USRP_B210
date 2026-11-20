#!/bin/bash
# Crea el ícono "Celda 5G" en el escritorio y en el menú de aplicaciones.
# El ícono abre scripts/lanzador.sh en una terminal. Uso: scripts/instalar_lanzador.sh
set -eu
raiz=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
case "$raiz" in *'"'*|*'$'*|*'`'*|*'\'*|*'%'*) echo "La ruta del proyecto tiene caracteres que no admite un .desktop." >&2; exit 1 ;; esac

escritorio=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Escritorio")
mkdir -p "$escritorio" "$HOME/.local/share/applications"

contenido="[Desktop Entry]
Type=Application
Name=Celda 5G
Comment=Levanta el núcleo y el panel; la celda se inicia desde el panel
Exec=bash \"$raiz/scripts/lanzador.sh\"
Path=$raiz
Terminal=true
Icon=network-wireless
Categories=Network;"

for destino in "$escritorio/Celda5G.desktop" "$HOME/.local/share/applications/celda5g.desktop"; do
    printf '%s\n' "$contenido" > "$destino"
    chmod +x "$destino"
    echo "Creado: $destino"
done
# KDE pide marcar el ícono del escritorio como confiable; con esto deja de preguntar.
gio set "$escritorio/Celda5G.desktop" metadata::trusted true 2>/dev/null || true
