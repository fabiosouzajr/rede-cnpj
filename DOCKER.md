# Docker Setup for RedeCNPJ

This guide explains how to run the RedeCNPJ application in a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the container:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

4. **Access the application:**
   Open your browser and navigate to: `http://localhost:5000/rede/`

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t rede-cnpj .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name rede-cnpj \
     -p 5000:5000 \
     -v $(pwd)/rede/bases:/app/bases \
     -v $(pwd)/rede/arquivos:/app/arquivos \
     -v $(pwd)/rede/rede.ini:/app/rede.ini \
     rede-cnpj
   ```

3. **View logs:**
   ```bash
   docker logs -f rede-cnpj
   ```

4. **Stop the container:**
   ```bash
   docker stop rede-cnpj
   docker rm rede-cnpj
   ```

## Configuration

### Port Configuration

To change the exposed port, edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Change 8080 to your desired port
```

Or update `rede.ini`:
```ini
porta_flask=8080
```

### Database Persistence

The databases in `rede/bases/` are automatically persisted using Docker volumes. This means your data will survive container restarts.

### Configuration File

The `rede.ini` file is mounted as a volume, so you can edit it directly on your host system and restart the container to apply changes.

## Troubleshooting

### Check if container is running:
```bash
docker ps
```

### View container logs:
```bash
docker-compose logs rede
# or
docker logs rede-cnpj
```

### Access container shell:
```bash
docker-compose exec rede bash
# or
docker exec -it rede-cnpj bash
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

## Notes

- The application will be available at `http://localhost:5000/rede/`
- Databases and uploaded files are persisted in volumes
- Configuration changes require a container restart to take effect

