#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Contributors
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
module: proxmox_sdn_zone
version_added: 1.5.0
short_description: Manage SDN zones within a Proxmox VE cluster
description:
  - Create, update or remove Software Defined Network (SDN) zones in a Proxmox VE cluster.
  - Pending SDN configuration changes are automatically applied after successful modifications.
author: Community Proxmox Contributors (@community-proxmox)
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  zone:
    description:
      - Identifier of the SDN zone.
    type: str
    required: true
  type:
    description:
      - SDN plugin type that should be used for the zone.
    type: str
    choices: ["evpn", "faucet", "qinq", "simple", "vlan", "vxlan"]
  state:
    description:
      - Desired state of the SDN zone.
    type: str
    choices: ["present", "absent"]
    default: present
  advertise_subnets:
    description:
      - Advertise EVPN subnets when using silent hosts.
    type: bool
  bridge:
    description:
      - Bridge that should be used for the zone.
    type: str
  bridge_disable_mac_learning:
    description:
      - Disable automatic MAC learning on the bridge.
    type: bool
  controller:
    description:
      - Name of the FRR controller used by the zone.
    type: str
  dhcp:
    description:
      - DHCP backend used by the zone.
    type: str
    choices: ["dnsmasq"]
  disable_arp_nd_suppression:
    description:
      - Disable IPv4 ARP and IPv6 neighbour discovery suppression.
    type: bool
  dns:
    description:
      - DNS API server used by the zone.
    type: str
  dnszone:
    description:
      - DNS zone managed for the SDN zone.
    type: str
  dp_id:
    description:
      - Faucet dataplane identifier.
    type: int
  exitnodes:
    description:
      - Comma separated list of exit node names.
    type: str
  exitnodes_local_routing:
    description:
      - Allow exit nodes to connect to EVPN guests through local routing.
    type: bool
  exitnodes_primary:
    description:
      - Primary exit node used for routing preferences.
    type: str
  fabric:
    description:
      - SDN fabric used as underlay for VXLAN zones.
    type: str
  ipam:
    description:
      - IPAM configuration identifier used for the zone.
    type: str
  lock_token:
    description:
      - Token used to unlock the global SDN configuration when modifying it.
    type: str
  mac:
    description:
      - Anycast logical router MAC address.
    type: str
  mtu:
    description:
      - MTU that should be configured for the zone.
    type: int
  nodes:
    description:
      - Comma separated list of cluster nodes participating in the zone.
    type: str
  peers:
    description:
      - Comma separated list of peer addresses.
    type: str
  reversedns:
    description:
      - Reverse DNS API server used by the zone.
    type: str
  rt_import:
    description:
      - Route target import configuration.
    type: str
  tag:
    description:
      - Service VLAN tag assigned to the zone.
    type: int
  vlan_protocol:
    description:
      - VLAN protocol used by the zone.
    type: str
    choices: ["802.1q", "802.1ad"]
  vrf_vxlan:
    description:
      - VXLAN identifier used for VRF separation.
    type: int
  vxlan_port:
    description:
      - UDP port used for VXLAN tunnels.
    type: int
extends_documentation_fragment:
  - community.proxmox.proxmox.actiongroup_proxmox
  - community.proxmox.proxmox.documentation
  - community.proxmox.attributes
"""

EXAMPLES = r"""
- name: Ensure an EVPN SDN zone exists
  community.proxmox.proxmox_sdn_zone:
    api_host: proxmox01
    api_user: root@pam
    api_password: secret
    validate_certs: false
    zone: tenant01
    type: evpn
    controller: frr01
    fabric: fabric01
    mtu: 1400

- name: Remove an unused SDN zone
  community.proxmox.proxmox_sdn_zone:
    api_host: proxmox01
    api_user: root@pam
    api_password: secret
    validate_certs: false
    zone: old-tenant
    state: absent
"""

RETURN = r"""
sdn_zone:
  description:
    - Details about the SDN zone after the module has finished.
  returned: when state is C(present)
  type: dict
  sample:
    zone: tenant01
    type: evpn
    mtu: 1400
sdn_configuration_applied:
  description:
    - Indicates whether the SDN configuration apply endpoint was triggered.
  returned: when configuration changes were performed outside of check mode
  type: bool
  sample: true
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.community.proxmox.plugins.module_utils.proxmox import (
    proxmox_auth_argument_spec,
    ProxmoxAnsible,
    ansible_to_proxmox_bool,
)
from ansible_collections.community.proxmox.plugins.module_utils.sdn import apply_sdn_configuration

try:  # pragma: no cover - proxmoxer is required at runtime
    from proxmoxer.core import ResourceException
except ImportError:  # pragma: no cover - handled in module_utils
    ResourceException = Exception


class ProxmoxSDNZoneModule(ProxmoxAnsible):
    """Manage SDN zones through the Proxmox API."""

    ZONE_OPTION_MAP = {
        "advertise_subnets": "advertise-subnets",
        "bridge": "bridge",
        "bridge_disable_mac_learning": "bridge-disable-mac-learning",
        "controller": "controller",
        "dhcp": "dhcp",
        "disable_arp_nd_suppression": "disable-arp-nd-suppression",
        "dns": "dns",
        "dnszone": "dnszone",
        "dp_id": "dp-id",
        "exitnodes": "exitnodes",
        "exitnodes_local_routing": "exitnodes-local-routing",
        "exitnodes_primary": "exitnodes-primary",
        "fabric": "fabric",
        "ipam": "ipam",
        "mac": "mac",
        "mtu": "mtu",
        "nodes": "nodes",
        "peers": "peers",
        "reversedns": "reversedns",
        "rt_import": "rt-import",
        "tag": "tag",
        "vlan_protocol": "vlan-protocol",
        "vrf_vxlan": "vrf-vxlan",
        "vxlan_port": "vxlan-port",
    }

    BOOLEAN_OPTIONS = {
        "advertise_subnets",
        "bridge_disable_mac_learning",
        "disable_arp_nd_suppression",
        "exitnodes_local_routing",
    }

    def get_zone(self, zone_name):
        try:
            return self.proxmox_api.cluster.sdn.zones(zone_name).get()
        except ResourceException as exc:
            status = getattr(exc, "status_code", None)
            if status == 404 or "404" in to_native(exc):
                return None
            self.module.fail_json(msg="Failed to retrieve SDN zone '{}': {}".format(zone_name, to_native(exc)))
        except Exception as exc:
            self.module.fail_json(msg="Failed to retrieve SDN zone '{}': {}".format(zone_name, to_native(exc)))

    def build_payload(self):
        payload = {}
        for option, api_field in self.ZONE_OPTION_MAP.items():
            value = self.module.params.get(option)
            if value is None:
                continue
            if option in self.BOOLEAN_OPTIONS:
                value = ansible_to_proxmox_bool(value)
            payload[api_field] = value
        return payload

    def build_updates(self, existing, desired):
        updates = {}
        for api_field, desired_value in desired.items():
            current_value = existing.get(api_field)
            if str(current_value) != str(desired_value):
                updates[api_field] = desired_value
        return updates

    def ensure_present(self):
        zone_name = self.module.params["zone"]
        zone_type = self.module.params.get("type")
        lock_token = self.module.params.get("lock_token")

        desired_payload = self.build_payload()
        existing_zone = self.get_zone(zone_name)

        if not existing_zone:
            create_payload = desired_payload.copy()
            create_payload.update({"zone": zone_name, "type": zone_type})
            if lock_token:
                create_payload["lock-token"] = lock_token

            if self.module.check_mode:
                msg = "SDN zone '{}' would be created (check mode).".format(zone_name)
                return True, create_payload, msg

            try:
                self.proxmox_api.cluster.sdn.zones.post(**create_payload)
            except Exception as exc:
                self.module.fail_json(msg="Failed to create SDN zone '{}': {}".format(zone_name, to_native(exc)))

            new_zone = self.get_zone(zone_name)
            msg = "SDN zone '{}' created.".format(zone_name)
            return True, new_zone, msg

        if zone_type and str(existing_zone.get("type")) != str(zone_type):
            self.module.fail_json(
                msg="SDN zone '{}' already exists with type '{}' which does not match the requested type '{}'".format(
                    zone_name, existing_zone.get("type"), zone_type
                )
            )

        updates = self.build_updates(existing_zone, desired_payload)
        if not updates:
            msg = "SDN zone '{}' already present.".format(zone_name)
            return False, existing_zone, msg

        if lock_token:
            updates["lock-token"] = lock_token

        if self.module.check_mode:
            msg = "SDN zone '{}' would be updated (check mode).".format(zone_name)
            return True, existing_zone, msg

        try:
            self.proxmox_api.cluster.sdn.zones(zone_name).put(**updates)
        except Exception as exc:
            self.module.fail_json(msg="Failed to update SDN zone '{}': {}".format(zone_name, to_native(exc)))

        new_zone = self.get_zone(zone_name)
        msg = "SDN zone '{}' updated.".format(zone_name)
        return True, new_zone, msg

    def ensure_absent(self):
        zone_name = self.module.params["zone"]
        lock_token = self.module.params.get("lock_token")

        existing_zone = self.get_zone(zone_name)
        if not existing_zone:
            msg = "SDN zone '{}' already absent.".format(zone_name)
            return False, None, msg

        if self.module.check_mode:
            msg = "SDN zone '{}' would be removed (check mode).".format(zone_name)
            return True, existing_zone, msg

        delete_kwargs = {}
        if lock_token:
            delete_kwargs["lock-token"] = lock_token

        try:
            if delete_kwargs:
                self.proxmox_api.cluster.sdn.zones(zone_name).delete(**delete_kwargs)
            else:
                self.proxmox_api.cluster.sdn.zones(zone_name).delete()
        except Exception as exc:
            self.module.fail_json(msg="Failed to remove SDN zone '{}': {}".format(zone_name, to_native(exc)))

        msg = "SDN zone '{}' removed.".format(zone_name)
        return True, None, msg


def main():
    module_args = proxmox_auth_argument_spec()

    zone_args = dict(
        zone=dict(type="str", required=True),
        type=dict(type="str", choices=["evpn", "faucet", "qinq", "simple", "vlan", "vxlan"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        advertise_subnets=dict(type="bool"),
        bridge=dict(type="str"),
        bridge_disable_mac_learning=dict(type="bool"),
        controller=dict(type="str"),
        dhcp=dict(type="str", choices=["dnsmasq"]),
        disable_arp_nd_suppression=dict(type="bool"),
        dns=dict(type="str"),
        dnszone=dict(type="str"),
        dp_id=dict(type="int"),
        exitnodes=dict(type="str"),
        exitnodes_local_routing=dict(type="bool"),
        exitnodes_primary=dict(type="str"),
        fabric=dict(type="str"),
        ipam=dict(type="str"),
        lock_token=dict(type="str"),
        mac=dict(type="str"),
        mtu=dict(type="int"),
        nodes=dict(type="str"),
        peers=dict(type="str"),
        reversedns=dict(type="str"),
        rt_import=dict(type="str"),
        tag=dict(type="int"),
        vlan_protocol=dict(type="str", choices=["802.1q", "802.1ad"]),
        vrf_vxlan=dict(type="int"),
        vxlan_port=dict(type="int"),
    )

    module_args.update(zone_args)

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[("api_password", "api_token_id")],
        required_together=[("api_token_id", "api_token_secret")],
        required_if=[("state", "present", ["type"])],
        supports_check_mode=True,
    )

    proxmox = ProxmoxSDNZoneModule(module)

    state = module.params["state"]
    if state == "present":
        changed, zone_data, message = proxmox.ensure_present()
    else:
        changed, zone_data, message = proxmox.ensure_absent()

    applied = False
    if changed:
        applied = apply_sdn_configuration(proxmox.proxmox_api, module, module.check_mode)

    result = dict(
        changed=changed,
        msg=message,
    )

    if zone_data is not None:
        result["sdn_zone"] = zone_data

    if applied:
        result["sdn_configuration_applied"] = True

    module.exit_json(**result)


if __name__ == "__main__":
    main()
