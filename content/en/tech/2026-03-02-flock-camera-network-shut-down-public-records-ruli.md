---
title: "Flock Camera Network Shut Down Over Public Records Ruling"
date: 2026-03-02T19:54:19+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-security", "flock", "camera", "network", "shut"]
description: "Flock camera network shut down after landmark public records ruling exposes surveillance data. Learn what this means for privacy rights."
image: "/images/20260302-flock-camera-network-shut-down.webp"
technologies: ["AWS", "Go"]
faq:
  - question: "why did Everett Washington shut down its Flock camera network"
    answer: "Everett, Washington shut down its Flock Safety license plate reader network in February 2026 after a public records ruling exposed a compliance gap between the city and its surveillance vendor. A public records request for camera footage and metadata revealed that Flock Safety stored data on its own private infrastructure, making it difficult for the city to fulfill its legal obligations under Washington's Public Records Act. This Flock camera network shut down public records ruling surveillance case is considered the first major instance of a public records dispute directly triggering a municipal camera network suspension."
  - question: "can a public records request force a city to shut down surveillance cameras"
    answer: "Yes, as demonstrated in Everett, Washington in February 2026, a public records dispute can force a city to pause its entire surveillance camera network. When cities contract surveillance infrastructure to private vendors like Flock Safety, public records obligations still follow the data regardless of vendor contract terms, creating a legal liability for the municipality. This means cities — not vendors — are legally responsible when data cannot be produced in a compliant format."
  - question: "what is Flock Safety and how many cities use it"
    answer: "Flock Safety is an AI-powered license plate reader (LPR) company founded in 2017 that provides automated camera networks to neighborhoods and police departments across the United States. By 2025, Flock Safety operated in over 5,000 communities, ranging from small homeowners associations to major municipal police departments. The Flock camera network shut down public records ruling surveillance case in Everett, Washington has raised concerns that similar legal challenges could affect thousands of active Flock deployments nationwide."
  - question: "are license plate reader networks legal under public records laws"
    answer: "License plate reader networks like Flock Safety operate legally in most U.S. jurisdictions, but they face growing legal scrutiny under state public records laws rather than traditional privacy statutes. The core issue is that private vendors store surveillance data on their own infrastructure, while public records obligations require cities to produce that data upon request — regardless of vendor contract limitations. Legal firms like Gibbs Mura LLP are actively pursuing class action litigation targeting Flock Safety's data practices, signaling an accelerating legal landscape around LPR networks in 2026."
  - question: "what happens to surveillance camera data when a city uses a private vendor like Flock Safety"
    answer: "When a city contracts with a private vendor like Flock Safety, the surveillance data is typically stored on the vendor's own infrastructure rather than city-controlled servers. Flock Safety contracts generally set data retention periods of around 30 days for standard footage, but these vendor terms do not override a city's obligations under state public records laws. This structural conflict between private vendor architecture and municipal legal accountability was the central cause of the Everett, Washington Flock camera network shutdown in February 2026."
---

A court ruling forced the city of Everett, Washington to pause its entire Flock Safety license plate reader network in February 2026. Not a hack. Not budget cuts. A public records dispute.

That's the kind of precedent that keeps municipal IT departments and civil liberties attorneys equally awake at night. The story isn't just local news — it's a signal about where automated surveillance law is heading, and how fast.

Cities are deploying AI-powered surveillance infrastructure faster than legal frameworks can govern it. Everett's pause is the first major case where a public records obligation directly triggered a network shutdown. It won't be the last.

> **Key Takeaways**
> - Everett, Washington temporarily shut down its Flock Safety LPR camera network in February 2026 after a public records ruling exposed data access gaps between the city and its vendor.
> - Flock Safety operates in over 5,000 communities across the U.S. — the legal logic from Everett could apply to thousands of active deployments overnight.
> - Public records laws, not privacy statutes, are emerging as the most immediate legal lever against automated license plate reader networks.
> - Municipal governments face a structural conflict: they contract surveillance infrastructure to private vendors, but public records obligations follow the data, not the vendor's terms.
> - Litigation from firms like Gibbs Mura LLP targeting Flock Safety's data practices signals that the class action landscape around LPR networks is accelerating in 2026.

---

## Background: How Everett Got Here

Flock Safety launched in 2017 with a straightforward pitch: give neighborhoods and police departments affordable, AI-powered license plate readers that automatically flag stolen vehicles and wanted suspects. The hardware is cheap. The software does the heavy lifting. By 2025, Flock operated in over 5,000 communities — contracts spanning small HOAs to major municipal police departments.

Everett was one of those cities. The network ran quietly until a public records request — centered on access to camera footage and associated metadata — created a legal dispute the city couldn't resolve without pausing operations. According to HeraldNet's February 2026 reporting, Everett temporarily suspended the entire Flock network while officials sorted out their compliance obligations.

The underlying problem is structural. Flock Safety stores data on its own infrastructure. Cities sign contracts governing retention periods — typically 30 days for standard footage — but public records obligations under state law don't bend to vendor contract terms. Washington's Public Records Act is notably strong. When a requester demands records, the city is responsible. If the vendor's system can't produce them in a compliant format, or if the contract limits city access, that's the city's legal problem.

That gap between vendor architecture and municipal legal obligation caused the shutdown. And it's not unique to Everett.

Gibbs Mura LLP has an active class action investigation targeting Flock Safety's data collection practices, citing concerns about how plate reader data is stored, shared with third parties, and retained beyond stated windows. The pressure is now coming from multiple directions simultaneously.

---

## The Public Records Angle Nobody Anticipated

Most surveillance policy debates focus on Fourth Amendment concerns — whether warrantless collection violates constitutional protections. Those cases move slowly through federal courts.

Public records law moves faster. State-level open records statutes are immediate, enforceable, and don't require proving constitutional harm. Washington's Public Records Act requires agencies to produce documents on request, with limited exceptions. When a city's surveillance data lives inside a private vendor's cloud, producing that data gets complicated fast.

Everett's pause happened because the city couldn't confidently demonstrate compliance. That's a direct operational consequence, not a theoretical legal risk. The shutdown lasted days, not weeks — but the signal is loud. A single records dispute can take an entire camera network offline.

---

## Flock's Data Architecture Creates Shared Liability

Flock Safety's model is SaaS-style infrastructure. Cities don't run servers. They access a dashboard. Plate reads, alerts, and associated metadata flow into Flock's cloud and stay there under contract-defined retention rules.

This creates a liability split that legal frameworks aren't designed to handle cleanly. The city is the data controller under most state interpretations — it commissioned the collection. But the data processor, Flock, holds actual custody. When records requests arrive, that split becomes a compliance gap.

Compare this to body camera vendors like Axon, which offers local storage options alongside cloud, giving agencies more direct data custody. The trade-off is cost and infrastructure complexity. But agencies maintain a cleaner records compliance posture. That trade-off is looking more attractive after Everett.

This approach can fail — and does fail — when cities prioritize deployment speed over governance architecture. Signing a vendor contract isn't the same as solving a records obligation. The two need to align before cameras go live, not after a court order forces the issue.

---

## Jurisdiction-by-Jurisdiction: The Regulatory Gap

How different regulatory environments handle this matters enormously right now.

| Dimension | Washington State | California | Texas | Federal Level |
|---|---|---|---|---|
| Public Records Strength | Very strong (PRA) | Strong (CPRA) | Moderate | No equivalent statute |
| LPR-Specific Regulation | Emerging case law | SB 210 data limits | Minimal | None active |
| Vendor Liability Exposure | Shared with city | Shifting toward vendor | City-primary | Undefined |
| Shutdown Risk Level | **High** (Everett precedent) | High | Lower | N/A |
| Class Action Activity | Active (Gibbs Mura) | Active | Limited | Growing |

California's Consumer Privacy Rights Act already imposes data minimization rules that affect how long LPR data can be kept. If California cities face similar records disputes, plaintiffs have even more statutory tools available. Texas sits in a lighter-touch regulatory zone for now — but that's a gap, not a safe harbor.

The compliance pressure is highest in states with strong open records traditions: most of the Northeast, the Pacific Northwest, and increasingly the Midwest. That covers a significant share of Flock's 5,000-plus active deployments.

---

## The Class Action Loop

Gibbs Mura's investigation into Flock Safety follows a pattern seen with other surveillance tech firms. The claims center on data collected beyond consent, retention exceeding stated limits, and potential third-party data sharing. Class actions in this space typically take 18 to 36 months to resolve — but they force discovery, which itself generates more public records exposure.

The dynamic is self-reinforcing. Litigation creates records requests. Records requests expose compliance gaps. Compliance gaps create operational shutdowns. Shutdowns generate press. Press generates more requests.

Cities caught in that loop don't get to opt out mid-cycle.

---

## Practical Implications

**Engineers building municipal surveillance integrations** need to understand that data custody architecture isn't just a vendor decision anymore. If you're building integrations with LPR systems or any surveillance infrastructure, assume public records law follows the data, not the contract terms. Design accordingly.

**City IT and legal teams**: Everett is a direct operating precedent. Review your Flock contracts — or equivalent vendor agreements — now. The specific question: can you pull all requested data independently, without vendor assistance? If the answer is "it depends," that's a compliance gap that needs closing before a records request forces the issue.

**Civil liberties advocates and researchers**: Public records law is proving more immediately effective than constitutional litigation for surfacing surveillance data. Targeted records requests are accelerating as a strategy precisely because they work faster than federal court timelines.

### Actions Worth Taking Now

Short-term (next one to three months): Audit data custody terms in existing LPR vendor contracts. Identify which records categories fall under state open records obligations. Run a tabletop exercise — what happens operationally if a records request arrives today?

Longer-term (next six to twelve months): Push for hybrid storage options that keep copies of flagged-plate data under direct city custody. Engage legal counsel on vendor contract amendments before renewals. Track state-level legislation; both California and Washington are seeing LPR-specific bills in 2026 legislative sessions.

**The genuine opportunity here**: cities that get data governance right now carry a real operational advantage. Clean public records compliance means fewer disruptions and lower litigation exposure. This is a solvable engineering and contracting problem — not a fundamental objection to surveillance technology itself.

**The real challenge**: Flock Safety's business model depends on centralized cloud infrastructure. Meaningful architecture changes affect their margins and their pitch. Cities pushing for local data custody may face contract friction or higher pricing tiers. That tension isn't going away.

---

## What Comes Next

The Everett shutdown is a preview, not an anomaly. Public records laws are outpacing constitutional litigation as the primary legal check on surveillance networks. Vendor-controlled data architectures create compliance gaps that cities can't simply contract their way out of. And class action litigation is accelerating the pace of both disclosure and operational disruption.

Watch Washington State's legislature for clarifying rules on vendor data custody. California's privacy enforcement arm has LPR data on its 2026 audit calendar. And Flock Safety's next contract cycle — covering thousands of municipalities — will face scrutiny from city attorneys who've now seen Everett's situation play out in real time.

Surveillance infrastructure deployed without clear data custody and public records compliance built in is a liability, not an asset. Engineers and administrators who treat governance as a legal afterthought will be managing their own version of Everett soon enough.

The question worth asking today: what does your city's vendor contract actually say about who controls the data?

---

*Sources: HeraldNet (February 25, 2026), Gibbs Mura LLP class action investigation documentation (classlawgroup.com). All regulatory comparisons reflect publicly available state statute text as of March 2026.*



## Related Posts


- [TikTok Refuses End-to-End Encryption: Child Safety Excuse?](/en/tech/tiktok-refuses-endtoend-encryption-child-safety-ex/)
- [Motorola GrapheneOS Partnership Brings Privacy to Android Security](/en/tech/motorola-grapheneos-partnership-privacy-android-se/)
- [AirSnitch Wi-Fi Client Isolation Bypass Attack 2026 Explained](/en/tech/airsnitch-wifi-client-isolation-bypass-attack-2026/)
- [Cybersecurity in 2026: Developer Threats, Vulnerabilities, and Defenses](/en/tech/cybersecurity-2026-developer-guide/)
- [Windows 11 Notepad Markdown RCE Flaw: CVE-2026-20841](/en/tech/windows-11-notepad-markdown-support-remote-code-ex/)

## References

1. [Flock Safety License Plate Reader Cameras Lawsuit – Gibbs Mura, A Law Group](https://www.classlawgroup.com/flock-safety-license-plate-reader-cameras-lawsuit)
2. [Everett temporarily pauses Flock camera network | HeraldNet.com](https://www.heraldnet.com/2026/02/25/everett-temporarily-pauses-flock-camera-network/)


---

*Photo by [Sajad Nori](https://unsplash.com/@sajadnori) on [Unsplash](https://unsplash.com/photos/gray-and-white-bird-on-black-speaker-1SjWqBMjOmM)*
