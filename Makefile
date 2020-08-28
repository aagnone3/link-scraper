include ./env

# variables
TAG ?= latest
DOCKER ?= docker
DOCKERFILE ?= Dockerfile
DOCKER_TAG ?= latest
WORKING_DIRECTORY ?= /opt  # must match WORKDIR in Dockerfile

# definitions
.DEFAULT_GOAL := help
DOCKER_REPO_URI := ${DOCKER_USERNAME}/${DOCKER_REPO}:${DOCKER_TAG}

# convenience function to run a command inside the container
define docker-command
	$(DOCKER) run \
		--mount type=bind,source=$(PWD)/data,target=$(WORKING_DIRECTORY)/data \
		-p 443:443 \
		-ti \
		--rm \
		$(DOCKER_REPO) \
			$(1) $(2) $(3) $(4) $(5) $(6)
endef

.PHONY: help
help: ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed -E 's/^([a-zA-Z_-]+):.*## (.*)$$/\1: \2/' | awk -F ':' '{ printf "%-10s %s\n", $$1, $$2 }'

.PHONY: login
login: ## Login to Docker
	$(DOCKER) login

.PHONY: build
build: ## Build the Docker image
	$(DOCKER) build \
		-t $(DOCKER_REPO) \
		.

.PHONY: image
image: build ## Build the Docker image (alias for `build` target)

.PHONY: tag
tag: login  ## Tag the Docker image
	$(DOCKER) tag $(DOCKER_REPO) $(DOCKER_REPO_URI)

.PHONY: push
push: tag  ## Push the Docker image to the Docker repository
	$(DOCKER) push $(DOCKER_REPO_URI)

.PHONY: shell
shell: ## Run the Docker image
	$(call docker-command, bash)

.PHONY: test
test: ## Test the application inside a Docker container
	$(call docker-command, python -m pytest -vvv)

.PHONY: Run
run: ## Run the application inside a Docker container
	$(call docker-command, python run.py $(ARGS))
