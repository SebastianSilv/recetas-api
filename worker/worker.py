"""
Worker: consume mensajes de RabbitMQ y procesa inserciones/eliminaciones
de recetas en MongoDB. Al finalizar actualiza el status de la tarea.
"""

import json
import os
import time
import boto3
import pika
from pymongo import MongoClient
from bson import ObjectId

QUEUE_NAME = "recetas_queue"


def get_param(param_env: str, fallback_env: str, fallback_default: str) -> str:
    param_name = os.getenv(param_env, "")
    if param_name:
        try:
            ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            return response["Parameter"]["Value"]
        except Exception as e:
            print(f"Parameter Store error ({param_name}): {e}")
    return os.getenv(fallback_env, fallback_default)


def get_mongo_uri() -> str:
    return get_param("MONGO_URI_PARAM", "MONGO_URI", "mongodb://localhost:27017")


def get_rabbitmq_url() -> str:
    return get_param("RABBITMQ_URL_PARAM", "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


def get_db():
    uri = get_mongo_uri()
    client = MongoClient(uri)
    db_name = os.getenv("MONGO_DB_NAME", "recetas_db")
    return client[db_name]


def process_message(body: bytes, db):
    message = json.loads(body)
    action = message.get("action")
    task_id = message.get("task_id")

    try:
        if action == "insert":
            data = message["data"]
            db["recetas"].insert_one(data)
            print(f"[worker] Receta insertada para task {task_id}")

        elif action == "delete":
            receta_id = message["receta_id"]
            db["recetas"].delete_one({"_id": ObjectId(receta_id)})
            print(f"[worker] Receta {receta_id} eliminada para task {task_id}")

        else:
            raise ValueError(f"Acción desconocida: {action}")

        db["tasks"].update_one({"task_id": task_id}, {"$set": {"status": "done"}})

    except Exception as e:
        print(f"[worker] Error procesando task {task_id}: {e}")
        db["tasks"].update_one({"task_id": task_id}, {"$set": {"status": "error"}})


def callback(ch, method, properties, body):
    db = get_db()
    process_message(body, db)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    url = get_rabbitmq_url()
    retries = 10
    for i in range(retries):
        try:
            params = pika.URLParameters(url)
            connection = pika.BlockingConnection(params)
            break
        except Exception as e:
            print(f"[worker] Esperando RabbitMQ... intento {i + 1}/{retries}: {e}")
            time.sleep(5)
    else:
        print("[worker] No se pudo conectar a RabbitMQ. Saliendo.")
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("[worker] Esperando mensajes. Ctrl+C para salir.")
    channel.start_consuming()


if __name__ == "__main__":
    main()
