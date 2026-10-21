# Network configuration

One physical port, two networks. This page builds that arrangement on the
host and proves it works before a single virtual machine exists.

## The two networks

| Network | Bridge | Range | Carries |
|---|---|---|---|
| Public | `vmbr0` | `203.0.113.10/26` | The host's own management traffic, and the DNAT target for published services |
| Private | `vmbr2` | `10.0.0.0/24` | All nine virtual machines |

The host holds `10.0.0.5` on `vmbr2`, and that address is the default
gateway for every guest. Guests reach the internet by being masqueraded onto
`vmbr0`; the outside world reaches the guests by being DNATed to the Nginx
proxy.

!!! info "Why there is no third network"
    A usual virtualisation host separates management, storage and guest
    traffic onto three interfaces. The EX44 has exactly one 1 Gbit/s port,
    so the separation has to be logical rather than physical. `vmbr0` is the
    only bridge with a real uplink, and everything that is not host
    management lives behind NAT.

## The configuration file

Proxmox 9 still uses `ifupdown2` and `/etc/network/interfaces`. The web
interface stages changes into `/etc/network/interfaces.new`; everything on
this page is edited by hand and applied with `ifreload -a`.

```bash
root@pve-01:~# nano /etc/network/interfaces
```

```text
auto lo
iface lo inet loopback

iface enp34s0 inet manual

auto vmbr0
iface vmbr0 inet static
        address 203.0.113.10/26
        gateway 203.0.113.1
        bridge-ports enp34s0
        bridge-stp off
        bridge-fd 0

auto vmbr2
iface vmbr2 inet static
        address 10.0.0.5/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0

        post-up   echo 1 > /proc/sys/net/ipv4/ip_forward
        post-up   iptables -t nat -A POSTROUTING -s '10.0.0.0/24' -o vmbr0 -j MASQUERADE
        post-down iptables -t nat -D POSTROUTING -s '10.0.0.0/24' -o vmbr0 -j MASQUERADE
        post-up   iptables -t raw -I PREROUTING -i fwbr+ -j CT --zone 1
        post-down iptables -t raw -D PREROUTING -i fwbr+ -j CT --zone 1
```

!!! danger "Replace `enp34s0` with the real uplink name"
    `enp34s0` is the name the reference build observed. Yours may be
    `eno1`, `enp0s31f6` or `ens3`. Get it from:

    ```console
    root@pve-01:~# ip -br link
    lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
    enp34s0          UP             00:00:00:00:00:00 <BROADCAST,MULTICAST,UP,LOWER_UP>
    ```

    A wrong name does not fail loudly. The bridge comes up with no port in
    it, the host has an address but no carrier, and the symptom is a host
    that looks configured and answers nothing.

!!! note "What each line does"
    `iface enp34s0 inet manual` hands the physical adapter to
    `ifupdown2` without giving it an address, because the bridge owns it
    now.

    `bridge-ports none` on `vmbr2` creates a bridge with no physical
    member. It is a pure virtual segment — the only way in or out is
    through the host.

    The `fwbr+` conntrack-zone rule is the one Proxmox's own documentation
    asks for when the firewall and NAT are both in use. Without it, a
    connection that is translated by the NAT and then inspected by the
    per-VM firewall can be classified as an invalid packet and dropped.

### Apply it

```console
root@pve-01:~# ifreload -a
```

!!! danger "Keep a second session open"
    Applying a network configuration to a remote host over the connection
    that the configuration governs is how people lock themselves out.
    Leave the current SSH session open, open a **second** one, and only
    close the first once the second works.

    If it does break, the Robot reset console and the
    [Hetzner Rescue System](01-rescue-mode.md) are both still available.

## Forwarding

!!! warning "Proxmox does not enable this for you"
    `/usr/lib/sysctl.d/10-pve.conf` — the file Proxmox ships — sets the
    bridge netfilter options, the IGMP behaviour and `fs.aio-max-nr`. It
    does **not** set `net.ipv4.ip_forward`. The kernel default is `0`, and
    with forwarding off the host acts as a bridge only: guests get an
    address, but nothing ever leaves.

    The `post-up` line in the configuration above turns it on at every
    interface start. To be certain it survives a reboot regardless of how
    the network is brought up, set it in sysctl as well:

    ```console
    root@pve-01:~# nano /etc/sysctl.d/99-forwarding.conf
    net.ipv4.ip_forward = 1
    ```

    ```console
    root@pve-01:~# sysctl --system | grep ip_forward
    net.ipv4.ip_forward = 1
    ```

## Publishing the services

Public traffic arrives at `203.0.113.10` on ports 80 and 443 and has to end
up at the Nginx proxy on `10.0.0.103`. That is a destination NAT rule.

```console
root@pve-01:~# iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 80 -j DNAT --to-destination 10.0.0.103:80
root@pve-01:~# iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 443 -j DNAT --to-destination 10.0.0.103:443
```

!!! note "These rules are not persistent on their own"
    `iptables` rules live in memory. The durable options are the Proxmox
    firewall's own NAT rules — see
    [Host firewall](../04-security/01-host-firewall.md) — or a systemd unit
    that installs them at boot. Whichever is chosen, the rules belong in
    the firewall configuration and not on a command line.

The two entries in the `[publish]` table of the
[lab inventory](../00-prerequisites/03-lab-inventory.md) are the complete
list of what is forwarded. Everything else that arrives on `vmbr0` is
dropped.

## The Robot firewall is a separate layer

Hetzner's packet filter runs **before** traffic reaches the host, and it is
the only thing standing between the internet and the host's own services
when the host configuration is wrong.

| Layer | Configured in | Protects against |
|---|---|---|
| Robot firewall | The Robot web interface | Everything, including traffic that arrives before the host's own rules exist |
| Host firewall | `/etc/pve/nodes/<node>/host.fw` | Traffic that reaches the host and is not covered by the Robot rules |
| VM firewall | Per-VM, in the Proxmox web interface | Traffic between guests |

The Robot rules are configured in
[Account, network and domain](../00-prerequisites/02-account-network-domain.md).
They survive a broken host configuration, which is exactly what makes them
worth having.

## Verification

Do all of this before creating any virtual machine. A network fault found
now costs five minutes; the same fault found after nine guests are running
costs a weekend.

### On the host

```console
root@pve-01:~# ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
enp34s0          UP             <no address>
vmbr0            UP             203.0.113.10/26
vmbr2            UP             10.0.0.5/24

root@pve-01:~# ip route
default via 203.0.113.1 dev vmbr0
10.0.0.0/24 dev vmbr2 proto kernel scope link src 10.0.0.5

root@pve-01:~# bridge link
2: enp34s0: <BROADCAST,MULTICAST,UP,LOWER_UP> master vmbr0 state forwarding
4: vmbr0: <BROADCAST,MULTICAST,UP,LOWER_UP> state forwarding priority 0 cost 100
6: vmbr2: <BROADCAST,MULTICAST,UP,LOWER_UP> state forwarding priority 0 cost 100

root@pve-01:~# cat /proc/sys/net/ipv4/ip_forward
1

root@pve-01:~# iptables -t nat -S POSTROUTING
-P POSTROUTING ACCEPT
-A POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE
```

Two things to check carefully:

- `enp34s0` must show **no address**. If it carries one, the physical
  adapter and the bridge are both claiming the uplink and the routing will
  be unpredictable.
- `vmbr0` must be `state forwarding`, not `state disabled`. A bridge with
  STP enabled — or one whose port never came up — sits in `disabled` and
  silently drops everything.

### From outside

```console
$ ping -c 3 203.0.113.10
$ ssh root@203.0.113.10
```

### From a guest

Once a guest exists on `vmbr2`:

```console
user@guest:~$ ip route
default via 10.0.0.5 dev eth0
10.0.0.0/24 dev eth0 proto kernel scope link src 10.0.0.101

user@guest:~$ ping -c 3 10.0.0.5
user@guest:~$ ping -c 3 1.1.1.1
user@guest:~$ dig +short cloud.example.com
```

`ping 10.0.0.5` proves the guest can reach the host. `ping 1.1.1.1` proves
forwarding and masquerading work. `dig` proves DNS resolution — a guest that
can reach the internet but cannot resolve names is missing a resolver, not a
route.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Host has an address but nothing answers | The bridge port never came up — wrong interface name | `ip -br link`, correct `bridge-ports` |
| Guest gets an address, cannot reach the internet | `ip_forward` is 0 | `sysctl net.ipv4.ip_forward=1` |
| Guest reaches the internet but cannot resolve | No resolver in the guest | Set the resolver in the guest, or point it at the host |
| Nothing reaches the guest from outside | Robot firewall, host firewall, or a missing DNAT rule | Check all three layers in order |
| SSH dies right after `ifreload -a` | The change broke the uplink | Robot console, then [Recovering from rescue mode](05-recover-from-rescue.md) |
| Guest traffic is dropped after enabling the VM firewall | Missing conntrack zone | The `fwbr+` rule in the configuration above |

## Checklist

- [ ] `enp34s0` replaced with the real uplink name
- [ ] `ifreload -a` applied and a second SSH session verified
- [ ] `ip -br addr` shows the public address on `vmbr0` only
- [ ] `ip route` shows the default via the public gateway
- [ ] `cat /proc/sys/net/ipv4/ip_forward` returns 1
- [ ] `iptables -t nat -S POSTROUTING` shows the masquerade rule
- [ ] DNAT rules for 80 and 443 present and made persistent
- [ ] Robot firewall configured before the first public reboot

## Related pages

- [Rescue mode](01-rescue-mode.md)
- [Proxmox VE installation](03-proxmox-installation.md)
- [Recovering from rescue mode](05-recover-from-rescue.md)
- [Host firewall](../04-security/01-host-firewall.md)
- [Lab inventory](../00-prerequisites/03-lab-inventory.md)
