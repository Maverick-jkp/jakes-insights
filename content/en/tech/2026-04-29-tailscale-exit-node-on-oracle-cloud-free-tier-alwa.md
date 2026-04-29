---
title: "Tailscale Exit Node on Oracle Cloud Free Tier: ARM Pitfalls"
date: 2026-04-29T20:43:54+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "tailscale", "exit", "node", "Docker"]
description: "Set up a Tailscale exit node on Oracle Cloud's free ARM tier (4 OCPUs, 24GB RAM) without the common pitfalls that silently break your VPN over time."
image: "/images/20260429-tailscale-exit-node-on-oracle-.webp"
technologies: ["Docker", "AWS", "Linux", "Rust", "Go"]
faq:
  - question: "tailscale exit node on oracle cloud free tier always-free arm instance setup pitfalls"
    answer: "The most common pitfalls include Oracle's two-layer firewall requiring both VCN Security List rules and OS-level iptables rules, IP forwarding being disabled by default on Ubuntu ARM64, and Oracle's idle instance reclamation policy which can terminate low-traffic nodes without warning. Each of these issues can cause your exit node to silently stop working even after a successful initial setup."
  - question: "why does my tailscale exit node stop working on oracle cloud after a few days"
    answer: "Oracle Cloud may reclaim Always Free instances it detects as idle, and a low-traffic Tailscale exit node can trigger this false-idle detection without a keepalive strategy in place. Additionally, iptables rules may not persist across reboots unless saved with netfilter-persistent, causing traffic forwarding to silently break after a restart."
  - question: "how to fix tailscale UDP traffic blocked on oracle cloud VCN"
    answer: "Oracle Cloud runs two independent firewall layers — the VCN Security List and the OS-level iptables — and both must allow UDP port 41641 for Tailscale to function. Opening the port in the Security List alone is not enough; you must also run 'sudo iptables -I INPUT -p udp --dport 41641 -j ACCEPT' at the OS level and save the rules with netfilter-persistent."
  - question: "does oracle always free arm instance work as a tailscale exit node setup pitfalls to avoid"
    answer: "Yes, Oracle's Always Free ARM Ampere A1 instance works well as a tailscale exit node, but there are several setup pitfalls to avoid including forgetting to enable IP forwarding with sysctl, missing the FORWARD iptables rule that allows traffic routing, and not accounting for Oracle's instance reclamation policy for low-activity VMs. Addressing all three layers — firewall, kernel routing, and instance activity — is required for a stable long-term setup."
  - question: "how to enable IP forwarding for tailscale exit node on ubuntu arm64"
    answer: "IP forwarding is disabled by default on Ubuntu ARM64 instances, including those on Oracle Cloud, and must be manually enabled for a Tailscale exit node to route traffic correctly. You can enable it by adding 'net.ipv4.ip_forward=1' and 'net.ipv6.conf.all.forwarding=1' to /etc/sysctl.conf and running 'sudo sysctl -p' to apply the changes."
---

Running a personal VPN exit node for zero dollars sounds like a trap. Oracle's Always Free ARM instances and Tailscale together make it technically real — but the gap between "it works" and "it actually *stays* working" is where most setups quietly collapse.

> **Key Takeaways**
> - Oracle Cloud's Always Free tier provides two ARM-based Ampere A1 instances with up to 4 OCPUs and 24GB RAM total — one of the most capable free compute options available in 2026.
> - The pitfalls in this setup are almost never about Tailscale itself. They're about Oracle's firewall architecture, kernel routing flags, and instance reclamation policies.
> - Ubuntu 22.04/24.04 on ARM64 runs Tailscale cleanly, but IP forwarding is disabled by default and iptables rules must be explicitly configured — or traffic drops silently with no error.
> - Oracle has reclaimed "idle" Always Free instances with minimal warning. A low-traffic Tailscale exit node can trigger false-idle detection without a keepalive strategy in place.

---

## Why This Setup Exists at All

CGNAT killed the home-hosting dream for most residential ISPs. Carrier-Grade NAT means your home IP isn't reachable from the public internet — no port-forwarding, no inbound connections, and self-hosting anything becomes a workaround exercise by default.

Tailscale's exit node feature solves half the problem. Route all your device traffic through a node that *does* have a real public IP. Oracle's Always Free tier provides exactly that: a persistent ARM64 VM (Ampere A1 architecture) with a static public IP, 1Gbps network interface, and 50GB boot volume — permanently free, no credit card expiry clock ticking.

The community caught on fast. Threads on r/Tailscale and write-ups on DEV Community — notably Vimal's "Invisible Tunnel" guide from late 2024 — show hundreds of engineers running this exact configuration for personal privacy, Plex sharing behind CGNAT, and remote home lab access. The fullmetalbrackets.com Plex/Tailscale guide specifically walks through the CGNAT bypass use case in detail.

The comments on those posts tell a different story, though. Setup works. Three days later, traffic stops. The instance disappears. UDP packets vanish into Oracle's VCN with no explanation. The concept is sound. The execution has sharp edges.

---

## The Pitfalls, One by One

### Pitfall #1: Oracle's Two-Layer Firewall

This trips up nearly every first-time setup. Oracle VCN runs two independent firewall layers: **Security Lists** at the VCN level, and **iptables/nftables** at the OS level. You can open UDP 41641 (Tailscale's default port) in the Security List and still get zero connectivity — because the OS firewall blocks it independently, and nobody tells you.

The fix is non-negotiable. On Oracle Linux or Ubuntu on ARM:

```bash
sudo iptables -I INPUT -p udp --dport 41641 -j ACCEPT
sudo iptables -I FORWARD -j ACCEPT
sudo netfilter-persistent save
```

Without the `FORWARD` rule, your instance accepts Tailscale traffic but won't route it onward. That's the exit node failing silently — no error message, just dead throughput and a confusing `tailscale status` that shows everything as healthy.

### Pitfall #2: IP Forwarding Disabled by Default

Tailscale's documentation covers this, but it's easy to skip on a fresh ARM instance. Linux doesn't forward packets between interfaces unless you explicitly tell it to.

```bash
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

Then advertise the exit node:

```bash
sudo tailscale up --advertise-exit-node
```

And approve it in the Tailscale admin console. Miss any one of these three steps and nothing works. The frustrating part: `tailscale status` reports the node as healthy regardless of whether routing is actually functioning.

### Pitfall #3: Instance Reclamation and the "Idle" Problem

Oracle's Always Free terms permit reclaiming instances with "low resource utilization." The exact threshold isn't publicly documented — Oracle's own FAQ uses vague language around "idle" without defining metrics or timelines.

A Tailscale exit node under light personal use (browsing, occasional SSH) generates minimal CPU load. That can look idle to Oracle's monitoring. Reported reclamation cases on r/Tailscale suggest this happens most frequently in the first 7–14 days, before Oracle's system establishes a usage baseline for your instance.

A practical mitigation: run a lightweight cron job generating periodic CPU activity, or configure a synthetic health check that pings an external endpoint on a schedule. It's inelegant. It works.

---

## Comparison: Always Free Exit Node Options in 2026

| Feature | Oracle Cloud ARM (Always Free) | AWS t2.micro (Free Tier) | Fly.io Free Tier |
|---|---|---|---|
| Monthly cost after trial | $0 permanent | $0 for 12 months only | $0 (limited) |
| vCPUs | Up to 4 (Ampere A1) | 1 (x86) | Shared |
| RAM | Up to 24GB total | 1GB | 256MB–512MB |
| Tailscale support | Yes, native | Yes | Yes (via Docker) |
| Static IP | Yes | Yes (Elastic IP, limited free) | Shared anycast |
| Reclamation risk | Yes (idle policy) | No (12-month guaranteed) | No |
| ARM64 compatibility | Native | No | Varies |
| Best for | Long-term personal exit node | Testing, under 1 year | Minimal traffic relay |

Oracle wins on raw specs for free-tier compute. AWS free tier is more *reliable* but expires after 12 months. Fly.io's free allowance is too constrained for sustained exit node traffic.

---

## Three Real Scenarios — and Where Each One Breaks

**Home lab behind CGNAT.** The canonical use case. You've got a Proxmox box, a Plex server, or a NAS that you want reachable remotely. Your ISP assigns a CGNAT address. The Oracle ARM instance becomes your public-facing relay; Tailscale handles the encrypted tunnel. The pitfall here is MTU mismatch — Tailscale's default MTU of 1280 occasionally conflicts with Oracle's VCN, causing large packet fragmentation. If you see intermittent TCP stalls on large file transfers, set `--mtu=1280` explicitly in your `tailscaled` config.

**Privacy-focused personal VPN.** Route all traffic from a laptop or phone through the Oracle exit node while traveling. Works well — with one important caveat. Oracle logs VCN flow data by default. This is not a zero-log setup. Oracle Cloud infrastructure is a third-party with terms of service and law enforcement compliance obligations. If privacy is the primary goal, that context matters.

**Developer remote access to home machines.** SSH into home lab nodes from a coffee shop or client site. This use case has the lowest traffic profile — and therefore the highest Oracle reclamation risk. A cron-based keepalive or a lightweight web service running on the instance will maintain enough visible activity to reduce that risk meaningfully.

---

## Conclusion

The pitfalls here aren't dealbreakers. They're solvable — but only if you know they exist before you start, not three days after your instance disappears.

The short list of what actually matters:

- Open UDP 41641 in *both* the Security List *and* iptables
- Enable `net.ipv4.ip_forward` and persist it across reboots
- Approve the exit node in the Tailscale admin panel
- Implement a keepalive strategy before Oracle's idle detection kicks in

Looking toward late 2026, Oracle has signaled tighter Always Free enforcement as their free tier user base has grown substantially. The reclamation risk around idle instances may get worse, not better. On the Tailscale side, releases from 1.60 onward added improved MTU negotiation — which directly reduces the packet fragmentation issues on Oracle's VCN that plagued earlier setups.

The configuration is worth doing. ARM64 performance on Ampere A1 handles sustained VPN traffic without strain, and the price-to-capability ratio for free infrastructure is genuinely hard to beat. Just don't skip the firewall steps, don't let your instance look abandoned, and go in with clear expectations about what "free" actually involves.

The r/Tailscale community has documented several keepalive approaches worth comparing — particularly if you're running this for anything close to production use.

## References

1. [r/Tailscale on Reddit: Is it possible to deploy Tailscale on a free Oracle VM instance?](https://www.reddit.com/r/Tailscale/comments/1n6ztpd/is_it_possible_to_deploy_tailscale_on_a_free/)
2. [How to expose Plex to share your library with others from behind CGNAT using Tailscale and a free Or](https://fullmetalbrackets.com/blog/expose-plex-tailscale-vps/)
3. [The "Invisible Tunnel": Host from Your Laptop via Oracle Cloud and Tailscale - DEV Community](https://dev.to/vimal/the-invisible-tunnel-host-from-your-laptop-via-oracle-cloud-and-tailscale-18b5)


---

*Photo by [Elliot Krueger](https://unsplash.com/@kruegerelliot) on [Unsplash](https://unsplash.com/photos/illuminated-exit-sign-in-dark-room-BaLEQXWHD7M)*
