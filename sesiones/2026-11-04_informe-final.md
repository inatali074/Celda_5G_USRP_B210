# Sesión 2026-11-04: informe final

## Qué se hizo
- Se redactó el informe final en LaTeX a partir de `informe/prompt_informe_final.md`:
  - `informe/informe_final.tex`, más una sección por archivo en `informe/secciones/`;
  - PDF: `informe/informe_final.pdf`, de 45 páginas.
- Figuras:
  - `informe/figuras/generar_figuras.py` genera la grilla con el SSB, el patrón TDD, la CCDF de PAPR (Monte Carlo con semilla fija, no son mediciones) y las curvas de ALOHA;
  - en TikZ: el RACH de 4 pasos, las cadenas de DFT-s-OFDM y la arquitectura.
- Se verificaron citas con las TS de `drive-download-*/Release_15/`:
  - TS 38.211 v15.10.0: tablas 6.3.3.1-2, 6.3.3.1-7, 6.3.3.2-1 y 6.3.3.2-3, §5.2.1, §5.3.1, §5.3.2 y §7.4.2;
  - TS 38.213 v15.15.0: §4.2 y §7.1.1;
  - TS 38.321 v15.14.0: RA-RNTI y tabla 7.3-2.
- Revisión de Codex en solo lectura: `revisiones/2026-11-04_codex-revision-informe.md`. Hizo 29 observaciones, ninguna crítica, y se integraron casi todas:
  - la consigna va primero;
  - se corrigieron los bits del PBCH (24 + 8 + 24 = 56);
  - se corrigió N_info: da 54 391,5, sin cambiar el TBS;
  - se aclaró la cadena de CB;
  - "máximo" pasó a "referencia aproximada";
  - el alcance del PRACH ahora se presenta como geométrico y orientativo;
  - el modelo de potencia DL se presenta como simplificado;
  - se suavizaron las atribuciones causales;
  - se agregaron una tabla de evidencia por etapa y la procedencia de los parámetros del SIB1;
  - se definió el jitter;
  - la bajada se informa como tasa del emisor.
- No se aplicó lo de las versiones exactas de TS 38.101-1, 38.212, 38.214, 38.306 y 24.501: no están en el proyecto.

## Hallazgos
- `prach-ConfigurationIndex` 159 es el formato B4: una ocasión por trama, en la subtrama 9 (slot 19). La guarda implícita es de 12,9 µs y el CP de 15,76 µs, lo que da un alcance geométrico de ~2 km.
- Con DFT-s-OFDM, 51 PRB no cumple 2^a·3^b·5^c (TS 38.211 §6.3.1.4): por eso el tramo B tuvo 50 PRB.
- **Hipótesis para P-004:** `zeroCorrelationZoneConfig` 0 da N_CS 0, y los 64 preámbulos salen de 64 raíces ZC. El slot del PRACH sería el más pesado. Para probarlo, subir ese parámetro y ver si "UL processor is busy" deja de concentrarse en el slot 19.
- Errores del prompt, corregidos con la evidencia:
  - n3 con `NR only` terminó por RLF;
  - K/OPc se grabaron con OYEI.

## Verificación de citas (misma sesión)
- Se contrastaron las 16 citas marcadas [verificar] con el texto de las TS Release 15. Las versiones bajadas de ETSI no se guardaron en el proyecto; la 38.331 sí estaba:
  - TS 38.101-1 v15.31.0;
  - TS 38.212 v15.13.0;
  - TS 38.214 v15.16.0;
  - TS 38.133 v15.35.0;
  - TS 24.501 v15.7.0;
  - TS 38.331 v15.30.0, la local.
- 15 citas coinciden. Ajustes:
  - la RLF se cita en TS 38.331 §5.3.10.3;
  - el N_TA,offset de 25 600 T_c corresponde a FR1 sin coexistencia LTE-NR;
  - según TS 24.501 §4.3.2, el UE deshabilita N1 y busca E-UTRA conectada al EPC.
- Queda marcada solo la del MCC 001 (UIT-T E.212): la UIT no deja bajarla sin iniciar sesión, y solo hay fuentes secundarias.

## Para retomar
- Conseguir el texto de UIT-T E.212 para cerrar la cita del MCC 001.
- Completar la tabla de comparación con EDGE y LTE.
- Repetir el ping y la bajada con la celda limpia, y actualizar el informe.
- Probar la hipótesis de `zeroCorrelationZoneConfig` (pedir el ok antes de tocar la configuración y antes de transmitir).
- Para recompilar: `cd informe && python3 figuras/generar_figuras.py && pdflatex informe_final.tex` (dos veces).
