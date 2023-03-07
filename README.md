# API for {{calendar on steriods}}

Just imagine a calendly, give it steriods and let it take care of your selfcare. yeah! that's about it.

- Written in Python.
- The name will {{calendar on steriods}} till a better name/domain name is synthesized.

Written with [Django](https://www.djangoproject.com/) and [DRF](https://www.django-rest-framework.org/)

## Getting started

To start project, run:

```bash
docker-compose up
```

The API will then be available at http://127.0.0.1:8000

production is at {{production url}}

## Project commands

Run unit tests:

```bash
docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py test"
```

Run linting:

```bash
docker-compose run --rm app sh -c "flake8"
```

Run tests and linting together:

```bash
docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py test && flake8"
```

## aws-vault

Add a new user to aws-vault:

```bash
aws-vault add <user>
```

Initialise aws-vault in current terminal on macOS/Linux:

```bash
aws-vault exec <USER> --duration=12h
```

Initialise aws-vault in current command prompt window on Windows:

```bash
aws-vault exec <USER> --duration=12h -- cmd.exe
```

## Docker

Build docker image in current directory:

```bash
docker build -t <tag> .
```

### Docker Compose

Starting services:

```bash
docker-compose up
```

Rebuilding services:

```bash
docker-compose up --build
```

Starting services with specific config file:

```bash
docker-compose -f <file-path> up
```

## Bastion Commands

### Authenticate with ECR

In order to pull the application image, authentication with ECR is required.

To authenticate with ECR:

```sh
$(aws ecr get-login --no-include-email --region us-east-1)
```

### Create a superuser

Replace the following variables:

- `<DB_HOST>`: The hostname for the database (retrieve from Terraform apply output)
- `<DB_PASS>`: The password for the database instance (retrieve from GitLab CI/CD variables)

```bash
docker run -it \
    -e DB_HOST=<DB_HOST> \
    -e DB_NAME=cos \
    -e DB_USER=cosappuser \
    -e DB_PASS=<DB_PASS> \
    <ECR_REPO>:latest \
    sh -c "python manage.py wait_for_db && python manage.py createsuperuser"
```

## Terraform (via Docker Compose)

Check `Makefile` for short cuts

### Initialise

Initialise the Terraform state file locally, and download and Terraform providers.

```sh
docker-compose -f deploy/docker-compose.yml terraform init
```

### Format (fmt)

Run Terraform auto format command on code.

```sh
docker-compose -f deploy/docker-compose.yml run --rm terraform fmt
```

### Validate

Run Terraform validation on code.

```sh
docker-compose -f deploy/docker-compose.yml run --rm terraform validate
```

### Manage workspaces

Terraform allows you to create, remove or select a workspace using the CLI.

List all workspaces:

```sh
docker-compose -f deploy/docker-compose.yml terraform workspace list
```

> In the below commands, replace `<name>` with the name of the workspace.

Create:

```sh
docker-compose -f deploy/docker-compose.yml terraform workspace new <name>
```

Select:

```sh
docker-compose -f deploy/docker-compose.yml terraform workspace select <name>
```

Delete:

```sh
docker-compose -f deploy/docker-compose.yml terraform workspace delete <name>
```

### Plan

Output a plan for changes Terraform will make to AWS resources.

```sh
docker-compose -f deploy/docker-compose.yml terraform plan
```

### Apply

Run Terraform apply to make changes described in plan to actual resources (this can create, remove or change resources)

```sh
docker-compose -f deploy/docker-compose.yml terraform apply
```

### Destroy

Remove any resources managed by Terraform (tear down all infrastructure) for selected workspace

```sh
docker-compose -f deploy/docker-compose.yml terraform destroy
```