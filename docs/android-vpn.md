# Android VPN automation

## Applications

- [WG Tunnel on Google Play](https://play.google.com/store/apps/details?id=com.zaneschepke.wireguardautotunnel&hl=en-US): WireGuard client and automatic tunnel management.
- [WiFiman on Google Play](https://play.google.com/store/apps/details?id=com.ubnt.usurvey&hl=en): identifies the home Wi-Fi access-point BSSIDs used in the trusted-network list.

The home tunnel is imported by scanning the QR code generated for the OPNsense WireGuard peer. Keep the QR code private because it contains the client's tunnel configuration.

## Personal configuration

| Auto-tunnel setting | Configuration |
| --- | --- |
| Tunnel on Wi-Fi | Enabled; preferred tunnel is `Default` |
| Tunnel on mobile data | Enabled; preferred tunnel is the home WireGuard profile |
| Tunnel on Ethernet | Disabled |
| Stop on no internet | Disabled |
| Start on boot | Enabled |
| Trusted Wi-Fi identification | Home Trusted-network BSSID entries |

On mobile data, auto-tunnel selects the home WireGuard profile. On a matching trusted home Wi-Fi connection, it disables the tunnel. Other Wi-Fi connections use the app's `Default` selection.

The OPNsense peer configuration uses AdGuard Home for DNS. The firewall grants remote clients the internal access described in [network security](network-and-security.md).

## BSSID maintenance

WiFiman is used to identify the BSSID for the Trusted Wi-Fi connection. Different access points and radio bands may have different BSSIDs, so the list needs reviewing after access-point replacement or changes to the home wireless setup.

BSSID matching associates the auto-tunnel rules with specific access-point radios.

For application behavior and permissions, see the [WG Tunnel auto-tunneling documentation](https://www.wgtunnel.com/docs/auto-tunneling/).
