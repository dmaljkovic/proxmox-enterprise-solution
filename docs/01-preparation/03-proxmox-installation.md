# Proxmox VE installation

Proxmox VE 9.2 on Debian 13 "Trixie", kernel 7.0, ZFS 2.4, installed onto the
mirrored NVMe pair prepared in [ZFS pool layout](02-zfs-pool.md).

## Before you start

| Prerequisite | Where it comes from |
|---|---|
| The Hetzner Rescue System is reachable over SSH | [Rescue mode](01-rescue-mode.md) |
| Both NVMe devices are raw, with no software RAID on them | [Rescue mode](01-rescue-mode.md) |
| The public address, gateway and prefix are known | [Account, network and domain](../00-prerequisites/02-account-network-domain.md) |
| The physical uplink's name is recorded | [Rescue mode](01-rescue-mode.md) |
| The firmware mode is known (`UEFI` or `Legacy`) | [Rescue mode](01-rescue-mode.md) |

## Downloading and verifying the ISO

```console
root@rescue ~ # mkdir -p /tmp/work && cd /tmp/work
root@rescue ~ # curl -LO https://enterprise.proxmox.com/iso/proxmox-ve_9.2-1.iso
root@rescue ~ # curl -LO https://enterprise.proxmox.com/iso/proxmox-ve_9.2-1.iso.sha256
```

Verify against the checksum published by Proxmox. This is the check that
matters:

```console
root@rescue ~ # sha256sum -c proxmox-ve_9.2-1.iso.sha256
proxmox-ve_9.2-1.iso: OK
```

The expected digest is:

```text
4e88fe416df9b527624a175f24c9aa07c714d3332afb1ee3dbf3879573ef2c6c
```

Proxmox also publishes a detached GPG signature next to the ISO:

```console
root@rescue ~ # curl -LO https://enterprise.proxmox.com/iso/proxmox-ve_9.2-1.iso.asc
root@rescue ~ # gpg --verify proxmox-ve_9.2-1.iso.asc proxmox-ve_9.2-1.iso
gpg: Good signature from "Proxmox Release <info@proxmox.com>" [unknown]
```

!!! warning "Compare the key, do not just read the result"
    `gpg --verify` reports "Good signature" for any key that is already in
    the keyring, including a key you added yourself. Check the fingerprint
    of the signing key against the one Proxmox publishes, and confirm the
    ISO came from `enterprise.proxmox.com` over HTTPS. The checksum file
    above is fetched over the same channel, so it verifies integrity and
    authenticity together — that is why it is the primary check.

## Booting the installer

### Method A — KVM Virtual Media

The cleanest option, and the one that avoids every interface-name problem
described below.

1. Request the **Remote console / KVM** add-on for the server from Robot
   support. It is free for dedicated servers; the request needs the server
   ID and the order number.
2. Prepare an SMB share that the KVM console can reach, holding
   `proxmox-ve_9.2-1.iso`.
3. In the KVM console, attach the ISO through **Virtual Media → Mount from
   SMB**.
4. Boot from the attached ISO.

The installer then runs on the real machine: the real NVMe devices, the real
NIC under its real name.

!!! note "The ISO mount is slow"
    Loading the image over SMB takes several minutes and the console shows
    no progress bar. It is a one-off cost.

### Method B — QEMU inside the Rescue System

The fallback when the KVM add-on is not available. QEMU runs on the rescue
host, with the two NVMe drives passed through as raw block devices and the
installer attached as a CD-ROM.

```console
root@rescue ~ # apt update && apt install -y qemu-system-x86 ovmf
```

Build the command. The network adapter is given the rescue host's own MAC
so that the address Hetzner sees on the network is unchanged:

```console
root@rescue ~ # MAC=$(ip link show eth0 | awk '/ether/ {print $2}')
root@rescue ~ # echo "Using MAC: $MAC"
Using MAC: 00:00:00:00:00:00
```

For a UEFI host:

```console
root@rescue ~ # qemu-system-x86_64 \
    -enable-kvm \
    -machine q35 \
    -cpu host \
    -m 16G \
    -boot d \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \
    -drive if=pflash,format=raw,file=/usr/share/OVMF/OVMF_VARS.fd \
    -drive file=/dev/nvme0n1,format=raw,if=none,id=drive0 \
    -device nvme,drive=drive0,serial=nvme0 \
    -drive file=/dev/nvme1n1,format=raw,if=none,id=drive1 \
    -device nvme,drive=drive1,serial=nvme1 \
    -cdrom /tmp/work/proxmox-ve_9.2-1.iso \
    -netdev user,id=net0 \
    -device virtio-net-pci,netdev=net0,mac="$MAC" \
    -nographic \
    -serial mon:stdio
```

For a legacy BIOS host, drop the two `-drive if=pflash` lines. The `nvme`
device model is what makes the installer see the drives as `/dev/nvme0n1`
and `/dev/nvme1n1` rather than as virtio disks.

Connect a VNC client to the display, or use the serial console as the
`-nographic` flag above provides one.

!!! danger "The interface name will be wrong afterwards"
    Inside QEMU the guest sees a virtio adapter, and the installer writes
    its predictable name — usually `enp0s31f6` — into
    `/etc/network/interfaces`. The physical NIC on the EX44 is called
    something else entirely. After the physical reboot the host will have
    no network.

    Fix it **before** rebooting into the hardware, using the procedure in
    [Recovering from rescue mode](05-recover-from-rescue.md). Method A does
    not have this problem.

### Unattended installation

Proxmox 8.2 introduced `proxmox-auto-install-assistant`, which embeds an
answer file into the ISO and adds an **Automated Installation** boot entry
that is selected after a ten-second timeout. It removes the VNC session
from the process entirely.

The answer file also solves the interface-name problem, by pinning the MAC
address to a name of your choosing:

```toml
# /tmp/work/answer.toml
[global]
keyboard = "en-us"
country = "de"
fqdn = "pve-01.example.com"
mailto = "admin@example.com"
timezone = "Europe/Berlin"
root-password-hashed = "$6$rounds=656000$..."
root-ssh-keys = [
    "ssh-ed25519 <your-public-key>"
]
reboot-mode = "power-off"

[network]
source = "from-answer"
cidr = "203.0.113.10/26"
gateway = "203.0.113.1"
dns = "1.1.1.1"
filter.ID_NET_NAME_MAC = "*<the mac of the uplink>"

[network.interface-name-pinning]
enabled = true

[network.interface-name-pinning.mapping]
"00:00:00:00:00:00" = "nic0"

[disk-setup]
filesystem = "zfs"
zfs.raid = "raid1"
disk-list = [
    "nvme0n1",
    "nvme1n1"
]
```

!!! warning "Generate the hash, never write the password"
    `root-password-hashed` takes a SHA-512 crypt hash, not the password.
    Generate it with `openssl passwd -6`, or with `mkpasswd -m yescrypt`
    from the `whois` package.

The answer file is validated and baked into a new ISO:

```console
root@rescue ~ # proxmox-auto-install-assistant validate-answer /tmp/work/answer.toml
root@rescue ~ # proxmox-auto-install-assistant prepare-iso \
    --fetch-from iso \
    --answer-file /tmp/work/answer.toml \
    --output /tmp/work/proxmox-auto.iso \
    /tmp/work/proxmox-ve_9.2-1.iso
```

The `xorriso` package is required for `prepare-iso`.

## The installer

The graphical installer is keyboard operable: `ALT` plus the underlined letter
of a field advances to the next step.

| Step | Answer |
|---|---|
| Language, keyboard, country | Your own |
| Target disks | Select **both** NVMe devices |
| Filesystem | **ZFS** |
| RAID level | **Mirror** |
| ZFS options | `ashift = 12`, compression `lz4`, checksum `on`, ARC maximum as below |
| Disk size | Leave the default so the pool uses the whole device |
| Location | Timezone, keyboard layout, country |
| Password and e-mail | Root password, at least 12 characters, and the address for Proxmox notifications |
| Network | Hostname `pve-01.example.com`, CIDR `203.0.113.10/26`, gateway `203.0.113.1`, DNS |

Two fields in the ZFS options step are worth a second look.

**ashift** must be 12 for 4 KiB sectors. It cannot be changed afterwards
without recreating the pool.

**The ARC maximum** is written to `/etc/modprobe.d/zfs.conf` during the
install. The default of 10 % of RAM is 6.4 GiB on a 64 GB host, which is
already reasonable. It is adjusted afterwards in
[ZFS pool layout](02-zfs-pool.md).

!!! tip "Leave some space for swap"
    The installer creates `rpool/swap` as a zvol, which Proxmox's own
    guidance discourages. If the pool is created with `hdsize` slightly
    smaller than the full device, the remaining space can hold a physical
    swap partition instead. This project keeps the zvol and lowers
    `vm.swappiness` — a pragmatic trade that costs one filesystem.

!!! warning "Pin the network interface names"
    The installer has a **Pin network interface names** checkbox. With it
    ticked, the interface keeps the same name across reboots and across
    reinstalls. It is the single most useful option on that screen, and it
    is what prevents the failure described in
    [Recovering from rescue mode](05-recover-from-rescue.md).

The installer reboots by itself once it finishes.

## After the first boot

### Repositories

Proxmox 9 uses the deb822 `.sources` format rather than the older `.list`
files. Two files are present:

```console
root@pve-01 ~ # ls /etc/apt/sources.list.d/
debian.sources  pve-enterprise.sources
```

Without a subscription, the enterprise repository has to be disabled and the
public one enabled. In
`/etc/apt/sources.list.d/pve-enterprise.sources` set `Enabled: no`:

```text
Types: deb
URIs: https://enterprise.proxmox.com/debian/pve
Suites: trixie
Components: pve-enterprise
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
Enabled: no
```

Then create `/etc/apt/sources.list.d/proxmox.sources`:

```text
Types: deb
URIs: http://download.proxmox.com/debian/pve
Suites: trixie
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
```

!!! warning "The public repository is not what you are paying for"
    Proxmox's own documentation states that the no-subscription repository
    is not recommended for production, because the packages are not as
    heavily tested. On a lab host that trades stability of the hypervisor
    for a €59 monthly bill, which is a reasonable trade — but it is a
    trade, and it is the reason a subscription is worth reconsidering if
    this host ever carries anything that matters.

### Update the system

Proxmox is a rolling release on top of Debian, and a partial upgrade can
leave the host in a broken state. Use `full-upgrade`, not `upgrade`:

```console
root@pve-01 ~ # apt update
root@pve-01 ~ # apt full-upgrade
root@pve-01 ~ # apt autoremove
```

A reboot is required afterwards, because the kernel is updated:

```console
root@pve-01 ~ # reboot
```

### Verify the versions

```console
root@pve-01 ~ # pveversion -v
proxmox-ve: 9.2.0
pve-manager: 9.2.21
pve-cluster: 9.1.6
pve-docs: 9.2.13
pve-container: 6.1.14
pve-firewall: 6.0.6
qemu-server: 9.2.11
pve-qemu-kvm: 11.0.3-4
libpve-common-perl: 9.2.3
libpve-network-perl: 1.6.7
ifupdown2: 3.3.0-1+pmx12
zfsutils-linux: 2.4.4-pve1
proxmox-default-kernel: 2.1.0
```

The three lines that matter here are `proxmox-ve: 9.2.0`, `ifupdown2` —
Proxmox's network stack is still `ifupdown2`, and `/etc/network/interfaces`
is still the configuration file — and `zfsutils-linux: 2.4.4-pve1`.

### Time synchronisation

`chrony` is the default NTP daemon and is already installed. Point it at
servers that answer from the same region as the host:

```console
root@pve-01 ~ # nano /etc/chrony/chrony.conf
```

```text
pool ntp.example.com iburst
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync
logdir /var/log/chrony
```

```console
root@pve-01 ~ # systemctl restart chrony
root@pve-01 ~ # chronyc tracking
Reference ID    : 0A0B0C0D (192.0.2.1)
Stratum         : 3
Ref time (UTC)  : Sun Oct 18 01:23:45 2026
System time     : 0.000007234 seconds fast of NTP time
Last offset     : -0.000001234 seconds
RMS offset      : 0.000008120 seconds
Frequency       : 23.421 ppm
Residual freq   : -0.014 ppm
Skew            : 0.052 ppm
```

The `Reference ID` must be a real server, not `0.0.0.0`. A host whose clock
drifts will fail TLS certificate validation in ways that look like
certificate problems.

### Hostname

```console
root@pve-01 ~ # hostnamectl set-hostname pve-01.example.com
root@pve-01 ~ # hostnamectl
```

### Root access over SSH

Copy the public key rather than the private one:

```console
root@pve-01 ~ # mkdir -p /root/.ssh && chmod 700 /root/.ssh
root@pve-01 ~ # nano /root/.ssh/authorized_keys
ssh-ed25519 <your-public-key> <comment>
```

```console
root@pve-01 ~ # chmod 600 /root/.ssh/authorized_keys
```

Verify the login works **before** closing the session you are in:

```console
$ ssh root@203.0.113.10
```

### Subscription status

```console
root@pve-01 ~ # pvesubscription get
```

"No subscription found" is the expected result for a host without one. It
is what makes the enterprise repository unusable and the public one
necessary.

## The network configuration file

Proxmox never edits `/etc/network/interfaces` directly. Changes made in the
web interface are staged into `/etc/network/interfaces.new` and only become
active when the interface is applied. The `pvenetcommit` systemd unit
performs the same step during boot.

For everything that follows, `/etc/network/interfaces` is edited by hand and
applied with:

```console
root@pve-01 ~ # ifreload -a
```

`ifup` and `ifdown` are explicitly discouraged by the Proxmox
documentation — they can drop guest traffic on a bridge.

## First access

The web interface is on port 8006:

```console
root@pve-01 ~ # ss -tlnp | grep 8006
LISTEN 0 4096 *:8006 *:*  users:(("pveproxy",pid=1234,fd=6))
```

Open `https://203.0.113.10:8006/` and accept the self-signed certificate. Log
in as `root` with the PAM realm.

!!! warning "Do not leave the web interface exposed"
    Port 8006 is reachable on the public address as soon as the host has
    one. It is restricted to the admin address by the Robot firewall and
    the host firewall — see
    [Host firewall](../04-security/01-host-firewall.md) — but that
    configuration has to exist before the first public reboot, not after.

## Checklist

- [ ] ISO checksum verified against the published `.sha256`
- [ ] Installer booted with the correct disk and filesystem selection
- [ ] `ashift` set to 12 and the RAID level set to Mirror
- [ ] Host boots into Proxmox with the expected hostname
- [ ] `pveversion -v` reports Proxmox VE 9.2
- [ ] Enterprise repository disabled, public repository enabled
- [ ] `apt full-upgrade` completed and the host rebooted
- [ ] `chronyc tracking` shows a real reference
- [ ] Root SSH key in place and verified in a second session
- [ ] `zpool status` shows both NVMe devices online

## Related pages

- [Rescue mode](01-rescue-mode.md)
- [ZFS pool layout](02-zfs-pool.md)
- [Network configuration](04-network-configuration.md)
- [Recovering from rescue mode](05-recover-from-rescue.md)
