---
title: "ChatGPT Share Links Used in LLMShare Malware Campaign"
date: 2026-06-14T21:01:00+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "chatgpt", "redirecting", "suspicious"]
description: "ChatGPT redirecting to suspicious sites isn't a glitch — it's LLMShare, a 5-stage attack chain exploiting real OpenAI URLs to deliver malware undetected."
image: "/images/20260614-chatgpt-redirecting-suspicious.webp"
faq:
  - question: "Why does ChatGPT redirect me to a download site I didn't expect?"
    answer: "A real chatgpt.com/s/ share link can be crafted to render attacker-controlled HTML that mimics a software download page. The redirect isn't a ChatGPT bug — attackers are abusing the platform's own sharing feature to host malicious content on a trusted domain."
  - question: "Is a chatgpt.com link actually safe to click?"
    answer: "Not automatically. The LLMShare campaign disclosed in May 2026 showed that real chatgpt.com/s/ URLs can serve pages that deliver credential-stealing malware for both Windows and macOS. The padlock and domain name give a false sense of security because the malicious content lives inside a legitimate share link."
  - question: "What malware gets dropped from these fake ChatGPT pages?"
    answer: "Windows users are targeted with an executable called Chat_GPT.exe, which only 9 out of 69 antivirus engines detected at the time of analysis. Mac users get Odyssey Stealer, a fork of AMOS that targets 12 Chromium browsers, 16 crypto wallets, and swaps out legitimate Ledger Live and Trezor apps with trojans."
  - question: "Does this same attack work on Claude or Grok too?"
    answer: "Yes — Push Security confirmed the identical pattern running on Claude Artifacts and shared Grok conversations at the same time as the ChatGPT campaign. This makes it a platform-wide problem affecting any AI tool that renders user-controlled HTML on a high-trust domain."
  - question: "How do URL filters keep missing this phishing technique?"
    answer: "Standard URL reputation filters flag suspicious domains, but the malicious link here is a real OpenAI domain — so it passes cleanly. The attacker-controlled redirect destination only appears after the user has already trusted and clicked the chatgpt.com share link, which is past the point most filters inspect."
---

Most people assume a `chatgpt.com` URL is safe. That assumption is exactly what attackers are exploiting right now.

In May 2026, Push Security disclosed the **LLMShare campaign** — a five-stage attack chain that turns ChatGPT's own content-sharing infrastructure into a malware delivery mechanism. No fake domains in the early stages. No obvious phishing indicators. Just a real OpenAI URL that leads, eventually, to credential-stealing software targeting both Windows and macOS. The question of ChatGPT redirecting to suspicious sites has a specific, technical answer — and it's more unsettling than most security alerts suggest.

This isn't a ChatGPT vulnerability in the traditional sense. OpenAI didn't ship broken code. What happened is that the platform's legitimate features — shareable conversation URLs, HTML/CSS rendering, a trusted domain — got combined in a way that creates a near-perfect phishing surface. The same pattern is already running on Claude, Grok, and a dozen other platforms.

**What's covered below:**
- How attackers weaponize legitimate `chatgpt.com/s/` share links
- The dual-platform malware payloads targeting Windows and macOS users
- Why standard defenses (URL filters, padlock indicators, ad verification) all miss this
- Concrete defensive controls that actually work

---

> **Key Takeaways**
> - The LLMShare campaign, disclosed by Push Security on May 29, 2026, abuses real `chatgpt.com/s/` URLs — not spoofed domains — to host malware distribution pages.
> - The macOS payload, Odyssey Stealer (a fork of AMOS), targets 12 Chromium browsers, 16 cryptocurrency wallets, and replaces legitimate Ledger Live and Trezor Suite apps with trojans.
> - The Windows executable `Chat_GPT.exe` was flagged by only 9 of 69 antivirus engines at analysis time, according to [Malwarebytes](https://www.malwarebytes.com/blog/threat-intel/2026/05/fake-chatgpt-download-site-infects-windows-and-mac-users-with-malware).
> - Push Security confirmed the same attack pattern running simultaneously on Claude Artifacts and shared Grok conversations — making this a platform-class problem, not a one-off incident.
> - The entire malicious infrastructure costs roughly $15/year for the attacker-controlled domain. The economics heavily favor the attackers.

---

## How AI Platforms Became Phishing Infrastructure

Malvertising campaigns impersonating software products aren't new. Attackers have targeted Zoom, 7-Zip, and VLC for years. But those campaigns always required a convincing fake domain — and domain reputation filters caught most of them.

AI platforms changed the equation. When ChatGPT launched content sharing via `chatgpt.com/s/` URLs, it created something security teams hadn't fully accounted for: a high-trust domain that renders attacker-controlled HTML and CSS without stripping markup. Users follow a link, see `chatgpt.com` in the address bar, see a padlock, and their threat model says "safe."

[According to Push Security's May 2026 disclosure](https://www.gblock.app/articles/chatgpt-share-links-llmshare-malware-push-security-may-2026), the attack chain runs in five stages: sponsored search ad → real `chatgpt.com/s/` URL → attacker-crafted "outage" page → redirect to `openew[.]app` → platform-specific malware installer. Every stage until that final redirect runs on infrastructure that security tools trust by default.

The `.app` TLD adds another layer of misdirection. It mandates HTTPS, so `openew[.]app` automatically displays the padlock that users associate with legitimate sites. Total attacker infrastructure cost: approximately **$15/year** for the domain. The macOS malware subscription (Odyssey Stealer, available as malware-as-a-service) runs around **$3,000/month** — but that gets amortized across every victim.

---

## The Attack in Detail

### Stage 1 — The Google Ad That Starts Everything

Attackers purchase Google Ads targeting search terms like "ChatGPT download." The ad points not to a fake OpenAI domain, but to a real `chatgpt.com/s/` URL. Ad network verification passes it. The domain is legitimate. Nothing flags.

[DigitalShield's analysis](https://www.escudodigital.com/en/technology/artificial-intelligence/cybercriminals-plant-malicious-links-in-chatgpt-responses-via-fake-websites.html) confirmed that ChatGPT renders the shared conversation's HTML and CSS without stripping markup. Attackers used this to build a pixel-perfect "service interruption" notice — complete with ChatGPT's visual chrome, code-viewing controls, and OpenAI branding. The fake message reads approximately: *"We're experiencing high traffic right now… Download our desktop app to continue."*

Clicking that download button redirects to `openew[.]app`.

### Stage 2 — The Dual-Platform Payload

`openew[.]app` serves different installers based on the visitor's operating system. Both are hostile.

[Malwarebytes documented both payloads in detail](https://www.malwarebytes.com/blog/threat-intel/2026/05/fake-chatgpt-download-site-infects-windows-and-mac-users-with-malware):

**Windows — `Chat_GPT.exe`**: Built with Inno Setup and the Electron framework to appear legitimate. Executes PowerShell with `-ExecutionPolicy Unrestricted -Command -`, meaning malicious instructions run entirely in memory — nothing writes to disk for scanners to find. Communicates with `188.137.246.189` via a `/laravel.php` endpoint and establishes persistence. Detection rate at analysis time: **9 out of 69 antivirus engines**.

**macOS — `ChatGpt.dmg`**: Delivers Odyssey Stealer, a fork of AMOS (Atomic Stealer, documented since 2023). Capabilities include:
- Credential harvesting from 12 Chromium-based browsers plus Firefox
- Telegram session extraction
- Scanning 16 cryptocurrency wallet directories
- Replacing legitimate Ledger Live and Trezor Suite applications with trojanized versions using captured `sudo` credentials

The macOS stealer costs roughly **12x more** than comparable Windows tools like Lumma (~$250/month). That premium signals deliberate targeting of a demographic the attacker considers worth it.

### Stage 3 — Why Standard Defenses Miss This

| Defense Layer | Does It Catch This? | Why It Fails |
|---|---|---|
| URL reputation filter | ❌ No | `chatgpt.com` is trusted; filter never checks share content |
| Browser HTTPS indicator | ❌ No | Both `chatgpt.com` and `openew[.]app` show padlocks |
| Google Ad verification | ❌ No | Ad destination is a real OpenAI URL |
| Antivirus (Windows) | ❌ Mostly | 9/69 engines flagged `Chat_GPT.exe` |
| Sandbox analysis | ❌ No | VM detection suppresses malicious behavior in analyst environments |
| DNS blocklist (openew[.]app) | ✅ Yes | Only reliable catch point before infection |

Every defense layer fails until the final redirect. The attacker-controlled chokepoint is `openew[.]app` — and only DNS/proxy-level blocking stops it before execution.

---

## This Is a Platform-Class Problem

ChatGPT isn't uniquely vulnerable. Push Security documented the same attack pattern running on two other platforms in 2026:

- **Claude Artifacts** hosting ClickFix lures
- **Shared Grok conversations** running social engineering scripts

Any platform combining three features carries equivalent exposure: a high-trust domain, user-generated HTML/CSS rendering, and shareable URLs. That list includes Notion, GitHub Pages, Google Sites, and Substack — platforms that security teams haven't traditionally monitored as phishing vectors.

AI products compound the risk in a specific way. Most users lack established download habits for these tools. Someone who has used Photoshop for ten years knows exactly where to get it. A user searching "ChatGPT download" for the first time has no baseline to compare against. That gap in learned behavior makes them significantly more susceptible to a convincing fake page — and this campaign is convincing.

---

## Defensive Controls That Actually Work

The core problem: this attack chain exploits trust that's legitimately earned. You can't un-trust `chatgpt.com`. So defenses need to focus on the one attacker-controlled point — the download domain.

**For enterprise security teams**: Block `openew[.]app` at DNS and proxy layers immediately. Flag any executable download where the HTTP referrer is `chatgpt.com` — legitimate OpenAI products don't distribute through share links. Apply browser isolation policies for externally sourced AI conversation URLs.

**For individual developers and power users**: Download ChatGPT exclusively from `openai.com` or official app stores (Mac App Store, Microsoft Store). If a ChatGPT page ever prompts a desktop download, treat it as an attack. Legitimate service interruptions don't require you to install anything.

**For security tool vendors**: The 9/69 detection rate on `Chat_GPT.exe` is a gap worth closing. In-memory PowerShell execution combined with Electron packaging and AI brand spoofing should become a detection signature category. The cloaking behavior — serving different content to analysis tools — is also detectable. Behavioral sandboxes that fingerprint VM-aware malware need updating for this payload class.

---

## What Comes Next

LLMShare proves that platform trust, not technical vulnerabilities, is the primary attack surface in 2026. The economics favor rapid rebranding — the same infrastructure can target any trending AI product with cosmetic changes. Standard perimeter defenses are structurally blind to this pattern until the final redirect.

**Near-term**: Expect similar campaigns targeting Gemini, Copilot, and any AI tool that achieves mainstream search volume. Infrastructure cost is negligible; only the malware subscription changes. OpenAI and other platforms will face pressure to add download-prompt detection within shared conversation rendering.

**Medium-term**: Platform providers will likely restrict HTML/CSS rendering in shared URLs or implement content security policies that block redirect-capable markup. Whether that happens before or after a high-profile breach is the open question.

**The one thing to act on now**: Train users that no legitimate AI platform will ever prompt a desktop download from a shared conversation link. That single behavior pattern identifies every variant of this attack, regardless of which platform it targets next.

---

*References: [Malwarebytes Threat Intelligence](https://www.malwarebytes.com/blog/threat-intel/2026/05/fake-chatgpt-download-site-infects-windows-and-mac-users-with-malware) | [DigitalShield / LLMShare Analysis](https://www.escudodigital.com/en/technology/artificial-intelligence/cybercriminals-plant-malicious-links-in-chatgpt-responses-via-fake-websites.html) | [Push Security via GBlock](https://www.gblock.app/articles/chatgpt-share-links-llmshare-malware-push-security-may-2026)*

## References

1. [Attackers Use Spoofed ChatGPT Site to Deliver Malware](https://blog.knowbe4.com/fake-chatgpt-download-site-delivers-malware)
2. [Cybercriminals plant malicious links in ChatGPT responses via fake websites | DigitalShield](https://www.escudodigital.com/en/technology/artificial-intelligence/cybercriminals-plant-malicious-links-in-chatgpt-responses-via-fake-websites.html)
3. [Attackers Abuse Shared Content for ChatGPT Phishing Campaign - Infosecurity Magazine](https://www.infosecurity-magazine.com/news/attackers-shared-content-chatgpt/)


---

*Photo by [Levart_Photographer](https://unsplash.com/@siva_photography) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it-drwpcjkvxuU)*
