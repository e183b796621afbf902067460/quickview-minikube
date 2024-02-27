# quickview-minikube

[![license](https://img.shields.io/:license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0.txt)

---
This repository contains `Helm Charts` orchestrated via `Helmfile` within a `Minikube` local cluster.
There is implementation of the entire business logic written on `Python`, 
enabling real-time transactions publishing via `Apache Kafka` and analyzing via `ClickHouse`. 
The icing on the cake is `Apache Superset` as BI tool to visualize all the transactions and blockchain analytics.

---

# Requirements

To run this project, make sure you have the following tools installed:

- [**Docker**](https://docs.docker.com/engine/install/ubuntu/) (v25.0.3 or above): Containerization platform for building, shipping, and running applications.


- [**Kubectl**](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) (v1.29.1 or above): Command-line tool for interacting with Kubernetes clusters.


- [**Minikube**](https://minikube.sigs.k8s.io/docs/start/) (v1.32.0 or above): Lightweight Kubernetes implementation for local development and testing.


- [**Helm**](https://helm.sh/docs/intro/install/) (v3.14.0 or above): Kubernetes package manager for managing applications and their dependencies.


- [**Helmfile**](https://medium.com/geekculture/helmfile-introduction-f63c42244dcc) (v0.162.0 or above): Declarative configuration for managing Helm releases.


- [**SOPs**](https://github.com/getsops/sops/releases/tag/v3.8.1) (v3.8.1 or above): Simple and lightweight tool for secrets operations that encrypts with PGP keys.


- [**GnuPG**](https://blog.gitguardian.com/a-comprehensive-guide-to-sops/) (v2.2.27 or above): Open-source implementation of the OpenPGP standard for encrypting data.

---

# Quickstart

To deploy project with default values and standard configuration, follow these steps:

- Clone current repository and change working directory:
```integrationperformancetest
git clone https://github.com/e183b796621afbf902067460/quickview-minikube.git && cd quickview-minikube/
```

- Deploy without having to do a bunch of setup, 
so use the `/etc/.pgp.asc` file and import existed PGP keys:
```integrationperformancetest
gpg --import etc/.pgp.asc
```

- Default secrets were encrypted using `FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4` PGP key, which was already imported in the step above, so paste it to `/etc/.sops.yaml`:
```yaml
creation_rules:
  - pgp: FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4
```

- Deploy project using `make` utility with **default** cluster configuration:
```integrationperformancetest
make deploy
```

- After all the steps done, just wait until all containers will be in `Running` state:
```integrationperformancetest
kubectl get all --all-namespaces
```

- When all containers in `Running` state, paste output of this command in browser:
```integrationperformancetest
echo "$(minikube ip):32123"
```

---

# Configuration

Another configuration can be provided depends on your system, 
so to change parameters follow these steps:

- Create PGP keys for secrets encryption:
```integrationperformancetest
gpg --full-generate-key
```

- List existed PGP keys and copy created one from previous step:
```integrationperformancetest
gpg --list-keys
```

- Paste created PGP key to `/etc/.sops.yaml`, it should look like:
```yaml
creation_rules:
  - pgp: FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4
```

---

**At this step, 
provide specific configuration for each container through `/master.d` and adjust values where it's needed or copy from `/default.d`!**

---

- Encrypt provided secrets using `sops` utility, example for `quickview` container:
```integrationperformancetest
sops --config etc/.sops.yaml --encrypt etc/quickview/master.d/secrets.raw.yaml > etc/quickview/master.d/secrets.yaml && rm -rf etc/quickview/master.d/secrets.raw.yaml
```

- Set `QUICKVIEW_ENVIRONMENT` environment variable to deploy with new configuration provided in `/master.d` directories:
```integrationperformancetest
export QUICKVIEW_ENVIRONMENT=master 
```

- Deploy project using `make` utility with **master** cluster configuration:
```integrationperformancetest
make deploy -e
```

**Set of possible arguments listed below.**

`QUICKVIEW_LOG_LEVEL`: Argument sets the log level for the application to "debug" by default, 
allowing for detailed logging information to be displayed. 
It's helpful for troubleshooting and debugging purposes.

`QUICKVIEW_HELMFILE_PATH`: Argument specifies the path to the configuration file used by the application. 
It points to the file containing configurations and deployment instructions which originally stored in `/helmfile.d/helmfile.yaml`.

`QUICKVIEW_ENVIRONMENT`: Argument defines the environment in which the application will be deployed. 
It typically represents a specific set of configurations, variables, 
and resources tailored for a particular deployment environment.

`QUICKVIEW_CPUS`: Argument configures the number of CPUs allocated to the cluster used by the application. 
Increasing the number of CPUs can improve performance, 
especially for resource-intensive workloads or applications with high concurrency requirements.

`QUICKVIEW_MEMORY`: Argument sets the amount of memory (in megabytes) allocated to the cluster used by the application. 
Allocating sufficient memory is essential for running applications smoothly, 
especially those with memory-intensive operations.
