# Levantar la red en otra PC

Todo corre en Docker. La PC nueva necesita Linux, Docker con Compose, y **USB 3** para la B210.

## En esta PC: armar el paquete
```bash
scripts/empaquetar_para_otra_pc.sh /ruta/al/pendrive/red5g
```
La carpeta de destino tiene que ser nueva o estar vacía. En un pendrive FAT o exFAT no se aplican los permisos de Linux, así que cualquiera que lo conecte puede leer las claves.

Hacen falta unos 10 GB libres. Con `--sin-imagenes` ocupa muy poco, pero la otra PC tiene que construir las imágenes, lo que lleva horas y requiere internet.

**El paquete contiene K, OPc y ADM de las SIM de laboratorio.** No lo subas a ningún lado y borralo del pendrive al terminar. No incluye `CONTEXTO_ANTECEDENTES.local.md`, `grabador/` ni el material de referencia: copialos aparte si los necesitás.

## En la PC nueva: instalar
```bash
cd /ruta/al/pendrive/red5g
bash instalar_en_otra_pc.sh ~/red5g-docker
```
Comprueba los requisitos, instala el proyecto y las imágenes, y carga los abonados. No usa sudo y **no transmite**. Elegí una carpeta que no sea `~/red5g`, que es el antecedente de solo lectura.

## Antes de transmitir
Estos comandos cambian el sistema: revisalos antes de correrlos.

```bash
# Hace que la CPU no baje la frecuencia. Dura hasta reiniciar.
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Buffers de red que recomienda UHD. Duran hasta reiniciar.
sudo sysctl -w net.core.wmem_max=33554432 net.core.rmem_max=33554432
```

Revisá también:
- **USB:** la B210 directa a un puerto USB 3, sin hub.
- **Jaula:** la B210 y sus antenas dentro. Siguen valiendo las reglas de RF del proyecto.
- **Docentes:** avisá que cambió la PC, si corresponde.

## Salida a Internet (NAT)
El celular recibe una IP del pool `10.45.0.0/16` (por ejemplo, `10.45.0.2`), que no existe fuera de la red 5G. Para que navegue, esa dirección se traduce dos veces antes de salir por la interfaz del host:

| Etapa | Dónde | Qué traduce | Quién la configura |
| :--- | :--- | :--- | :--- |
| 1 | Contenedor `open5gs` | `10.45.0.0/16` → `10.53.1.2`, la IP del contenedor en la red `ran` | `docker/open5gs/entrypoint.sh`, al arrancar |
| 2 | Host | `10.53.1.0/24` → la IP de la interfaz de salida del host | Docker, al crear la red `ran` |

```
celular 10.45.0.2 ──N3/GTP-U──▶ UPF ─▶ ogstun 10.45.0.1
        ─▶ MASQUERADE (contenedor) ─▶ 10.53.1.2 ─▶ MASQUERADE (Docker, host) ─▶ Internet
```

**Normalmente no hay que hacer nada a mano:**
- La etapa 1 la arma el entrypoint de Open5GS: crea `ogstun`, le asigna `10.45.0.1/16` y agrega
  `iptables -t nat -A POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE`.
  Solo afecta el espacio de red del contenedor, que corre con `NET_ADMIN` y `net.ipv4.ip_forward=1` (ver `docker-compose.yml`).
- La etapa 2 la arma Docker para toda red `bridge`: activa `ip_forward` en el host y agrega su propia regla `MASQUERADE` para `10.53.1.0/24`.
- El SMF les entrega a los teléfonos los DNS `8.8.8.8` y `8.8.4.4` y una MTU de 1400 bytes (`config/open5gs/open5gs-5gc.yml`).

Los valores del pool y de `ogstun` están en `config/open5gs/network.env` y tienen que coincidir con la sección `session` de `config/open5gs/open5gs-5gc.yml`.

### Comprobar la NAT
Con la red levantada (los nombres de contenedor empiezan con `5g-`):

```bash
# Etapa 1: la regla del contenedor
docker exec 5g-open5gs-1 iptables -t nat -S POSTROUTING

# El contenedor llega a Internet (si esto falla, el problema está en la etapa 2 o en el host)
docker exec 5g-open5gs-1 ping -c 3 8.8.8.8

# Reenvío de IP en el host: tiene que dar 1
sysctl net.ipv4.ip_forward
```

Si el teléfono tiene IP, el contenedor llega a Internet, pero el teléfono no navega, mirá el panel web (`http://localhost:8080`). Los contadores de `ogstun` muestran si el tráfico del teléfono llega al núcleo.

### Si no hay salida a Internet
Estos comandos cambian la red del host: revisalos antes de correrlos.

- **Docker sin control de iptables.** Si `/etc/docker/daemon.json` tiene `"iptables": false`, Docker no crea la etapa 2. Sacá esa opción y reiniciá Docker (`sudo systemctl restart docker`).
- **Firewall del host.** `ufw` o `firewalld` pueden bloquear el reenvío entre la red de Docker y la interfaz de salida. Con `ufw`, por ejemplo: `sudo ufw default allow routed`.
- **Subredes superpuestas.** Si la red del host ya usa `10.53.1.0/24` o `10.45.0.0/16`, hay que cambiar la subred de la red `ran` en `docker-compose.yml` o el pool en `config/open5gs/`, y actualizar las IP de las configuraciones.
- **NAT manual en el host**, solo si Docker no la crea. Reemplazá `<interfaz>` por la de salida a Internet, que se ve con `ip route get 8.8.8.8`:
  ```bash
  sudo sysctl -w net.ipv4.ip_forward=1
  sudo iptables -t nat -A POSTROUTING -s 10.53.1.0/24 -o <interfaz> -j MASQUERADE
  ```
  Duran hasta reiniciar.

## Arrancar y apagar
```bash
cd ~/red5g-docker
./start.sh    # menú; 1–4 transmite, 0 o EOF sale sin transmitir
./stop.sh     # Corta la transmisión, guarda los logs y apaga todo
```

## Comprobar que anda
1. Consola con 4 paneles, y el gNB conectado al AMF.
2. Panel de eventos sin líneas `~ tiempo real` todos los segundos.
3. SIM 3 o SIM 4 en un teléfono: registro e IP en el panel de conexiones. Los teléfonos necesitan el APN `Metodos1`, MCC `001`, MNC `01`, IPv4.

## Qué comparar con la PC anterior
Esta prueba responde si los cortes venían de la PC. Usá la misma configuración, un solo teléfono y video continuo durante al menos 3 minutos:

| Dato | PC anterior (2026-11-02, 18:38 a 18:48 UTC) |
| :--- | :--- |
| Reconexiones | Una cada 18 s |
| PUSCH con error | 73 % |
| Fallas de tiempo real | Unas 40 en 10 min, con episodios sostenidos |

**Si los cortes desaparecen,** venían de la PC o de su USB. **Si siguen igual,** quedan el reloj de la B210 y la configuración.

## Opcional: compilar para la CPU nueva
Las imágenes usan `MARCH=x86-64-v3`, que funciona en cualquier CPU con AVX2. Si hace falta más rendimiento, se puede cambiar `MARCH` y `NUM_JOBS` en `docker-compose.yml` y reconstruir `gnb-radio`. Los Dockerfile rechazan `native` a propósito, así que usá un valor explícito, como `x86-64-v4` en una CPU con AVX-512.

El menú ofrece n78 TDD (3525 MHz) y n3 FDD (1842,5 MHz), cada una con CP-OFDM o DFT-s-OFDM de subida. n3 DFT-s-OFDM nunca se probó en el aire. Todas incluyen métricas JSON y volcado IQ; el binario crece sin límite mientras haya subida. Al terminar, borrar `/tmp/gnb_rx_symbols.bin` del volumen `gnb-logs`. Para saltear el menú: `./start.sh gnb_b210_00101_n78_cpofdm.yml` o `GNB_CONFIG=gnb_b210_00101_n3_dfts.yml ./start.sh`.
