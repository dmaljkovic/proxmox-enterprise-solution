# Hardware and budget

## Server specification

The project runs on a single Hetzner dedicated server, product **EX44**.

| Component | Specification | Notes |
|---|---|---|
| CPU | Intel Core i5-13500 | 13th generation, 6 Performance cores + 8 Efficiency cores; 14 cores / 20 threads with Hyper-Threading |
| Memory | 64 GB DDR4 ECC | Sized for the ZFS ARC and the guest estate together |
| Storage | 2 × 512 GB NVMe (DC Edition) | Mirrored; see [ZFS pool layout](../01-preparation/02-zfs-pool.md) |
| Network | 1 × 1 Gbit/s port | 1 Gbit/s guaranteed bandwidth, unlimited traffic subject to Hetzner's traffic policy |
| Location | FSN 1 (Falkenstein) or HEL 1 (Helsinki) | Choose the one closest to the majority of users |
| Power | On-site 24/7 service | Included with the dedicated product line |

The full specification, current availability and current pricing are on the
[Hetzner EX44 product page](https://www.hetzner.com/dedicated-rootserver/ex44/).

## Why one server

The design assumes a single host with a mirrored disk pair. That buys three
things that matter more here than raw capacity:

- **ZFS mirroring.** A single disk failure takes the host down but does not
  destroy the pool. This is the failure that a previous iteration of this
  project actually suffered.
- **Reproducibility.** The whole estate can be torn down and rebuilt from the
  documentation, because every VM is created from a template on a scripted
  basis.
- **Cost.** The entire estate — nine VMs, identity provider, directory, database,
  monitoring and documentation server — runs on one monthly invoice.

The trade-off is explicit: there is no high availability. The recovery path is
restore-from-backup, not failover, and that is what
[Backup and restore](../06-maintenance/02-backup-restore.md) documents.

## Sizing rationale

| Guest estate | Host | Headroom |
|---|---|---|
| 14 vCPU | 14 cores / 20 threads | One vCPU per physical core, no core oversubscription |
| 32 GB RAM | 64 GB | 32 GB for the host, ZFS ARC and burst |
| 210 GB | ~512 GB usable after mirroring | ~300 GB for snapshots, replication and new guests |

The guest disk figure is the sum of the virtual disk sizes in the
[lab inventory](03-lab-inventory.md). ZFS snapshots and the ZFS ARC are
consumed from the host's remaining space, and Sanoid retention is what keeps
that consumption bounded. The [backup strategy](../04-security/05-backup-strategy.md)
page sets the retention window that fits inside the margin.

## Cost

| Item | Basis | Notes |
|---|---|---|
| EX44 dedicated server | Monthly rental | Check the product page for the current rate and whether VAT applies to your jurisdiction |
| Extra IPv4 address | Optional | Only needed if a second address is required for a service |
| Backup target | Storage or a second small server | Off-site replication cannot use the mirrored pair on the same host — see below |
| Domain | Annual | Needed for the five public hostnames in [Lab inventory](03-lab-inventory.md) |
| Let's Encrypt certificates | Free | Five certificates, automated renewal, see [Nginx reverse proxy and TLS](../03-software/03-nginx-reverse-proxy.md) |

!!! danger "Mirrored disks are not a backup"
    ZFS mirroring protects against a disk failure. It does **not** protect
    against accidental deletion, a bad `zpool destroy`, ransomware, or the loss
    of the host itself. Off-site replication to a different physical machine is
    the only thing that survives the failure of this server, and it is a
    separate line item in the budget above.

## What the monthly rental does not cover

- **IPv4 address rental** if the account has none free.
- **A second public address** for services that need their own address.
- **Backup storage** sized for the snapshot retention window.
- **The domain registration**, renewed annually.

## Next steps

Once the server is provisioned:

1. Record the real public address, gateway and prefix length from the Robot
   console into a local file that is **not** committed to this repository.
2. Follow [Account, network and domain](02-account-network-domain.md) to set up
   DNS and the Hetzner firewall.
3. Follow [Rescue mode](../01-preparation/01-rescue-mode.md) to bootstrap the
   host.
