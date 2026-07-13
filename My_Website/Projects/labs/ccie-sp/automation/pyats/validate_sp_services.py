#!/usr/bin/env python3
"""pyATS validation skeleton for BGP, ISIS, and VPN services."""

from __future__ import annotations

from pyats import aetest


class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect(self, testbed):
        testbed.connect(log_stdout=False)


class ValidateControlPlane(aetest.Testcase):
    @aetest.test
    def bgp_vpnv4_summary(self, testbed):
        for device in testbed.devices.values():
            output = device.execute("show bgp vpnv4 unicast summary")
            assert "Idle" not in output, f"{device.name}: vpnv4 neighbor idle"

    @aetest.test
    def isis_neighbors(self, testbed):
        for device in testbed.devices.values():
            output = device.execute("show isis neighbors")
            assert "Total adjacency count: 0" not in output, f"{device.name}: no ISIS adjacencies"

    @aetest.test
    def vpnv6_summary(self, testbed):
        for device in testbed.devices.values():
            output = device.execute("show bgp vpnv6 unicast summary")
            assert "Idle" not in output, f"{device.name}: vpnv6 neighbor idle"


class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect(self, testbed):
        for device in testbed.devices.values():
            device.disconnect()


if __name__ == "__main__":
    aetest.main()
