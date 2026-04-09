variable "name"             { type = string }
variable "vpc_id"           { type = string }
variable "subnet_ids"       { type = list(string) }
variable "sg_id"            { type = string }
variable "api_instance_ids" { type = list(string) }

# ── Load Balancer ─────────────────────────────────────────────────────────────
resource "aws_lb" "this" {
  name               = var.name
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.sg_id]
  subnets            = var.subnet_ids

  tags = {
    Name    = var.name
    Project = "recetas-api"
  }
}

# ── Target Group: apunta al puerto 8000 de la API ────────────────────────────
resource "aws_lb_target_group" "api" {
  name        = "${var.name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}

# ── Registrar instancias API en el Target Group ───────────────────────────────
resource "aws_lb_target_group_attachment" "api" {
  count            = length(var.api_instance_ids)
  target_group_arn = aws_lb_target_group.api.arn
  target_id        = var.api_instance_ids[count.index]
  port             = 8000
}

# ── Listener HTTP en puerto 80 ────────────────────────────────────────────────
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

output "dns_name" { value = aws_lb.this.dns_name }
