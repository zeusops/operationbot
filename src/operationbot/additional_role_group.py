from typing import Union

from operationbot import config as cfg
from operationbot.role import Role
from operationbot.roleGroup import RoleGroup


class AdditionalRoleGroup(RoleGroup):
    def __init__(self, name="Additional"):
        super().__init__(name, isInline=False)

    def removeRole(self, role: Union[str, Role]) -> None:
        super().removeRole(role)

        # In case the role was removed from in the middle of the list, reorder
        # the emojis
        for role_, emoji in zip(self.roles, cfg.ADDITIONAL_ROLE_EMOJIS):
            role_.emoji = emoji
