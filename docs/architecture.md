# Architecture and workload inventory

## Physical and virtual layout

The lab runs on a single compact Proxmox VE system with approximately 32 GiB of RAM, NVMe-backed workload storage, and a separate SATA backup disk. OPNsense is a VM; application services run in LXC containers.

The host network separates three paths:

| Path | Purpose |
| --- | --- |
| Dedicated WAN bridge | Connects the external uplink to the OPNsense VM |
| VLAN-aware internal bridge | Carries the internal networks between OPNsense, workloads, and the UniFi switch |
| Dedicated emergency bridge | Provides direct-connect host management when routed access is unavailable |

Normal Proxmox administration uses the Management VLAN. The emergency interface has no default gateway and provides direct-connect access for recovery.

## Logical networks

All addresses below are illustrative.

| VLAN | Role | Example subnet |
| --- | --- | --- |
| 10 | Management | `10.77.10.0/24` |
| 20 | Trusted | `10.77.20.0/24` |
| 30 | IoT | `10.77.30.0/24` |
| 40 | Guest/Work | `10.77.40.0/24` |
| 50 | Servers | `10.77.50.0/24` |
| — | WireGuard tunnel | `10.77.60.0/24` |

UniFi networks use OPNsense as their third-party gateway. Wi-Fi networks map Trusted, Home-IoT, and Guest/Work clients to their corresponding VLANs. IoT Wi-Fi uses 2.4 GHz; the other two networks support additional bands.

## Workload inventory

The lab contains ten configured workloads:

| Type | Workload | Placement | Role |
| --- | --- | --- | --- |
| VM | OPNsense | WAN and internal trunk | Routing, firewall, DHCP, upstream DNS, remote access |
| LXC | UniFi Network | Management | Switching and wireless configuration |
| LXC | AdGuard Home | Servers | Client DNS filtering and local service-name rewrites |
| LXC | SearXNG | Servers | Self-hosted search |
| LXC | NPMplus | Servers | Internal HTTPS reverse proxy |
| LXC | Gluetun | Servers | Separate VPN/proxy service |
| LXC | Uptime Kuma | Servers | Service and infrastructure monitoring |
| LXC | Radicale | Servers | CalDAV and CardDAV |
| LXC | Hermes Agent | Servers | Infrastructure and documentation automation |
| LXC | Matrix/Synapse | Servers | Messaging, with an administration interface |

Workloads are configured to start with the host. New workloads must also be added to the backup job's explicit inclusion list.

## Service integration

- OPNsense connects the internal networks and provides remote access through WireGuard.
- AdGuard Home resolves client DNS queries, while NPMplus provides HTTPS access to internal applications.
- Uptime Kuma monitors services and infrastructure management endpoints.
- The direct-connect management path provides access to Proxmox during recovery.
- Scheduled archives and offline/off-site copies provide workload and host rebuild information.

See [network security](network-and-security.md), [DNS and HTTPS](dns-and-https.md), and [backup design](backup-and-recovery.md).
