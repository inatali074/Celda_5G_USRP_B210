# syntax=docker/dockerfile:1
FROM ubuntu:26.04
ARG OCUDU_TAG=release_26_10
ARG OCUDU_COMMIT=e0db566aac6e6376ddd60e83c84f58698fcc4d70
ARG UHD_VERSION=4.9.0.1
ARG MARCH=x86-64-v3
ARG NUM_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN test "${MARCH}" != native && test -n "${MARCH}" \
    && test "${NUM_JOBS}" -gt 0 \
    && git clone --depth 1 --branch "${OCUDU_TAG}" https://gitlab.com/ocudu/ocudu.git /src \
    && test "$(git -C /src rev-parse HEAD)" = "${OCUDU_COMMIT}"
WORKDIR /src
# Se reutilizan los instaladores del commit fijado, sin dependencias de DPDK.
RUN docker/scripts/install_dependencies.sh build \
    && docker/scripts/install_docker_dependencies.sh build \
    && docker/scripts/install_uhd_dependencies.sh build \
    && apt-get update && apt-get install -y --no-install-recommends libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*
RUN docker/scripts/build_uhd.sh "${UHD_VERSION}" "-march=${MARCH}" "${NUM_JOBS}"
ENV UHD_DIR=/opt/uhd/${UHD_VERSION}
ENV PATH=/opt/uhd/${UHD_VERSION}/bin:${PATH}
ENV LD_LIBRARY_PATH=/opt/uhd/${UHD_VERSION}/lib:/opt/uhd/${UHD_VERSION}/lib64:/opt/uhd/${UHD_VERSION}/lib/x86_64-linux-gnu
# ENABLE_ZEROMQ no figura en el Dockerfile de referencia: se exige confirmación en fuente.
RUN grep -Rq 'ENABLE_ZEROMQ' CMakeLists.txt cmake \
    && docker/scripts/builder.sh -c gcc -m "-j${NUM_JOBS} gnb" \
       -DBUILD_TESTING=False -DENABLE_UHD=On -DENABLE_DPDK=Off \
       -DENABLE_ZEROMQ=On -DMARCH="${MARCH}" -DCMAKE_INSTALL_PREFIX=/opt/ocudu /src \
    && grep -Eq '^ENABLE_ZEROMQ:BOOL=(ON|On|TRUE|True|1)$' build/CMakeCache.txt \
    && install -Dm755 build/apps/gnb/gnb /usr/local/bin/gnb
# Las imágenes quedan en el contenedor y no dependen del UHD del host.
RUN uhd_images_downloader -t b2xx \
    && find /opt/uhd -name 'usrp_b210_fpga.bin' -print -quit | grep -q . \
    && ldconfig && rm -rf /src
WORKDIR /tmp
ENTRYPOINT ["/usr/local/bin/gnb"]
