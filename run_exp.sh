#!/bin/bash
DOCKER_API_TCP="tcp://0.0.0.0:2375"
if ! cat /lib/systemd/system/docker.service | grep "$DOCKER_API_TCP" 2>&1 > /dev/null; then

    sed -i "/^ExecStart=/ s|$| -H $DOCKER_API_TCP|" /lib/systemd/system/docker.service

    systemctl daemon-reload
    service docker restart
fi
for e in $(seq 2 3); do
    for c in 0 1; do
        echo "Run core $c tests (exec $e)"
        for w in 500 400 300 200 100; do
            for i in 1 3 5 7 9 11; do
                echo "Running experiment $i (w=$w)"
                if [ "$c" -eq 0 ]; then
                    yamlfile="./docker-compose-free5GC.yaml"
                    corepath="free5gc"
                    filler="./filler_free5gc.sh"
                elif [ "$c" -eq 1 ]; then
                    yamlfile="./docker-compose-open5GS.yaml"
                    corepath="open5gs"
                    filler="./filler_open5gs.sh"
                fi
                echo ">>> Cleaning up old containers and data..."
                cd tester
                make clean > /dev/null 2>&1
                docker volume prune -f > /dev/null 2>&1
                cd ..

                echo ">>> run core network..."
                if [ "$c" -eq 0 ]; then
                    cd gtp5g
                    make
                    sudo make install
                    cd ..
                fi
                cd $corepath
                docker compose up -d
                cd ..
                sleep 15

                echo ">>> Filling UE data"
                sudo bash $filler -n $i

                echo ">>> Building and running Tester (Parallel Launcher)..."
                cd tester
                make build
                make run
                cd ..

                echo ">>> Building gnb"
                cd ueransim
                docker compose -f "$yamlfile" build
                cd ..

                cd tester
                echo ">>> Setting up Metrics Collector..."
                make monitor-up
                cd ..

                echo "Waiting 5 seconds for InfluxDB to initialize..."
                sleep 5

                echo ">>> Launching $i gnbs..."
                cd ueransim
                docker compose -f "$yamlfile" up -d --scale ueransim-gnb=$i
                cd ..

                cd tester
                echo ">>> Launching $i UEs for $w seconds..."
                make launch N=$i U=100 T=$w

                sleep 120

                cd ..
                echo ">>> [5/5] Collecting experiment $i data"
                python3 generate.py --gnb-start 1 --gnb-count $i
                mv ueransim_metrics.csv result-logs-$e-$c-$w-$i.csv
                docker exec influxdb sh -c "influx query 'from(bucket:\"database\") |> range(start:-5m)' --raw" > result-logs-influxdb-$e-$c-$w-$i.csv

                echo ">>> Cleaning up old containers and data..."
                cd ueransim 
                docker compose -f "$yamlfile" down
                cd ..
                cd $corepath
                docker compose down -v
                cd ..

                cd tester
                make clean > /dev/null 2>&1
                docker image prune --filter="dangling=true" -f
                docker volume prune -f > /dev/null 2>&1
                docker container prune -f
                docker network prune -f
                cd ..
                sleep 15
            done
        done
    done
done