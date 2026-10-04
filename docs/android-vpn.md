# Android VPN automation

## Applications

- [WG Tunnel on Google Play](https://play.google.com/store/apps/details?id=com.zaneschepke.wireguardautotunnel&hl=en-US): WireGuard client and automatic tunnel management.
- [WiFiman on Google Play](https://play.google.com/store/apps/details?id=com.ubnt.usurvey&hl=en): identifies the home Wi-Fi access-point BSSIDs used in the trusted-network list.

The home tunnel is imported by scanning the QR code generated for the OPNsense WireGuard peer. Keep the QR code private because it contains the client's tunnel configuration.

## Personal configuration

| Auto-tunnel setting | Configuration |
| --- | --- |
| App-wide default tunnel | Home WireGuard profile; `Default tunnel` enabled in that profile's configuration |
| Tunnel on Wi-Fi | Enabled; uses the home WireGuard profile via `Default`; tunnel disabled on trusted home Wi-Fi |
| Tunnel on mobile data | Enabled; preferred tunnel is the home WireGuard profile |
| Tunnel on Ethernet | Disabled |
| Stop on no internet | Disabled |
| Start on boot | Enabled |
| Trusted Wi-Fi identification | Home Trusted-network BSSID entries |

On mobile data and Wi-Fi networks not listed as trusted, auto-tunnel activates the home WireGuard profile. On a matching trusted home Wi-Fi BSSID, it disables the tunnel so the phone uses the home network directly.

`Default` is a selection that refers to the app-wide default tunnel, not a separate tunnel profile. The home profile's **Default tunnel** switch must be enabled; selecting `Default` in the Wi-Fi automation settings alone does not assign a default profile.

The OPNsense peer configuration uses AdGuard Home for DNS. The firewall grants remote clients the internal access described in [network security](network-and-security.md).

## Default-tunnel setup and checks

1. Open the imported home WireGuard profile's **View configuration** screen.
2. Under **General**, enable **Default tunnel** for that profile.
3. In **Auto-tunnel**, keep Wi-Fi enabled with preferred tunnel `Default`, and keep the home profile selected for mobile data.
4. Keep the trusted home BSSIDs configured and the auto-tunnel service running.

Check the transitions from mobile data to untrusted Wi-Fi, then back to trusted home Wi-Fi. The home tunnel should activate on the first two and stop on the trusted connection. While connected through the tunnel, check a recent handshake, DNS resolution, and approved internal HTTPS access.

If untrusted Wi-Fi does not start the tunnel, check the home profile's **Default tunnel** switch as well as the Wi-Fi automation setting and service state.

## BSSID maintenance

WiFiman is used to identify the BSSID for the Trusted Wi-Fi connection. Different access points and radio bands may have different BSSIDs, so the list needs reviewing after access-point replacement or changes to the home wireless setup.

BSSID matching associates the auto-tunnel rules with specific access-point radios.

For application behavior and permissions, see the [WG Tunnel auto-tunneling documentation](https://www.wgtunnel.com/docs/auto-tunneling/).
