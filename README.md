# Home Infrastructure Lab

**Proxmox VE · OPNsense · UniFi · Linux · Self-hosted services**

A personally maintained infrastructure lab combining virtualized compute, segmented networking, internal HTTPS, remote access, and documented recovery procedures.

Maintained by [tob9292](https://github.com/tob9292).

## Project at a glance

| Area | Implementation |
| --- | --- |
| Compute | One Proxmox VE host with OPNsense and Docker01 VMs plus LXC containers |
| Networking | Five VLANs separating Management, Trusted, IoT, Guest/Work, and Servers |
| Routing and remote access | OPNsense stateful firewall, DHCP, and WireGuard |
| Switching and wireless | UniFi-managed switching and VLAN-mapped Wi-Fi networks |
| Internal services | DNS filtering, reverse proxy, monitoring, firewall log collection, search, calendars, document management, password vault, dashboard, and local IoT control |
| Administration | Named accounts, TOTP MFA on key management interfaces, and SSH public-key authentication |
| Recovery | Scheduled workload and host-configuration backups, offline/off-site copies, and emergency access procedures |
| Documentation | A private Obsidian knowledge base, with selected material rewritten for this public portfolio |

## Physical hardware

| Component | Hardware |
| --- | --- |
| Proxmox host | TekLager TLSense 10810U; Intel Core i7-10810U; 32 GB DDR4 SO-DIMM RAM |
| Workload storage | Samsung PM9A1 1 TB NVMe SSD |
| Local backup storage | Samsung 870 EVO 500 GB SATA SSD |
| Switch | UniFi Flex 2.5G (`USW-Flex-2.5G-8`), with eight 2.5 GbE ports and a 10 GbE combination uplink |
| Access point | UniFi U7 Pro Wall, powered by a separate PoE injector |

See the [hardware details and host installation photo](docs/architecture.md#physical-hardware) and [UniFi hardware and AP installation photo](docs/network-and-security.md#network-hardware).

## Architecture

```mermaid
flowchart LR
    Internet((Internet)) --> WAN[Dedicated WAN bridge]
    subgraph Host[Single Proxmox VE 9.2 host]
        WAN --> FW[OPNsense VM<br/>Routing / Firewall / DHCP / Unbound / WireGuard]
        FW --> Trunk[VLAN-aware internal bridge]
        Trunk --> LXCs[Infrastructure LXCs<br/>UniFi · AdGuard · NPMplus · VictoriaLogs · Uptime Kuma]
        Trunk --> Docker[Docker01 VM<br/>Paperless · Vaultwarden · Homarr · Beszel<br/>Dockhand · SearXNG · Radicale · Roborock]
        Backup[(SATA Backup SSD<br/>Nightly VM/LXC + Host Config)]
        Emergency[Direct-connect emergency bridge] --> Management[Host management]
    end
    Trunk --> Switch[UniFi Flex 2.5G Switch]
    Switch --> AP[UniFi U7 Pro Wall AP]
    AP --> Clients[Trusted · IoT · Guest/Work Wi-Fi]
    Phone[Android / WG Tunnel] -. WireGuard .-> FW
```

OPNsense, Docker01, and the five infrastructure LXCs run on the Proxmox VE host, connected through dedicated WAN and VLAN-aware internal bridges, with nightly backups written to a separate SATA SSD.

## Key design decisions

| Decision | Rationale |
| --- | --- |
| Dedicated out-of-band emergency bridge | Direct-connect Proxmox management with no gateway preserves host recovery even when the OPNsense VM is down or misconfigured |
| Internal-only wildcard HTTPS (DNS-01) | Certbot + Porkbun DNS-01 issues trusted TLS certificates for internal services without opening WAN TCP 80 or 443 |
| Default-deny IoT with local Roborock MQTT | IoT VLAN blocks IPv6, RFC1918, and outbound internet by default; the vacuum runs cloud-free via NPMplus HTTPS/MQTT TLS |
| Layered observability | Separates reachability checks (Uptime Kuma), host/SMART metrics (Beszel), and structured firewall log search (VictoriaLogs + Vector) |
| Allowlist-enforced public portfolio | Private Obsidian vault and exports stay local; a tested Python checker (`check_public_content.py`) + Gitleaks gate every public commit |

## Lab in operation

![Proxmox VE host overview and configured VM/LXC workloads](assets/screenshots/proxmox-overview.png)

Proxmox brings the firewall VM, application containers, storage, and host resources into one management view. The [architecture page](docs/architecture.md) explains each workload's role.

<details>
<summary>View resource and SMART monitoring (Beszel)</summary>

![Beszel dashboard monitoring the Proxmox host, Docker01, and all five infrastructure LXCs](assets/screenshots/beszel-overview.png)

Beszel tracks CPU, memory, disk, systemd services, and physical NVMe/SATA SMART health across the host and all Linux guests.

</details>

<details>
<summary>View reachability monitoring (Uptime Kuma)</summary>

![Uptime Kuma monitors grouped into Applications and Core Network](assets/screenshots/uptime-kuma.png)

The [monitoring page](docs/monitoring.md) covers DNS resolution, reverse-proxy connectivity, management endpoints, Beszel resource metrics, and VictoriaLogs firewall logging.

</details>

## Explore the project

- [Architecture and workload inventory](docs/architecture.md)
- [Network segmentation and administrative security](docs/network-and-security.md)
- [DNS and internal HTTPS](docs/dns-and-https.md)
- [Service and infrastructure monitoring](docs/monitoring.md)
- [Backup and recovery design](docs/backup-and-recovery.md)
- [Android VPN automation](docs/android-vpn.md)
- [Cloud-free Roborock](docs/cloud-free-roborock.md)
- [Automation and documentation workflow](docs/automation-and-documentation.md)
- [Firewall change procedure](docs/runbooks/firewall-change.md)
- [DNS troubleshooting procedure](docs/runbooks/dns-troubleshooting.md)

## Project goals

This project demonstrates practical work with VLANs and inter-network policy, Linux virtualization, service dependencies, authentication, backup scheduling, and maintainable operational documentation.

The documentation covers the network layout, service configuration, administration workflows, and recovery procedures.

## Public documentation conventions

Addresses in `10.77.0.0/16`, domains under `example.com`, and generic account names are illustrative replacements. They preserve the relationships between components while keeping live endpoint details private.

Configuration exports, credentials, MFA recovery material, private keys, original screenshots, and vault history remain private.

Screenshots show the actual services, with live addresses, registered domains, device identifiers, and private browsing information removed.

Hardware photos show the installed equipment. Public copies have location and other image metadata removed; the original photographs remain private.
