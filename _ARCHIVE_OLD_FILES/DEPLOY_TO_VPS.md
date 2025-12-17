# How to Deploy PhazeVPN Server to VPS

The PhazeVPN server code has been fixed to support real encryption and handshakes. You now need to deploy it to your VPS.

## 1. Upload Code to VPS
You need to copy the `phazevpn-protocol-go` directory to your VPS.
Assuming your VPS IP is `YOUR_VPS_IP` and user is `root`:

```bash
scp -r /media/jack/Liunux/secure-vpn/phazevpn-protocol-go root@YOUR_VPS_IP:/opt/phazevpn/
```

## 2. Install Go on VPS
SSH into your VPS and install Go:
```bash
ssh root@YOUR_VPS_IP
apt update
apt install -y golang-go
```

## 3. Build and Run Server
On the VPS:
```bash
cd /opt/phazevpn/phazevpn-protocol-go
go mod tidy
go build -o phazevpn-server main.go

# Run the server (example)
./phazevpn-server -host 0.0.0.0 -port 51821 -network 10.9.0.0/24
```

## 4. Allow Port in Firewall
Ensure port 51821/udp is open:
```bash
ufw allow 51821/udp
```

# How to Use the Client (Local)

I have already built the client binary for you at `phazevpn-client/phazevpn-bin`.
Run the Python GUI:
```bash
cd /media/jack/Liunux/secure-vpn/phazevpn-client
python3 phazevpn-client.py
```
Select "PhazeVPN" protocol and connect.
