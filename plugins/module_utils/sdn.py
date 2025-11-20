# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Contributors
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Utility helpers for interacting with Proxmox SDN configuration."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.text.converters import to_native


def apply_sdn_configuration(proxmox_api, module, check_mode=False):
    """Apply pending SDN configuration changes on the cluster.

    The Proxmox API keeps SDN changes pending until an explicit apply call is
    made. Several modules can share this helper to ensure that their changes are
    activated once the API operations succeed.

    :param proxmox_api: Authenticated proxmoxer API client.
    :param module: The active :class:`ansible.module_utils.basic.AnsibleModule`.
    :param check_mode: Whether the module is currently operating in check mode.
    :return: ``True`` if an apply operation was attempted, ``False`` otherwise.
    """

    if check_mode:
        return False

    try:
        proxmox_api.cluster.sdn.put(apply=1)
    except Exception as exc:  # pragma: no cover - handled in tests via mocks
        module.fail_json(msg="Failed to apply SDN configuration: {}".format(to_native(exc)))

    return True
