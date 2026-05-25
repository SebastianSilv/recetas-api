#!/bin/bash
set -e

apt-get update -y
apt-get install -y curl gnupg apt-transport-https

curl -1sLf 'https://dl.cloudsmith.io/public/rabbitmq/rabbitmq-erlang/setup.deb.sh' | bash
curl -1sLf 'https://dl.cloudsmith.io/public/rabbitmq/rabbitmq-server/setup.deb.sh' | bash

apt-get update -y
apt-get install -y erlang rabbitmq-server

systemctl enable rabbitmq-server
systemctl start rabbitmq-server

rabbitmq-plugins enable rabbitmq_management

echo "RabbitMQ instalado y corriendo."

rabbitmqctl add_user recetas recetas123
rabbitmqctl set_user_tags recetas administrator
rabbitmqctl set_permissions -p / recetas ".*" ".*" ".*"