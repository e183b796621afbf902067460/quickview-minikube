# Makefile

# Default values for variables
QUICKVIEW_LOG_LEVEL := debug
QUICKVIEW_HELMFILE_PATH := helmfile.d/helmfile.yaml
QUICKVIEW_ENVIRONMENT := default
QUICKVIEW_CPUS := 4
QUICKVIEW_MEMORY := 8192

# Define targets
.PHONY: deploy minikubeDelete minikubeStart

# Target to delete minikube
minikubeDelete:
	minikube delete

# Target to start minikube
minikubeStart: minikubeDelete
	minikube start --vm-driver=docker --cpus=$(QUICKVIEW_CPUS) --memory=$(QUICKVIEW_MEMORY)

# Target to run helmfile sync command
deploy: minikubeStart
	helmfile --log-level $(QUICKVIEW_LOG_LEVEL) --environment $(QUICKVIEW_ENVIRONMENT) sync -f $(QUICKVIEW_HELMFILE_PATH)

