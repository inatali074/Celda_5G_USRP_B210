# Solo lectura: SELECT y READ BINARY/RECORD. Nunca VERIFY, AUTHENTICATE, UPDATE ni comandos propietarios.
import ctypes as C
L = C.CDLL("libpcsclite.so.1")
ctx = C.c_long(); assert L.SCardEstablishContext(2, None, None, C.byref(ctx)) == 0
n = C.c_ulong(1024); b = C.create_string_buffer(1024)
rc = L.SCardListReaders(ctx, None, b, C.byref(n))
assert rc == 0, hex(rc & 0xffffffff)
r = b.raw.split(b"\0")[0]; print("lector:", r.decode())
h = C.c_long(); proto = C.c_ulong()
rc = L.SCardConnect(ctx, r, 2, 3, C.byref(h), C.byref(proto))
assert rc == 0, "SCardConnect " + hex(rc & 0xffffffff)
print("protocolo T=" + str(proto.value - 1))
pci = C.c_void_p.in_dll(L, "g_rgSCardT0Pci") if False else C.addressof(C.c_char.in_dll(L, "g_rgSCardT0Pci" if proto.value == 1 else "g_rgSCardT1Pci"))
H = lambda x: bytes(x).hex().upper()
rl = C.c_ulong(0); al = C.c_ulong(64); atr = (C.c_ubyte * 64)(); st = C.c_ulong(); pr = C.c_ulong()
L.SCardStatus(h, None, C.byref(rl), C.byref(st), C.byref(pr), atr, C.byref(al))
print("ATR:", H(atr[:al.value]))
def raw(a):
    buf = (C.c_ubyte * len(a))(*a); out = (C.c_ubyte * 300)(); ln = C.c_ulong(300)
    rc = L.SCardTransmit(h, C.c_void_p(pci), buf, len(a), None, out, C.byref(ln))
    assert rc == 0, hex(rc & 0xffffffff)
    d = list(out[:ln.value]); return d[:-2], d[-2], d[-1]
def tx(a):
    d, s1, s2 = raw(a)
    if s1 == 0x6C: d, s1, s2 = raw(a[:-1] + [s2])
    if s1 in (0x61, 0x9F): d, s1, s2 = raw([0, 0xC0, 0, 0, s2])
    return d, s1, s2
def sel(fid, p1=0):
    return tx([0, 0xA4, p1, 4, len(fid)] + fid + [0])
def size(fcp):
    i = 2
    while i < len(fcp):
        t, l = fcp[i], fcp[i+1]
        if t == 0x80: return int.from_bytes(fcp[i+2:i+2+l], "big")
        i += 2 + l
    return 0
def rd(fid):
    d, s1, s2 = sel(fid)
    if s1 != 0x90: return f"{s1:02X}{s2:02X}"
    n = size(d)
    if not n: return "sin tamaño"
    r, a, b = tx([0, 0xB0, 0, 0, min(n, 255)])
    return H(r) if a == 0x90 else f"{a:02X}{b:02X}"
sel([0x3F, 0x00])
print("ICCID 2FE2:", rd([0x2F, 0xE2]))
d, s1, s2 = sel([0x2F, 0x00])
aid = None
if s1 == 0x90:
    r, a, b = tx([0, 0xB2, 1, 4, 0x20])
    if a == 0x90 and len(r) > 4 and r[2] == 0x4F:
        aid = r[4:4+r[3]]
print("AID USIM:", H(aid) if aid else None)
if aid:
    d, s1, s2 = sel(aid, 4)
    print("SELECT ADF:", f"{s1:02X}{s2:02X}")
    for n, f in [("IMSI", 0x6F07), ("AD", 0x6FAD), ("UST", 0x6F38), ("HPLMNwAcT", 0x6F62), ("OPLMNwAcT", 0x6F61), ("PLMNwAcT", 0x6F60), ("EHPLMN", 0x6FD9), ("FPLMN", 0x6F7B), ("SPN", 0x6F46)]:
        print(f"{n}:", rd([f >> 8, f & 255]))
    d, s1, s2 = sel([0x5F, 0xC0])
    print("DF_5GS 5FC0:", f"{s1:02X}{s2:02X}")
    # Estado que escribe el teléfono: ubicación y contexto de EPS.
    for n, f in [("LOCI", 0x6F7E), ("PSLOCI", 0x6F73), ("EPSLOCI", 0x6FE3), ("EPSNSC", 0x6FE4)]:
        print(f"{n}:", rd([f >> 8, f & 255]))
