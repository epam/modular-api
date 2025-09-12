

DOCKER_EXECUTABLE := podman

SERVER_IMAGE_NAME := public.ecr.aws/x4s4z8e1/syndicate/modular-api
SERVER_IMAGE_TAG ?= $(shell python -c "from modular_api.version import __version__; print(__version__)")
ADDITIONAL_BUILD_PARAMS ?=

HELM_REPO_NAME := syndicate

install:
	uv sync --all-groups --all-extras

image-arm64:
	$(DOCKER_EXECUTABLE) build $(ADDITIONAL_BUILD_PARAMS) --platform linux/arm64 -t $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 .

image-amd64:
	$(DOCKER_EXECUTABLE) build $(ADDITIONAL_BUILD_PARAMS) --platform linux/amd64 -t $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64 .


image-manifest:
	-$(DOCKER_EXECUTABLE) manifest rm $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)
	$(DOCKER_EXECUTABLE) manifest create $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64
	$(DOCKER_EXECUTABLE) manifest annotate $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 --arch arm64
	$(DOCKER_EXECUTABLE) manifest annotate $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64 --arch amd64

push-arm64:
	$(DOCKER_EXECUTABLE) push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64


push-amd64:
	$(DOCKER_EXECUTABLE) push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64

push-manifest:
	$(DOCKER_EXECUTABLE) manifest push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)

clear:
	-rm modular_api.log modular_api_cli.log


clean-installed-modules:
	-rm -r modular_api/modules
	-rm modular_api/web_service/commands_base.json


push-helm-chart:
	helm package --dependency-update deployment/helm/modular-api
	helm s3 push modular-api-$(SERVER_IMAGE_TAG).tgz $(HELM_REPO_NAME) --relative
	-rm modular-api-$(SERVER_IMAGE_TAG).tgz
