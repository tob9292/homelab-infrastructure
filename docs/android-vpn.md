# Android VPN automation

## Applications

- [WG Tunnel on Google Play](https://play.google.com/store/apps/details?id=com.zaneschepke.wireguardautotunnel&hl=en-US): WireGuard client and automatic tunnel management.
- [WiFiman on Google Play](https://play.google.com/store/apps/details?id=com.ubnt.usurvey&hl=en): identifies the home Wi-Fi access-point BSSIDs used in the trusted-network list.

The home tunnel is imported by scanning the QR code generated for the OPNsense WireGuard peer. Keep the QR code private because it contains the client's tunnel configuration.

## Personal configuration

Wi-Fi and mobile data use the same configuration: both are enabled with preferred tunnel `Default`. The default tunnel is the home WireGuard profile.

| Auto-tunnel setting | Configuration |
| --- | --- |
| Default tunnel | Home WireGuard profile |
| Tunnel on Wi-Fi | Enabled; preferred tunnel `Default` |
| Tunnel on mobile data | Enabled; preferred tunnel `Default` |
| Trusted Wi-Fi | Home network identified by its trusted BSSID entries |
| Tunnel on Ethernet | Disabled |
| Stop on no internet | Disabled |
| Start on boot | Enabled |
| Auto-tunnel service | Enabled |

On mobile data or Wi-Fi that does not match a trusted home BSSID, the phone automatically uses the home WireGuard tunnel. When it connects to the trusted home Wi-Fi, auto-tunnel disables the tunnel and the phone uses the local network directly.

## WireGuard client profile

This is the phone profile's configuration layout. Addresses use the repository's illustrative `10.77.0.0/16` range, the endpoint is an example domain, and both keys are placeholders. It is a documentation example, not an importable profile.

```ini
[Interface]
PrivateKey = <PHONE_PRIVATE_KEY>
Address = 10.77.60.2/32
DNS = 10.77.50.10

[Peer]
PublicKey = <OPNSENSE_PUBLIC_KEY>
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0, ::/0
```

The interface address identifies the phone inside the WireGuard network, and DNS points to AdGuard Home. The peer public key identifies OPNsense; the endpoint is its WAN listener. `AllowedIPs` specifies full-tunnel destination routes, not permission to access every internal service.

The firewall grants remote clients the internal access described in [network security](network-and-security.md).

## Default-tunnel setup and checks

1. Open the imported home WireGuard profile's **View configuration** screen.
2. Under **General**, enable **Default tunnel** for that profile.
3. In **Auto-tunnel**, enable both **Tunnel on Wi-Fi** and **Tunnel on mobile data**, with preferred tunnel `Default` for both.
4. Keep the trusted home BSSIDs configured and the auto-tunnel service running.

Check the transitions from mobile data to untrusted Wi-Fi, then back to trusted home Wi-Fi. The home tunnel should activate on the first two and stop on the trusted connection. While connected through the tunnel, check a recent handshake, DNS resolution, and approved internal HTTPS access.

If mobile data or untrusted Wi-Fi does not start the tunnel, check the home profile's **Default tunnel** switch, the corresponding automation setting, and the auto-tunnel service state.

## BSSID maintenance

WiFiman is used to identify the BSSID for the Trusted Wi-Fi connection. Different access points and radio bands may have different BSSIDs, so the list needs reviewing after access-point replacement or changes to the home wireless setup.

BSSID matching associates the auto-tunnel rules with specific access-point radios.

For application behavior and permissions, see the [WG Tunnel auto-tunneling documentation](https://www.wgtunnel.com/docs/auto-tunneling/).
