#!/bin/bash
set -euo pipefail

# BSD 2-Clause License

# Copyright (c) 2020-2025, Supreeth Herle
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.




[ ${#MNC} == 3 ] && EPC_DOMAIN="epc.mnc${MNC}.mcc${MCC}.3gppnetwork.org" || EPC_DOMAIN="epc.mnc0${MNC}.mcc${MCC}.3gppnetwork.org"
[ ${#MNC} == 3 ] && IMS_DOMAIN="ims.mnc${MNC}.mcc${MCC}.3gppnetwork.org" || IMS_DOMAIN="ims.mnc0${MNC}.mcc${MCC}.3gppnetwork.org"

mkdir -p /var/run/kamailio
mkdir -p /etc/kamailio_pcscf
cp /mnt/pcscf/pcscf.cfg /etc/kamailio_pcscf
cp /mnt/pcscf/pcscf.xml /etc/kamailio_pcscf
cp /mnt/pcscf/kamailio_pcscf.cfg /etc/kamailio_pcscf
cp -r /mnt/pcscf/route /etc/kamailio_pcscf
cp /mnt/pcscf/tls.cfg /etc/kamailio_pcscf
cp /mnt/pcscf/dispatcher.list /etc/kamailio_pcscf

umask 077
python3 /opt/ims/ims_base/sql_init.py
sed -i 's/^#!define WITH_RX$/##!define WITH_RX/' /etc/kamailio_pcscf/pcscf.cfg
if [[ ${IMS_N5:-0} == 1 ]]; then
 sed -i 's/^##!define WITH_N5$/#!define WITH_N5/' /etc/kamailio_pcscf/pcscf.cfg
fi
REGISTRATION_EXPIRES_ENV=3600

sed -i 's|PCSCF_IP|'$PCSCF_IP'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|REGISTRATION_EXPIRES_ENV|'$REGISTRATION_EXPIRES_ENV'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|SCP_IP|'$SCP_IP'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|PCSCF_PUB_IP|'$PCSCF_PUB_IP'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|EPC_DOMAIN|'$EPC_DOMAIN'|g' /etc/kamailio_pcscf/pcscf.cfg
sed -i 's|MYSQL_IP|'$MYSQL_IP'|g' /etc/kamailio_pcscf/pcscf.cfg

sed -i 's|PCSCF_IP|'$PCSCF_IP'|g' /etc/kamailio_pcscf/pcscf.xml
sed -i 's|REGISTRATION_EXPIRES_ENV|'$REGISTRATION_EXPIRES_ENV'|g' /etc/kamailio_pcscf/pcscf.xml
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/kamailio_pcscf/pcscf.xml
sed -i 's|EPC_DOMAIN|'$EPC_DOMAIN'|g' /etc/kamailio_pcscf/pcscf.xml
sed -i 's|PCRF_BIND_PORT|'$PCRF_BIND_PORT'|g' /etc/kamailio_pcscf/pcscf.xml
sed -i 's|PCSCF_BIND_PORT|'$PCSCF_BIND_PORT'|g' /etc/kamailio_pcscf/pcscf.xml

sed -i 's|RTPENGINE_IP|'$RTPENGINE_IP'|g' /etc/kamailio_pcscf/kamailio_pcscf.cfg
sed -i 's|RTPENGINE_IP|'$RTPENGINE_IP'|g' /etc/kamailio_pcscf/route/rtp.cfg

# Add static route to route traffic back to UE as there is not NATing
ip route replace 10.46.0.0/24 via 10.53.2.2
# Route needed for VoWiFi client where internet APN is used


python3 /opt/ims/ims_base/render_password.py
rm -f /kamailio_pcscf.pid
exec kamailio -f /etc/kamailio_pcscf/kamailio_pcscf.cfg -P /kamailio_pcscf.pid -m 32 -M 1024 -DD -E -e $@

# Sync docker time
#ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
