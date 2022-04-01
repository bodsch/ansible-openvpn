# Ansible Role:  `openvpn`

Ansible role to install and configure openvpn server.

## Requirements & Dependencies

The ipv4 filter requires python's `netaddr` be installed on the ansible controller.


### Operating systems

Tested on

* Arch Linux
* Debian based
    - Debian 10 / 11

## configuration

```yaml
openvpn_directory: /etc/openvpn

openvpn_diffie_hellman_keysize: 2048

# server or client
openvpn_type: ""

openvpn_service:
  state: started
  enabled: true

openvpn_logging: {}

openvpn_easyrsa: {}

openvpn_certificate: {}

openvpn_server: {}

openvpn_clients: {}

openvpn_subnet:
  ip:  10.8.3.0
  mask: 255.255.255.0

openvpn_pushed_routes: []

openvpn_iptables:
  enabled: false

openvpn_dns:
  push: false
  server: ''
  domain: ''

openvpn_client_users: []
```

### `openvpn_logging`

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

**example**
```yaml
openvpn_easyrsa:
  directory: /etc/easy-rsa
  openssl_config: ""
  key_size: 4096
  ca_expire: 3650
  cert_expire: 3650
  crl_days: 180
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
    enabled: false
  cipher: AES-256-GCM
  user: nobody
  group: nogroup
```

### `openvpn_clients`

**example**
```yaml
openvpn_clients:
  server_name:
    remote: ""
    port: 1194
    proto: udp
    device: tun
    ping: 20
    ping_restart: 45
    tls_auth:
      enabled: false
```

### `openvpn_subnet`

Use distinct subnets for every VPN server, if client IPs are persisted!
(`ifconfig-pool-persist` in openvpn `server.conf`)

**example**
```yaml
openvpn_subnet:
  ip:  10.8.3.0
  mask: 255.255.255.0
```

### `openvpn_pushed_routes`

List of routes which are propagated to client. Try to keep these nets small!

**example**
```yaml
openvpn_pushed_routes:
  - net: 172.25.220.0
    mask: 255.255.255.0
```

### `openvpn_iptables`

**example**
```yaml
openvpn_iptables:
  enabled: false
```

### `openvpn_dns`

**example**
```yaml
openvpn_dns:
  push: false
  server: ''
  domain: ''
```

### `openvpn_client_users`

**example**
```yaml
openvpn_client_users:
  - name: darillium.matrix.lan
    state: absent
    static_ip: 10.8.3.10
```



## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://gitlab.com/bodsch/ansible-openvpn/-/tags)!


## Author

- Bodo Schulz

## License

[Apache](LICENSE)

`FREE SOFTWARE, HELL YEAH!`
