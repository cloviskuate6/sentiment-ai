terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

# Réseau Docker partagé entre Jenkins et les autres services [cite: 3]
resource "docker_network" "cicd" {
  name = "cicd-network"
}

# Image Docker locale buildée par Jenkins [cite: 4]
resource "docker_image" "sentiment" {
  name         = "sentiment-ai:${var.image_tag}"
  keep_locally = true
}

# Conteneur staging [cite: 4]
resource "docker_container" "sentiment_staging" {
  name    = var.container_name
  image   = docker_image.sentiment.image_id
  restart = "unless-stopped"

  networks_advanced {
    name = docker_network.cicd.name
  }

  # Configuration du port : application sur 8085, exposée sur var.app_port [cite: 4]
  ports {
    internal = 8085
    external = var.app_port
  }

  env = [
    "ENV=staging",
    "LOG_LEVEL=INFO"
  ]

  # Healthcheck pointant sur le port 8085 pour éviter le statut 'unhealthy' [cite: 4]
  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:8085/health"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
}