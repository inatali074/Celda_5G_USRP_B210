#!/bin/bash
set -euo pipefail
umask 077
[[ ${IMS_DB_PASSWORD:-} =~ ^[A-Za-z0-9_]{16,}$ && $IMS_DB_PASSWORD != CAMBIAR* ]] || { echo "Configurar IMS_DB_PASSWORD"; exit 1; }

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

cp /mnt/pyhss/config.yaml ./
cp /mnt/pyhss/default_ifc.xml ./
cp /mnt/pyhss/default_sh_user_data.xml ./

INSTALL_PREFIX="/pyhss"

sed -i 's|PYHSS_IP|'$PYHSS_IP'|g' ./config.yaml
sed -i 's|PYHSS_BIND_PORT|'$PYHSS_BIND_PORT'|g' ./config.yaml
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' ./config.yaml
sed -i 's|OP_MCC|'$MCC'|g' ./config.yaml
sed -i 's|OP_MNC|'$MNC'|g' ./config.yaml
sed -i 's|MYSQL_IP|'$MYSQL_IP'|g' ./config.yaml
sed -i 's|INSTALL_PREFIX|'$INSTALL_PREFIX'|g' ./config.yaml

# Sync docker time
#ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

python3 - <<'PYHSS'
import os,yaml
p='config.yaml'
x=yaml.safe_load(open(p));x['database']['password']=os.environ['IMS_DB_PASSWORD']
yaml.safe_dump(x,open(p,'w'))
PYHSS
redis-server --daemonize yes

cd services
python3 apiService.py >/dev/null 2>&1 &
# Sleep is needed to let db be populated in a non-overlapping fashion
sleep 5
python3 diameterService.py &
# Sleep is needed to let db be populated in a non-overlapping fashion
sleep 5
exec python3 hssService.py $@
