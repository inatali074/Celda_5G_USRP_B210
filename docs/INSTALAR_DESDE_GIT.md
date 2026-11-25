# Instalar la celda en otra PC desde GitHub

Esta guía deja una PC recién clonada igual que las PC donde ya funciona la celda: OCUDU (gNB) con USRP B210, Open5GS, MongoDB y el panel web, todo en Docker. La puede seguir una persona o una IA. Los pasos están en orden y cada uno termina con un chequeo.

Si tenés un pendrive armado con `scripts/empaquetar_para_otra_pc.sh`, usá en cambio [`LEVANTAR_EN_OTRA_PC.md`](LEVANTAR_EN_OTRA_PC.md): ese paquete ya trae las imágenes y las claves. Después de instalar desde un paquete, comprobá `docker image inspect 5g-dashboard:latest`. Si falta, porque el paquete es de una versión anterior del empaquetador, corré `docker compose build dashboard`.

## Para una IA que siga esta guía
- **Lo que decide y hace la persona, no la IA:**
  - **Iniciar el gNB o transmitir con la B210.** Lo hace la persona en el paso 8, con el botón **Iniciar** del panel o con una opción de `./start.sh`, dentro de la jaula de Faraday o en un entorno de RF autorizado.
  - **Todo lo que lleva `sudo` o cambia la red o el firewall** (pasos 1, 7 y 10). La IA muestra el comando, explica qué cambia y espera. La oferta de `sudo` del lanzador también la acepta o rechaza la persona.
  - **Las claves de las SIM** (K, OPc, ADM). La IA no las inventa, no las busca, no abre esos archivos y no los muestra. Las consigue la persona (paso 4).
- Todo lo del proyecto va en contenedores (consigna de los docentes). No instales Open5GS, MongoDB ni el gNB en el host.
- No subas a GitHub `config/secretos/`, `.env`, `*.local.*`, `logs/` ni paquetes armados para otra PC. El repo es público.
- `CLAUDE.md`, `AGENTS.md` y `GEMINI.md` describen el trabajo del grupo original, con tres IAs y archivos locales que no vienen en el clon. Para instalar alcanza esta guía.

## 1. Requisitos de la PC
| Requisito | Por qué | Cómo se comprueba |
|---|---|---|
| Linux x86-64 con Docker Engine nativo (no Docker Desktop, que no pasa el USB). Funciona en Ubuntu 25.04 y 26.04 y en Debian 13 | Acceso del contenedor a la B210 | `cat /etc/os-release` y `docker info \| grep -i 'operating system'` |
| CPU con AVX2 (nivel x86-64-v3), 8 o más hilos | Las imágenes se compilan con `x86-64-v3`; el gNB procesa en tiempo real | `grep -m1 -o -w avx2 /proc/cpuinfo` y `nproc`. Con glibc reciente: `/lib64/ld-linux-x86-64.so.2 --help \| grep x86-64-v3` dice `supported` |
| 16 GB de RAM o más, y 30 GB libres | Compilar OCUDU y las imágenes (~8 GB) | `free -h` y `df -h ~` |
| USB 3, directo, sin hub | La B210 a 23,04 MS/s no entra en USB 2 | Con la B210 conectada: `lsusb \| grep -E '2500:00(20\|21)\|04b4:00f3'` y `lsusb -t` (tiene que decir `5000M`) |
| Docker Compose **2.24 o posterior** | `docker-compose.yml` usa `env_file` con `required` | `docker compose version` |
| `git`, `screen`, `python3`, `lsusb`, `flock`, `setsid` | Scripts de arranque, consola, panel y lanzador | `command -v git screen python3 lsusb flock setsid` |
| Módulos `tun` y `sctp` | Túnel del UPF y N2 entre gNB y AMF | `ls /dev/net/tun` y `modinfo sctp` |

**Si falta software, la persona lo instala:**
```bash
# Ubuntu
sudo apt install docker.io docker-compose-v2 git screen usbutils python3 util-linux
# Debian 13 (ahí el paquete de Compose v2 se llama docker-compose)
sudo apt install docker.io docker-compose git screen usbutils python3 util-linux

sudo usermod -aG docker "$USER"    # después cerrar sesión y volver a entrar
```
Chequeo: `docker info` responde sin sudo.

## 2. Clonar
```bash
git clone https://github.com/inatali074/Celda_5G_USRP_B210.git ~/Celda_5G_USRP_B210
cd ~/Celda_5G_USRP_B210
docker compose config --quiet && echo "compose ok"
```
No uses la carpeta `~/red5g`: en las PC del grupo es un antecedente de solo lectura.

## 3. `.env`: no hace falta, y mejor no importar uno
Con los valores por defecto de `docker-compose.yml` arranca todo; no hace falta crear un `.env`. Compose lo lee si existe, y un `.env` traído de otra PC puede cambiar `GNB_CONFIG`, `OPEN5GS_CONFIG` o `COMPOSE_PROJECT_NAME`. Con otro nombre de proyecto, los contenedores dejan de llamarse `5g-…` y los scripts no los encuentran. Hacé el primer arranque sin `.env` ni archivos `docker-compose.override.yml`.

## 4. Secretos
Van en `config/secretos/`, que no está en git: la carpeta con permisos 700 y cada archivo con 600. El bloque no pisa un archivo que ya exista:
```bash
(umask 077; mkdir -p config/secretos)
[ -e config/secretos/usim.env ] || (umask 077; cp config/usim.ejemplo.env config/secretos/usim.env)
```
Después la persona completa `USIM_K` y `USIM_OPC`.

| Archivo | Para qué | ¿Obligatorio? | De dónde sale |
|---|---|---|---|
| `usim.env` | K y OPc de las SIM de laboratorio, para dar de alta los abonados en Open5GS | **Sí** | Pedírselas a un integrante del grupo por un canal privado. **No** están en el repo |
| `sip_credenciales.conf` | Contraseñas de los internos SIP | Solo para la central SIP (paso 11) | Copiar `config/sip/credenciales.ejemplo.conf` y poner contraseñas propias |
| `ims_mysql.env` | Contraseñas de la base de IMS | Solo para IMS (paso 11) | Ver `docker/ims/README.md` |
| `sim_adm.env` | ADM para regrabar las SIM | No: solo para grabar SIM | El grupo, si hace falta |

Una IA solo comprueba que existan y tengan permisos 600, con `ls -l config/secretos/`. No los abre.

## 5. Construir las imágenes
Llevan entre 30 minutos y unas horas, según la PC, y requieren internet. No transmiten.
```bash
docker pull mongo:6.0
docker compose build open5gs dashboard
docker compose --profile radio build gnb-radio
```
- `gnb-radio` compila OCUDU `release_26_10` en un commit fijado, con UHD 4.9.0.1, y baja el firmware de la B210 dentro de la imagen. Los Dockerfile bajan el commit exacto, no la etiqueta, así que el código fuente no cambia aunque la etiqueta se mueva (el build sigue necesitando que GitLab y GitHub sirvan ese commit). No cambies los commits por tu cuenta.
- Con poca RAM el compilador se puede quedar sin memoria. Ya usa `NUM_JOBS: "2"` en `docker-compose.yml`.

Chequeo: `docker images` muestra `5g-open5gs`, `5g-dashboard`, `5g-gnb-radio` y `mongo:6.0`. El lanzador y `start.sh` usan `--no-build`, así que si falta una imagen, no arrancan.

## 6. Cargar los abonados
```bash
docker compose up -d --no-build --wait --wait-timeout 180 mongodb || { echo "MongoDB no quedó sano"; exit 1; }
for imsi in 001010000000003 001010000000004; do
    bash scripts/cargar_abonado.sh "$imsi" || { echo "Falló la carga de $imsi"; break; }
done
docker compose stop mongodb
```
- Son la SIM 3 y la SIM 4, con PLMN 001/01 (ver la tabla de SIM en `PROYECTO.md`). Si tenés otras tarjetas, confirmá primero su IMSI.
- `cargar_abonado.sh` lee K y OPc de `config/secretos/usim.env` sin mostrarlos, y usa **el mismo par para todos los IMSI**. Antes de cargar, la persona confirma que sus tarjetas tienen esas claves.

## 7. Ajustes del host (los aprueba la persona)
Estos comandos cambian el sistema y duran hasta reiniciar.
```bash
# Módulos del kernel: túnel del UPF y SCTP del N2
sudo modprobe tun
sudo modprobe sctp

# La CPU no baja la frecuencia (el lanzador también lo ofrece)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Buffers de red que recomienda UHD
sudo sysctl -w net.core.wmem_max=33554432 net.core.rmem_max=33554432
```
Chequeos, sin sudo:
- `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor` da `performance`.
- `ls /dev/net/tun` existe.
- `ip route` y `docker network ls` no muestran otra red en `10.53.1.0/24`, `10.53.2.0/24` ni `10.45.0.0/16`. Si se superponen, Compose falla al crear las redes; ver la sección «Subredes superpuestas» de `LEVANTAR_EN_OTRA_PC.md`.

## 8. Ícono y primer arranque (lo hace la persona)
```bash
scripts/instalar_lanzador.sh    # una sola vez: crea "Celda 5G" en el escritorio y en el menú
```
1. **En GNOME,** si el ícono aparece con una cruz, hacé clic derecho y elegí «Permitir ejecutar». En KDE puede pedir confirmación la primera vez. Sin entorno gráfico, o si el ícono no anda: `bash scripts/lanzador.sh` desde una terminal.
2. **Doble clic en el ícono:**
   - abre una terminal que ofrece pasar la CPU a `performance` (con sudo: lo decide la persona);
   - levanta MongoDB, Open5GS y el panel (`http://localhost:8080`) **sin radio**.
   - **No cierres esa terminal:** al cerrarla se apaga todo.
3. **En el panel,** arriba, la persona elige la configuración y aprieta **Iniciar**. Recién ahí transmite la B210.

| Opción | Banda | Subida |
|---|---|---|
| 1 | n78 TDD, 3525 MHz | CP-OFDM (la más usada; recomendada para empezar) |
| 2 | n78 TDD | DFT-s-OFDM |
| 3 | n3 FDD, 1842,5 / 1747,5 MHz | CP-OFDM |
| 4 | n3 FDD | DFT-s-OFDM |

Sin el panel: `./start.sh` muestra el mismo menú y `./stop.sh` apaga todo.

## 9. Comprobar que funciona
1. Consola del gNB (`screen -r red5g`, o `docker logs 5g-gnb-radio-1`). Tiene que decir:
   - `Operating over USB 3`;
   - `N2: Connection to AMF ... completed`;
   - `gNB started`.
2. En el panel no aparecen líneas `~ tiempo real` todos los segundos. Si aparece "UL processor is busy" seguido, reiniciá la celda.
3. Teléfono con la SIM 3 o la SIM 4:
   - red **solo 5G (NR only / SA)**;
   - APN `Metodos1`, MCC `001`, MNC `01`, IPv4.

   En el panel tiene que aparecer registrado y con IP `10.45.0.x`.
4. Salida a Internet desde el núcleo: `docker compose exec -T dashboard ping -c 3 8.8.8.8`. El panel comparte la red de Open5GS y trae `ping`. Después, comprobá que el teléfono navegue.

## 10. Si algo falla
| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `Operating over USB 2`, o la B210 no aparece | Puerto USB 2 o hub | Conectarla directa a un puerto USB 3 y mirar `lsusb -t` |
| El gNB no encuentra la B210 aunque `lsusb` la ve | Docker Desktop o permisos USB | Usar Docker Engine nativo. Si hacen falta reglas udev, las agrega la persona |
| Compose falla al crear redes o contenedores | Subredes superpuestas | Leer el error de Compose; paso 7 |
| Open5GS no queda `healthy` | Falta `tun` o `sctp` | Paso 7; `docker logs 5g-open5gs-1` |
| El teléfono no ve la red | Teléfono fuera de SA o con otra PLMN | Modo NR only; la celda usa 001/01 |
| Se registra pero no navega | NAT o firewall del host | «Salida a Internet» en `LEVANTAR_EN_OTRA_PC.md`; los cambios de red los hace la persona |
| "UL processor is busy" seguido | La CPU no alcanza el tiempo real | Governor en `performance`; reiniciar la celda |
| La terminal del lanzador se cerró de golpe, o `start.sh` dice que el gNB no arrancó | Apagado sin confirmar | Correr `./stop.sh` y confirmar con `docker ps` que no quede `5g-gnb-radio-1`. Si no se puede confirmar, desconectar la B210 |
| Al frenar: `Could not stop application after 5 seconds` | El gNB tarda en cerrar | Es conocido. Confirmar con `docker ps` que se detuvo |

## 11. Opcional: central SIP e IMS
El primer arranque se hace sin SIP ni IMS.
- **Central SIP:** crear `config/secretos/sip_credenciales.conf` (paso 4) y construir la imagen con `docker compose --profile voz build sip`. Después se elige SIP en el panel o en `start.sh`.
- **IMS (VoNR, etapa 1):** necesita sus imágenes, sus contraseñas y cargar los abonados en PyHSS. Seguí `docker/ims/README.md` completo. Para revisar la configuración sin mostrar contraseñas: `docker compose --profile ims config --quiet`.

Más contexto: `README.md` (consola del gNB), `PROYECTO.md` (decisiones y estado) y `sesiones/` (qué se probó y cuándo).
