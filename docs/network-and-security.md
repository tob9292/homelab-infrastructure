# Network segmentation and administrative security

## Routing policy

OPNsense routes between five internal VLANs. Internal addressing and policy are IPv4-only. The WAN uses DHCP, with IPv6 disabled. The unnumbered internal parent interface has its legacy default allow rules disabled.

The general interface-rule structure is:

1. Permit required internal services.
2. Block other restricted private-network destinations.
3. Permit remaining outbound internet traffic.

Key inter-network access rules:

| Source | Selected permitted internal access |
| --- | --- |
| Management | Firewall administration, infrastructure DNS/NTP, and NPMplus administration |
| Trusted clients | AdGuard DNS and internal HTTPS through NPMplus |
| Designated Trusted administrator workstation | Server-VLAN SSH, NPMplus administration, and broader access to selected management systems |
| IoT | AdGuard DNS, firewall NTP, and a specific media-service exception |
| Guest/Work | AdGuard DNS and firewall NTP |
| Servers | Required infrastructure services, with selected cross-VLAN automation and monitoring exceptions |
| WireGuard clients | AdGuard DNS and internal proxy HTTPS; other private destinations are restricted |

Hermes has selected access to the administration workstation for documentation integration and to the Proxmox API. Uptime Kuma has selected access to infrastructure management endpoints for monitoring.

## Management-plane controls

| Platform | Routine identity and authentication | Additional control |
| --- | --- | --- |
| OPNsense | Named administrator; password-first TOTP | Built-in root account disabled; WebGUI bound to Management and Trusted |
| Proxmox VE | Named PAM account with TOTP for the WebGUI; SSH public keys for shell access | Management VLAN and separate direct-connect recovery path |
| NPMplus | Named administrator with two-factor authentication | Built-in Administrator account disabled; routed access to the administration port restricted |

NPMplus account settings manage application administrators. Proxmox shell administration uses a named account with SSH public-key authentication and passwordless sudo. Keep administrative SSH keys securely stored.

## Reverse-proxy access list

The `Internal Networks` list applies to seven internal proxy hosts. It permits Management, Trusted, Servers, and WireGuard client networks, followed by denial of other source addresses. IoT and Guest/Work are not included.

`Satisfy Any` and `Pass Auth to Upstream` are disabled. The list controls access to the proxy hosts by source address. OPNsense separately restricts routed access to the NPMplus administration panel.

NPMplus HTTP and HTTPS services are available internally, with no WAN port forwards for either service.

## Traffic paths and access controls

Inter-VLAN traffic passes through OPNsense. Devices in the same subnet communicate through the switch or virtual bridge. Access controls for these local connections belong at the application or workload level.

Keep account recovery material and backup archives private, and use the documented console or direct-connect procedures for recovery access.

For controlled changes, use the [firewall change procedure](runbooks/firewall-change.md).
