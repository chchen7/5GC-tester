# Variables
IMAGE_NAME = tester
CONTAINER_NAME = tester
DATA_DIR = $(shell pwd)/data
CONFIG_DIR = $(shell pwd)/config
DOCKER_SOCK = /var/run/docker.sock

# Lucas Metrics Collector Variables
COLLECTOR_REPO = https://github.com/lucas-schierholt/ColetorDeMetricas-DockerStats
COLLECTOR_DIR = ColetorDeMetricas-DockerStats

.PHONY: all build run launch monitor-prepare monitor-up monitor-down clean logs

all: build

# 1. Build Tester Image (Parallel Launcher)
build:
	docker build -t $(IMAGE_NAME) .

# 2. Run Tester Container
run:
	@mkdir -p $(DATA_DIR)
	docker run -d \
		--name $(CONTAINER_NAME) \
		-v $(DOCKER_SOCK):$(DOCKER_SOCK) \
		-v $(DATA_DIR):/data \
		-v $(CONFIG_DIR):/config \
		$(IMAGE_NAME)

# 3. Node-RED Monitor: Prepare (Clone and Permissions)
monitor-prepare:
	@if [ ! -d "$(COLLECTOR_DIR)" ]; then \
		echo "Cloning Lucas Metrics Collector..."; \
		git clone $(COLLECTOR_REPO); \
	fi
	chmod -R 777 $(COLLECTOR_DIR)/nodered_data/

# 4. Node-RED Monitor: Start (Docker Compose Up)
monitor-up: monitor-prepare
	cd $(COLLECTOR_DIR) && docker compose -f coleta.yml up -d
	@echo "Monitor system is starting. Access InfluxDB at http://localhost:8086"

# 5. Node-RED Monitor: Stop (Docker Compose Down)
monitor-down:
	@if [ -d "$(COLLECTOR_DIR)" ]; then \
		cd $(COLLECTOR_DIR) && docker compose -f coleta.yml down; \
	fi

# 6. Launch Parallel UEs
N ?= 1
U ?= 100
T ?= 1000
launch:
	docker exec $(CONTAINER_NAME) parallel_launcher -n $(N) -u $(U) -t $(T)

# 7. Clean All (Tester, Monitor, and Source Code)
clean: monitor-down
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	@if [ -d "$(COLLECTOR_DIR)" ]; then \
		rm -rf $(COLLECTOR_DIR); \
	fi
	@echo "Cleaning complete. Tester removed and $(COLLECTOR_DIR) deleted."

# 8. View Tester Logs
logs:
	docker logs -f $(CONTAINER_NAME)