output "alb_dns_name" {
  description = "DNS del Load Balancer — usa esta URL para acceder a la API"
  value       = module.alb.dns_name
}

output "api_1_public_ip" {
  description = "IP pública de la instancia API 1"
  value       = module.ec2_api_1.public_ip
}

output "api_2_public_ip" {
  description = "IP pública de la instancia API 2"
  value       = module.ec2_api_2.public_ip
}

output "mongodb_private_ip" {
  description = "IP privada de MongoDB"
  value       = module.ec2_mongodb.private_ip
}

output "rabbitmq_private_ip" {
  description = "IP privada de RabbitMQ"
  value       = module.ec2_rabbitmq.private_ip
}

output "worker_public_ip" {
  description = "IP pública del Worker"
  value       = module.ec2_worker.public_ip
}

output "swagger_url" {
  description = "URL de la documentación Swagger"
  value       = "http://${module.alb.dns_name}/docs"
}
