#!/usr/bin/env python3
"""Barrido de potencia en recepción con la B210. No abre ningún canal de transmisión."""
import argparse
import csv

import numpy as np
import uhd

FS = 25e6       # Se descartan los bordes del filtro: útil central de 20 MHz.
NFFT = 1024
PASO = 20e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", type=float, default=3300e6)
    ap.add_argument("--fin", type=float, default=3800e6)
    ap.add_argument("--ganancia", type=float, default=40)
    ap.add_argument("--antena", default="RX2")
    ap.add_argument("--vueltas", type=int, default=3)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()

    usrp = uhd.usrp.MultiUSRP("type=b200")
    usrp.set_rx_rate(FS)
    usrp.set_rx_gain(args.ganancia)
    usrp.set_rx_antenna(args.antena)
    st = uhd.usrp.StreamArgs("fc32", "sc16")
    rx = usrp.get_rx_stream(st)
    buf = np.zeros((1, NFFT), dtype=np.complex64)
    meta = uhd.types.RXMetadata()

    centros = np.arange(args.inicio + PASO / 2, args.fin, PASO)
    util = np.abs(np.fft.fftshift(np.fft.fftfreq(NFFT, 1 / FS))) <= PASO / 2
    ventana = np.hanning(NFFT)
    filas = []
    for vuelta in range(args.vueltas):
        for fc in centros:
            usrp.set_rx_freq(uhd.types.TuneRequest(float(fc)))
            cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
            cmd.stream_now = True
            rx.issue_stream_cmd(cmd)
            for _ in range(200):   # Descarta el transitorio de sintonía.
                rx.recv(buf, meta, 0.5)
            psd = []
            for _ in range(1000):  # Unos 40 ms, para ver ráfagas TDD de 5 ms.
                rx.recv(buf, meta, 0.5)
                espectro = np.fft.fftshift(np.fft.fft(buf[0] * ventana))
                psd.append(np.abs(espectro[util]) ** 2)
            rx.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))
            psd = np.array(psd)
            filas.append((vuelta, fc / 1e6,
                          10 * np.log10(psd.mean() + 1e-20),
                          10 * np.log10(psd.max(axis=0).mean() + 1e-20),
                          10 * np.log10(np.median(psd) + 1e-20)))

    with open(args.salida, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["vuelta", "centro_MHz", "media_dB", "maxhold_dB", "mediana_dB"])
        for fila in filas:
            w.writerow([fila[0], fila[1]] + [f"{x:.1f}" for x in fila[2:]])


if __name__ == "__main__":
    main()
