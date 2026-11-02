#!/usr/bin/env python3
"""Prueba si K/OPc de config/secretos/usim.env coinciden con la USIM del lector.

Uso: python3 -I scripts/probar_autenticacion.py <IMSI esperado>

Manda UN solo AUTHENTICATE (TS 31.102 §7.1) con SQN=0, sin VERIFY, UPDATE ni
reintentos. No imprime K, OPc, RES, CK, IK ni AUTS.
Milenage según TS 35.206; se valida antes con el test set 1 de TS 35.208.
"""
import ctypes as C
import os
import pathlib
import sys

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def milenage(k, opc, rand, sqn, amf):
    def e(x):
        c = Cipher(algorithms.AES(k), modes.ECB()).encryptor()
        return c.update(x) + c.finalize()

    def rot(x, n):
        return x[n:] + x[:n]

    def c(i):
        return bytes(15) + bytes([i])

    temp = e(xor(rand, opc))
    in1 = sqn + amf + sqn + amf
    out1 = xor(e(xor(temp, rot(xor(in1, opc), 8))), opc)

    def out(n, i):
        return xor(e(xor(rot(xor(temp, opc), n), c(i))), opc)

    o2, o3, o4, o5 = out(0, 1), out(4, 2), out(8, 4), out(12, 8)
    return {"mac_a": out1[:8], "mac_s": out1[8:], "res": o2[8:], "ak": o2[:6],
            "ck": o3, "ik": o4, "ak_s": o5[:6]}


def autotest():
    h = bytes.fromhex
    r = milenage(h("465b5ce8b199b49faa5f0a2ee238a6bc"),
                 h("cd63cb71954a9f4e48a5994e37a02baf"),
                 h("23553cbe9637a89d218ae64dae47bf35"),
                 h("ff9bb4d0b607"), h("b9b9"))
    esperado = {"mac_a": "4a9ffac354dfafb3", "mac_s": "01cfaf9ec4e871e9",
                "res": "a54211d5e3ba50bf", "ak": "aa689c648370",
                "ck": "b40ba9a3c58b2a05bbf0d987b21bf8cb",
                "ik": "f769bcd751044604127672711c6d3441", "ak_s": "451e8beca43b"}
    for nombre, valor in esperado.items():
        if r[nombre].hex() != valor:
            sys.exit(f"Milenage no pasa TS 35.208 en {nombre}; no se toca la tarjeta.")
    print("Milenage: pasa el test set 1 de TS 35.208")


def claves():
    ruta = pathlib.Path(__file__).resolve().parent.parent / "config/secretos/usim.env"
    d = dict(l.strip().split("=", 1) for l in ruta.read_text().splitlines()
             if "=" in l and not l.lstrip().startswith("#"))
    return bytes.fromhex(d["USIM_K"]), bytes.fromhex(d["USIM_OPC"])


def imsi_de(ef):
    digitos = "".join(f"{b & 15:X}{b >> 4:X}" for b in ef[1:9])
    return digitos[1:].rstrip("F")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    autotest()
    k, opc = claves()

    L = C.CDLL("libpcsclite.so.1")
    ctx = C.c_long()
    assert L.SCardEstablishContext(2, None, None, C.byref(ctx)) == 0
    n = C.c_ulong(1024)
    b = C.create_string_buffer(1024)
    assert L.SCardListReaders(ctx, None, b, C.byref(n)) == 0
    lector = b.raw.split(b"\0")[0]
    h = C.c_long()
    proto = C.c_ulong()
    rc = L.SCardConnect(ctx, lector, 2, 3, C.byref(h), C.byref(proto))
    assert rc == 0, hex(rc & 0xffffffff)
    pci = C.addressof(C.c_char.in_dll(L, "g_rgSCardT0Pci" if proto.value == 1 else "g_rgSCardT1Pci"))

    def raw(a):
        buf = (C.c_ubyte * len(a))(*a)
        out = (C.c_ubyte * 300)()
        ln = C.c_ulong(300)
        rc = L.SCardTransmit(h, C.c_void_p(pci), buf, len(a), None, out, C.byref(ln))
        assert rc == 0, hex(rc & 0xffffffff)
        d = bytes(out[:ln.value])
        return d[:-2], d[-2], d[-1]

    def tx(a):
        d, s1, s2 = raw(a)
        if s1 == 0x6C:
            d, s1, s2 = raw(a[:-1] + [s2])
        if s1 in (0x61, 0x9F):
            d, s1, s2 = raw([0, 0xC0, 0, 0, s2])
        return d, s1, s2

    def sel(fid, p1=0):
        return tx([0, 0xA4, p1, 4, len(fid)] + fid + [0])

    sel([0x3F, 0x00])
    sel([0x2F, 0x00])
    r, s1, _ = tx([0, 0xB2, 1, 4, 0x20])
    assert s1 == 0x90 and r[2] == 0x4F, "No se pudo leer EF_DIR"
    aid = list(r[4:4 + r[3]])
    _, s1, s2 = sel(aid, 4)
    assert s1 == 0x90, f"SELECT ADF {s1:02X}{s2:02X}"
    _, s1, s2 = sel([0x6F, 0x07])
    assert s1 == 0x90, f"SELECT IMSI {s1:02X}{s2:02X}"
    ef, s1, s2 = tx([0, 0xB0, 0, 0, 9])
    imsi = imsi_de(ef)
    if imsi != sys.argv[1]:
        sys.exit(f"La tarjeta tiene IMSI {imsi}, no {sys.argv[1]}; no se autentica.")
    print("IMSI de la tarjeta:", imsi)

    rand = os.urandom(16)
    sqn = bytes(6)
    amf = bytes.fromhex("8000")
    m = milenage(k, opc, rand, sqn, amf)
    autn = xor(sqn, m["ak"]) + amf + m["mac_a"]
    d, s1, s2 = tx([0, 0x88, 0, 0x81, 34, 16] + list(rand) + [16] + list(autn))
    print(f"Estado de AUTHENTICATE: {s1:02X}{s2:02X}")

    if (s1, s2) == (0x98, 0x62):
        print("RESULTADO: error de MAC. K/OPc NO coinciden con esta tarjeta.")
    elif s1 == 0x90 and d[:1] == b"\xdc" and d[1] == 14:
        auts = d[2:16]
        sqn_ms = xor(auts[:6], m["ak_s"])
        mac_s = milenage(k, opc, rand, sqn_ms, bytes(2))["mac_s"]
        if mac_s == auts[6:]:
            print("RESULTADO: AUTS con MAC-S válido. K/OPc COINCIDEN.")
            print("SQN de la tarjeta:", int.from_bytes(sqn_ms, "big"))
        else:
            print("RESULTADO: AUTS con MAC-S inválido. Sin confirmar: revisar.")
    elif s1 == 0x90 and d[:1] == b"\xdb":
        print("RESULTADO:", "RES correcto. K/OPc COINCIDEN." if d[2:2 + d[1]] == m["res"]
              else "RES distinto. K/OPc NO coinciden.")
    else:
        print("RESULTADO: respuesta inesperada, sin conclusión.")
    L.SCardDisconnect(h, 0)
    L.SCardReleaseContext(ctx)


if __name__ == "__main__":
    main()
