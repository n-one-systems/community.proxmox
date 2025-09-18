from unittest.mock import MagicMock

from ansible_collections.community.proxmox.plugins.module_utils import sdn


def test_apply_sdn_configuration_check_mode():
    module = MagicMock()
    proxmox_api = MagicMock()

    applied = sdn.apply_sdn_configuration(proxmox_api, module, check_mode=True)

    assert applied is False
    proxmox_api.cluster.sdn.put.assert_not_called()


def test_apply_sdn_configuration_executes():
    module = MagicMock()
    proxmox_api = MagicMock()

    applied = sdn.apply_sdn_configuration(proxmox_api, module, check_mode=False)

    assert applied is True
    proxmox_api.cluster.sdn.put.assert_called_once_with(apply=1)
