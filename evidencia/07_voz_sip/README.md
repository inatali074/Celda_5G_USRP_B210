# Evidencia 07: llamadas de voz SIP entre dos teléfonos (2026-11-12)

Celda n78 TDD, opción 1 del menú (`gnb_b210_00101_n78_cpofdm.yml`). Central Asterisk 20.6 en el contenedor `sip` (`10.53.1.10`), cliente Linphone 6.2.10 en los dos teléfonos.

| Interno | Teléfono | SIM | IP de la sesión PDU |
| --- | --- | --- | --- |
| 1001 | Motorola Edge 30 | SIM 4 (…004) | 10.45.0.4 |
| 1002 | Redmi Note 14 5G | SIM 3 (…003) | 10.45.0.5 |

## Archivos
- `asterisk_llamadas_2026-11-12.log`: log de Asterisk con `pjsip set logger on`, desde los primeros intentos de registro hasta el final de las llamadas. Se reemplazaron por `<redactado>` los valores `nonce`, `cnonce`, `opaque` y `response` de la autenticación Digest, porque permitirían probar contraseñas por fuerza bruta. También se anonimizaron el nombre del dispositivo y el nombre para mostrar de una cuenta.
- `pjsip_contacts_2026-11-12.txt`: estado de los registros al guardar la evidencia.

## Qué muestra
1. **Registro SIP con autenticación Digest** (RFC 3261 §22, MD5 con `qop=auth`): `REGISTER` → `401 Unauthorized` con el desafío → `REGISTER` con `Authorization` → `200 OK`. Los primeros intentos fallaron porque el teléfono tenía una contraseña distinta de la del servidor; se verificó recalculando el Digest.
2. **Eco (600) desde el Redmi:** `INVITE` → `401` → `INVITE` autenticado → `100 Trying` → `Answer()` → `200 OK` con SDP `m=audio … RTP/AVP 8 0` (G.711 ley A y ley μ) → `Echo()`.
3. **Llamadas entre los teléfonos, en los dos sentidos** (líneas con `answered`):
   - Motorola (1001) llama al 1002: `PJSIP/1002-00000005 answered PJSIP/1001-00000004`.
   - Redmi (1002) llama al 1001: `PJSIP/1001-00000007 answered PJSIP/1002-00000006`.
   - En las dos, "Strict RTP learning complete - Locking on source address 10.53.1.2:…" para cada pata: llegó audio RTP de los dos teléfonos y Asterisk lo puenteó. Las llamadas terminan con `BYE` → `200 OK`.
4. **Traducción de direcciones del núcleo:** los paquetes salen del teléfono con su IP de sesión PDU (`Via: … 10.45.0.x`) y llegan a Asterisk desde `10.53.1.2`, la IP del contenedor `open5gs`, por el MASQUERADE del UPF. Por eso PJSIP usa `rtp_symmetric`, `force_rport`, `rewrite_contact` y se identifica a cada teléfono por usuario, no por IP.

## Cómo se relaciona con la teoría
- **El camino de la voz** es teléfono → gNB (PDCP/RLC/MAC sobre NR) → UPF por N3 (GTP-U) → N6 → Asterisk. Es voz sobre IP en la sesión PDU por defecto, con 5QI 9 (no GBR, TS 23.501 tabla 5.7.4-1). **No es VoNR:** VoNR usa IMS, señalización con 5QI 5 y un flujo de voz GBR con 5QI 1 (100 ms de presupuesto de retardo y 10⁻² de pérdida). Acá la voz comparte el flujo con el resto del tráfico, sin prioridad.
- **G.711** usa 64 kbit/s por sentido (más los encabezados RTP/UDP/IP), muy por debajo de la capacidad de subida y bajada de la celda.
- **Llamadas entrantes y ahorro de energía:** cuando Android suspende Linphone, el teléfono deja de contestar los `OPTIONS` de Asterisk (cada 30 s) y la central lo marca "Unavail": una llamada hacia él recibe `404`. En el estado de los registros guardado, el Redmi figura así. Con Linphone en primer plano, los dos contestan con un retardo de ida y vuelta de 30–120 ms.
