import copy
from hashlib import sha256

from modular_api.helpers.exceptions import ModularApiConfigurationException
from modular_api.helpers.log_helper import get_logger

ALLOW = 'Allow'
DENY = 'Deny'

_LOG = get_logger(__name__)


def policy_sort(policy_list: list) -> dict:
    """
    Sort all user policies by "Effect" - Allow/Deny.
    """
    deny_actions = dict()
    allow_actions = dict()
    # todo check for old-style policies, remove after 3.85 prod update
    for item in policy_list:
        if item.get('Group') or item.get('MountPoint'):
            _LOG.error(
                f'Found old style RBAC v1 policy. Some policy still contains '
                f'"MountPoint":"{item.get("MountPoint")}" and/or '
                f'"Group":"{item.get("Group")}"'
            )
            raise ModularApiConfigurationException(
                'Invalid policies detected. Please contact support team'
            )
    # =====
    for item in policy_list:
        module = item['Module']
        allow = True if item['Effect'] == ALLOW else False
        resources = item['Resources']
        if allow:
            if module not in allow_actions.keys():
                allow_actions[module] = []
            allow_actions[module].extend(resources)
        else:
            if module not in deny_actions.keys():
                deny_actions[module] = []
            deny_actions[module].extend(resources)

    policy = {ALLOW: set(), DENY: set()}
    for module, items in allow_actions.items():
        for value in items:
            policy[ALLOW].add(f'/{module}@{value}')
    for module, items in deny_actions.items():
        for value in items:
            policy[DENY].add(f'/{module}@{value}')

    return policy


def check_entire_module(*args) -> bool:
    """
    Check if entire module allowed
    """
    allowed = args[0]
    module = args[1]
    for val in allowed:
        if val == f'{module}*':
            return True
    return False


def check_module_present(*args) -> bool:
    """
    Check if module name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    for val in allowed:
        if val.startswith(module):
            return True
    return False


def check_entire_group(*args) -> bool:
    """
    Check if entire group allowed
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    for val in allowed:
        if val == f'{module}{group}:*':
            return True
    return False


def check_in_group(*args) -> bool:
    """
    Check if group name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    for val in allowed:
        if val.startswith(f'{module}{group}'):
            return True
    return False


def check_entire_subgroup(*args) -> bool:
    """
    Check if entire subgroup allowed
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val == f'{module}{group}/{subgroup}:*':
            return True
    return False


def check_in_subgroup(*args) -> bool:
    """
    Check if subgroup name is in allowed resources
    """
    allowed = args[0]
    module = args[1]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val.startswith(f'{module}{group}/{subgroup}'):
            return True
    return False


def check_root_command(*args) -> bool:
    """
    Check if root command name is in allowed module
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    for val in allowed:
        if val == f'{module}{command}':
            return True
    return False


def check_group_command(*args) -> bool:
    """
    Check if command name is in allowed group
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    group = args[3]
    for val in allowed:
        if val == f'{module}{group}:{command}':
            return True
    return False


def check_subgroup_command(*args) -> bool:
    """
    Check if command name is in allowed subgroup
    """
    allowed = args[0]
    module = args[1]
    command = args[2]
    group = args[3]
    subgroup = args[4]
    for val in allowed:
        if val == f'{module}{group}/{subgroup}:{command}':
            return True
    return False


def check_permission(
        policy: list,
        module: str,
        command=None,
        group=None,
        subgroup=None,
        atype: str = 'default',
) -> bool:
    """
    1. Check user permissions by "Deny" rules
    2. Check user permissions by "Allow" rules
    """
    policy = policy_sort(policy)
    module = f'{module}@'
    denied = policy[DENY]
    allowed = policy[ALLOW]
    # ===== check DENIED =====
    for value in denied:
        if value.startswith('/*@'):
            return False
    if f'{module}*' in denied:
        return False
    if f'{module}{command}' in denied:
        return False
    if f'{module}{group}:*' in denied:
        return False
    if f'{module}{group}:{command}' in denied:
        return False
    if f'{module}{group}/{subgroup}:*' in denied:
        return False
    if f'{module}{group}/{subgroup}:{command}' in denied:
        return False
    # ====== check ALLOWED =====
    for value in allowed:
        if value.startswith('/*@'):
            return True
    allow_map = {
        "entire_module": check_entire_module,
        "module": check_module_present,
        "entire_group": check_entire_group,
        "group": check_in_group,
        "entire_subgroup": check_entire_subgroup,
        "subgroup": check_in_subgroup,
        "root_command": check_root_command,
        "group_command": check_group_command,
        "subgroup_command": check_subgroup_command
    }
    verifier = allow_map.get(atype)
    if verifier:
        return verifier(allowed, module, command, group, subgroup)

    return True


# ── recursive deny helpers ──────────────────────────────────────────

def _deny_filter_body(
        denied: set,
        module_prefix: str,
        original_body: dict,
        filtered_body: dict,
        group_path: str,
) -> None:
    """
    Recursively walk *original_body* and delete denied entries from
    the corresponding *filtered_body* (which is a deep-copy).

    Policy format examples that are checked:
        /{module}@{group_path}:*          - deny entire group / sub-group
        /{module}@{group_path}:{command}  - deny single command
        /{module}@{command}               - deny root-level command
    """
    bd = 'body'
    for item_name, item_content in original_body.items():
        if item_name not in filtered_body:
            continue

        if item_content.get('type') == 'group':
            new_path = (
                f'{group_path}/{item_name}' if group_path else item_name
            )
            # whole group denied?
            if f'{module_prefix}{new_path}:*' in denied:
                del filtered_body[item_name]
                continue
            # recurse into children
            child_body = item_content.get(bd)
            if child_body and bd in filtered_body.get(item_name, {}):
                _deny_filter_body(
                    denied=denied,
                    module_prefix=module_prefix,
                    original_body=child_body,
                    filtered_body=filtered_body[item_name][bd],
                    group_path=new_path,
                )
        else:
            # leaf command
            if group_path:
                check = f'{module_prefix}{group_path}:{item_name}'
            else:
                check = f'{module_prefix}{item_name}'
            if check in denied:
                del filtered_body[item_name]


def filter_meta_by_deny_priority(
        sorted_policy: dict,
        all_meta: dict,
) -> dict:
    """
    Remove every resource that is explicitly **denied**.
    Supports arbitrary group nesting depth.
    """
    bd = 'body'
    user_commands = copy.deepcopy(all_meta)
    denied = sorted_policy[DENY]

    if not denied:
        return user_commands

    # global deny -> nothing is available
    if any(v.startswith('/*@') for v in denied):
        return {}

    for module, module_content in all_meta.items():
        module_prefix = f'{module}@'

        # whole module denied
        if f'{module_prefix}*' in denied:
            del user_commands[module]
            continue

        _deny_filter_body(
            denied=denied,
            module_prefix=module_prefix,
            original_body=module_content[bd],
            filtered_body=user_commands[module][bd],
            group_path='',
        )

    return user_commands


# ── recursive allow helpers ─────────────────────────────────────────

def _allow_filter_body(
        allowed: set,
        module_prefix: str,
        original_body: dict,
        filtered_body: dict,
        group_path: str,
) -> None:
    """
    Recursively walk *original_body* and delete entries from the
    corresponding *filtered_body* that are **not** allowed.

    Policy format examples that are checked:
        /{module}@{group_path}:*          - allow entire group / sub-group
        /{module}@{group_path}:{command}  - allow single command
        /{module}@{command}               - allow root-level command
    """
    bd = 'body'
    for item_name, item_content in original_body.items():
        if item_name not in filtered_body:
            continue

        if item_content.get('type') == 'group':
            new_path = (
                f'{group_path}/{item_name}' if group_path else item_name
            )

            # entire group explicitly allowed -> keep everything below
            if f'{module_prefix}{new_path}:*' in allowed:
                continue

            # is *anything* under this path allowed?  (prefix check)
            # use separator-aware matching to avoid false positives
            # e.g. "task" must not match "taskmanager"
            prefix = f'{module_prefix}{new_path}'
            if not any(
                v.startswith(prefix + ':') or v.startswith(prefix + '/')
                for v in allowed
            ):
                del filtered_body[item_name]
                continue

            # recurse into children
            child_body = item_content.get(bd)
            if child_body and bd in filtered_body.get(item_name, {}):
                _allow_filter_body(
                    allowed=allowed,
                    module_prefix=module_prefix,
                    original_body=child_body,
                    filtered_body=filtered_body[item_name][bd],
                    group_path=new_path,
                )
        else:
            # leaf command
            if group_path:
                check = f'{module_prefix}{group_path}:{item_name}'
            else:
                check = f'{module_prefix}{item_name}'
            if check not in allowed:
                del filtered_body[item_name]


def filter_meta_by_allow_priority(
        sorted_policy: dict,
        all_meta: dict,
) -> dict:
    """
    Keep only resources that are explicitly **allowed**.
    Supports arbitrary group nesting depth.
    """
    bd = 'body'
    user_commands = copy.deepcopy(all_meta)
    allowed = sorted_policy[ALLOW]

    # global allow -> keep everything
    if any(v.startswith('/*@') for v in allowed):
        return user_commands

    for module, module_content in all_meta.items():
        module_prefix = f'{module}@'

        # entire module allowed
        if f'{module_prefix}*' in allowed:
            continue

        # nothing in this module allowed at all
        if not any(v.startswith(module_prefix) for v in allowed):
            del user_commands[module]
            continue

        _allow_filter_body(
            allowed=allowed,
            module_prefix=module_prefix,
            original_body=module_content[bd],
            filtered_body=user_commands[module][bd],
            group_path='',
        )

    return user_commands


# todo refactor mount point to be set by module
def filter_commands_by_permissions(
        available_commands: dict,
        group_policy: list,
) -> dict:
    """
    Filter for user permissions. The rules summary described below:
    1) Deny effect has more priority than Allow;
    2) If some command/groups/subgroups/modules are not in user policy(ies)
       then they will not be available to use;
    3) Entire API rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "*",
            "Resources": [
                "*"
            ]
        }
    4) Module rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "*"
            ]
        }
    5) Module-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$command_name_1",
                "$command_name_2",
                ...
                "$command_name_N",
            ]
        }
    6) Module-group rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$group_name_1:*",
                "$group_name_2:*",
                ...
                "$group_name_N:*",
            ]
        }
    7) Module-group-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "$group_name_1:$command_name_1",
                "$group_name_2:$command_name_2",
                ...
                "$group_name_N:$command_name_N",
            ]
        }
    8) Module-group-subgroup rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "group_name_1/$subgroup_name_1:*",
                "group_name_2/$subgroup_name_2:*",
                ...
                "group_name_N/$subgroup_name_N:*",
            ]
        }
    9) Module-group-subgroup-command rule:
       {
            "Effect": "Allow/Deny",
            "Description": "$Purpose_description", - does not impact on logic
            "Module": "$module_name",
            "Resources": [
                "group_name_1/$subgroup_name_1:$command_name_1",
                "group_name_2/$subgroup_name_2:$command_name_2",
                ...
                "group_name_N/$subgroup_name_N:$command_name_N",
            ]
        }
    10) Arbitrary depth group rule (N levels):
       {
            "Effect": "Allow/Deny",
            "Module": "$module_name",
            "Resources": [
                "g1/g2/.../gN:*",
                "g1/g2/.../gN:$command_name",
            ]
        }
    """
    all_meta = copy.deepcopy(available_commands)
    if '/' in available_commands.keys():
        #  "/" stands for "m3admin" endpoint in API-meta, but in policy
        #  we use "m3admin" in module name property instead of "/"
        all_meta['/m3admin'] = all_meta['/']
        del all_meta['/']
    del available_commands

    sorted_policy = policy_sort(group_policy)

    filtered_by_deny = filter_meta_by_deny_priority(
        sorted_policy=sorted_policy,
        all_meta=all_meta,
    )
    del all_meta
    filtered_by_allow = filter_meta_by_allow_priority(
        sorted_policy=sorted_policy,
        all_meta=filtered_by_deny,
    )

    user_meta = dict()
    for key, value in filtered_by_allow.items():
        #  rollback from temp "m3admin" module name to default endpoint "/"
        if key == '/m3admin':
            user_meta['/'] = value
        else:
            user_meta[key] = value

    return user_meta


def hash_user_name(user_name):
    return sha256(user_name.encode('utf-8')).hexdigest()
