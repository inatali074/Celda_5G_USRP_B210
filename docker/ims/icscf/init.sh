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

[ ${#MNC} == 3 ] && IMS_DOMAIN="ims.mnc${MNC}.mcc${MCC}.3gppnetwork.org" || IMS_DOMAIN="ims.mnc0${MNC}.mcc${MCC}.3gppnetwork.org"

mkdir -p /var/run/kamailio
mkdir -p /etc/kamailio_icscf
cp /mnt/icscf/icscf.cfg /etc/kamailio_icscf
cp /mnt/icscf/icscf.xml /etc/kamailio_icscf
cp /mnt/icscf/kamailio_icscf.cfg /etc/kamailio_icscf

umask 077
python3 /opt/ims/ims_base/sql_init.py
mysql icscf <<SQL
INSERT INTO nds_trusted_domains (trusted_domain) SELECT '$IMS_DOMAIN' WHERE NOT EXISTS (SELECT 1 FROM nds_trusted_domains WHERE trusted_domain='$IMS_DOMAIN');
INSERT INTO s_cscf (name,s_cscf_uri) SELECT 'S-CSCF','sip:scscf.$IMS_DOMAIN:6060' WHERE NOT EXISTS (SELECT 1 FROM s_cscf WHERE s_cscf_uri='sip:scscf.$IMS_DOMAIN:6060');
INSERT INTO s_cscf_capabilities (id_s_cscf,capability) SELECT id,0 FROM s_cscf WHERE NOT EXISTS (SELECT 1 FROM s_cscf_capabilities WHERE id_s_cscf=s_cscf.id);
SQL
REGISTRATION_EXPIRES_ENV=3600

sed -i 's|ICSCF_IP|'$ICSCF_IP'|g' /etc/kamailio_icscf/icscf.cfg
sed -i 's|REGISTRATION_EXPIRES_ENV|'$REGISTRATION_EXPIRES_ENV'|g' /etc/kamailio_icscf/icscf.cfg
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/kamailio_icscf/icscf.cfg
sed -i 's|MYSQL_IP|'$MYSQL_IP'|g' /etc/kamailio_icscf/icscf.cfg

sed -i 's|ICSCF_IP|'$ICSCF_IP'|g' /etc/kamailio_icscf/icscf.xml
sed -i 's|REGISTRATION_EXPIRES_ENV|'$REGISTRATION_EXPIRES_ENV'|g' /etc/kamailio_icscf/icscf.xml
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/kamailio_icscf/icscf.xml
sed -i 's|PYHSS_BIND_PORT|'$PYHSS_BIND_PORT'|g' /etc/kamailio_icscf/icscf.xml
sed -i 's|ICSCF_BIND_PORT|'$ICSCF_BIND_PORT'|g' /etc/kamailio_icscf/icscf.xml

python3 /opt/ims/ims_base/render_password.py
rm -f /kamailio_icscf.pid
exec kamailio -f /etc/kamailio_icscf/kamailio_icscf.cfg -P /kamailio_icscf.pid -DD -E -e $@

# Sync docker time
#ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
