#!/bin/bash
set -e

apt-get update -y
apt-get install -y python3-pip python3-venv git

cd /home/ubuntu
git clone https://github.com/TU_USUARIO/recetas-api.git app
cd app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cat > /home/ubuntu/app/.env <<EOF
MONGO_URI_PARAM=${mongo_uri_param}
RABBITMQ_URL_PARAM=${rabbitmq_url_param}
AWS_REGION=${aws_region}
MONGO_DB_NAME=recetas_db
EOF

cat > /etc/systemd/system/recetas-worker.service <<EOF
[Unit]
Description=Recetas Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app
EnvironmentFile=/home/ubuntu/app/.env
ExecStart=/home/ubuntu/app/venv/bin/python worker/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable recetas-worker
systemctl start recetas-worker

echo "Worker instalado y corriendo."
