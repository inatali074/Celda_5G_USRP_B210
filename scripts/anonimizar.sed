#!/bin/sed -Ef
# Oculta el identificador de todo abonado que no sea de los PLMN de laboratorio.
# Decide por identificador, no por línea: protege los de laboratorio, oculta el resto y los restaura.
s/suci-0-(001-01|722-999)-/@LABSUCI@\1-/g
s/imsi-(00101|722999)/@LABIMSI@\1/g
s/suci-0-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9a-fA-F]+/&@/g
s/(suci-0-[0-9]+-[0-9]+-[0-9]+-[0-9]+-[0-9]+-)[0-9a-fA-F]+@/\1ANONIMIZADO/g
s/imsi-([0-9]{5})[0-9]+/imsi-\1ANONIMIZADO/g
s/@LABSUCI@/suci-0-/g
s/@LABIMSI@/imsi-/g
