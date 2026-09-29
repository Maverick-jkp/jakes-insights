---
title: "Self-Hosted Smart Home Without YAML: Is Gladys Assistant 5 Beginner-Friendly?"
date: 2026-09-30T01:28:44+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-web", "self-hosted", "smart", "home"]
description: "Self-hosted smart home without YAML? Gladys Assistant 5 takes on Home Assistant's 70,000+ installs with a beginner-first approach."
image: "/images/20260930-self-hosted-smart-home-without.webp"
faq:
  - question: "Does Gladys actually work without touching any config files?"
    answer: "Yes — Gladys Assistant 5 is designed from the ground up to use a browser-based UI exclusively, with zero YAML required at any stage. You set up automations, integrations, and dashboards entirely through point-and-click interfaces. It's one of the few self-hosted platforms where that promise holds end-to-end, not just for basic features."
  - question: "How much RAM does a local smart home hub realistically need?"
    answer: "Gladys Assistant 5 runs on 150–400MB of RAM, which makes it comfortable on a Raspberry Pi 4 or even older hardware. For comparison, Home Assistant typically consumes roughly double that once a few integrations are loaded. If you're running other services on the same machine, that difference adds up fast."
  - question: "Is Gladys good enough if you only have around 30 devices?"
    answer: "For a typical starter setup — lights, sensors, a thermostat, maybe some plugs — Gladys's 30-odd integrations will likely cover everything you need. Where it starts to hurt is niche or newer devices that Home Assistant already supports but Gladys hasn't added yet. It's worth checking the integration list against your specific hardware before committing."
  - question: "What are the real risks of a solo-developer open source project long term?"
    answer: "The honest risk is bus-factor: Gladys is maintained primarily by one developer, Pierre-Gilles Leymarie, which means updates depend heavily on his continued involvement. The community is also small and largely French-speaking, so English troubleshooting resources are thinner than you'd find with Home Assistant. It's a real consideration if you're planning a setup you'd hand off or maintain for years."
  - question: "Can a non-technical person set this up on a weekend realistically?"
    answer: "For someone comfortable installing software and navigating a router config page, yes — a basic Gladys setup is genuinely achievable in a few hours, not a lost weekend. The browser UI handles what most platforms would push into configuration files. That said, anything beyond supported integrations will require digging into workarounds, which is where the beginner-friendly framing starts to have limits."
---

Most home automation platforms force you into one of two choices: surrender your data to a cloud service, or spend weekends buried in YAML files debugging indentation errors. Gladys Assistant 5 challenges that assumption directly — and the numbers behind it deserve a hard look.

The self-hosted smart home space has fractured sharply in 2026. Home Assistant commands the conversation with 70,000+ GitHub stars and hundreds of thousands of forum members. But a quieter segment of the market is asking a different question: what if you want local control *without* becoming a configuration file expert? That's exactly the gap Gladys targets. Whether a self-hosted smart home without YAML is truly achievable — and whether Gladys Assistant 5 is beginner-friendly enough to deliver on that promise — has real stakes for any tech professional considering the leap.

This article examines the architecture, trade-offs, and real-world implications of choosing Gladys over the dominant alternatives.

> **Key Takeaways**
> - Gladys Assistant 5 runs entirely locally with command response times under 10ms, making it one of the fastest locally-operated home automation platforms available in 2026.
> - The platform supports approximately 30 integrations versus Home Assistant's 2,000+, but consumes only 150–400MB RAM — roughly half the resource footprint of its main competitor.
> - Setup costs run €120–€250 for a complete starter kit, with documented electricity savings of 15–28% in the first year, achieving ROI in under 18 months.
> - Gladys requires zero YAML configuration by design, deploying entirely through a browser-based UI — a meaningful distinction for non-specialist users.
> - The platform's small but active community (primarily French-speaking) and solo-developer maintenance model represent real long-term risks worth weighing.

---

## Why "No YAML" Is a Real Product Decision

Home automation's complexity problem isn't new. But it's gotten harder to ignore.

Home Assistant has evolved into an extraordinarily capable platform — its 2,000+ integrations cover nearly every smart device category imaginable. The trade-off is a learning curve that now resembles a cliff face for newcomers. Between YAML automations, Node-RED flows, template syntax, and the Lovelace dashboard editor, a first-time user can easily spend 20+ hours before a single light turns on reliably.

The no-YAML self-hosting question became relevant as the self-hosting movement broadened from hobbyist developers to privacy-conscious professionals who want control without complexity.

Gladys Assistant started as a French open-source project by solo developer Pierre-Gilles Leymarie. It's grown steadily to roughly 2,500 GitHub stars — a fraction of Home Assistant's footprint, but the project has maintained a consistent design philosophy: no configuration files, no cloud dependency, no YAML. Period.

The timing matters. In 2026, EU privacy regulations tightened further around smart home data. Cloud-connected platforms like Google Home and Amazon Alexa face increasing scrutiny over data retention. According to [WikiOT's 2026 technical summary](https://wikiot.fr/en/domotique/gladys-assistant/gladys-assistant-guide-complet-2026), Gladys processes all commands locally with full-pipeline latency under 15ms — a specification that cloud-dependent platforms structurally can't match.

---

## Main Analysis

### The No-YAML Architecture: What It Actually Means

Gladys Assistant 5 handles automation entirely through its browser-based interface. No configuration file format to learn. Scenes, schedules, and triggers are set through point-and-click flows — closer to Apple's Shortcuts app than to Home Assistant's YAML-driven system.

The technical foundation is Node.js with Docker containerization. According to [Gladys's official documentation](https://gladysassistant.com/docs/), installation paths exist for Mini-PC (recommended), Synology NAS, Unraid NAS, and Raspberry Pi — all requiring Docker as the only real prerequisite. Post-install configuration happens in a browser: create an admin account, name your home, start adding devices.

That's genuinely simpler than most alternatives. A Docker-capable Linux machine with 2GB RAM and 2 virtual CPU cores handles roughly 100 connected devices and 20 complex automations, per [WikiOT's hardware specs](https://wikiot.fr/en/domotique/gladys-assistant/gladys-assistant-guide-complet-2026). No Python environment management. No config.yaml. No restarting services after every edit.

The beginner-friendliness question has a concrete answer at this layer: yes. If you can run a Docker container, you can install Gladys.

### Integration Depth: The Real Trade-Off

The platform's beginner-friendly design comes with a hard constraint. Gladys supports approximately 30 integrations. Home Assistant supports 2,000+.

According to [selfhosting.sh's comparison](https://selfhosting.sh/compare/home-assistant-vs-gladys/), Gladys works well within specific protocol boundaries: Zigbee (via Zigbee2MQTT), Z-Wave, MQTT, Philips Hue, and Sonos. Step outside those boundaries — say, you want to connect a Bosch dishwasher, a Velux smart skylight, or an older Insteon device — and you'll hit a wall.

Zigbee2MQTT integration is worth highlighting specifically. According to [WikiOT](https://wikiot.fr/en/domotique/gladys-assistant/gladys-assistant-guide-complet-2026), Zigbee 3.0 covers 4,000+ certified compatible devices with mesh topology spanning 150m², 24–36 month battery life on sensors, and mesh reactivity under 12ms. If your device ecosystem fits within Zigbee or MQTT, the 30-integration limit feels less like a wall and more like a curated list.

The practical ceiling for beginner-friendly self-hosted setups using Gladys: smart lighting, temperature sensors, motion sensors, smart plugs, and basic HVAC control. That covers 80% of what most first-time home automation users actually want.

### Performance and Resource Footprint

The numbers here favor Gladys significantly over Home Assistant for constrained hardware.

| Metric | Gladys Assistant | Home Assistant |
|---|---|---|
| RAM Usage | 150–400MB | 300–800MB |
| Docker Image Size | ~500MB | ~1GB |
| Startup Time | 10–20 seconds | 30–60 seconds |
| Minimum Hardware | Raspberry Pi 3 | Raspberry Pi 4 |
| Command Latency | <10ms (local) | Variable |
| Voice Assistant | None | Local Assist + cloud |
| Mobile App | Progressive Web App | Native iOS/Android |
| API Support | REST only | REST + WebSocket |
| Community Size | ~2,500 GitHub stars | 70,000+ GitHub stars |
| Configuration Format | Browser UI only | YAML + UI |

*Sources: [selfhosting.sh](https://selfhosting.sh/compare/home-assistant-vs-gladys/), [WikiOT 2026](https://wikiot.fr/en/domotique/gladys-assistant/gladys-assistant-guide-complet-2026)*

These specs tell a clear story. Gladys runs leaner, starts faster, and responds quicker at the command level. Server power consumption sits under 5 watts continuous, which matters for always-on deployments. On a refurbished mini-PC with 8GB RAM — a Beelink Mini S13 or equivalent Intel NUC — Gladys barely registers in task manager.

Home Assistant's broader capability comes at a real resource cost. For a Raspberry Pi 3 owner, or anyone running multiple Docker services on a small NAS, the memory delta between 150MB and 500MB is the difference between a stable system and constant swap usage.

### Cost Reality Check

[WikiOT's 2026 data](https://wikiot.fr/en/domotique/gladys-assistant/gladys-assistant-guide-complet-2026) puts the entry cost at €120–€250 for a complete starter kit: mini-PC or Raspberry Pi, USB Zigbee coordinator, and five sensors. [Gladys's own documentation](https://gladysassistant.com/docs/) breaks down specific device costs — a Zigbee temperature/humidity sensor at $19.99, a four-pack of Zigbee smart plugs with energy monitoring at $16.99, an IKEA TRÅDFRI bulb at $13.99.

Documented first-year electricity savings run 15–28%, with connected thermostats (€45–€130) delivering 15–22% heating savings specifically. ROI lands under 18 months by WikiOT's calculation. That's a defensible number for a privacy-first local setup with zero ongoing subscription costs.

---

## Practical Implications: Who Should Actually Deploy This

The core challenge with self-hosted home automation isn't capability — it's the gap between what people want to control and what they're willing to learn to control it.

**Scenario 1: The privacy-conscious developer on a mixed NAS setup.** Running Gladys alongside Nextcloud and Jellyfin on a Synology NAS with 8GB RAM is viable. Gladys's 150–400MB footprint doesn't crowd out other services. Start with a Zigbee coordinator USB stick and five sensors. Learn the protocol boundary before committing to more hardware.

**Scenario 2: The tech professional with a mixed-brand device ecosystem.** If you already own Nest thermostats, Ring cameras, and Samsung SmartThings sensors, Gladys isn't the right answer. The 30-integration ceiling will frustrate you within a month. Home Assistant's 2,000 integrations exist precisely for mixed-ecosystem situations. According to [selfhosting.sh](https://selfhosting.sh/compare/home-assistant-vs-gladys/), Gladys supports basic RTSP camera streams only — no ONVIF, no motion detection pipelines. That's a meaningful gap for anyone with existing security hardware.

**Scenario 3: The non-technical household member who needs to maintain the system.** This is where Gladys's browser-UI-only approach becomes a genuine advantage. No YAML means no breakage from a misplaced space character. Automations created in the UI stay in the UI. If something breaks, there's no config file archaeology required. The tradeoff: the primarily French-speaking community and solo-developer maintenance model mean support response times for English-language edge cases can be slow.

**What to watch:** Leymarie has signaled new integration work for 2026–2027. If Gladys expands its integration count past 50–60 while preserving the no-YAML design, it becomes a much stronger general recommendation. The GitHub repository's integration pull requests are the leading signal worth tracking.

---

## Conclusion & Future Outlook

Gladys Assistant 5 answers the self-hosted smart home without YAML question with a clear yes — but within a defined scope. The platform genuinely delivers beginner-friendly local automation within the Zigbee/MQTT/Hue/Sonos ecosystem. Its resource efficiency, sub-10ms local latency, and browser-only configuration make it the most accessible entry point in the self-hosted home automation space as of late 2026.

**Key findings:**
- Gladys is faster to deploy and cheaper to run than Home Assistant on constrained hardware.
- The 30-integration ceiling is a real constraint, not a minor footnote.
- Documented €120–€250 entry cost with 15–28% energy savings in year one makes the economics credible.
- Solo-developer maintenance and a small community are the platform's most significant long-term risks.

Near-term, expect Gladys to add 5–10 integrations over the next six months based on current GitHub activity patterns. That won't close the gap with Home Assistant, but it'll widen the addressable device list meaningfully. If Leymarie brings on additional core maintainers or the project attracts a broader contributor base, the community risk diminishes substantially — and that's the signal worth tracking above everything else.

The bottom line: if your device wishlist fits within Zigbee and MQTT, and you want local control without becoming a YAML expert, Gladys Assistant 5 is the most honest beginner-friendly option available. The question worth asking before you buy any hardware: does your current device ecosystem fit within those protocol boundaries?

## References

1. [Self-Hosting | XDA](https://www.xda-developers.com/self-hosting/)
2. [Best Home Assistant Add-Ons 2026: Top 10 Picks](https://smarthomeassistant.co.uk/articles/home-automation/home-assistant-best-addons)
3. [Home Assistant für Einsteiger: Smart Home ohne Cloud - Blog.Freeware-base.de](https://blog.freeware-base.de/home-assistant-fuer-einsteiger/)


---

*Photo by [Jakub Żerdzicki](https://unsplash.com/@jakubzerdzicki) on [Unsplash](https://unsplash.com/photos/a-cell-phone-is-connected-to-a-light-switch-We56jns_zLE)*
