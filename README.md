# C3D3 Dagster Research
Depends on: [raffaelo](https://github.com/e183b796621afbf902067460/raffaelo) and [medici](https://github.com/e183b796621afbf902067460/medici), [d3f1nance](https://github.com/e183b796621afbf902067460/d3f1nance) and [c3f1nance](https://github.com/e183b796621afbf902067460/c3f1nance), [d3tl](https://github.com/e183b796621afbf902067460/d3tl) and [c3tl](https://github.com/e183b796621afbf902067460/c3tl).

---

Dagster is used for C3D3 Research ETL orchestration.

# Configuration

- Clone current repository:
```
git clone https://github.com/e183b796621afbf902067460/c3d3-dagster-research.git
```

- Get into the project folder:
```
cd c3d3-dagster-research/
```

- Set environment variables in [.env](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/c3d3/.env).

# Master

- Run docker-compose (`sudo`):
```
docker-compose up -d --build --force-recreate minio
```
- Create `dagster-compute-logs` Bucket and Access Keys at the MinIO's UI.
- Set Access and Secret Keys in [docker-compose](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/docker-compose.yaml) and Bucket name in [dagster](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/c3d3/dagster.yaml), also configure hosts and ports.
- Run another one docker-compose (`sudo`):
```
docker-compose up -d --build --force-recreate dagit daemon postgres rabbitmq flower 
```
# Worker

- Set Access and Secret Keys in [docker-compose](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/docker-compose.yaml) and Bucket name in [dagster](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/c3d3/dagster.yaml), also configure hosts and ports.
- Configure [celery](https://github.com/e183b796621afbf902067460/c3d3-dagster-research/blob/master/c3d3/celery.yaml) hosts and posrts.
- Run docker-compose (`sudo`):
```
docker-compose up -d --build --force-recreate worker
```

After setup every worker can be seen in the Flower's UI.

# Exit
- To stop all running containers:
```
docker stop $(docker ps -a -q)
```
- And remove it all:
```
docker rm $(docker ps -a -q)
```
