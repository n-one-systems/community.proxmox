import pytest
from unittest.mock import MagicMock, patch

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import ProxmoxAnsible
from ansible_collections.community.proxmox.plugins.modules import proxmox_sdn_zone


@pytest.fixture
def module_args_present():
    return {
        "api_host": "localhost",
        "api_user": "root@pam",
        "api_password": "secret",
        "validate_certs": False,
        "zone": "tenant01",
        "type": "evpn",
        "state": "present",
        "controller": "frr01",
        "fabric": "fabric01",
        "mtu": 1400,
        "advertise_subnets": True,
    }


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.cluster = MagicMock()
    api.cluster.sdn = MagicMock()
    api.cluster.sdn.zones = MagicMock()
    api.cluster.sdn.zones.post = MagicMock()
    api.cluster.sdn.zones.return_value = MagicMock()
    api.cluster.sdn.zones.return_value.put = MagicMock()
    api.cluster.sdn.zones.return_value.delete = MagicMock()
    return api


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_ensure_present_creates_zone(mock_init, module_args_present, mock_api):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_present
    module.check_mode = False

    proxmox = proxmox_sdn_zone.ProxmoxSDNZoneModule(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api
    proxmox.get_zone = MagicMock(side_effect=[None, {"zone": "tenant01", "type": "evpn"}])

    changed, zone_data, msg = proxmox.ensure_present()

    assert changed is True
    assert zone_data == {"zone": "tenant01", "type": "evpn"}
    assert "created" in msg

    mock_api.cluster.sdn.zones.post.assert_called_once_with(
        zone="tenant01",
        type="evpn",
        controller="frr01",
        fabric="fabric01",
        mtu=1400,
        **{"advertise-subnets": 1}
    )


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_ensure_present_updates_zone(mock_init, module_args_present, mock_api):
    module_args_present["mtu"] = 1500

    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_present
    module.check_mode = False

    proxmox = proxmox_sdn_zone.ProxmoxSDNZoneModule(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api
    proxmox.get_zone = MagicMock(
        side_effect=[
            {
                "zone": "tenant01",
                "type": "evpn",
                "mtu": 1400,
                "controller": "frr01",
                "fabric": "fabric01",
                "advertise-subnets": 1,
            },
            {
                "zone": "tenant01",
                "type": "evpn",
                "mtu": 1500,
                "controller": "frr01",
                "fabric": "fabric01",
                "advertise-subnets": 1,
            },
        ]
    )

    changed, zone_data, msg = proxmox.ensure_present()

    assert changed is True
    assert zone_data["zone"] == "tenant01"
    assert zone_data["type"] == "evpn"
    assert zone_data["mtu"] == 1500
    assert "updated" in msg

    mock_api.cluster.sdn.zones.return_value.put.assert_called_once_with(mtu=1500)


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_ensure_present_no_change(mock_init, module_args_present, mock_api):
    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_present
    module.check_mode = False

    proxmox = proxmox_sdn_zone.ProxmoxSDNZoneModule(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api
    proxmox.get_zone = MagicMock(return_value={
        "zone": "tenant01",
        "type": "evpn",
        "controller": "frr01",
        "fabric": "fabric01",
        "mtu": 1400,
        "advertise-subnets": 1,
    })

    changed, zone_data, msg = proxmox.ensure_present()

    assert changed is False
    assert zone_data["zone"] == "tenant01"
    assert "already present" in msg
    mock_api.cluster.sdn.zones.return_value.put.assert_not_called()


@patch.object(ProxmoxAnsible, "__init__", return_value=None)
def test_ensure_absent_removes_zone(mock_init, module_args_present, mock_api):
    module_args_present["state"] = "absent"

    module = MagicMock(spec=AnsibleModule)
    module.params = module_args_present
    module.check_mode = False

    proxmox = proxmox_sdn_zone.ProxmoxSDNZoneModule(module)
    proxmox.module = module
    proxmox.proxmox_api = mock_api
    proxmox.get_zone = MagicMock(return_value={"zone": "tenant01"})

    changed, zone_data, msg = proxmox.ensure_absent()

    assert changed is True
    assert zone_data is None
    assert "removed" in msg
    mock_api.cluster.sdn.zones.return_value.delete.assert_called_once_with()


@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.apply_sdn_configuration")
@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.ProxmoxSDNZoneModule")
@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.AnsibleModule")
def test_main_applies_configuration(mock_ansible_module, mock_zone_module, mock_apply, module_args_present):
    module = MagicMock()
    module.params = module_args_present
    module.check_mode = False
    module.exit_json = lambda **kwargs: (_ for _ in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (_ for _ in ()).throw(SystemExit(kwargs))
    mock_ansible_module.return_value = module

    zone_instance = MagicMock()
    zone_instance.ensure_present.return_value = (True, {"zone": "tenant01"}, "created")
    zone_instance.proxmox_api = MagicMock()
    mock_zone_module.return_value = zone_instance

    with pytest.raises(SystemExit) as exc:
        proxmox_sdn_zone.main()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["sdn_zone"] == {"zone": "tenant01"}
    assert result["sdn_configuration_applied"] is True
    assert result["msg"] == "created"

    mock_apply.assert_called_once_with(zone_instance.proxmox_api, module, False)


@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.apply_sdn_configuration")
@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.ProxmoxSDNZoneModule")
@patch("ansible_collections.community.proxmox.plugins.modules.proxmox_sdn_zone.AnsibleModule")
def test_main_skip_apply_when_unchanged(mock_ansible_module, mock_zone_module, mock_apply, module_args_present):
    module = MagicMock()
    module.params = module_args_present
    module.check_mode = False
    module.exit_json = lambda **kwargs: (_ for _ in ()).throw(SystemExit(kwargs))
    module.fail_json = lambda **kwargs: (_ for _ in ()).throw(SystemExit(kwargs))
    mock_ansible_module.return_value = module

    zone_instance = MagicMock()
    zone_instance.ensure_present.return_value = (False, {"zone": "tenant01"}, "unchanged")
    zone_instance.proxmox_api = MagicMock()
    mock_zone_module.return_value = zone_instance

    with pytest.raises(SystemExit) as exc:
        proxmox_sdn_zone.main()

    result = exc.value.args[0]
    assert result["changed"] is False
    assert "sdn_configuration_applied" not in result

    mock_apply.assert_not_called()
