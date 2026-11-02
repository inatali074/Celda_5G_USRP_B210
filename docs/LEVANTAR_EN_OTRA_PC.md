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

## Arrancar y apagar
```bash
cd ~/red5g-docker
./start.sh    # Pide escribir "si": TRANSMITE
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
