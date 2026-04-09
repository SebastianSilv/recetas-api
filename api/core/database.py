import os
import boto3
from motor.motor_asyncio import AsyncIOMotorClient

client: AsyncIOMotorClient = None


def get_mongo_uri() -> str:
    """
    Obtiene la URI de MongoDB desde AWS Parameter Store si está disponible,
    de lo contrario usa la variable de entorno local.
    """
    param_name = os.getenv("MONGO_URI_PARAM", "")
    if param_name:
        try:
            ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            return response["Parameter"]["Value"]
        except Exception as e:
            print(f"No se pudo obtener el parámetro de Parameter Store: {e}")

    return os.getenv("MONGO_URI", "mongodb://localhost:27017")


def get_rabbitmq_url() -> str:
    """
    Obtiene la URL de RabbitMQ desde AWS Parameter Store si está disponible,
    de lo contrario usa la variable de entorno local.
    """
    param_name = os.getenv("RABBITMQ_URL_PARAM", "")
    if param_name:
        try:
            ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            return response["Parameter"]["Value"]
        except Exception as e:
            print(f"No se pudo obtener el parámetro de Parameter Store: {e}")

    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


async def connect_db():
    global client
    uri = get_mongo_uri()
    client = AsyncIOMotorClient(uri)
    print("Conectado a MongoDB")


async def close_db():
    if client:
        client.close()
        print("Desconectado de MongoDB")


def get_database():
    db_name = os.getenv("MONGO_DB_NAME", "recetas_db")
    return client[db_name]
