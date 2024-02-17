# Docker 
*A powerful containerization platform*

## Introduction
Docker revolutionizes software development by providing a standardized way to package, distribute, and run applications 
within containers. It offers:
- Consistency: Ensuring that applications run uniformly across different environments. 
- Isolation: Encapsulating dependencies and configurations within self-contained containers. 
- Efficiency: Optimizing resource utilization and reducing overhead compared to traditional virtualization. 
- Scalability: Enabling easy scaling of applications both horizontally and vertically.

## Use `d` alias 
Alias not to die:
```bash
alias d="docker"
```

## Image Management
- `d pull <image>`: Download an image from Docker Hub.
- `d build -t <tag> .`: Build an image from a Dockerfile in the current directory.
- `d images`: List all locally available Docker images.
- `d rmi <image>`: Remove a Docker image.
- `d tag <image> <tag>`: Tag an existing image with a new tag.

## Container Lifecycle
- `d run <image>`: Create and start a container from an image.
- `d ps`: List all running containers.
- `d stop <container>`: Stop a running container.
- `d rm <container>`: Remove a stopped container.
- `d start <container>`: Start a stopped container.
- `d exec -it <container> <command>`: Execute a command inside a running container.

## Dockerfile
Sample Dockerfile:
```Dockerfile
FROM alpine:latest

COPY . /app
WORKDIR /app

RUN apk update && apk add python3

CMD ["python3", "app.py"]
```

## Docker Compose
- `docker-compose up`: Create and start containers defined in the docker-compose.yml.
- `docker-compose down`: Stop and remove containers, networks, and volumes defined in the docker-compose.yml.
- `docker-compose build`: Build or rebuild services.
- `docker-compose logs`: View output from containers.
- `docker-compose ps`: List containers.

docker-compose.yml example:
```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "5000:5000"
  redis:
    image: "redis:alpine"
```

## Docker Volumes
Docker volumes provide persistent storage for containers and allow data to persist beyond the lifetime of a container.
- `d volume create <volume-name>`: Create a volume.
- `d volume ls`: List all volumes.
- `d volume inspect <volume-name>`: Display detailed information about a volume.
- `d volume rm <volume-name>`: Remove a volume.
- `d run -d -v <volume-name>:<container-path> <image>`: Using dockers with volumes. 

## Docker Networking
Docker networking facilitates communication between containers and external networks.
- `d network create <network-name>`: Create a Docker network.
- `d network ls`: List Docker networks.
- `d network inspect <network-name>`: Display detailed information about a network.
- `d network rm <network-name>`: Remove a Docker network.
- `d run --network=<network-name> <image>`: Attach a container to a specific network.
- `d network connect <network-name> <container>`: Connect a running container to a network.
- `d network disconnect <network-name> <container>`: Disconnect a container from a network.