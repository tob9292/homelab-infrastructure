# Firewall change procedure

## Purpose

Update an OPNsense rule, retain administrative access, and validate the intended network policy.

## Before the change

1. Write down the intended source, destination, protocol, port, and expected denied traffic.
2. Record the current rule order and the interface where client traffic enters the firewall.
3. Save a private configuration export. Create a boot environment when the change warrants a system-level rollback point.
4. Confirm access to the Proxmox VM console. Keep a working administrative session open.
5. Identify both an allowed client and a client that should remain blocked.

## Apply

1. Change the smallest relevant rule or alias.
2. Place the service exception before the broader private-network block where appropriate.
3. Give the rule a description matching its current network and purpose.
4. Apply the change and inspect firewall logs for the expected source and destination.

## Validate

| Check | Expected result |
| --- | --- |
| Allowed client to intended service | Connection succeeds |
| Disallowed network to the same service | Connection is blocked |
| Allowed client to unrelated private service | Existing restriction remains |
| DNS and ordinary internet use | Continue according to that network's policy |
| Administrative access | Remains available through the approved path |

Start a fresh connection after changing a rule. Where necessary, clear the identified state for that connection while keeping unrelated sessions active.

For internal HTTPS, test by hostname with certificate verification enabled and a trusted certificate chain.

## Roll back

If the intended policy is not achieved, revert the individual rule while the retained session is available. Use console recovery if the network management path is lost. Restore a full configuration or boot environment only when warranted, taking account of other changes made since that restore point.

## Update documentation

Update the private owning platform note and validation record first. Then rewrite only the relevant architectural change for the public [network-security page](../network-and-security.md), without copying live addresses, exports, or credentials.
