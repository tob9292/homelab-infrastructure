# Service and infrastructure monitoring

## Uptime Kuma

Uptime Kuma runs in a Servers-VLAN LXC and groups monitors into Applications and Core Network. The dashboard brings application reachability and infrastructure checks into one view.

![Uptime Kuma dashboard with application, DNS, proxy, and management-endpoint monitors](../assets/screenshots/uptime-kuma.png)

## Monitored services

| Group | Monitor | Purpose |
| --- | --- | --- |
| Applications | SearXNG | Check access to the search application |
| Core Network | AdGuard — External DNS Resolution | Check resolution of an external name |
| Core Network | AdGuard — Internal DNS Rewrite | Check resolution of an internal service name |
| Core Network | AdGuard DNS | Check the DNS service |
| Core Network | Internet Ping | Check external connectivity |
| Core Network | NPMplus — Reverse Proxy | Check access through the reverse proxy |
| Core Network | NPMplus — Reverse Proxy — TCP | Check connectivity to the proxy's monitored TCP port |
| Core Network | OPNsense | Check firewall management-endpoint reachability |
| Core Network | Proxmox VE | Check host management-endpoint reachability |
| Core Network | UniFi Controller | Check controller reachability |

The separate DNS monitors distinguish upstream name resolution from local service-name rewrites. The reverse-proxy monitors separate the application-facing path from TCP connectivity. Management-endpoint checks cover the systems used to administer the lab.

## Following a failure

Start with the failed monitor's history, then follow the service's dependencies:

1. For DNS failures, compare the internal rewrite and external resolution checks. Follow the [DNS troubleshooting procedure](runbooks/dns-troubleshooting.md) through AdGuard, Unbound, and the upstream resolver.
2. For a proxied application failure, compare the reverse-proxy and TCP checks, then inspect the proxy-host configuration and backend service.
3. For management-endpoint failures, check the workload state in Proxmox, the network path, and the relevant firewall access rule.
4. After making a change, check the affected monitor and confirm access from the intended client network.

The dashboard displays recent check results and uptime percentages for each monitor. Monitor history helps locate when a failure began and whether related services were affected.

See [architecture](architecture.md), [network policy](network-and-security.md), and [DNS and HTTPS](dns-and-https.md).
