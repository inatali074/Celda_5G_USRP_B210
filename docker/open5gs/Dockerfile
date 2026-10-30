# syntax=docker/dockerfile:1
FROM ubuntu:22.04
ARG OPEN5GS_TAG=v2.8.0
ARG OPEN5GS_COMMIT=157f611a530e292e40ec50f9d23f0ef5d4fcd6a6
ARG NUM_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive
# Dependencias de la referencia oficial; MongoDB y WebUI quedan afuera.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git python3 python3-setuptools python3-wheel ninja-build \
    build-essential flex bison libsctp-dev libgnutls28-dev libgcrypt-dev \
    libssl-dev libidn11-dev libmongoc-dev libbson-dev libyaml-dev \
    libnghttp2-dev libmicrohttpd-dev libcurl4-gnutls-dev libtins-dev \
    meson gettext libtalloc-dev cmake iproute2 iptables \
    && rm -rf /var/lib/apt/lists/*
RUN test "${NUM_JOBS}" -gt 0 \
    && git clone --depth 1 --branch "${OPEN5GS_TAG}" https://github.com/open5gs/open5gs.git /open5gs \
    && test "$(git -C /open5gs rev-parse HEAD)" = "${OPEN5GS_COMMIT}" \
    && cd /open5gs && meson build --prefix=/open5gs/install \
    && ninja -j "${NUM_JOBS}" -C build && ninja -C build install \
    && test -x /open5gs/build/tests/app/5gc
# La ruta de 5gc viene del oficial; su disponibilidad en v2.8.0 se comprueba al construir.
ENV PATH=/open5gs/build/tests/app:${PATH}
COPY entrypoint.sh /usr/local/bin/open5gs-entrypoint
RUN chmod 755 /usr/local/bin/open5gs-entrypoint
WORKDIR /open5gs
ENTRYPOINT ["/usr/local/bin/open5gs-entrypoint"]
CMD ["5gc", "-c", "/config/open5gs-5gc.yml"]
