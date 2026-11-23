# DNS troubleshooting procedure

## Purpose

Locate a fault along the client → AdGuard → Unbound → upstream path, or distinguish DNS problems from reverse-proxy problems.

The commands use illustrative addresses and domains. Substitute the actual values when working privately on the lab.

## Checks

1. Confirm the client's assigned VLAN, address, gateway, and DNS server, including any DHCP options or manual DNS settings.
2. Query AdGuard directly for an external name and an internal service name.
3. If AdGuard fails on external names, query Unbound directly from an authorized administration network.
4. Inspect the relevant service logs, firewall policy, and system time if upstream resolution or validation fails.
5. If internal names resolve, validate HTTPS separately by service hostname.

Example checks with a system that has `dig` installed:

```sh
dig @10.77.50.10 example.com
dig @10.77.50.10 status.home.example.com
dig @10.77.10.1 example.com
curl --head https://status.home.example.com
```

Use the private service hostname for the HTTPS check and keep certificate verification enabled.

## Interpretation

| Observation | Investigate |
| --- | --- |
| Direct AdGuard query succeeds; normal client resolution fails | DHCP/client DNS settings or client-side overrides |
| AdGuard fails; Unbound succeeds | AdGuard upstream settings, reachability, filtering, or service health |
| AdGuard and Unbound both fail | Unbound, upstream connectivity, firewall policy, time, or DNSSEC/TLS errors |
| External names work; local service name fails | Local wildcard rewrite and the queried namespace |
| Local name resolves; HTTPS fails | Proxy availability, certificate trust/name, access list, or backend application |

Run the relevant checks from the affected network to test its DNS settings and firewall policy.

See [DNS and HTTPS architecture](../dns-and-https.md).
