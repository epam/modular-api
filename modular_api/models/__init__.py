import os
import pymongo

from modular_sdk.commons.helpers import classproperty
from modular_sdk.models.pynamongo.adapter import PynamoDBToPymongoAdapter
from modular_api.helpers.constants import ServiceMode, Env
from modular_api.services import SP
from modular_sdk.models.pynamongo.models import Model, SafeUpdateModel


class MongoClientSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> pymongo.MongoClient:
        if cls._instance is None:
            env = SP.env
            cls._instance = pymongo.MongoClient(env.mongo_uri())
        return cls._instance


class PynamoDBToPymongoAdapterSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> PynamoDBToPymongoAdapter:
        if cls._instance is None:
            env = SP.env
            cls._instance = PynamoDBToPymongoAdapter(
                db=MongoClientSingleton.get_instance().get_database(
                    env.mongo_database()
                )
            )
        return cls._instance

    @classproperty
    def is_docker(cls) -> bool:
        return os.getenv(Env.MODE, Env.MODE.default) \
            in (ServiceMode.ONPREM, ServiceMode.PRIVATE)


class BaseModel(Model):
    @classmethod
    def is_mongo_model(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.is_docker

    @classmethod
    def mongo_adapter(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.get_instance()


class BaseSafeUpdateModel(SafeUpdateModel):
    @classmethod
    def is_mongo_model(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.is_docker

    @classmethod
    def mongo_adapter(cls) -> PynamoDBToPymongoAdapter:
        return PynamoDBToPymongoAdapterSingleton.get_instance()
