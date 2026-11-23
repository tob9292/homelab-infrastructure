# Cloud-free Roborock

I paired a Roborock Saros 20 Neo Complete with Roborock Local Server running in Docker on a Proxmox VM. The robot stays on IoT VLAN 30 with internet access blocked. LocalRock on Android controls it from Trusted VLAN 20. Pairing and day-to-day control use the local server.

## Docker Compose installation

I deployed the server with Docker Compose on a Debian VM in Servers VLAN 50. The Compose file builds `roborock-local-server:local` from the upstream checkout with `build: .`. It mounts `config.toml` and the secrets directory read-only, and mounts the data directory read/write so pairing state survives container recreation.

I configured the embedded MQTT broker and set the server to `external_tls` mode so NPMplus handles certificates. Compose publishes TCP `555` and `8881` on the VM's Servers VLAN address, with backend access restricted to NPMplus. The container health check requests `/admin` over HTTP on port `555`. [Upstream Docker Compose installation](https://python-roborock.github.io/local_roborock_server/installation/#method-1-docker-compose).

## Local service path

AdGuard Home resolves `api-rr.home.example.com` to NPMplus on Servers VLAN 50. NPMplus terminates TLS and forwards HTTPS on TCP `443` to the server's HTTP port `555`. A separate TCP stream forwards MQTT over TLS on `8883` to plain MQTT on `8881`. The server advertises the proxy ports and trusts NPMplus for forwarded client addresses. [Reverse proxy documentation](https://python-roborock.github.io/local_roborock_server/reverse_proxy/).

Certbot uses Porkbun DNS for DNS-01 domain validation. Let's Encrypt issues the wildcard certificate, and NPMplus uses that same certificate for HTTPS on TCP `443` and MQTT over TLS on TCP `8883`.

## VLAN and firewall policy

This page uses illustrative addresses and a placeholder MAC. OPNsense reserves `10.77.30.50` for `<ROBOT_MAC>`. The reservation, the `ROBOROCK` host alias, and the robot's entry in the HTTPS access list use the same address.

| Source | Destination | Rule |
| --- | --- | --- |
| IoT VLAN 30 | AdGuard Home (`10.77.50.10`) | Allow TCP/UDP `53` |
| IoT VLAN 30 | OPNsense | Allow UDP `123` for NTP |
| IoT VLAN 30 | Other DNS destinations | Block TCP/UDP `53` |
| IoT VLAN 30, robot only | NPMplus (`10.77.50.12`) | Allow TCP `443` and `8883` |
| IoT VLAN 30, robot only | All remaining destinations | Block, including internet access |
| Trusted VLAN 20 | NPMplus (`10.77.50.12`) | Allow TCP `443` and `8883` |

These rules use IPv4. OPNsense blocks IPv6 on the IoT VLAN. The robot's proxy allowance precedes its block rule, and the Trusted MQTT allowance precedes the general block on other private destinations.

## What worked

The PC onboarding wizard's **New vacuum** option paired the robot without a cloud import. I joined the robot's temporary Wi-Fi from the PC, sent the onboarding packet, and returned to the Trusted network. Once the DHCP lease and firewall alias matched, the server recovered the public key. One final pairing cycle brought the robot online. [Cloud-free onboarding documentation](https://python-roborock.github.io/local_roborock_server/onboarding/#onboarding-a-vacuum-that-was-never-on-the-cloud).

LocalRock could list the robot over HTTPS but showed **MQTT not connected (reconnecting)** even after Trusted clients could reach port `8883`. From the LocalRock device list, I opened the three-dot menu, selected **Sign out**, and signed back in to the same local server. The fresh session restored MQTT.
