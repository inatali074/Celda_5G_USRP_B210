# Etapa: registro (parcial, 2026-10-30)

**Confirma:** N2. El gNB abre la asociación SCTP con el AMF (puerto 38412) y completa NG Setup con PLMN 722/999 (`2026-10-30_n2_gnb.log`, `2026-10-30_n2_amf.log`).

**No confirma:** 5G-AKA, registro ni sesión PDU. srsUE se detiene en `NAS5G Switching on` (`2026-10-30_srsue_parado.log`), antes de la búsqueda de celda.

## Registro real por aire (2026-10-30, 14:25 hora local)
`2026-10-30_registro_real_amf.log`: la SIM 1 presenta SUCI con esquema nulo (`suci-0-722-999-0-0-0-…`), hay una falla de sincronización esperada (causa 21, AUTS: la tarjeta tenía el SQN adelantado), se resincroniza y termina en `Registration complete`. Confirma 5G-AKA con Milenage (TS 33.501 §6.1) con una USIM sin DF_5GS.

**No confirma sesión PDU:** a los 3 s el gNB informa que el UE no la pidió, y luego el UE se da de baja.
