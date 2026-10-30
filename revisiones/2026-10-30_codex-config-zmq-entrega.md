Creados:

- [network.env](config/open5gs/network.env)
- [open5gs-5gc.yml](config/open5gs/open5gs-5gc.yml)
- [gnb_zmq.yml](config/gnb/gnb_zmq.yml)
- [ue.conf](config/srsue/ue.conf)

Modifiqué únicamente `srsue` en [docker-compose.yml:136](docker-compose.yml#L136): carga `/run/secretos/usim.env`, exige ambas variables y ejecuta srsUE con K/OPc por argumentos.

Elegí **n3 FDD, ARFCN 368500, 20 MHz, 106 PRB, SCS 15 kHz y 23,04 MS/s**. Evidencia en las referencias locales indicadas:

- `s4g/srsue/src/stack/rrc_nr/rrc_nr_procedures.cc:439`: rechaza SCS común distinto de 15 kHz; impide la prueba solicitada con μ=1.
- `ocudu/configs/gnb_rf_b210_fdd_srsUE.yml:5`: respalda n3, 20 MHz y 15 kHz; `:28` fija 23,04 MS/s.
- `s4g/srsue/ue.conf.example:46`: puertos ZMQ 2000/2001.
- `s4g/srsue/src/main.cc:205` y `:208`: existen `usim.opc` y `usim.k`.
- `s4g/srsue/src/stack/upper/nas_5g.cc:534`: SD cero significa omitir SD.

Pasaron las verificaciones estáticas de YAML/INI, opciones de srsUE, sintaxis shell y coherencia de red. Transform precoding queda desactivado por defecto.

**Sin confirmar:** compilación, arranque, registro, sesión PDU, tráfico y coincidencia de credenciales con MongoDB. No ejecuté Docker, sudo ni USRP; no accedí a secretos ni modifiqué los archivos prohibidos.
