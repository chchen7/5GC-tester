# -------------------------------
# Stage 1: Build Go binary
# -------------------------------
FROM golang:1.25.5 AS builder
WORKDIR /free-ran-ue

COPY free-ran-ue/ .
RUN go mod download

RUN make bin

# -------------------------------
# Stage 2: Build Node.js / Yarn
# -------------------------------
FROM node:20 AS consolebuilder
WORKDIR /free-ran-ue

COPY free-ran-ue/ .
RUN cd console/frontend && yarn install

RUN make console

# -------------------------------
# Stage 3: Build the final image
# -------------------------------
FROM debian:bookworm-slim
WORKDIR /free-ran-ue

RUN apt-get update && \
    apt-get install -y iproute2 && \
    apt-get install -y net-tools && \
    apt-get install -y iputils-ping && \
    apt-get install -y iperf3 && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /free-ran-ue/build/free-ran-ue /free-ran-ue/free-ran-ue
COPY --from=consolebuilder /free-ran-ue/build/console /free-ran-ue/console
