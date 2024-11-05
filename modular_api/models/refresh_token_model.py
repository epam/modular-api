import os
from pynamodb.attributes import UnicodeAttribute
from modular_api.helpers.constants import Env
from modular_api.models import BaseModel

USERNAME = 'u'
VERSION = 'v'


class RefreshToken(BaseModel):
    class Meta:
        table_name = 'ModularRefreshToken'
        region = os.environ.get(Env.AWS_REGION)

    username = UnicodeAttribute(hash_key=True, attr_name=USERNAME)
    version = UnicodeAttribute(attr_name=VERSION, null=True)
