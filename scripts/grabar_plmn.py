#!/usr/bin/env python3
"""Cambia el PLMN de una USIM ya grabada, en cualquiera de los dos sentidos.

Uso:
  python3 -I scripts/grabar_plmn.py --probar
  python3 -I scripts/grabar_plmn.py <IMSI actual> <ICCID> <PLMN actual> <IMSI nuevo> <PLMN nuevo> [--escribir]

Prueba 001/01 sobre la SIM 3, y vuelta atrás:
  ... 722999000000003 <ICCID> 722999 001010000000003 00101 --escribir
  ... 001010000000003 <ICCID> 00101 722999000000003 722999 --escribir

Cambios (TS 31.102 v15.7.0), solo los necesarios:
  EF_HPLMNwAcT, EF_OPLMNwAcT, EF_PLMNwAcT (§4.2.54, §4.2.53, §4.2.5): cambia el PLMN de
    las entradas del PLMN actual; conserva el AcT, incluido NG-RAN.
  EF_EHPLMN (§4.2.84): igual, en sus entradas de 3 bytes.
  EF_AD byte 4 (§4.2.18): largo del MNC del PLMN nuevo.
  EF_LOCI byte 11, EF_PSLOCI byte 14, EF_EPSLOCI byte 18 (§4.2.17, §4.2.23, §4.2.91):
    pasan a "not updated" si un teléfono dejó otro estado.
  EF_IMSI (§4.2.2): se escribe al final. Si algo se corta antes, la tarjeta conserva el
    IMSI actual y se puede volver a correr con los mismos argumentos.

No toca K, OPc, ICCID ni usa comandos propietarios. Si el PLMN nuevo está en EF_FPLMN, no
escribe nada. Con la ADM aplica las reglas de grabar_ng_ran.py: una sola presentación, en
ref. 0x0C, con al menos 3 intentos, sin reintentos. Sin --escribir no manda ningún VERIFY.
Antes de escribir guarda los valores originales en evidencia/sim/.

Límites: si se corta durante un UPDATE, o después de escribir EF_IMSI, hay que restaurar a
mano desde la copia. La vuelta atrás restaura el PLMN y el IMSI, pero deja los estados en
"not updated" aunque antes fueran otros.
"""
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from grabar_ng_ran import (ESTADOS, LISTAS, MIN_INTENTOS, NOT_UPDATED, RAIZ, REF_ADM, Tarjeta,
                           exigir, iccid_de, imsi_de, leer_adm)

EHPLMN = 0x6FD9
AD = 0x6FAD
IMSI = 0x6F07
FPLMN = 0x6F7B


def codificar_plmn(plmn):
    """TS 24.008 §10.5.1.3: 722999 -> 279299; 00101 -> 00F110."""
    exigir(len(plmn) in (5, 6) and plmn.isdigit(), f"PLMN inválido: {plmn}")
    mcc, mnc = plmn[:3], plmn[3:]
    d3 = mnc[2] if len(mnc) == 3 else "F"
    return bytes.fromhex(mcc[1] + mcc[0] + d3 + mcc[2] + mnc[1] + mnc[0])


def codificar_imsi(imsi):
    """TS 31.102 §4.2.2: largo, luego dígitos con paridad impar de 15 dígitos."""
    exigir(len(imsi) == 15 and imsi.isdigit(), f"IMSI inválido: {imsi}")
    d = "9" + imsi
    return b"\x08" + bytes(int(d[i + 1] + d[i], 16) for i in range(0, 16, 2))


def reemplazar_entradas(contenido, viejo, nuevo, paso):
    """Devuelve el contenido con el PLMN cambiado en las entradas de `paso` bytes."""
    r = bytearray(contenido)
    for i in range(0, len(r) - len(r) % paso, paso):
        if bytes(r[i:i + 3]) == viejo:
            r[i:i + 3] = nuevo
    return bytes(r)


def tiene_ng_ran(contenido, plmn):
    """Alguna entrada del PLMN con NG-RAN (byte 1 del AcT, b4)."""
    return any(contenido[i:i + 3] == plmn and contenido[i + 3] & 0x08
               for i in range(0, len(contenido) - len(contenido) % 5, 5))


def nuevo_estado(contenido, offset):
    r = bytearray(contenido)
    r[offset] = NOT_UPDATED
    return bytes(r)


def nuevo_ad(contenido, largo_mnc):
    r = bytearray(contenido)
    r[3] = (r[3] & 0xF0) | largo_mnc
    return bytes(r)


def plmn_en(contenido, plmn):
    return any(contenido[i:i + 3] == plmn for i in range(0, len(contenido) - 2, 3))


def diferencias(antes, despues):
    """Tramos contiguos [(offset, bytes nuevos)], para no reescribir el archivo entero."""
    tramos, i = [], 0
    while i < len(antes):
        if antes[i] != despues[i]:
            j = i
            while j < len(antes) and antes[j] != despues[j]:
                j += 1
            tramos.append((i, despues[i:j]))
            i = j
        else:
            i += 1
    return tramos


def probar():
    h = bytes.fromhex
    assert codificar_plmn("722999") == h("279299")
    assert codificar_plmn("00101") == h("00F110")
    assert codificar_imsi("722999000000003") == h("087922990900000030")
    assert imsi_de(codificar_imsi("001010000000003")) == "001010000000003"
    assert codificar_imsi("001010000000003") == h("080910100000000030")
    lista = h("279299480027929980002792990080FFFFFFFFFF")
    nueva = reemplazar_entradas(lista, h("279299"), h("00F110"), 5)
    assert nueva == h("00F110480000F110800000F1100080FFFFFFFFFF")
    assert reemplazar_entradas(nueva, h("00F110"), h("279299"), 5) == lista
    assert reemplazar_entradas(h("279299FFFFFFFFFFFFFFFFFF"), h("279299"), h("00F110"), 3) == h("00F110FFFFFFFFFFFFFFFFFF")
    assert reemplazar_entradas(h("27F243279299"), h("279299"), h("00F110"), 3) == h("27F24300F110")
    assert tiene_ng_ran(lista, h("279299"))
    assert not tiene_ng_ran(h("2792994000FFFFFFFFFF"), h("279299"))
    assert nuevo_ad(h("00000003"), 2) == h("00000002")
    assert nuevo_estado(h("FFFFFFFF279299FFFEFF03"), 10)[10] == 1
    assert plmn_en(h("27021327F243FFFFFF"), h("27F243"))
    assert not plmn_en(h("27021327F243FFFFFF"), h("00F110"))
    assert diferencias(h("00112233"), h("00FF22EE")) == [(1, h("FF")), (3, h("EE"))]
    assert diferencias(h("0011"), h("0011")) == []
    print("Pruebas sin tarjeta: OK")


def escribir(t, fid, offset, datos):
    _, s1, s2 = t.sel([fid >> 8, fid & 255])
    exigir(s1 == 0x90, f"SELECT {fid:04X}: {s1:02X}{s2:02X}")
    _, s1, s2 = t.raw([0, 0xD6, offset >> 8, offset & 255, len(datos)] + list(datos))
    return s1 == 0x90, f"{s1:02X}{s2:02X}"


def main():
    args = sys.argv[1:]
    if args == ["--probar"]:
        probar()
        return
    grabar = "--escribir" in args
    args = [a for a in args if a != "--escribir"]
    if len(args) != 5:
        sys.exit(__doc__)
    imsi_actual, iccid_esperado, plmn_actual, imsi_nuevo, plmn_nuevo = args
    probar()
    exigir(imsi_actual.startswith(plmn_actual), "El IMSI actual no corresponde al PLMN actual.")
    exigir(imsi_nuevo.startswith(plmn_nuevo), "El IMSI nuevo no corresponde al PLMN nuevo.")
    exigir(plmn_actual != plmn_nuevo, "Los PLMN son iguales.")
    viejo, nuevo = codificar_plmn(plmn_actual), codificar_plmn(plmn_nuevo)

    t = Tarjeta()
    t.sel([0x3F, 0x00])
    iccid = iccid_de(t.leer(0x2FE2))
    t.adf()
    imsi = imsi_de(t.leer(IMSI))
    if imsi != imsi_actual or iccid != iccid_esperado:
        sys.exit(f"La tarjeta es IMSI {imsi}, ICCID {iccid}: no es la pedida. No se hace nada.")
    print(f"Tarjeta: IMSI {imsi}, ICCID {iccid}")

    if plmn_en(t.leer(FPLMN), nuevo):
        sys.exit("El PLMN nuevo está en EF_FPLMN. No se hace nada: revisar antes de seguir.")

    # (nombre, fid, contenido actual, contenido deseado). EF_IMSI va último.
    archivos = []
    for nombre, fid in LISTAS.items():
        c = t.leer(fid)
        if any(c[i:i + 3] == nuevo for i in range(0, len(c) - 4, 5)):
            sys.exit(f"{nombre} ya tiene el PLMN nuevo: la vuelta atrás no sería exacta. No se hace nada.")
        if not tiene_ng_ran(c, viejo):
            sys.exit(f"{nombre} no tiene NG-RAN en el PLMN actual. Correr antes grabar_ng_ran.py. No se hace nada.")
        archivos.append((nombre, fid, c, reemplazar_entradas(c, viejo, nuevo, 5)))
    c = t.leer(EHPLMN)
    archivos.append(("EHPLMN", EHPLMN, c, reemplazar_entradas(c, viejo, nuevo, 3)))
    c = t.leer(AD)
    exigir(len(c) >= 4, "EF_AD demasiado corto.")
    archivos.append(("AD", AD, c, nuevo_ad(c, len(plmn_nuevo) - 3)))
    for nombre, (fid, offset, _) in ESTADOS.items():
        c = t.leer(fid)
        archivos.append((nombre, fid, c, nuevo_estado(c, offset)))
    c = t.leer(IMSI)
    archivos.append(("IMSI", IMSI, c, codificar_imsi(imsi_nuevo)))

    planes = [(n, f, c, d, diferencias(c, d)) for n, f, c, d in archivos]
    for nombre, fid, c, _, tramos in planes:
        for offset, datos in tramos:
            viejos = c[offset:offset + len(datos)].hex().upper()
            print(f"  {nombre} ({fid:04X}) offset {offset}: {viejos} -> {datos.hex().upper()}")
    if not grabar:
        print("Sin --escribir: no se mandó VERIFY ni se cambió nada.")
        return

    restantes, estado = t.intentos(REF_ADM)
    print(f"Intentos de ADM en ref. 0x{REF_ADM:02X}: {restantes} (estado {estado})")
    if restantes is None or restantes < MIN_INTENTOS:
        sys.exit("No se puede confirmar que queden intentos suficientes. No se presenta la ADM.")

    marca = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
    copia = RAIZ / f"evidencia/sim/{marca}_{iccid}_antes_plmn.txt"
    copia.parent.mkdir(parents=True, exist_ok=True)
    copia.write_text("".join(f"{n} {f:04X} {c.hex().upper()}\n" for n, f, c, _, _ in planes))
    print("Copia de los valores originales:", copia.relative_to(RAIZ))

    ok, estado = t.verify(REF_ADM, leer_adm())
    if not ok:
        sys.exit(f"ADM rechazada ({estado}). No se reintenta ni se cambió nada.")
    print("ADM aceptada")

    for nombre, fid, _, deseado, tramos in planes:
        for offset, datos in tramos:
            ok, estado = escribir(t, fid, offset, datos)
            if not ok:
                sys.exit(f"Falló la escritura de {nombre} ({estado}). Se corta acá; "
                         "los anteriores quedaron escritos, ver la copia.")
        leido = t.leer(fid)
        if leido != deseado:
            sys.exit(f"{nombre}: la relectura NO coincide: {leido.hex().upper()}. "
                     "Se corta acá; los anteriores quedaron escritos, ver la copia.")
        print(f"{nombre}: {leido.hex().upper()[:40]} (relectura correcta)")
    print("RESULTADO: grabación verificada.")


if __name__ == "__main__":
    main()
