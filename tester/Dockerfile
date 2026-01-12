# Stage 1: Build the launcher binary
FROM golang:1.21-alpine AS builder
WORKDIR /app

# Only need standard library for a simple launcher, usually no 'go get' required
RUN go mod init tester

COPY parallel_launcher.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o parallel_launcher parallel_launcher.go

# Stage 2: Final runtime image
FROM alpine:latest
# Keep docker-cli so parallel_launcher can execute docker commands
RUN apk add --no-cache docker-cli bash

WORKDIR /root/
COPY --from=builder /app/parallel_launcher /usr/local/bin/

# Keep the container running
CMD ["sleep", "infinity"]