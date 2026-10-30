# syntax=docker/dockerfile:1
FROM ubuntu:22.04
ARG SRSRAN_TAG=release_25_10
ARG SRSRAN_COMMIT=6bcbd9e5bf8686aa7085202cd847c5ddd64a9c16
ARG MARCH=x86-64-v3
ARG NUM_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git build-essential cmake pkg-config libfftw3-dev \
    libmbedtls-dev libboost-program-options-dev libsctp-dev libzmq3-dev iproute2 \
    && rm -rf /var/lib/apt/lists/*
RUN test "${MARCH}" != native && test -n "${MARCH}" && test "${NUM_JOBS}" -gt 0 \
    && git clone --depth 1 --branch "${SRSRAN_TAG}" https://github.com/srsran/srsRAN_4G.git /src \
    && test "$(git -C /src rev-parse HEAD)" = "${SRSRAN_COMMIT}"
# ISA fija, coherente con x86-64-v3 (sin AVX-512) y sin drivers de radio para la prueba sin RF.
RUN cmake -S /src -B /src/build -DCMAKE_BUILD_TYPE=Release \
    -DGCC_ARCH="${MARCH}" -DAUTO_DETECT_ISA=OFF -DHAVE_SSE=ON -DHAVE_AVX=ON -DHAVE_AVX2=ON -DHAVE_FMA=ON \
    -DENABLE_SRSUE=ON -DENABLE_SRSENB=OFF -DENABLE_SRSEPC=OFF \
    -DENABLE_UHD=OFF -DENABLE_BLADERF=OFF -DENABLE_SOAPYSDR=OFF \
    -DENABLE_GUI=OFF -DENABLE_HARDSIM=OFF -DENABLE_ZEROMQ=ON \
    && cmake --build /src/build --parallel "${NUM_JOBS}" \
    && cmake --install /src/build && ldconfig
ENTRYPOINT ["/usr/local/bin/srsue"]
CMD ["/config/ue.conf"]
