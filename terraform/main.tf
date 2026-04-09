terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6.0"
}

provider "aws" {
  region = var.aws_region
}

# ── Datos de la VPC por defecto ───────────────────────────────────────────────
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ── Security Groups ───────────────────────────────────────────────────────────
module "sg" {
  source = "./modules/sg"
  vpc_id = data.aws_vpc.default.id
}

# ── EC2: MongoDB ──────────────────────────────────────────────────────────────
module "ec2_mongodb" {
  source            = "./modules/ec2"
  name              = "recetas-mongodb"
  instance_type     = var.instance_type
  key_name          = var.key_name
  security_group_id = module.sg.mongodb_sg_id
  user_data         = file("${path.module}/scripts/install_mongodb.sh")
}

# ── EC2: RabbitMQ ─────────────────────────────────────────────────────────────
module "ec2_rabbitmq" {
  source            = "./modules/ec2"
  name              = "recetas-rabbitmq"
  instance_type     = var.instance_type
  key_name          = var.key_name
  security_group_id = module.sg.rabbitmq_sg_id
  user_data         = file("${path.module}/scripts/install_rabbitmq.sh")
}

# ── EC2: API (x2 para el balanceador) ────────────────────────────────────────
module "ec2_api_1" {
  source            = "./modules/ec2"
  name              = "recetas-api-1"
  instance_type     = var.instance_type
  key_name          = var.key_name
  security_group_id = module.sg.api_sg_id
  user_data = templatefile("${path.module}/scripts/install_api.sh", {
    mongo_uri_param    = aws_ssm_parameter.mongo_uri.name
    rabbitmq_url_param = aws_ssm_parameter.rabbitmq_url.name
    aws_region         = var.aws_region
  })
}

module "ec2_api_2" {
  source            = "./modules/ec2"
  name              = "recetas-api-2"
  instance_type     = var.instance_type
  key_name          = var.key_name
  security_group_id = module.sg.api_sg_id
  user_data = templatefile("${path.module}/scripts/install_api.sh", {
    mongo_uri_param    = aws_ssm_parameter.mongo_uri.name
    rabbitmq_url_param = aws_ssm_parameter.rabbitmq_url.name
    aws_region         = var.aws_region
  })
}

# ── EC2: Worker ───────────────────────────────────────────────────────────────
module "ec2_worker" {
  source            = "./modules/ec2"
  name              = "recetas-worker"
  instance_type     = var.instance_type
  key_name          = var.key_name
  security_group_id = module.sg.worker_sg_id
  user_data = templatefile("${path.module}/scripts/install_worker.sh", {
    mongo_uri_param    = aws_ssm_parameter.mongo_uri.name
    rabbitmq_url_param = aws_ssm_parameter.rabbitmq_url.name
    aws_region         = var.aws_region
  })
}

# ── Parameter Store ───────────────────────────────────────────────────────────
resource "aws_ssm_parameter" "mongo_uri" {
  name  = "/recetas/mongo_uri"
  type  = "SecureString"
  value = "mongodb://${module.ec2_mongodb.private_ip}:27017"
}

resource "aws_ssm_parameter" "rabbitmq_url" {
  name  = "/recetas/rabbitmq_url"
  type  = "SecureString"
  value = "amqp://guest:guest@${module.ec2_rabbitmq.private_ip}:5672/"
}

# ── Application Load Balancer ─────────────────────────────────────────────────
module "alb" {
  source     = "./modules/alb"
  name       = "recetas-alb"
  vpc_id     = data.aws_vpc.default.id
  subnet_ids = data.aws_subnets.default.ids
  sg_id      = module.sg.alb_sg_id
  api_instance_ids = [
    module.ec2_api_1.instance_id,
    module.ec2_api_2.instance_id,
  ]
}
