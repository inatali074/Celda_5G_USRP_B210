#!/usr/bin/env python3
"""Genera Diagramas_UL_DL_Paging_5G.html (diagramas en HTML/CSS con la explicación al costado).

Las tablas y notas (análisis, link budget, estados, glosario) se toman de Diagramas_UL_DL_Paging_5G.md;
los diagramas y sus explicaciones están definidos en la plantilla de abajo (objeto DIAGRAMAS).

Uso:  python3 generar_html.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
MD = BASE / "Diagramas_UL_DL_Paging_5G.md"
HTML = BASE / "Diagramas_UL_DL_Paging_5G.html"


def extraer(lineas, desde, hasta=None, incluir_desde=False):
    """Devuelve el texto entre la línea que empieza con `desde` y la que empieza con `hasta`."""
    i = next(k for k, l in enumerate(lineas) if l.startswith(desde))
    j = len(lineas) if hasta is None else next(k for k, l in enumerate(lineas) if k > i and l.startswith(hasta))
    bloque = lineas[i if incluir_desde else i + 1:j]
    while bloque and bloque[-1].strip() in ("", "---"):
        bloque.pop()
    return "\n".join(bloque).strip()


def main():
    lineas = MD.read_text(encoding="utf-8").splitlines()
    trozos = {
        "titulo": lineas[0].lstrip("# ").strip(),
        "intro": extraer(lineas, "# Diagramas", "## 0."),
        "analisis": extraer(lineas, "## 0.", "## 1."),
        "ul_notas": extraer(lineas, "> **Si el celular no pide", "### 1.3", incluir_desde=True),
        "conceptos": extraer(lineas, "### 1.3", "## 2."),
        "link_budget": extraer(lineas, "### 2.3", "## 3."),
        "estados": extraer(lineas, "### 3.1", "### 3.2"),
        "paging_cierre": extraer(lineas, "**Tiempo total:**", "## 4.", incluir_desde=True),
        "glosario": extraer(lineas, "## 4."),
    }
    literal = json.dumps(trozos, ensure_ascii=False).replace("</", "<\\/")
    HTML.write_text(PLANTILLA.replace("__TROZOS__", literal), encoding="utf-8")
    print(f"Generado: {HTML}")


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagramas 5G UL/DL/Paging</title>
<style>
  :root {
    --bg: #f5f6f8; --panel: #ffffff; --text: #1c2230; --muted: #5d6676; --border: #dde1e8;
    --accent: #2f5bd3; --code: #eef1f6; --quote: #eef3ff; --hover: #fff7d6;
    --ue: #e6f4ea; --ue-b: #34a853; --b210: #fdf0e1; --b210-b: #e8710a; --gnb: #e8f0fe; --gnb-b: #3367d6;
    --core: #f3e8fd; --core-b: #9334e6; --net: #eceff1; --net-b: #607d8b;
    --nota: #fff8c4; --nota-b: #c9a800; --linea: #8a94a6;
  }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --bg: #12151b; --panel: #1b1f27; --text: #e4e7ed; --muted: #9aa3b2; --border: #2e3440;
    --accent: #7aa2ff; --code: #242a35; --quote: #1f2635; --hover: #3a3420;
    --ue: #1b3324; --ue-b: #5bc77a; --b210: #3a2a18; --b210-b: #f29b4b; --gnb: #1d2a44; --gnb-b: #7aa2ff;
    --core: #2e2140; --core-b: #b98af5; --net: #262b33; --net-b: #90a4ae;
    --nota: #3b3618; --nota-b: #d9bd2b; --linea: #6b7486; } }
  :root[data-theme="dark"] {
    --bg: #12151b; --panel: #1b1f27; --text: #e4e7ed; --muted: #9aa3b2; --border: #2e3440;
    --accent: #7aa2ff; --code: #242a35; --quote: #1f2635; --hover: #3a3420;
    --ue: #1b3324; --ue-b: #5bc77a; --b210: #3a2a18; --b210-b: #f29b4b; --gnb: #1d2a44; --gnb-b: #7aa2ff;
    --core: #2e2140; --core-b: #b98af5; --net: #262b33; --net-b: #90a4ae;
    --nota: #3b3618; --nota-b: #d9bd2b; --linea: #6b7486; }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text);
         font: 15px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); min-height: 100vh; }
  nav { position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 20px 14px;
        background: var(--panel); border-right: 1px solid var(--border); }
  nav h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 0 0 10px; }
  nav a { display: block; padding: 4px 8px; border-radius: 6px; color: var(--text); text-decoration: none; font-size: 14px; }
  nav a.h3 { padding-left: 20px; font-size: 13px; color: var(--muted); }
  nav a.h4 { padding-left: 34px; font-size: 12px; color: var(--muted); }
  h4 { margin: 26px 0 8px; font-size: 16px; }
  pre { background: var(--code); padding: 12px 14px; border-radius: 8px; overflow-x: auto; font-size: 13px; line-height: 1.45; }
  pre code { background: none; padding: 0; }
  .conceptos { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 4px 20px 16px; }
  nav a:hover { background: var(--quote); color: var(--accent); }
  .tema { margin-top: 16px; width: 100%; padding: 8px; border-radius: 8px; border: 1px solid var(--border);
          background: var(--bg); color: var(--text); cursor: pointer; font-size: 13px; }
  main { padding: 28px 36px 80px; min-width: 0; }
  h1 { font-size: 26px; line-height: 1.25; margin: 0 0 12px; }
  h2 { margin-top: 48px; padding-bottom: 6px; border-bottom: 2px solid var(--border); }
  h3 { margin-top: 30px; color: var(--accent); }
  code { background: var(--code); padding: 1px 5px; border-radius: 4px; font-size: .9em; }
  blockquote { margin: 14px 0; padding: 8px 14px; background: var(--quote); border-left: 4px solid var(--accent); border-radius: 0 8px 8px 0; }
  blockquote p { margin: 6px 0; }
  .tabla { overflow-x: auto; margin: 14px 0; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; background: var(--panel); }
  th, td { border: 1px solid var(--border); padding: 6px 10px; vertical-align: top; text-align: left; }
  th { background: var(--code); }
  .resumen { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin: 12px 0; }
  .leyenda { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 14px; font-size: 13px; color: var(--muted); }
  .chip { padding: 2px 10px; border-radius: 999px; border: 1px solid; }

  /* ---------- Diagrama de cadena (flujo) ---------- */
  .cadena { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .cab { display: grid; grid-template-columns: minmax(260px, 380px) 1fr; background: var(--code);
         font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
  .cab div { padding: 8px 14px; }
  .fila { display: grid; grid-template-columns: minmax(260px, 380px) 1fr; border-top: 1px solid var(--border); }
  .fila:hover { background: var(--hover); }
  .fila .izq { padding: 10px 14px 18px; position: relative; display: flex; flex-direction: column; align-items: center; }
  .fila .der { padding: 12px 16px; border-left: 1px dashed var(--border); }
  .caja { width: 100%; border: 2px solid; border-radius: 10px; padding: 7px 10px; text-align: center; position: relative; }
  .caja .t { font-weight: 600; }
  .caja .d { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .flechaAbajo::after { content: "▼"; position: absolute; left: 50%; bottom: -17px; transform: translateX(-50%);
                        font-size: 11px; color: var(--linea); }
  .num { display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; padding: 0 6px;
         border-radius: 999px; background: var(--accent); color: #fff; font-size: 12px; font-weight: 700; margin-right: 8px; }
  .der .num { float: left; margin-top: 1px; }
  .der p { margin: 0; overflow: hidden; }
  .etapa { border-top: 1px solid var(--border); padding: 8px 14px; font-weight: 700; font-size: 14px; border-left: 6px solid; }
  .aire { border-top: 1px solid var(--border); display: grid; grid-template-columns: minmax(260px, 380px) 1fr; }
  .aire .izq { text-align: center; padding: 10px; font-size: 13px; color: var(--muted); }
  .aire .onda { font-size: 20px; letter-spacing: 4px; color: var(--accent); }
  .aire .der { padding: 10px 16px; border-left: 1px dashed var(--border); font-size: 14px; }
  .decision .caja { border-style: double; border-width: 4px; }
  .rama { font-size: 12px; font-weight: 700; color: var(--muted); margin-bottom: 4px; }
  .ue { background: var(--ue); border-color: var(--ue-b); } .b210 { background: var(--b210); border-color: var(--b210-b); }
  .gnb { background: var(--gnb); border-color: var(--gnb-b); } .core { background: var(--core); border-color: var(--core-b); }
  .net { background: var(--net); border-color: var(--net-b); }

  /* ---------- Diagrama de secuencia ---------- */
  .secuencia { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow-x: auto; }
  .sec-int { min-width: var(--minw); }
  .sfila { display: grid; grid-template-columns: minmax(0, 1fr) 340px; border-top: 1px solid var(--border); }
  .sfila:hover { background: var(--hover); }
  .sfila.cabecera { border-top: none; position: sticky; top: 0; z-index: 2; background: var(--panel); }
  .sfila.cabecera:hover { background: var(--panel); }
  .carriles { position: relative; padding: 10px 0; min-height: 58px; display: flex; flex-direction: column; justify-content: center; }
  .vida { position: absolute; top: 0; bottom: 0; width: 0; border-left: 2px dotted var(--linea); opacity: .55; }
  .participantes { display: grid; padding: 10px 0; }
  .part { margin: 0 4px; border: 2px solid; border-radius: 8px; padding: 6px 4px; text-align: center; font-size: 12px; font-weight: 700; }
  .msg { position: relative; z-index: 1; }
  .etq { position: relative; left: 50%; transform: translateX(-50%); width: max(100%, 210px); text-align: center;
         font-size: 12.5px; line-height: 1.35; padding: 0 4px 3px; }
  .etq span { background: var(--panel); padding: 0 3px; border-radius: 4px; }
  .sfila:hover .etq span { background: var(--hover); }
  .linea { position: relative; height: 0; border-top: 2px solid var(--text); }
  .linea.punteada { border-top-style: dashed; }
  .linea.haciaDer::after, .linea.haciaIzq::after { content: ""; position: absolute; top: -7px; border: 6px solid transparent; }
  .linea.haciaDer::after { right: -2px; border-left: 10px solid var(--text); border-right: 0; }
  .linea.haciaIzq::after { left: -2px; border-right: 10px solid var(--text); border-left: 0; }
  .snota { position: relative; z-index: 1; background: var(--nota); border: 1px solid var(--nota-b); border-radius: 6px;
           font-size: 12.5px; padding: 5px 8px; text-align: center; }
  .salt { position: relative; z-index: 1; margin: 0 6px; border-top: 2px dashed var(--muted); font-size: 12px; font-weight: 700;
          color: var(--muted); padding-top: 3px; }
  .sfila .der { padding: 10px 14px; border-left: 1px dashed var(--border); font-size: 14px; }
  .sfila.cabecera .der { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); display: flex; align-items: center; }

  #buscar { width: 100%; max-width: 420px; padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border);
            background: var(--panel); color: var(--text); font-size: 14px; }
  @media (max-width: 900px) {
    .layout { grid-template-columns: 1fr; }
    nav { position: static; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
    main { padding: 18px 16px 60px; }
    .cab { display: none; }
    .fila, .aire { grid-template-columns: 1fr; }
    .fila .der, .aire .der { border-left: none; border-top: 1px dashed var(--border); }
  }
</style>
</head>
<body>
<div class="layout">
  <nav>
    <h2>Contenido</h2>
    <div id="indice"></div>
    <button class="tema" id="btnTema">Cambiar tema claro / oscuro</button>
  </nav>
  <main id="contenido"></main>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script>
const T = __TROZOS__;

/* =====================================================================
   DIAGRAMAS (cada paso con su explicación al costado)
   ===================================================================== */
const CADENA_UL = [
  { etapa: "📱 CELULAR — transmite (TS 38.212 / 38.211 §6.3)", c: "ue" },
  { n: 1, c: "ue", t: "Transport Block (MAC)", d: "datos IP + BSR/PHR",
    e: "La MAC junta en un bloque de bits todo lo que se manda en este slot: los datos IP y los reportes BSR/PHR." },
  { n: 2, c: "ue", t: "CRC 24 bits", d: "TS 38.212 §6.2.1",
    e: "Agrega 24 bits de control para que el receptor pueda saber si el bloque llegó **bien o mal**." },
  { n: 3, c: "ue", t: "Codificación LDPC", d: "BG1 bloques grandes / BG2 chicos",
    e: "Agrega bits redundantes para **corregir errores** sin tener que retransmitir. *Qué es un LDPC: ver 1.3-A.*" },
  { n: 4, c: "ue", t: "Rate matching + RV", d: "versión de redundancia HARQ",
    e: "Recorta o repite bits para que entren **justo** en los PRBs concedidos. Si hay un reenvío, se manda otra \"parte\" de los bits (otra RV)." },
  { n: 5, c: "ue", t: "Scrambling", d: "secuencia con el C-RNTI",
    e: "Hace un XOR con una secuencia Gold propia del celular (C-RNTI) y de la celda (PCI). Así la interferencia de otro usuario se ve como ruido. **No es cifrado.** *Ver 1.3-B.*" },
  { n: 6, c: "ue", t: "Modulación", d: "π/2-BPSK · QPSK · 16/64/256-QAM",
    e: "Agrupa bits en símbolos complejos: QPSK = 2 bits, 64-QAM = 6 bits. Con **mejor señal** se usan más bits por símbolo." },
  { n: 7, c: "ue", t: "DFT (transform precoding)", d: "M = 12·N_PRB puntos → baja PAPR",
    e: "Reparte cada símbolo sobre todas las subportadoras asignadas. La señal queda con **menos picos** (PAPR) y el amplificador gasta menos batería. **Este paso convierte el UL en DFT-s-OFDM.** *PAPR y efecto en el celular: ver 1.3-E.*" },
  { n: 8, c: "ue", t: "Mapeo en PRBs contiguos + DM-RS", d: "asignación tipo 1 (RIV)",
    e: "Ubica los datos en los PRBs que concedió la gNB, que tienen que ser **contiguos** por la DFT, y suma pilotos DM-RS (valores conocidos) para medir el canal." },
  { n: 9, c: "ue", t: "IFFT 1536 + CP", d: "CP 108 muestras (120 en símbolos 0 y 7)",
    e: "Pasa de frecuencia a tiempo (genera la señal OFDM) y copia el final de cada símbolo al principio. Ese **prefijo cíclico** absorbe los ecos. 1536 × 15 kHz = 23.04 MS/s: *ver 1.3-C.*" },
  { n: 10, c: "ue", t: "Timing Advance", d: "adelanta el slot N_TA",
    e: "Transmite un poco antes para compensar la distancia y llegar **alineado** al slot de la gNB." },
  { n: 11, c: "ue", t: "DAC → LO 1747.5 MHz → PA", d: "≤ +23 dBm (Power Class 3)",
    e: "Pasa la señal a analógico, la sube a la frecuencia de UL y la amplifica con la potencia que fija el control de potencia (≈ −25 dBm a 2 m)." },
  { aire: "Interfaz Uu · FSPL a 2 m ≈ 43.3 dB",
    e: "La señal viaja por el aire y pierde ≈ 43 dB en 2 m (espacio libre a 1747.5 MHz)." },
  { etapa: "📡 USRP B210 — recibe (Radio Unit, split 8)", c: "b210" },
  { n: 12, c: "b210", t: "Antena en puerto RX2", d: "",
    e: "Recibe por **RX2**. El puerto TX/RX queda libre para transmitir el DL a 1842.5 MHz al mismo tiempo (FDD)." },
  { n: 13, c: "b210", t: "LNA + mezclador 1747.5 MHz", d: "rx_gain ≈ 45 dB",
    e: "Amplifica la señal débil agregando poco ruido y la baja a banda base." },
  { n: 14, c: "b210", t: "ADC 12 bits · 23.04 MS/s", d: "FPGA: DDC + timestamps",
    e: "Digitaliza 23.04 millones de muestras I/Q por segundo y la FPGA les pone marca de tiempo." },
  { n: 15, c: "b210", t: "USB 3.0 → PC", d: "muestras I/Q",
    e: "Manda las muestras a la PC. La B210 **no entiende de PRBs ni de bits**: solo convierte la señal." },
  { etapa: "🖥️ gNB srsRAN/OCUDU — decodifica (PHY → MAC)", c: "gnb" },
  { n: 16, c: "gnb", t: "Quitar CP + FFT 1536", d: "",
    e: "Descarta el CP (donde cayeron los ecos) y pasa de tiempo a frecuencia para recuperar cada subportadora." },
  { n: 17, c: "gnb", t: "Extraer los PRBs concedidos", d: "",
    e: "Se queda solo con los PRBs que le había asignado a este celular." },
  { n: 18, c: "gnb", t: "Estimación de canal + ecualización", d: "con DM-RS, 1 tap",
    e: "Compara los DM-RS recibidos con los conocidos, mide cuánto **deformó el canal** la señal y lo corrige con una división por subportadora." },
  { n: 19, c: "gnb", t: "IDFT", d: "transform de-precoding",
    e: "Deshace la DFT del paso 7." },
  { n: 20, c: "gnb", t: "Demodulación (LLR) + descrambling", d: "",
    e: "Calcula para cada bit **qué tan seguro** está de que es 0 o 1 (un valor \"soft\" llamado LLR) y quita el scrambling (invirtiendo el signo del LLR). *Ver 1.3-D.*" },
  { n: 21, c: "gnb", t: "HARQ + decodificación LDPC", d: "AVX-512",
    e: "Si es un reenvío, suma la copia anterior (más energía) y el decodificador LDPC corrige los errores." },
  { decision: true, n: 22, c: "gnb", t: "¿CRC OK?", e: "Verifica el CRC del paso 2." },
  { rama: "Sí", n: 23, c: "core", t: "MAC → RLC → PDCP → SDAP → GTP-U → UPF", d: "",
    e: "El paquete IP sube por las capas y va al core por el túnel GTP-U (N3)." },
  { rama: "No", n: 24, c: "gnb", t: "Retransmisión", d: "nuevo DCI 0_x con el mismo NDI", ultimo: true,
    e: "Pide reenviar con un nuevo DCI que tiene el **mismo NDI**." },
];

const CADENA_DL = [
  { etapa: "🖥️ gNB srsRAN/OCUDU — transmite (TS 38.212 / 38.211 §7.3)", c: "gnb" },
  { n: 1, c: "gnb", t: "Capas superiores + scheduler", d: "UPF → GTP-U → SDAP → PDCP → RLC → MAC",
    e: "El paquete llega del core, el PDCP lo cifra y el RLC lo segmenta. La MAC decide **a quién** le transmite, **cuántos PRBs** le da y **qué MCS** usa, según el CQI del celular." },
  { n: 2, c: "gnb", t: "CRC 24 bits + segmentación", d: "",
    e: "Agrega el CRC y, si el bloque es muy grande, lo corta en pedazos para el LDPC." },
  { n: 3, c: "gnb", t: "LDPC (datos) · Polar (control)", d: "",
    e: "Los datos se protegen con LDPC. El control (DCI, MIB) usa **código Polar**, que funciona mejor con bloques chicos. *Ver 1.3-A.*" },
  { n: 4, c: "gnb", t: "Rate matching + RV + scrambling", d: "",
    e: "Ajusta la cantidad de bits a los PRBs elegidos y los mezcla con una secuencia de la celda y del celular. *Ver 1.3-B.*" },
  { n: 5, c: "gnb", t: "Modulación QPSK → 256-QAM", d: "",
    e: "Con buen canal usa 256-QAM (8 bits por símbolo). Con canal malo usa QPSK (2 bits), que es más robusta." },
  { n: 6, c: "gnb", t: "Mapeo en la grilla + señales de referencia", d: "PRBs tipo 0 (RBG) o tipo 1 · DM-RS · CSI-RS · SSB cada 20 ms",
    e: "Los PRBs pueden **no ser contiguos**, porque en DL no hay DFT. Suma pilotos: DM-RS (para demodular), CSI-RS (para que el celular mida el canal) y SSB (para que los celulares encuentren la celda)." },
  { n: 7, c: "gnb", t: "IFFT 1536 + CP 4.69 µs", d: "",
    e: "Genera la señal OFDM. **En DL no hay DFT:** la gNB está enchufada y tolera más picos de potencia (PAPR), por eso es CP-OFDMA puro." },
  { n: 8, c: "gnb", t: "UHD → USB 3.0", d: "23.04 MS/s",
    e: "Envía 23.04 millones de muestras I/Q por segundo a la B210." },
  { etapa: "📡 USRP B210 — irradia", c: "b210" },
  { n: 9, c: "b210", t: "FPGA DUC → DAC 12 bits", d: "",
    e: "La FPGA interpola las muestras y el DAC las pasa a analógico." },
  { n: 10, c: "b210", t: "Mezclador LO 1842.5 MHz + tx_gain", d: "tx_gain ≈ 75 dB → P_tx ≈ −5 dBm (estimado)",
    e: "Sube la señal a la frecuencia de DL y la amplifica." },
  { n: 11, c: "b210", t: "Puerto TX/RX → antena +3 dBi", d: "EIRP ≈ −3 dBm",
    e: "Irradia la señal. La potencia irradiada equivalente es −5 − 1 (cables) + 3 (antena) ≈ **−3 dBm**." },
  { aire: "Aire · FSPL a 2 m ≈ 43.8 dB",
    e: "La señal pierde ≈ 43.8 dB en 2 m a 1842.5 MHz." },
  { etapa: "📱 CELULAR — recibe", c: "ue" },
  { n: 12, c: "ue", t: "Antena → LNA → mezclador → ADC", d: "P_rx ≈ −46.8 dBm · RSRP ≈ −78 dBm",
    e: "Llegan ≈ −47 dBm, muy por encima de la **sensibilidad de −91 dBm** (TS 38.101-1): ≈ 44 dB de margen. La señal se amplifica, se baja y se digitaliza." },
  { n: 13, c: "ue", t: "Sincronismo con SSB", d: "PSS/SSS → PCI = 1",
    e: "Con PSS y SSS el celular alinea su reloj y su frecuencia y confirma que es la celda PCI 1." },
  { n: 14, c: "ue", t: "Quitar CP + FFT", d: "",
    e: "Igual que en la gNB: descarta el CP y separa las subportadoras." },
  { decision: true, n: 15, c: "ue", t: "¿Hay un DCI 1_1 con mi C-RNTI en el PDCCH?", d: "búsqueda ciega en su CORESET",
    e: "No sabe dónde está su mensaje de control, así que **prueba varias posiciones** del CORESET. Si el CRC cierra con su C-RNTI, el DCI es para él." },
  { rama: "No", n: "—", c: "ue", t: "Duerme hasta el próximo monitoreo", d: "",
    e: "No hay nada para él: apaga el receptor y ahorra batería." },
  { rama: "Sí", n: 16, c: "ue", t: "Lee el DCI", d: "PRBs · MCS · K0 · K1",
    e: "El DCI le dice **dónde** están sus datos (PRBs), **cómo** vienen (MCS) y **cuándo** responder (K1)." },
  { n: 17, c: "ue", t: "PDSCH: DM-RS → ecualización → LLR", d: "",
    e: "Corrige el canal con los DM-RS y calcula los LLR, igual que la gNB en el UL. *Ver 1.3-D.*" },
  { n: 18, c: "ue", t: "HARQ + LDPC + CRC", d: "",
    e: "Si es un reenvío suma las copias, después decodifica el LDPC y verifica el CRC." },
  { n: 19, c: "ue", t: "HARQ-ACK/NACK + CQI por PUCCH", d: "K1 slots después", ultimo: true,
    e: "Avisa si llegó bien (ACK) o mal (NACK) y reporta la calidad del canal (CQI). **La gNB usa ese CQI en el paso 1.**" },
];

const SEC_UL = {
  p: [["UE", "📱 Celular (CONNECTED)", "ue"], ["B", "📡 B210", "b210"], ["G", "🖥️ gNB (scheduler)", "gnb"], ["C", "☁️ UPF", "core"]],
  f: [
    { nota: ["UE"], t: "Llega un paquete IP a enviar. NO tiene PRBs asignados.",
      e: "Punto de partida: el celular está conectado, pero **sin permiso** para transmitir datos." },
    { de: "UE", a: "G", t: "SR (Scheduling Request) por PUCCH formato 0/1, en su ocasión sr_period",
      e: "Avisa \"tengo algo para mandar\". Solo puede hacerlo en sus momentos reservados del PUCCH. Es como **levantar la mano**." },
    { nota: ["G"], t: "El scheduler decide cuánto y dónde (FDMA: PRBs · TDMA: slot)",
      e: "Acá actúa el **método de acceso**: la gNB reparte frecuencia y tiempo entre los usuarios." },
    { de: "G", a: "UE", t: "PDCCH · DCI 0_1 (C-RNTI): RIV · MCS · K2 · SLIV · NDI · RV · HARQ id · TPC",
      e: "El **permiso (grant)**: qué PRBs (RIV), en qué slot (K2) y en qué símbolos (SLIV), qué modulación (MCS), si es dato nuevo (NDI) y un ajuste de potencia (TPC). Solo este celular lo puede leer." },
    { nota: ["UE"], t: "Espera K2 slots (≥ 4 ms por defecto en srsRAN)", e: "Tiempo para preparar la transmisión." },
    { de: "UE", a: "B", t: "PUSCH (DFT-s-OFDM, 1747.5 MHz): BSR + primeros datos",
      e: "Transmite en los PRBs concedidos. Suma un **BSR** que dice cuántos bytes le faltan enviar." },
    { de: "B", a: "G", t: "Muestras I/Q por USB 3.0", e: "La B210 solo digitaliza y pasa las muestras a la PC." },
    { de: "G", a: "C", t: "Paquete IP por túnel GTP-U (N3)", e: "La gNB decodifica, recupera el paquete IP y lo manda al core." },
    { nota: ["G"], t: "En NR no hay PHICH: el ACK del UL es implícito",
      e: "El canal de ACK de 4G (PHICH) **no existe** en 5G." },
    { de: "G", a: "UE", t: "DCI 0_1 con NDI invertido = ACK + nuevo grant según el BSR",
      e: "Si el NDI cambia, significa \"lo anterior llegó bien, mandá lo nuevo\". El tamaño del nuevo permiso sale del BSR." },
    { de: "UE", a: "G", t: "PUSCH con el resto de los datos", e: "Termina de enviar." },
    { de: "G", a: "UE", punt: true, t: "TA Command (MAC CE) + TPC",
      e: "Corrección periódica del adelanto de tiempo (si el celular se movió) y de la potencia." },
  ]
};

const SEC_DL = {
  p: [["I", "🌐 Internet", "net"], ["C", "☁️ UPF", "core"], ["G", "🖥️ gNB (scheduler)", "gnb"], ["B", "📡 B210", "b210"], ["UE", "📱 Celular (CONNECTED)", "ue"]],
  f: [
    { de: "UE", a: "G", t: "CSI report por PUCCH (CQI, RI) medido sobre CSI-RS",
      e: "El celular informa qué tan bueno es el canal (**CQI** 0–15) y cuántas capas soporta (**RI**, 1 en SISO)." },
    { de: "I", a: "C", t: "Paquete IP hacia 10.45.0.2", e: "Llega un paquete de Internet para el celular." },
    { de: "C", a: "G", t: "GTP-U (N3, UDP 2152) con el TEID de la sesión",
      e: "La UPF lo mete en el túnel N3. El **TEID** identifica de qué celular y de qué sesión es." },
    { nota: ["G"], t: "Adaptación de enlace: CQI alto → MCS alto. Elige PRBs (FDMA) y slot (TDMA)",
      e: "El scheduler decide frecuencia, tiempo y modulación." },
    { de: "G", a: "B", t: "Slot n: PDCCH (DCI 1_1, C-RNTI) + PDSCH (K0 = 0, mismo slot)",
      e: "En el **mismo slot** manda el aviso (PDCCH) y los datos (PDSCH)." },
    { de: "B", a: "UE", t: "RF 1842.5 MHz", e: "La B210 lo irradia." },
    { nota: ["UE"], t: "Decodifica el PDSCH", e: "Cadena de recepción (pasos 12–18 del diagrama anterior)." },
    { alt: "Si el CRC es correcto" },
    { de: "UE", a: "G", t: "HARQ-ACK por PUCCH (slot n+K1, ≥ 4 ms por defecto)", e: "Confirma que llegó bien." },
    { alt: "Si el CRC es erróneo" },
    { de: "UE", a: "G", t: "HARQ-NACK", e: "Avisa que hay que reenviar." },
    { de: "G", a: "UE", t: "Retransmisión (mismo HARQ id, otra RV) → combinación soft",
      e: "La gNB reenvía otra versión de los datos y el celular la **suma** a la anterior: es más probable que decodifique bien." },
    { de: "G", a: "UE", punt: true, t: "Si bajó la calidad (nuevo CQI) → baja el MCS",
      e: "**Adaptación de enlace:** menos velocidad, pero menos errores." },
  ]
};

const SEC_PAGING = {
  p: [["W", "🌐 WhatsApp", "net"], ["N", "🐧 NAT / ogstun", "net"], ["U", "UPF", "core"], ["S", "SMF", "core"],
      ["A", "AMF", "core"], ["G", "🖥️ gNB + B210", "gnb"], ["UE", "📱 Celular (IDLE)", "ue"]],
  f: [
    { nota: ["UE"], t: "Duerme con DRX y se despierta solo en su Paging Occasion",
      e: "Está **registrado pero dormido**: no tiene recursos y escucha el PDCCH solo unos ms por ciclo (0.32–2.56 s)." },
    { de: "W", a: "N", t: "Mensaje o llamada WhatsApp (paquete IP)", e: "Llega por Internet a la IP pública de la PC." },
    { de: "N", a: "U", t: "Destino 10.45.0.2", e: "La NAT y `ogstun` lo entregan a la UPF." },
    { nota: ["U"], t: "Túnel N3 desactivado → guarda el paquete en buffer",
      e: "En IDLE no hay túnel hacia la gNB, así que la UPF guarda el paquete." },
    { de: "U", a: "S", t: "PFCP Session Report (Downlink Data Report, N4)", e: "Avisa \"tengo datos para este usuario\"." },
    { de: "S", a: "A", t: "Namf_Communication_N1N2MessageTransfer", e: "La AMF es la que sabe cómo ubicar al celular." },
    { de: "A", a: "G", t: "NGAP Paging (5G-S-TMSI, lista de TAI)",
      e: "Ordena buscar al celular por su identidad temporal **5G-S-TMSI** (nunca el IMSI) en su área de seguimiento." },
    { nota: ["G"], t: "Espera la Paging Occasion del celular (calculada con UE_ID)",
      e: "Solo puede llamarlo cuando el celular está despierto." },
    { de: "G", a: "UE", t: "PDCCH DCI 1_0 con P-RNTI (0xFFFE) → PDSCH: RRC Paging (ng-5G-S-TMSI)",
      e: "El P-RNTI es común a todos los celulares. Dentro del mensaje va la identidad buscada." },
    { nota: ["UE"], t: "Reconoce su identidad → despierta", e: "Ve su 5G-S-TMSI en la lista." },
    { de: "UE", a: "G", t: "Msg1 PRACH: preámbulo Zadoff-Chu (1747.5 MHz)",
      e: "No tiene recursos, así que vuelve a entrar por **acceso aleatorio**." },
    { de: "G", a: "UE", t: "Msg2 RAR (TA + grant + TC-RNTI)", e: "Respuesta con el adelanto de tiempo, el permiso para el Msg3 y un ID temporal." },
    { de: "UE", a: "G", t: "Msg3 RRCSetupRequest (causa: mt-Access)",
      e: "Pide conexión con causa **mt-Access**, que significa \"me llamaron\" (terminada en el móvil)." },
    { de: "G", a: "UE", t: "Msg4 RRCSetup (resolución de contienda → C-RNTI, SRB1)",
      e: "Confirma que ganó el acceso, le da su C-RNTI y abre la señalización (SRB1)." },
    { de: "UE", a: "G", t: "RRCSetupComplete + NAS Service Request",
      e: "**No se vuelve a registrar:** pide reactivar sus datos y conserva la misma IP." },
    { de: "G", a: "A", t: "NGAP InitialUEMessage (Service Request)", e: "La gNB pasa el pedido a la AMF." },
    { de: "A", a: "S", t: "Nsmf_PDUSession_UpdateSMContext", e: "Reactivar el plano de usuario de la sesión PDU." },
    { de: "A", a: "G", t: "NGAP InitialContextSetupRequest (TEID de la UPF + claves)",
      e: "Le da a la gNB las claves de seguridad y a dónde mandar los datos de subida." },
    { de: "G", a: "UE", t: "RRC SecurityModeCommand + RRCReconfiguration (DRB1)",
      e: "Activa el cifrado en radio y crea el portador de datos **DRB1**." },
    { de: "UE", a: "G", t: "SecurityModeComplete + RRCReconfigurationComplete", e: "El celular confirma." },
    { de: "G", a: "A", t: "InitialContextSetupResponse (TEID de la gNB)", e: "La gNB informa a dónde mandarle los datos de bajada." },
    { de: "A", a: "S", t: "Actualiza el túnel N3", e: "" },
    { de: "S", a: "U", t: "PFCP Session Modification (TEID de la gNB)", e: "El túnel N3 queda armado en ambos sentidos." },
    { de: "U", a: "G", t: "Libera el buffer → GTP-U", e: "Sale el paquete que estaba guardado." },
    { de: "G", a: "UE", t: "DCI 1_1 (C-RNTI) + PDSCH (CP-OFDMA, 1842.5 MHz)", e: "Entrega por radio, igual que en el DL normal." },
    { nota: ["UE"], t: "🔔 Suena la notificación o la llamada de WhatsApp",
      e: "Demora total: hasta un ciclo DRX (≤ 2.56 s) más ~100–300 ms de reconexión." },
  ]
};

/* =====================================================================
   RENDER
   ===================================================================== */
const md = s => marked.parse(s || "");
const inl = s => marked.parseInline(s || "");
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function cadena(pasos) {
  let h = '<div class="cadena"><div class="cab"><div>Bloque</div><div>Qué hace</div></div>';
  pasos.forEach((p, i) => {
    if (p.etapa) { h += `<div class="etapa ${p.c}">${esc(p.etapa)}</div>`; return; }
    if (p.aire) {
      h += `<div class="aire"><div class="izq"><div class="onda">〰〰〰</div>${esc(p.aire)}</div><div class="der">${inl(p.e)}</div></div>`;
      return;
    }
    const sig = pasos[i + 1];
    const flecha = !p.ultimo && sig && !sig.etapa && !sig.aire && !sig.rama ? " flechaAbajo" : "";
    const rama = p.rama ? `<div class="rama">${p.rama === "Sí" ? "✔ Sí" : "✘ No"}</div>` : "";
    h += `<div class="fila${p.decision ? " decision" : ""}"><div class="izq">${rama}
            <div class="caja ${p.c}${flecha}"><div class="t">${p.decision ? "◆ " : ""}${esc(p.t)}</div>${p.d ? `<div class="d">${esc(p.d)}</div>` : ""}</div></div>
          <div class="der"><span class="num">${p.n}</span><p>${inl(p.e)}</p></div></div>`;
  });
  return h + "</div>";
}

function secuencia(def) {
  const N = def.p.length, idx = {};
  def.p.forEach((p, i) => idx[p[0]] = i);
  const centro = i => (i + 0.5) / N * 100;
  const vidas = def.p.map((_, i) => `<div class="vida" style="left:${centro(i)}%"></div>`).join("");
  let h = `<div class="secuencia"><div class="sec-int" style="--minw:${N * 120 + 340}px">`;
  h += `<div class="sfila cabecera"><div class="participantes" style="grid-template-columns:repeat(${N},1fr)">` +
       def.p.map(p => `<div class="part ${p[2]}">${esc(p[1])}</div>`).join("") +
       `</div><div class="der">Explicación</div></div>`;
  let n = 0;
  def.f.forEach(f => {
    let izq = "", der = "";
    if (f.alt) {
      izq = `<div class="salt">${esc(f.alt)}</div>`;
    } else if (f.nota) {
      const a = Math.min(...f.nota.map(k => idx[k])), b = Math.max(...f.nota.map(k => idx[k]));
      const ancho = Math.max((b - a + 1) / N * 100, 0);
      let izqPct = a / N * 100;
      // notas de una sola columna: se ensanchan un poco centradas en el participante
      const extra = b === a ? Math.min(100 / N * 0.6, 12) : 0;
      izqPct = Math.max(0, Math.min(100 - ancho - 2 * extra, izqPct - extra));
      izq = `<div class="snota" style="margin-left:${izqPct}%;width:${ancho + 2 * extra}%">${esc(f.t)}</div>`;
      der = f.e ? `<p>${inl(f.e)}</p>` : "";
    } else {
      n++;
      const a = idx[f.de], b = idx[f.a];
      const L = centro(Math.min(a, b)), W = Math.abs(b - a) / N * 100;
      const dir = b > a ? "haciaDer" : "haciaIzq";
      izq = `<div class="msg" style="margin-left:${L}%;width:${W}%"><div class="etq"><span><b>${n}.</b> ${esc(f.t)}</span></div>
             <div class="linea ${dir}${f.punt ? " punteada" : ""}"></div></div>`;
      der = `<span class="num">${n}</span><p>${inl(f.e) || "&nbsp;"}</p>`;
    }
    h += `<div class="sfila"><div class="carriles">${vidas}${izq}</div><div class="der">${der}</div></div>`;
  });
  return h + "</div></div>";
}

function leyenda() {
  return `<div class="leyenda">
    <span class="chip ue">Celular</span><span class="chip b210">USRP B210</span><span class="chip gnb">gNB</span>
    <span class="chip core">Core 5G</span><span class="chip net">Internet / NAT</span>
    <span>· Pasá el mouse sobre una fila para resaltar el paso y su explicación</span></div>`;
}

const html = `
<h1>${esc(T.titulo)}</h1>
${md(T.intro)}

<h2>0. Análisis del diagrama de bloques actual</h2>
${md(T.analisis)}

<h2>1. UPLINK (celular → gNB): DFT-s-OFDM sobre FDD</h2>
<h3>1.1 Cadena de transmisión y recepción</h3>
${leyenda()}
${cadena(CADENA_UL)}
<div class="resumen">${inl("**En resumen:** el celular convierte bits en una señal de radio robusta (1–11), la B210 solo la digitaliza (12–15) y la gNB deshace cada paso en orden inverso (16–24). Lo propio del **método de acceso UL** está en los pasos 7–8 (DFT + PRBs contiguos = DFT-s-OFDM / FDMA) y 10 (todos llegan alineados al mismo slot = TDMA).")}</div>

<h3>1.2 Método de acceso en el tiempo: cómo pide y obtiene recursos</h3>
${leyenda()}
${secuencia(SEC_UL)}
${md(T.ul_notas)}

<h3>1.3 Conceptos clave de la cadena</h3>
<div class="conceptos">${md(T.conceptos)}</div>

<h2>2. DOWNLINK (gNB → celular): CP-OFDMA sobre FDD</h2>
<h3>2.1 Cadena de transmisión y recepción</h3>
${leyenda()}
${cadena(CADENA_DL)}
<div class="resumen">${inl("**En resumen:** la gNB elige y arma la transmisión (1–8), la B210 la irradia (9–11) y el celular la recibe (12–19). Diferencias con el UL: en DL **no hay DFT** (CP-OFDMA puro, PRBs que pueden estar separados) y el celular **no pide nada**: revisa el PDCCH para ver si la gNB le asignó algo.")}</div>

<h3>2.2 Interacción de mensajes en DL</h3>
${leyenda()}
${secuencia(SEC_DL)}

<h3>2.3 Presupuesto de enlace y sensibilidad (aula, d = 2 m, SISO)</h3>
${md(T.link_budget)}

<h2>3. Celular registrado pero sin usar recursos: le llega un WhatsApp</h2>
<h3>3.1 Estados del celular</h3>
${md(T.estados)}
<h3>3.2 Diagrama de comunicación (paging iniciado por la red, TS 23.502 §4.2.3.3)</h3>
${leyenda()}
${secuencia(SEC_PAGING)}
${md(T.paging_cierre)}

<h2>4. Glosario de siglas</h2>
<p><input id="buscar" type="search" placeholder="Buscar una sigla o palabra (ej.: HARQ, potencia)…"></p>
<div id="glosario">${md(T.glosario)}</div>
`;

const main = document.getElementById("contenido");
main.innerHTML = html;

main.querySelectorAll("table").forEach(t => {
  const w = document.createElement("div"); w.className = "tabla";
  t.parentNode.insertBefore(w, t); w.appendChild(t);
});

// Índice lateral
const indice = document.getElementById("indice");
main.querySelectorAll("h2, h3, .conceptos h4").forEach((h, i) => {
  h.id = "sec" + i;
  const a = document.createElement("a");
  a.href = "#" + h.id; a.textContent = h.textContent; a.className = h.tagName.toLowerCase();
  indice.appendChild(a);
});

// Buscador del glosario
document.getElementById("buscar").addEventListener("input", e => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll("#glosario tbody tr").forEach(tr => {
    tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? "" : "none";
  });
});

// Tema claro / oscuro
const raiz = document.documentElement;
try { const t = localStorage.getItem("tema5g"); if (t) raiz.dataset.theme = t; } catch (e) {}
document.getElementById("btnTema").onclick = () => {
  const oscuro = raiz.dataset.theme === "dark" || (!raiz.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  raiz.dataset.theme = oscuro ? "light" : "dark";
  try { localStorage.setItem("tema5g", raiz.dataset.theme); } catch (e) {}
};
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
