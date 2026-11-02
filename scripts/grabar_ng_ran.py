#!/usr/bin/env python3
"""Agrega NG-RAN a las listas de PLMN de una USIM ya grabada y limpia sus estados de rechazo.

Uso:
  python3 -I scripts/grabar_ng_ran.py --probar
  python3 -I scripts/grabar_ng_ran.py <IMSI> <ICCID>             # sin escribir ni presentar ADM
  python3 -I scripts/grabar_ng_ran.py <IMSI> <ICCID> --escribir

Cambios (TS 31.102 v15.7.0), un byte por archivo y solo si hace falta:
  EF_HPLMNwAcT, EF_OPLMNwAcT, EF_PLMNwAcT: en las entradas 722/999 con E-UTRAN
    (AcT '4000'), prende NG-RAN (byte 1, b4): '4000' -> '4800' (§4.2.54, §4.2.53, §4.2.5).
  EF_LOCI byte 11 '03' -> '01', EF_PSLOCI byte 14 '03' -> '01',
    EF_EPSLOCI byte 18 '02' -> '01': pasan a "not updated" (§4.2.17, §4.2.23, §4.2.91).

No toca K, OPc, IMSI, ICCID ni comandos propietarios. Presenta la ADM como mucho una
vez, solo en la referencia 0x0C, nunca en 0x0A (ADM1, 3 intentos), y solo si quedan al
menos 3 intentos. Sin --escribir no manda ningún VERIFY: la consulta de intentos (P3=0)
está definida para PIN en TS 102 221 §11.1.9 y no está garantizada para esta referencia
en esta tarjeta. Un fallo o una relectura distinta corta la ejecución, sin reintentos.
Antes de escribir guarda los valores originales en evidencia/sim/. No imprime la ADM.
"""
import ctypes as C
import datetime
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLMN = bytes.fromhex("279299")  # 722/999, TS 24.008
REF_ADM = 0x0C
MIN_INTENTOS = 3
LISTAS = {"HPLMNwAcT": 0x6F62, "OPLMNwAcT": 0x6F61, "PLMNwAcT": 0x6F60}
ESTADOS = {"LOCI": (0x6F7E, 10, 0x03), "PSLOCI": (0x6F73, 13, 0x03), "EPSLOCI": (0x6FE3, 17, 0x02)}
NOT_UPDATED = 0x01


def exigir(condicion, mensaje):
    """Comprobación que no desaparece con python -O, a diferencia de assert."""
    if not condicion:
        sys.exit(mensaje)


def cambios_lista(contenido):
    """Devuelve [(offset, valor)] para prender NG-RAN en las entradas 722/999 con E-UTRAN."""
    cambios = []
    for i in range(0, len(contenido) - len(contenido) % 5, 5):
        if contenido[i:i + 3] == PLMN and contenido[i + 3:i + 5] == b"\x40\x00":
            cambios.append((i + 3, 0x48))
    return cambios


def cambios_estado(contenido, offset, rechazo):
    if len(contenido) > offset and contenido[offset] == rechazo:
        return [(offset, NOT_UPDATED)]
    return []


def aplicar(contenido, cambios):
    r = bytearray(contenido)
    for offset, valor in cambios:
        r[offset] = valor
    return bytes(r)


def imsi_de(ef):
    return "".join(f"{b & 15:X}{b >> 4:X}" for b in ef[1:9])[1:].rstrip("F")


def iccid_de(ef):
    return "".join(f"{b & 15:X}{b >> 4:X}" for b in ef).rstrip("F")


def probar():
    h = bytes.fromhex
    hplmn = h("279299400027929980002792990080")
    assert cambios_lista(hplmn) == [(3, 0x48)]
    assert aplicar(hplmn, cambios_lista(hplmn)) == h("279299480027929980002792990080")
    assert cambios_lista(aplicar(hplmn, [(3, 0x48)])) == []
    assert cambios_lista(h("27F243400027929900800000")) == []
    assert cambios_lista(h("FF" * 15)) == []
    assert cambios_estado(h("FFFFFFFF279299FFFEFF03"), 10, 3) == [(10, 1)]
    assert cambios_estado(h("FFFFFFFF279299FFFEFF01"), 10, 3) == []
    assert cambios_estado(h("FFFFFFFFFFFFFF279299FFFEFF03"), 13, 3) == [(13, 1)]
    assert cambios_estado(h("0BF6" + "FF" * 15 + "02"), 17, 2) == [(17, 1)]
    assert imsi_de(h("087922990900000030")) == "722999000000003"
    assert iccid_de(h("98103254769810325476")) == "89012345678901234567"
    print("Pruebas sin tarjeta: OK")


class Tarjeta:
    def __init__(self):
        self.L = C.CDLL("libpcsclite.so.1")
        self.ctx = C.c_long()
        exigir(self.L.SCardEstablishContext(2, None, None, C.byref(self.ctx)) == 0, "Sin contexto PC/SC")
        n = C.c_ulong(1024)
        b = C.create_string_buffer(1024)
        exigir(self.L.SCardListReaders(self.ctx, None, b, C.byref(n)) == 0, "Sin lector")
        self.h = C.c_long()
        proto = C.c_ulong()
        rc = self.L.SCardConnect(self.ctx, b.raw.split(b"\0")[0], 2, 3, C.byref(self.h), C.byref(proto))
        exigir(rc == 0, "SCardConnect " + hex(rc & 0xffffffff))
        nombre = "g_rgSCardT0Pci" if proto.value == 1 else "g_rgSCardT1Pci"
        self.pci = C.addressof(C.c_char.in_dll(self.L, nombre))

    def raw(self, a):
        buf = (C.c_ubyte * len(a))(*a)
        out = (C.c_ubyte * 300)()
        ln = C.c_ulong(300)
        rc = self.L.SCardTransmit(self.h, C.c_void_p(self.pci), buf, len(a), None, out, C.byref(ln))
        exigir(rc == 0, "SCardTransmit " + hex(rc & 0xffffffff))
        d = bytes(out[:ln.value])
        return d[:-2], d[-2], d[-1]

    def tx(self, a):
        """Solo para SELECT y READ. VERIFY y UPDATE usan raw, sin repetir el comando."""
        datos, cmd = b"", a
        for _ in range(8):
            d, s1, s2 = self.raw(cmd)
            datos += d
            if s1 == 0x6C:
                cmd = cmd[:-1] + [s2]
            elif s1 in (0x61, 0x9F):
                cmd = [0, 0xC0, 0, 0, s2]
            else:
                return datos, s1, s2
        sys.exit("Demasiados 61xx/6Cxx seguidos; se corta.")

    def sel(self, fid, p1=0):
        return self.tx([0, 0xA4, p1, 4, len(fid)] + fid + [0])

    def adf(self):
        self.sel([0x3F, 0x00])
        self.sel([0x2F, 0x00])
        r, s1, _ = self.tx([0, 0xB2, 1, 4, 0x20])
        exigir(s1 == 0x90 and len(r) > 4 and r[2] == 0x4F, "No se pudo leer EF_DIR")
        _, s1, s2 = self.sel(list(r[4:4 + r[3]]), 4)
        exigir(s1 == 0x90, f"SELECT ADF {s1:02X}{s2:02X}")

    def leer(self, fid):
        d, s1, s2 = self.sel([fid >> 8, fid & 255])
        exigir(s1 == 0x90, f"SELECT {fid:04X}: {s1:02X}{s2:02X}")
        i, n = 2, 0
        while i < len(d):
            if d[i] == 0x80:
                n = int.from_bytes(d[i + 2:i + 2 + d[i + 1]], "big")
                break
            i += 2 + d[i + 1]
        exigir(0 < n <= 4096, f"Tamaño de {fid:04X}: {n}")
        r = b""
        while len(r) < n:
            parte = min(n - len(r), 255)
            d, s1, s2 = self.tx([0, 0xB0, len(r) >> 8, len(r) & 255, parte])
            exigir(s1 == 0x90 and len(d) == parte, f"READ {fid:04X}: {s1:02X}{s2:02X}")
            r += d
        return r

    def intentos(self, ref):
        """VERIFY sin datos (TS 102 221 §11.1.9). Sin garantía para esta referencia: solo con --escribir."""
        _, s1, s2 = self.raw([0, 0x20, 0, ref, 0])
        return s2 & 15 if s1 == 0x63 and s2 & 0xF0 == 0xC0 else None, f"{s1:02X}{s2:02X}"

    def verify(self, ref, clave):
        _, s1, s2 = self.raw([0, 0x20, 0, ref, len(clave)] + list(clave))
        return s1 == 0x90, f"{s1:02X}{s2:02X}"

    def escribir_byte(self, fid, offset, valor):
        d, s1, s2 = self.sel([fid >> 8, fid & 255])
        exigir(s1 == 0x90, f"SELECT {fid:04X}: {s1:02X}{s2:02X}")
        _, s1, s2 = self.raw([0, 0xD6, offset >> 8, offset & 255, 1, valor])
        return s1 == 0x90, f"{s1:02X}{s2:02X}"


def leer_adm():
    ruta = RAIZ / "config/secretos/sim_adm.env"
    d = dict(l.strip().split("=", 1) for l in ruta.read_text().splitlines() if "=" in l)
    clave = bytes.fromhex(d["SIM_ADM_HEX"])
    if len(clave) != 8:
        sys.exit("SIM_ADM_HEX debe tener 8 bytes.")
    return clave


def main():
    args = sys.argv[1:]
    if args == ["--probar"]:
        probar()
        return
    escribir = "--escribir" in args
    args = [a for a in args if a != "--escribir"]
    if len(args) != 2:
        sys.exit(__doc__)
    imsi_esperado, iccid_esperado = args
    probar()

    t = Tarjeta()
    t.sel([0x3F, 0x00])
    iccid = iccid_de(t.leer(0x2FE2))
    t.adf()
    imsi = imsi_de(t.leer(0x6F07))
    if imsi != imsi_esperado or iccid != iccid_esperado:
        sys.exit(f"La tarjeta es IMSI {imsi}, ICCID {iccid}: no es la pedida. No se hace nada.")
    print(f"Tarjeta: IMSI {imsi}, ICCID {iccid}")

    archivos = {}
    for nombre, fid in LISTAS.items():
        c = t.leer(fid)
        archivos[nombre] = (fid, c, cambios_lista(c))
    for nombre, (fid, offset, rechazo) in ESTADOS.items():
        c = t.leer(fid)
        archivos[nombre] = (fid, c, cambios_estado(c, offset, rechazo))

    pendientes = 0
    for nombre, (fid, c, cambios) in archivos.items():
        pendientes += len(cambios)
        for offset, valor in cambios:
            print(f"  {nombre} ({fid:04X}) byte {offset + 1}: {c[offset]:02X} -> {valor:02X}")
    if not pendientes:
        print("No hay nada para cambiar.")
        return

    if not escribir:
        print("Sin --escribir: no se mandó VERIFY ni se cambió nada.")
        return
    restantes, estado = t.intentos(REF_ADM)
    print(f"Intentos de ADM en ref. 0x{REF_ADM:02X}: {restantes} (estado {estado})")
    if restantes is None or restantes < MIN_INTENTOS:
        sys.exit("No se puede confirmar que queden intentos suficientes. No se presenta la ADM.")

    marca = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
    copia = RAIZ / f"evidencia/sim/{marca}_{iccid}_antes.txt"
    copia.parent.mkdir(parents=True, exist_ok=True)
    copia.write_text("".join(f"{n} {f:04X} {c.hex().upper()}\n" for n, (f, c, _) in archivos.items()))
    print("Copia de los valores originales:", copia.relative_to(RAIZ))

    ok, estado = t.verify(REF_ADM, leer_adm())
    if not ok:
        sys.exit(f"ADM rechazada ({estado}). No se reintenta ni se cambió nada.")
    print("ADM aceptada")

    for nombre, (fid, c, cambios) in archivos.items():
        for offset, valor in cambios:
            ok, estado = t.escribir_byte(fid, offset, valor)
            if not ok:
                sys.exit(f"Falló la escritura de {nombre} byte {offset + 1} ({estado}). "
                         "Se corta acá; los anteriores quedaron escritos, ver la copia.")
        leido = t.leer(fid)
        if leido != aplicar(c, cambios):
            sys.exit(f"{nombre}: la relectura NO coincide: {leido.hex().upper()}. "
                     "Se corta acá; los anteriores quedaron escritos, ver la copia.")
        print(f"{nombre}: {leido.hex().upper()[:40]} (relectura correcta)")
    print("RESULTADO: grabación verificada.")


if __name__ == "__main__":
    main()
