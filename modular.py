#!/usr/local/bin/python
import json
import os
import sys
from typing import TYPE_CHECKING, cast, Generator

import pymongo
from pymongo.operations import IndexModel

if TYPE_CHECKING:
    from modular_api.models import BaseModel

from modular_api_cli.modular_cli_group.modular import modular
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger('init')


class IndexesCreator:
    main_index_name = 'main'
    hash_key_order = pymongo.ASCENDING
    range_key_order = pymongo.DESCENDING

    def __init__(self, models: tuple['BaseModel', ...]):
        self._models = models

    @staticmethod
    def _get_hash_range(model: 'BaseModel') -> tuple[str, str | None]:
        h, r = None, None
        for attr in model.get_attributes().values():
            if attr.is_hash_key:
                h = attr.attr_name
            if attr.is_range_key:
                r = attr.attr_name
        return cast(str, h), r

    @staticmethod
    def _iter_indexes(model: 'BaseModel'
                      ) -> Generator[tuple[str, str, str | None], None, None]:
        """
        Yields tuples: (index name, hash_key, range_key) indexes of the given
        model. Currently, only global secondary indexes are used so this
        implementation wasn't tested with local ones. Uses private PynamoDB
        API because cannot find public methods that can help
        """
        for index in model._indexes.values():
            name = index.Meta.index_name
            h, r = None, None
            for attr in index.Meta.attributes.values():
                if attr.is_hash_key:
                    h = attr.attr_name
                if attr.is_range_key:
                    r = attr.attr_name
            yield name, cast(str, h), r

    def _iter_all_indexes(self, model: 'BaseModel'
                          ) -> Generator[tuple[str, str, str | None], None, None]:
        yield self.main_index_name, *self._get_hash_range(model)
        yield from self._iter_indexes(model)

    @staticmethod
    def _exceptional_indexes() -> tuple[str, ...]:
        return (
            '_id_',
        )

    def _ensure_indexes(self, model: 'BaseModel'):
        table_name = model.Meta.table_name
        _LOG.info(f'Going to check indexes for {table_name}')
        collection = model.mongodb_handler().mongodb.collection(table_name)
        existing = collection.index_information()
        for name in self._exceptional_indexes():
            existing.pop(name, None)
        needed = {}
        for name, h, r in self._iter_all_indexes(model):
            needed[name] = [(h, self.hash_key_order)]
            if r:
                needed[name].append((r, self.range_key_order))
        to_create = []
        to_delete = set()
        for name, data in existing.items():
            if name not in needed:
                to_delete.add(name)
                continue
            # name in needed so maybe the index is valid, and we must keep it
            # or the index has changed, and we need to re-create it
            if data.get('key', []) != needed[name]:  # not valid
                to_delete.add(name)
                to_create.append(IndexModel(
                    keys=needed[name],
                    name=name
                ))
            needed.pop(name)
        for name, keys in needed.items():  # all that left must be created
            to_create.append(IndexModel(
                keys=keys,
                name=name
            ))
        for name in to_delete:
            _LOG.info(f'Going to remove index: {name}')
            collection.drop_index(name)
        if to_create:
            _message = ','.join(
                json.dumps(i.document,
                           separators=(',', ':')) for i in to_create
            )
            _LOG.info(f'Going to create indexes: {_message}')
            collection.create_indexes(to_create)

    def create(self):
        _LOG.debug('Going to sync indexes with code')
        for model in self._models:
            self._ensure_indexes(model)


def init():
    """
    Separate init for docker container. This method just skips if necessary
    items already exist. So, 1 exit code will be only if something really fails
    :return:
    """
    # TODO maybe some to click
    from modular_api.helpers.password_util import generate_password, secure_string
    from modular_api.services import SERVICE_PROVIDER as SP
    policy = SP.policy_service.describe_policy('admin_policy')
    if not policy:
        _LOG.info('admin policy does not exist. Creating')
        policy = SP.policy_service.create_policy_entity(
            policy_name='admin_policy',
            policy_content=[{
                "Description": "Admin policy",
                "Module": "*",
                "Effect": "Allow",
                "Resources": ["*"]
            }]
        )
        policy.hash = SP.policy_service.calculate_policy_hash(
            policy_item=policy
        )
        SP.policy_service.save_policy(policy_item=policy)
    else:
        _LOG.info('admin policy already exists. Skipping')
    group = SP.group_service.describe_group('admin_group')
    if not group:
        _LOG.info('admin group does not exist. Creating')
        group = SP.group_service.create_group_entity(
            group_name='admin_group',
            policies=['admin_policy']
        )

        group.hash = SP.group_service.calculate_group_hash(
            group_item=group
        )
        SP.group_service.save_group(group_item=group)
    else:
        _LOG.info('admin group already exists. Skipping')
    user = SP.user_service.describe_user('admin')
    if not user:
        _LOG.info('admin user does not exist. Creating')
        user_password = os.getenv('MODULAR_API_INIT_PASSWORD')
        if user_password:
            is_autogenerated = False
        else:
            user_password = generate_password()
            is_autogenerated = True

        user = SP.user_service.create_user_entity(
            username='admin',
            password=secure_string(user_password),
            group=['admin_group']
        )

        user.hash = SP.user_service.calculate_user_hash(user)
        SP.user_service.save_user(user_item=user)

        if is_autogenerated:
            print(f'Autogenerated password: {user_password}')
    else:
        _LOG.info('admin user already exists. Skipping')

    _LOG.debug('Initialization finished')


admin_policy = [{
    "Description": "Admin policy",
    "Module": "*",
    "Effect": "Allow",
    "Resources": ["*"]
}]


def init():
    """
    Separate init for docker container. This method just skips if necessary
    items already exist. So, 1 exit code will be only if something really fails
    :return:
    """
    # TODO maybe some to click
    from modular_api.helpers.password_util import generate_password, secure_string
    from modular_api.services import SERVICE_PROVIDER as SP
    policy = SP.policy_service.describe_policy('admin_policy')
    if not policy:
        print('admin policy does not exist. Creating')
        policy = SP.policy_service.create_policy_entity(
            policy_name='admin_policy',
            policy_content=admin_policy
        )
        policy.hash = SP.policy_service.calculate_policy_hash(
            policy_item=policy
        )
        SP.policy_service.save_policy(policy_item=policy)
    else:
        print('admin policy already exists. Skipping')
    group = SP.group_service.describe_group('admin_group')
    if not group:
        print('admin group does not exist. Creating')
        group = SP.group_service.create_group_entity(
            group_name='admin_group',
            policies=['admin_policy']
        )

        group.hash = SP.group_service.calculate_group_hash(
            group_item=group
        )
        SP.group_service.save_group(group_item=group)
    else:
        print('admin group already exists. Skipping')
    user = SP.user_service.describe_user('admin')
    if not user:
        print('admin user does not exist. Creating')
        user_password = os.getenv('MODULAR_API_INIT_PASSWORD')
        if user_password:
            is_autogenerated = False
        else:
            user_password = generate_password()
            is_autogenerated = True

        user = SP.user_service.create_user_entity(
            username='admin',
            password=secure_string(user_password),
            group=['admin_group']
        )

        user.hash = SP.user_service.calculate_user_hash(user)
        SP.user_service.save_user(user_item=user)

        if is_autogenerated:
            print(f'Autogenerated password: {user_password}')
    else:
        print('admin user already exists. Skipping')
    print('Initialization finished')


if __name__ == '__main__':
    # TODO move to modular click or make normal CLI with argparse
    if len(sys.argv) == 2 and sys.argv[1] == 'init':
        try:
            init()
        except Exception:
            sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] == 'create-indexes':
        from modular_api.models.audit_model import Audit
        from modular_api.models.group_model import Group
        from modular_api.models.policy_model import Policy
        from modular_api.models.stats_model import Stats
        from modular_api.models.user_model import User
        from modular_api.models.refresh_token_model import RefreshToken
        try:
            IndexesCreator((
                Audit, Group, Policy, Stats, User, RefreshToken
            )).create()
        except Exception:
            sys.exit(1)
    else:
        modular()
