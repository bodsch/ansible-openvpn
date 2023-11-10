# Ansible Role:  `openvpn`

Ansible role to install and configure openvpn server.


[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-openvpn/main.yml?branch=main)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-openvpn)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-openvpn)][releases]
[![Ansible Quality Score](https://img.shields.io/ansible/quality/50067?label=role%20quality)][quality]

[ci]: https://github.com/bodsch/ansible-openvpn/actions
[issues]: https://github.com/bodsch/ansible-openvpn/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-openvpn/releases
[quality]: https://galaxy.ansible.com/bodsch/openvpn

## Requirements & Dependencies

The ipv4 filter requires python's `netaddr` be installed on the ansible controller.

Ansible Collections

- [bodsch.core](https://github.com/bodsch/ansible-collection-core)

```bash
ansible-galaxy collection install bodsch.core
```
or
```bash
ansible-galaxy collection install --requirements-file collections.yml
```

### Operating systems

Tested on

* Arch Linux
* Artix Linux
* Debian based
    - Debian 11

## configuration

```yaml
openvpn_directory: /etc/openvpn

openvpn_diffie_hellman_keysize: 2048

openvpn_mtu: 1500
openvpn_mssfix: 1360

openvpn_keepalive:
  interval: 10
  timeout: 120

# server or client
openvpn_type: ""

openvpn_service:
  state: started
  enabled: true

openvpn_systemd: {}

openvpn_logging: {}

openvpn_easyrsa: {}

openvpn_certificate: {}

openvpn_server: {}

openvpn_persistent_pool: []

openvpn_mobile_clients: []

openvpn_config_save_dir: ""

openvpn_subnet:
  ip:  10.8.3.0
  mask: 255.255.255.0

openvpn_iptables:
  enabled: false

openvpn_push:
  routes: []
  route_gateway: ""
  dhcp_options:
    domains: []
    dns: []
  sndbuf: 393216
  rcvbuf: 393216
```

### `openvpn_systemd`

If OpenVPN has a dependency on another service (e.g. on sshd), then it should be possible 
here to force the service into a corresponding dependency.  
(Assuming that I have understood the systemd documentation correctly!)

```yaml
openvpn_systemd:
  requires_services:
    - sshd.service
```

### `openvpn_logging`

`verbose` Set the appropriate level of log  file verbosity.

- `0` is silent, except for fatal errors
- `4` is reasonable for general usage
- `5` and `6` can help to debug connection problems
- `9` is extremely verbose

`mute` Silence repeating messages.  
At most 20 sequential messages of the same message category will be output to the log.


**example**
```yaml
openvpn_logging:
  directory: /var/log/openvpn
  file: openvpn.log
  status: status.log
  verbosity: 3
  mute: 10
  append: true
```

### `openvpn_easyrsa`

The best way to create a PKI for OpenVPN is to separate your CA duty from each server & client.  
The CA should ideally be on a secure environment (whatever that means to you.)  
**Loss/theft of the CA key destroys the security of the entire PKI.**

The crl file has a runtime of 180 days (default).  
After these 180 days have expired, the VPN clients will no longer establish a connection to the server!  
For this reason I have integrated `crl_warn`.  
If `expired` is configured with `true`, each time the role is run, it checks whether the crl file is still valid.  
If the runtime is less than `expire_in_days`, the crl file is automatically renewed.

**example**
```yaml
openvpn_easyrsa:
  directory: /etc/easy-rsa
  openssl_config: ""
  key_size: 4096
  ca_expire: 3650
  cert_expire: 3650
  crl_days: 180
  crl_warn:
    expired: true
    expire_in_days: 20
  x509_dn_mode: cn_only
  # Choices for crypto alg are: (each in lower-case)
  #  * rsa
  #  * ec
  #  * ed
  crypto_mode: ec
  rsa_curve: secp384r1
  # sha256, sha224, sha384, sha512
  digest: sha512
```

### `openvpn_certificate`

**example**
```yaml
openvpn_certificate:
  req_country: DE
  req_province: Hamburg
  req_city: Hamburg
  req_org: ACME Inc.
  req_email: openvpn@acme.inc
  req_ou: Special Forces
  req_cn_ca: 'Open VPN'
  req_cn_server: '{{ ansible_fqdn }}'
```

### `openvpn_server`

`user` / `group` It's a good idea to reduce the OpenVPN daemon's privileges after initialization.

`tls_auth` For extra security beyond that provided by SSL/TLS, create an
"HMAC firewall" to help block DoS attacks and UDP port flooding.


**example**
```yaml
openvpn_server:
  # network interface connected to internal net
  interface: eth0
  # external IP of VPN server (EIP)
  external_ip: '' # {{ ansible_default_ipv4.address }}'
  # Which local IP address should OpenVPN
  # listen on? (optional)
  listen_ip: ''
  # valid: 'udp' or 'tcp'
  proto: udp
  # Which TCP/UDP port should OpenVPN listen on?
  port: 1194
  # valid: 'tun' or 'tap'
  # "tun" will create a routed IP tunnel,
  # "tap" will create an ethernet tunnel.
  device: tun
  max_clients: 10
  tls_auth:
    enabled: true
  cipher: AES-256-GCM
  user: nobody
  group: nogroup
```

### `openvpn_mobile_clients`

The generated OVPN files for mobile clients are stored on the VPN server under `/root/vpn-configs`.

You can also transfer them to the Ansible controller.  
To do this, `openvpn_config_save_dir` must be configured accordingly.

`tls_auth` is recommended when is activated in `openvpn_server`!

| variable       | default       | description |
| :---           | :---          | :---        |
| `name`         | `-`           |  |
| `state`        | `present`     |  |
| `roadrunner`   | `false`       |  |
| `remote`       | `-`           |  |
| `port`         | `1194`        |  |
| `proto`        | `udp`         |  |
| `device`       | `tun`         |  |
| `ping`         | `20`          |  |
| `ping_restart` | `45`          |  |
| `cert`         | `${name}.crt` |  |
| `key`          | `${name}.key` |  |

**example**
```yaml
openvpn_mobile_clients:
  - name: molecule_static
    state: present
    remote: server
    port: 1194
    proto: udp
    device: tun
    ping: 20
    ping_restart: 45
    cert: molecule_static.crt
    key: molecule_static.key

  - name: roadrunner_one
    state: present
    roadrunner: true
    remote: server
    port: 1194
    proto: udp
    device: tun
    ping: 20
    ping_restart: 45
    cert: roadrunner_one.crt
    key: roadrunner_one.key
```

#### `openvpn_persistent_pool`


**example**
```yaml
openvpn_persistent_pool:
  - name: molecule_mobile
    state: present
    static_ip: 10.8.3.10
```


### `openvpn_subnet`

Configure server mode and supply a VPN subnet for OpenVPN to draw client addresses from.
The server will take 10.8.0.1 for itself, the rest will be made available to clients.
Each client will be able to reach the server on 10.8.0.1.

Use distinct subnets for every VPN server, if client IPs are persisted!
(`ifconfig-pool-persist` in openvpn `server.conf`)

**example**
```yaml
openvpn_subnet:
  ip:  10.8.3.0
  mask: 255.255.255.0
```

### `openvpn_push`

Configuration options that can be pushed to the VPN client.

```yaml
openvpn_push:
  routes: []
  dhcp_options:
    domains: []
    dns: []
  sndbuf: 393216
  rcvbuf: 393216
```

#### `routes`

Push routes to the client to allow it to reach other private subnets behind the server.  
Remember that these private subnets will also need to know to route the OpenVPN client address pool
(10.8.0.0/255.255.255.0) back to the OpenVPN server.

List of routes which are propagated to client. Try to keep these nets small!

**example**
```yaml
openvpn_push:
  routes:
    - net: 10.8.3.0
      netmask: 255.255.255.0
```

#### `dhcp_options.dns`

**example**
```yaml
openvpn_push:
  dhcp_options:
    dns:
      - 10.15.0.2
      - 10.15.0.5
```

#### `dhcp_options.domains`

**example**
```yaml
openvpn_push:
  dhcp_options:
    domains:
      - matrix.vpn
      - customer.vpn
```

### `openvpn_iptables`

**example**
```yaml
openvpn_iptables:
  enabled: false
```

### example configuration for a openvpn server with 2 clients


#### example configuration for mobile clients

```yaml

openvpn_type: server

openvpn_persistent_pool:
  - name: client1.example.com
    state: present
    static_ip: 172.25.0.10
  - name:  client2.example.com
    state: present
    static_ip: 172.25.0.11

openvpn_subnet:
  ip: 172.25.0.0
  netmask: 255.255.255.0

openvpn_push:
  routes:
    - net: 172.25.0.0
      netmask: 255.255.255.0
```

#### example configuration for static client 1

```yaml
openvpn_type: client

openvpn_mobile_clients:
  - name: client1.example.com
    remote: vpn.example.com
    port: 1194
    proto: udp
    device: tun
    ping: 20
    ping_restart: 45
    cert: client1.example.com.crt
    key: client1.example.com.key
    tls_auth:
      enabled: true
```


#### example configuration for roadrunner client

```yaml
openvpn_type: server

openvpn_mobile_clients:
  - name: client2.example.com
    remote: vpn.example.com
    roadrunner: true
    port: 1194
    proto: udp
    device: tun
    ping: 20
    ping_restart: 45
    cert: client2.example.com.crt
    key: client2.example.com.key
    tls_auth:
      enabled: true
```

---

## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-openvpn/tags)!

---

## Author

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
