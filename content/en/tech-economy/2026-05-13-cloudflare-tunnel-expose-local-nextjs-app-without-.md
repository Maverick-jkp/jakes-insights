---
title: "Expose a Local Next.js App on Raspberry Pi With Cloudflare Tunnel"
date: 2026-05-13T21:19:54+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "tunnel", "expose", "Next.js"]
description: "Expose your local Next.js app publicly using Cloudflare Tunnel on Raspberry Pi — zero open ports, just an encrypted outbound connection via cloudflared."
image: "/images/20260513-cloudflare-tunnel-expose-local.webp"
technologies: ["Next.js", "Linux", "Go", "Cloudflare"]
faq:
  - question: "how to expose local Next.js app without port forwarding on Raspberry Pi"
    answer: "You can use a Cloudflare Tunnel expose local Next.js app without port forwarding Raspberry Pi setup by installing the cloudflared daemon, which creates an outbound encrypted connection to Cloudflare's edge network. This means your router never needs inbound ports opened, and your home IP address stays hidden from the public internet."
  - question: "does Cloudflare Tunnel work on Raspberry Pi 4"
    answer: "Yes, the cloudflared daemon runs natively on ARM-based devices including the Raspberry Pi 4, with official packages available for both 32-bit and 64-bit Raspberry Pi OS. This makes a Cloudflare Tunnel expose local Next.js app without port forwarding Raspberry Pi setup fully supported without any workarounds or manual compilation."
  - question: "why can't I port forward on my home internet connection"
    answer: "Over 60% of residential IPv4 connections in North America now operate behind carrier-grade NAT (CGNAT), which makes traditional port forwarding impossible at the router level. ISPs are also increasingly blocking inbound connections on residential plans, making port forwarding unreliable even when it technically appears configured correctly."
  - question: "is Cloudflare Tunnel free for personal projects"
    answer: "Cloudflare's free tier includes full Tunnel access with no data transfer caps for self-hosted personal projects, according to Cloudflare's official pricing page. This makes it a cost-effective alternative to paid reverse proxy services or VPS hosting just to expose a home lab application publicly."
  - question: "how long does it take to set up Cloudflare Tunnel for a Next.js app"
    answer: "A Next.js app running on localhost:3000 can typically be tunneled to a public domain in under 10 minutes with zero firewall or router configuration changes required. The cloudflared daemon handles the connection automatically, and Cloudflare routes incoming traffic through the tunnel to your local service."
aliases:
  - "/tech/2026-05-13-cloudflare-tunnel-expose-local-nextjs-app-without-/"

---

Running a Next.js app on a Raspberry Pi at home is easy. Making it publicly accessible without opening your router to the internet — that's where most developers get stuck.

> **Key Takeaways**
> - Cloudflare Tunnel creates an encrypted outbound connection from your Raspberry Pi to Cloudflare's edge network, eliminating the need to open any inbound ports on your router.
> - The `cloudflared` daemon runs natively on ARM-based devices like the Raspberry Pi 4, with official packages available for both 32-bit and 64-bit Raspberry Pi OS as of 2026.
> - Cloudflare's free tier includes Tunnel access with no data transfer caps for self-hosted personal projects, per Cloudflare's official pricing page.
> - Port forwarding exposes your home IP address directly; Cloudflare Tunnel proxies all traffic through Cloudflare's network, masking your origin entirely.
> - Next.js apps running on `localhost:3000` can be tunneled to a public domain in under 10 minutes with zero firewall configuration changes.

---

## The Problem With Port Forwarding in 2026

Port forwarding works. It's also a liability most home lab operators shouldn't accept.

When you forward port 80 or 443 from your router to a Raspberry Pi, you're publishing your home IP address to the public internet. Every scan, every bot, every brute-force attempt hits your device directly. And with ISPs increasingly rotating dynamic IPs — or blocking inbound connections entirely on residential plans — port forwarding is becoming less reliable even when it's technically permitted.

The residential ISP landscape has shifted significantly. According to Cloudflare's 2025 Connectivity Cloud report, over 60% of residential IPv4 connections in North America now operate behind carrier-grade NAT (CGNAT), which makes traditional port forwarding impossible regardless of router settings. If your ISP uses CGNAT, you simply can't forward ports — the architecture won't allow it.

That's why using Cloudflare Tunnel to expose a local Next.js app without port forwarding has become a standard pattern among self-hosters. It sidesteps the networking problem entirely by reversing the connection direction. Instead of the internet reaching into your network, your device reaches out to Cloudflare.

---

## How Cloudflare Tunnel Actually Works

The architecture is straightforward. `cloudflared` — Cloudflare's open-source tunnel daemon — runs as a process on your Raspberry Pi. It establishes persistent outbound connections to Cloudflare's nearest edge data center using the QUIC or HTTP/2 transport protocol. When a user visits your domain, Cloudflare routes the request through that tunnel to your local service. No inbound firewall rules. No open ports. No exposed IP.

According to Cloudflare's official documentation, each tunnel creates four concurrent connections to two separate Cloudflare data centers by default — that's built-in redundancy at the network level, not something you have to configure manually.

**Timeline of how a request flows:**

1. User hits `yourapp.yourdomain.com`
2. DNS resolves to Cloudflare's Anycast network (a CNAME pointing to `*.cfargotunnel.com`)
3. Cloudflare matches the hostname to your tunnel configuration
4. Request travels through the persistent tunnel connection to `cloudflared` on the Pi
5. `cloudflared` forwards it to `localhost:3000` (your Next.js dev or production server)
6. Response takes the same path back

Total latency overhead from the tunnel itself is typically 5–15ms according to community benchmarks on the Cloudflare Community forum. Negligible for most web applications.

---

## Setting Up the Tunnel: Four Stages

### Stage 1: Install `cloudflared` on Raspberry Pi

Cloudflare maintains ARM builds of `cloudflared` for Raspberry Pi OS. For a 64-bit Pi 4 or Pi 5 running Raspberry Pi OS Bookworm (current stable release as of May 2026):

```bash
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb
```

For 32-bit Raspberry Pi OS, swap `arm64` for `arm`. Cloudflare's GitHub releases page lists all available architectures.

### Stage 2: Authenticate and Create the Tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create my-nextjs-app
```

The login command opens a browser window — use SSH port forwarding or run this from a desktop session on the Pi. The tunnel create command generates a credentials file stored in `~/.cloudflared/`.

### Stage 3: Configure the Tunnel

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/pi/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: app.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

The ingress block maps your public hostname to your local Next.js server. The catch-all `http_status:404` at the end is required — `cloudflared` rejects configs without it.

### Stage 4: DNS and Service Setup

```bash
cloudflared tunnel route dns my-nextjs-app app.yourdomain.com
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

The `route dns` command creates a CNAME record in Cloudflare's DNS automatically — no manual DNS editing required. The service install registers `cloudflared` as a systemd service, so it restarts on reboot.

---

## Cloudflare Tunnel vs. the Alternatives

This setup isn't the only option. Here's how it compares against the main alternatives:

| Feature | Cloudflare Tunnel | Tailscale Funnel | ngrok Free Tier |
|---|---|---|---|
| **Cost** | Free (personal use) | Free up to 3 nodes | Free with limits |
| **Custom Domain** | Yes (bring your own) | Yes (tailscale.io subdomain or custom) | No (random URL) |
| **Persistent URL** | Yes | Yes | No |
| **Hides Origin IP** | Yes | Yes | Yes |
| **CGNAT Compatible** | Yes | Yes | Yes |
| **ARM/Pi Support** | Yes (official packages) | Yes (official packages) | Yes |
| **Traffic Limits** | None stated for personal | 3 services, bandwidth limits apply | 1GB/month data |
| **TLS Termination** | Cloudflare edge | Tailscale edge | ngrok edge |
| **Setup Complexity** | Medium (DNS required) | Low | Very low |
| **Best For** | Production-grade self-hosting | Team/private access | Quick demos |

Cloudflare Tunnel wins on production readiness and the absence of bandwidth caps for personal use. Tailscale Funnel — launched in 2023 and significantly more mature by 2025 — is simpler to configure but has tighter traffic restrictions at the free tier. ngrok's free tier no longer supports custom domains or persistent URLs following their 2024 pricing restructure, which makes it a poor fit for anything beyond short-lived testing.

The one hard trade-off with Cloudflare Tunnel: your domain must be on Cloudflare's nameservers. That's a firm requirement, not a suggestion. If your domain currently sits on Route 53 or Namecheap DNS, you'll need to transfer nameserver management to Cloudflare before any of this works. That migration is the only meaningful friction point in the entire setup — and it can take up to 24 hours to propagate.

This approach can also fail when Cloudflare itself experiences an outage. Because all traffic routes through their edge, any disruption upstream takes your service offline regardless of what's happening on your Pi. For personal projects, that's an acceptable trade. For anything business-critical, build in a fallback.

---

## Three Scenarios Where This Setup Pays Off

**Scenario 1: Home lab with a portfolio site**
A developer running a Next.js portfolio or blog on a Pi 4 gets a production-quality HTTPS endpoint with automatic TLS (Cloudflare manages the certificate), DDoS protection at the edge, and zero monthly hosting costs. The tunnel setup effectively replaces a $10–20/month VPS for static or low-traffic workloads — not a marginal saving over time.

**Scenario 2: API development with mobile clients**
Building a Next.js API route that a mobile app needs to call? Expose it through Cloudflare Tunnel during development and share a stable URL with teammates or device testers. No more "works on my machine" network issues. The URL stays constant between Pi reboots because it's tied to the tunnel ID, not an IP address — which matters more than it sounds when you're coordinating across devices or team members.

**Scenario 3: Bypassing ISP CGNAT**
If your ISP uses CGNAT — common with many fiber and 5G home internet providers in 2026 — port forwarding is architecturally impossible, full stop. Cloudflare Tunnel is one of the few clean solutions that works regardless of what's happening at the network layer between your Pi and the public internet. No workarounds, no VPS intermediaries. Just a process running on the Pi that reaches outward.

**One feature worth tracking:** In Q1 2026, Cloudflare added support for UDP-based services in Tunnel (previously TCP-only). That opens the door to more reliable handling of WebSocket-heavy Next.js apps and real-time services. If your app uses Server-Sent Events or WebSocket connections, that update changes the calculus meaningfully.

---

## What Comes Next

The case for this setup comes down to three things: CGNAT compatibility makes it work where port forwarding can't, Cloudflare's edge handles TLS and DDoS so you don't have to, and the free tier has no meaningful traffic restrictions for personal projects.

The numbers behind it matter. Over 60% of North American residential connections now use CGNAT — that makes Cloudflare Tunnel a practical necessity for a large portion of home lab operators, not an optimization. The four-connection redundancy built into every tunnel delivers better uptime than most port-forwarding configurations. And setup takes under 10 minutes once your domain is on Cloudflare's nameservers.

Over the next 6–12 months, expect Cloudflare to push Tunnel deeper into their developer platform. Tighter Workers integration and Tunnel-native observability are already in beta. The Raspberry Pi 5's substantially better I/O performance is also driving a new wave of self-hosting guides, as more developers discover what's actually possible on sub-$100 hardware.

The ceiling on what you can self-host for free just got considerably higher. If you're running a Next.js app on a Pi and haven't set up Cloudflare Tunnel yet, the question worth sitting with is: what have you been keeping local that's actually ready to go public?

## References

1. [Set up Cloudflare Tunnel · Cloudflare Docs](https://developers.cloudflare.com/tunnel/setup/)
2. [Cloudflare Tunnel Setup: Expose Self-Hosted Apps Without Port Forwarding - Security-First Server Man](https://panelica.com/blog/cloudflare-tunnel-setup-expose-self-hosted-apps-without-port-forwarding)


---

*Photo by [Compagnons](https://unsplash.com/@sigmund) on [Unsplash](https://unsplash.com/photos/people-sitting-on-chair-in-front-of-computer-monitor-Fa9b57hffnM)*
