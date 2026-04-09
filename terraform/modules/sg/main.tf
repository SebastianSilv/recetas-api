variable "vpc_id" {
  type = string
}

# ── ALB: acepta tráfico HTTP público ─────────────────────────────────────────
resource "aws_security_group" "alb" {
  name        = "recetas-alb-sg"
  description = "SG del Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── API: acepta tráfico solo desde el ALB ────────────────────────────────────
resource "aws_security_group" "api" {
  name        = "recetas-api-sg"
  description = "SG de las instancias de la API"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restringir a tu IP en producción
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── MongoDB: acepta tráfico solo desde la API y el Worker ────────────────────
resource "aws_security_group" "mongodb" {
  name        = "recetas-mongodb-sg"
  description = "SG de MongoDB"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id, aws_security_group.worker.id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── RabbitMQ: acepta tráfico desde la API y el Worker ────────────────────────
resource "aws_security_group" "rabbitmq" {
  name        = "recetas-rabbitmq-sg"
  description = "SG de RabbitMQ"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5672
    to_port         = 5672
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id, aws_security_group.worker.id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Worker: solo necesita salida a MongoDB y RabbitMQ ────────────────────────
resource "aws_security_group" "worker" {
  name        = "recetas-worker-sg"
  description = "SG del Worker"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "alb_sg_id"      { value = aws_security_group.alb.id }
output "api_sg_id"      { value = aws_security_group.api.id }
output "mongodb_sg_id"  { value = aws_security_group.mongodb.id }
output "rabbitmq_sg_id" { value = aws_security_group.rabbitmq.id }
output "worker_sg_id"   { value = aws_security_group.worker.id }
