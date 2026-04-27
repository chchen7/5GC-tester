# fru-compose

In this compose repo, there are for types of compose for using:

| | Type | Compose File |
| - | - | - |
| 1 | Basic | [docker-compose.yaml](docker-compose.yaml) |
| 2 | Static NR-DC | [docker-compose-dc-static.yaml](docker-compose-dc-static.yaml) |
| 3 | Dynamic NR-DC | [docker-compose-dc-dynamic.yaml](docker-compose-dc-dynamic.yaml)|
| 4 | ULCL | [docker-compose-ulcl.yaml](docker-compose-ulcl.yaml) |

## How to use?

The compose user guides are also at [free-ran-ue official website](https://free-ran-ue.github.io/doc-user-guide/).

### Get this `fru-compose` repo

```bash
git clone https://github.com/free-ran-ue/fru-compose
```

### (Optional) Build free-ran-ue image by yourself

If you want to use the pr-build image on the [docker hub](https://hub.docker.com/r/alonza0314/free-ran-ue/tags), you can just skip this step.

```bash
cd fru-compose
git clone https://github.com/free-ran-ue/free-ran-ue
make
```

After building, use `docker images` cli to check image. The image will be named with `alonza0314/free-ran-ue:latest`.

### Up the compose

```bash
cd fru-compose
docker compose -f <target compose file> up
```

### Down the compose

```bash
docker compose -f <target compose file> down
```

## Docker Hub

- [alonza0314/free-ran-ue](https://hub.docker.com/r/alonza0314/free-ran-ue/tags)
