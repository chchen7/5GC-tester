FROM ubuntu:20.04 AS builder

LABEL maintainer="Free5GC <support@free5gc.org>"
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="$PATH:/cmake/bin"
ARG TARGET_ARCH=x86_64

RUN apt-get update \
    && apt-get install -y build-essential libsctp-dev lksctp-tools iproute2 wget git ca-certificates

RUN mkdir /cmake \
    && cd /cmake \
    && wget https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-${TARGET_ARCH}.sh -O cmake_installer.sh \
    && chmod +x cmake_installer.sh \
    && ./cmake_installer.sh --skip-license \
    && cd /

RUN cd /root \
    && git clone -b v3.2.6 -j `nproc` https://github.com/aligungr/UERANSIM \
    && cd UERANSIM \
    && make -j `nproc`

# Runtime Stage
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y libsctp-dev lksctp-tools iproute2 iputils-ping procps psmisc \
    && apt-get clean

WORKDIR /ueransim
RUN mkdir -p config/ binder/ /etc/iproute2 && touch /etc/iproute2/rt_tables

COPY --from=builder /root/UERANSIM/build/nr-gnb .
COPY --from=builder /root/UERANSIM/build/nr-ue .
COPY --from=builder /root/UERANSIM/build/nr-cli .
COPY --from=builder /root/UERANSIM/build/nr-binder binder/
COPY --from=builder /root/UERANSIM/build/libdevbnd.so binder/

VOLUME [ "/ueransim/config" ]