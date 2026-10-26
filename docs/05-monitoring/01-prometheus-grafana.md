# Prometheus and Grafana Monitoring

Brief description: Deploy Prometheus and Grafana monitoring stack on Proxmox host.

## Prerequisites

- [ ] Proxmox host access
- [ ] All VMs running
- [ ] IP addresses documented

## Prometheus Installation

### Step 1: Create User

```bash
useradd --no-create-home --shell /bin/false prometheus
```

### Step 2: Install Prometheus

```bash
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-amd64.tar.gz
tar -xzf prometheus-2.51.0.linux-amd64.tar.gz

sudo cp prometheus-2.51.0.linux-amd64/prometheus /usr/local/bin/
sudo cp prometheus-2.51.0.linux-amd64/promtool /usr/local/bin/
sudo cp -r prometheus-2.51.0.linux-amd64/consoles /etc/prometheus
sudo cp -r prometheus-2.51.0.linux-amd64/console_libraries /etc/prometheus

sudo chown -R prometheus:prometheus /etc/prometheus
```

### Step 3: Configure Prometheus

```bash
sudo nano /etc/prometheus/prometheus.yml
```

Add:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'rocketchat-node'
    static_configs:
      - targets: ['<rocketchat-ip>:9100']

  - job_name: 'nextcloud-node'
    static_configs:
      - targets: ['<nextcloud-ip>:9100']

  - job_name: 'nginx-node'
    static_configs:
      - targets: ['<nginx-ip>:9100']
```

### Step 4: Create Service

```bash
sudo nano /etc/systemd/system/prometheus.service
```

Add:

```ini
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/

[Install]
WantedBy=multi-user.target
```

Start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

## Node Exporter Installation

On each VM:

```bash
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar -xzf node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/

# Create service
cat > /tmp/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=default.target
EOF

sudo useradd --no-create-home --shell /bin/false node_exporter
sudo cp /tmp/node_exporter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter

# Allow from Proxmox
sudo ufw allow from <proxmox-ip> to any port 9100
```

## Grafana Installation

```bash
apt install -y apt-transport-https software-properties-common wget

wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key
echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

apt update
apt install -y grafana

systemctl enable grafana-server
systemctl start grafana-server
```

## Verification

- [ ] Prometheus installed and running
- [ ] Node exporters on all VMs
- [ ] Targets showing as UP
- [ ] Grafana installed
- [ ] Dashboards accessible

## Next Steps

- [Hetzner Monitoring](02-hetzner-monitoring.md)
