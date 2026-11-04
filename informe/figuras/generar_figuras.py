#!/usr/bin/env python3
"""Genera las figuras del informe final (PDF vectorial).

Uso: python3 informe/figuras/generar_figuras.py
Salida: informe/figuras/*.pdf

Las figuras de grilla y TDD se dibujan con los parámetros de la celda n78
(51 PRB, SCS 30 kHz, SSB en la subportadora 14 desde el punto A, patrón
DDDDDDSUUU de 5 ms, PRACH en el slot 19). Las curvas de PAPR son una
simulación de Monte Carlo con semilla fija; no son mediciones.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parent

# Paleta de referencia (orden categórico fijo) y tintas de texto.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#d9d8d4", "#fcfcfb"
LS = ["-", "--", "-.", ":"]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.edgecolor": INK2,
    "axes.labelcolor": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "legend.frameon": False,
    "lines.linewidth": 1.6,
})


def guardar(fig, nombre):
    fig.savefig(OUT / nombre, bbox_inches="tight")
    plt.close(fig)
    print("ok", nombre)


# ---------------------------------------------------------------- grilla SSB
def fig_grilla_ssb():
    n_prb, sc_ssb0 = 51, 14  # SSB: offsetToPointA=2 PRB(15 kHz) + kSSB=4 -> 420 kHz = 14 sc de 30 kHz
    n_sc = n_prb * 12
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.grid(False)
    # Fondo: PDSCH/otros
    ax.add_patch(Rectangle((0, 0), 14, n_sc, fc="#f0efec", ec="none"))
    # CORESET (ilustrativo, primer símbolo)
    ax.add_patch(Rectangle((0, 0), 1, n_sc, fc=C[3], ec="white", lw=1, alpha=0.85))
    s0 = sc_ssb0
    # Símbolo 2: PSS (sc 56..182 del SSB)
    ax.add_patch(Rectangle((2, s0 + 56), 1, 127, fc=C[0], ec="white", lw=1))
    # Símbolo 3 y 5: PBCH completo (240 sc)
    for l in (3, 5):
        ax.add_patch(Rectangle((l, s0), 1, 240, fc=C[2], ec="white", lw=1))
    # Símbolo 4: SSS al centro y PBCH a los costados
    ax.add_patch(Rectangle((4, s0 + 56), 1, 127, fc=C[1], ec="white", lw=1))
    ax.add_patch(Rectangle((4, s0), 1, 48, fc=C[2], ec="white", lw=1))
    ax.add_patch(Rectangle((4, s0 + 192), 1, 48, fc=C[2], ec="white", lw=1))
    # Contorno del SSB
    ax.add_patch(Rectangle((2, s0), 4, 240, fc="none", ec=INK, lw=1.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, n_sc)
    ax.set_xticks(np.arange(14) + 0.5, [str(i) for i in range(14)])
    yt = np.arange(0, n_prb + 1, 5) * 12
    ax.set_yticks(yt, [str(int(v / 12)) for v in yt])
    ax.set_xlabel("símbolo OFDM $l$ del slot 0 (μ = 1, 0,5 ms)")
    ax.set_ylabel("PRB (desde el punto A)")
    for x in range(15):
        ax.axvline(x, color="white", lw=0.8)
    lab = dict(color=INK, fontsize=8, va="center")
    ax.text(6.3, s0 + 120, "SS/PBCH block\n240 sc × 4 símb.\n= 20 PRB (7,2 MHz)", **lab)
    ax.text(6.3, s0 + 300, "PSS y SSS: 127 sc (3,81 MHz)\nPBCH + DM-RS del PBCH", **lab)
    ax.text(1.1, n_sc - 40, "CORESET / PDCCH", **lab)
    ax.text(8.0, 520, "resto: PDSCH, DM-RS, CSI-RS/TRS", color=INK2, fontsize=8)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=C[0], label="PSS"), Patch(fc=C[1], label="SSS"),
                       Patch(fc=C[2], label="PBCH"), Patch(fc=C[3], label="CORESET")],
              loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4)
    guardar(fig, "fig_grilla_ssb.pdf")


# ---------------------------------------------------------------- patrón TDD
def fig_tdd():
    fig, ax = plt.subplots(figsize=(6.6, 1.9))
    ax.grid(False)
    patron = "DDDDDDSUUU" * 2
    col = {"D": C[0], "U": C[1]}
    for s, t in enumerate(patron):
        if t == "S":
            ax.add_patch(Rectangle((s, 0), 8 / 14, 1, fc=C[0], ec="none"))
            ax.add_patch(Rectangle((s + 8 / 14, 0), 6 / 14, 1, fc="#f0efec", ec="none"))
            ax.add_patch(Rectangle((s, 0), 1, 1, fc="none", ec="white", lw=2))
            ax.text(s + 0.5, 0.5, "S", ha="center", va="center", color=INK, fontsize=9)
        else:
            ax.add_patch(Rectangle((s, 0), 1, 1, fc=col[t], ec="white", lw=2))
            ax.text(s + 0.5, 0.5, t, ha="center", va="center", color="white", fontsize=9,
                    fontweight="bold")
    ax.annotate("SSB", xy=(0.5, 1.02), xytext=(0.5, 1.55), ha="center",
                arrowprops=dict(arrowstyle="->", color=INK), color=INK, fontsize=8)
    ax.annotate("PRACH (formato B4)", xy=(19.5, 1.02), xytext=(17.6, 1.55), ha="center",
                arrowprops=dict(arrowstyle="->", color=INK), color=INK, fontsize=8)
    ax.annotate("8 D + 6 guarda", xy=(6.5, -0.02), xytext=(8.2, -0.6), ha="left",
                arrowprops=dict(arrowstyle="->", color=INK), color=INK, fontsize=8)
    ax.axvline(10, color=INK, lw=1, ls="--")
    ax.text(3, -0.45, "período 1: 5 ms", ha="center", color=INK2, fontsize=8)
    ax.text(14, -0.45, "período 2: 5 ms", ha="center", color=INK2, fontsize=8)
    ax.set_xlim(0, 20)
    ax.set_ylim(-0.8, 1.9)
    ax.set_xticks(np.arange(20) + 0.5, [str(i) for i in range(20)])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("slot dentro de la trama de 10 ms (0,5 ms por slot)")
    guardar(fig, "fig_tdd.pdf")


# ---------------------------------------------------------------- PAPR
def papr_db(x):
    p = np.abs(x) ** 2
    return 10 * np.log10(p.max(axis=1) / p.mean(axis=1))


def qam(m, shape, rng):
    k = int(np.sqrt(m))
    re = rng.integers(0, k, shape) * 2 - (k - 1)
    im = rng.integers(0, k, shape) * 2 - (k - 1)
    s = re + 1j * im
    return s / np.sqrt(np.mean(np.abs(s) ** 2))


def ofdm(n_act, n_fft, sym, os=4):
    """Mapea n_act subportadoras centradas y aplica IFFT sobremuestreada."""
    L = n_fft * os
    X = np.zeros((sym.shape[0], L), complex)
    idx = (np.arange(n_act) - n_act // 2) % L
    X[:, idx] = sym
    return np.fft.ifft(X, axis=1)


def ccdf(v, g):
    return np.array([(v > x).mean() for x in g])


def fig_papr():
    rng = np.random.default_rng(5)
    g = np.linspace(2, 13, 221)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 3.0), sharey=True)
    n_sim = 20000
    for i, n in enumerate([16, 64, 256, 1024]):
        s = qam(4, (n_sim, n), rng)
        v = papr_db(ofdm(n, n, s))
        a1.semilogy(g, ccdf(v, g), color=C[i], ls=LS[i], label=f"N = {n}")
        gl = 10 ** (g / 10)
        a1.semilogy(g, 1 - (1 - np.exp(-gl)) ** (2.8 * n), color=C[i], lw=0.8, alpha=0.6)
    a1.set_title("CP-OFDM, QPSK: CCDF frente a N", fontsize=9, color=INK)
    a1.set_xlabel("umbral $\\gamma_0$ [dB]")
    a1.set_ylabel("Pr{PAPR > $\\gamma_0$}")
    a1.legend(loc="lower left", fontsize=8)
    # CP-OFDM contra DFT-s-OFDM con M = 612 sc (51 PRB) en FFT de 768
    M, N = 612, 768
    for j, (mod, nom) in enumerate([(4, "QPSK"), (16, "16QAM")]):
        s = qam(mod, (n_sim, M), rng)
        v_o = papr_db(ofdm(M, N, s))
        v_d = papr_db(ofdm(M, N, np.fft.fft(s, axis=1) / np.sqrt(M)))
        a2.semilogy(g, ccdf(v_o, g), color=C[0], ls=LS[j], label=f"CP-OFDM {nom}")
        a2.semilogy(g, ccdf(v_d, g), color=C[1], ls=LS[j], label=f"DFT-s-OFDM {nom}")
    a2.set_title("51 PRB (M = 612), FFT de 768", fontsize=9, color=INK)
    a2.set_xlabel("umbral $\\gamma_0$ [dB]")
    a2.legend(loc="lower left", fontsize=7)
    for a in (a1, a2):
        a.set_ylim(1e-4, 1.2)
        a.set_xlim(2, 13)
    guardar(fig, "fig_ccdf_papr.pdf")


# ---------------------------------------------------------------- ALOHA
def fig_aloha():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.7))
    G = np.linspace(0, 4, 400)
    a1.plot(G, G * np.exp(-G), color=C[0], label="ranurado: $S = Ge^{-G}$")
    a1.plot(G, G * np.exp(-2 * G), color=C[1], ls="--", label="puro: $S = Ge^{-2G}$")
    a1.plot([1], [np.exp(-1)], "o", color=C[0], ms=5)
    a1.text(1.15, 0.36, "1/e ≈ 0,368", fontsize=8, color=INK)
    a1.set_xlabel("carga ofrecida $G$ [intentos por ranura]")
    a1.set_ylabel("throughput $S$")
    a1.set_title("ALOHA (un canal)", fontsize=9, color=INK)
    a1.legend(fontsize=7, loc="upper right")
    a1.set_ylim(0, 0.5)
    k = np.arange(1, 101)
    for i, n in enumerate([64, 16]):
        a2.plot(k, (1 - 1 / n) ** (k - 1), color=C[i], ls=LS[i], label=f"{n} preámbulos")
    a2.set_xlabel("UE en la misma ocasión de PRACH")
    a2.set_ylabel("Pr{sin colisión}")
    a2.set_title("PRACH con contienda", fontsize=9, color=INK)
    a2.legend(fontsize=7)
    a2.set_ylim(0, 1.02)
    guardar(fig, "fig_aloha.pdf")


if __name__ == "__main__":
    fig_grilla_ssb()
    fig_tdd()
    fig_papr()
    fig_aloha()
