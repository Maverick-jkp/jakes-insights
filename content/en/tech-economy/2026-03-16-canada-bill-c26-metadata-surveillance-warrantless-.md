---
title: "Canada Bill C-22 Metadata Surveillance and Developer Privacy Risk"
date: 2026-03-16T20:11:19+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-data", "canada", "bill", "c-26", "Go"]
description: "Bill C-22 replaces C-26 with new surveillance powers. Canadian developers face real metadata and warrantless access risks worth understanding now."
image: "/images/20260316-canada-bill-c26-metadata-surve.webp"
technologies: ["Go"]
faq:
  - question: "What is Canada Bill C-26 metadata surveillance warrantless access developer privacy risk?"
    answer: "Canada Bill C-26 was a 2022 cybersecurity bill that embedded surveillance provisions allowing warrantless access to user metadata, creating significant privacy risks for developers and service providers. Though C-26 never passed, its warrantless access provisions migrated into Bill C-22 (Part 2), which is now moving through Parliament and poses the same legal exposure for anyone building software or storing data under Canadian jurisdiction."
  - question: "Can Canadian police access user data without a warrant under Bill C-22?"
    answer: "Yes, Bill C-22 Part 2 allows law enforcement to obtain basic subscriber information — including name, address, email, and IP address — from telecom and service providers without a court order. This approach has previously been struck down by the Supreme Court of Canada in R v Spencer (2014), raising serious constitutional concerns about the new legislation."
  - question: "How does Canada Bill C-26 metadata surveillance warrantless access developer privacy risk affect SaaS developers?"
    answer: "Developers running SaaS products or APIs on Canadian infrastructure can receive government compliance demands for user data with no judicial oversight and limited requirements to notify affected users. This means user data — including IP addresses and subscriber details — could be disclosed to law enforcement without a court order and potentially without the user ever knowing."
  - question: "What are mandatory backdoors in Canadian telecom legislation?"
    answer: "Bill C-22 requires telecom operators and service providers to maintain built-in technical interception capabilities, effectively mandating backdoor infrastructure that enables government surveillance. Security engineers widely regard such mandatory backdoors as systemic vulnerabilities because any access point built for government use can potentially be exploited by malicious actors as well."
  - question: "What happened to Bill C-26 in Canada?"
    answer: "Bill C-26 was tabled in 2022 but never passed, facing opposition from the Canadian Civil Liberties Association, Privacy Commissioner Philippe Dufresne, and constitutional critics over its broad ministerial powers and surveillance provisions. In March 2026, the government introduced Bill C-22, which effectively carries forward C-26's controversial warrantless metadata access provisions under a restructured two-part framework."
aliases:
  - "/tech/2026-03-16-canada-bill-c26-metadata-surveillance-warrantless-/"

---

Canadian lawmakers just handed security agencies a new toolkit. Bill C-26 is dead. Bill C-22 is replacing it — and the privacy tradeoffs buried inside it deserve serious scrutiny from anyone building software, running infrastructure, or storing user data under Canadian jurisdiction.

This isn't abstract policy. The conversation around Canadian metadata surveillance, warrantless access, and developer privacy risk is now live, because the legislation is moving. And some of the most alarming provisions from C-26 didn't disappear — they migrated.

> **Key Takeaways**
> - Bill C-22 (Part 2) replaces Bill C-26 but retains warrantless metadata access provisions that expose Canadian developers and their users to government disclosure demands without judicial oversight.
> - The legislation requires telecom operators and service providers to maintain technical interception capabilities — mandatory backdoor infrastructure that security engineers widely regard as a systemic vulnerability.
> - University of Ottawa law professor Michael Geist (March 2026) has noted that the bill's subscriber data access provisions allow law enforcement to obtain name, address, and IP address data without a warrant, continuing a pattern the Supreme Court of Canada struck down in *R v Spencer* (2014).
> - Developers building SaaS products or APIs on Canadian infrastructure face concrete legal exposure: compliance demands could arrive with no court order, and the bill offers limited notification requirements to affected users.

---

## From C-26 to C-22 — What Didn't Change

Canada's "lawful access" legislation has a long and contentious history. The original push dates back to the early 2000s, when security agencies lobbied for mandatory interception capabilities inside telecom networks. Parliament shelved multiple versions over two decades because of public backlash and constitutional concerns.

Bill C-26 was the most recent attempt — tabled in 2022 under the Trudeau government. It focused on cybersecurity obligations for critical infrastructure operators. But it also embedded surveillance provisions that critics flagged immediately. The Canadian Civil Liberties Association and Privacy Commissioner Philippe Dufresne both raised concerns about the bill's broad ministerial powers and inadequate oversight.

C-26 never passed. In March 2026, the government introduced Bill C-22, which splits the mandate into two parts. Part 1 addresses critical infrastructure cybersecurity — largely uncontroversial. Part 2 is where the metadata surveillance and warrantless access problem resurfaces directly.

According to Public Safety Canada's March 2026 backgrounder, Part 2 of C-22 is specifically designed to provide law enforcement with "timely access to basic subscriber information" — meaning name, address, email, and IP address — from telecommunications providers. The stated goal is modernizing lawful interception for today's digital environment.

Michael Geist, Canada Research Chair in Internet and E-Commerce Law at the University of Ottawa, published a detailed breakdown on March 13, 2026, noting that while the bill removes some of the most egregious C-26 provisions, it retains warrantless access to subscriber data and introduces mandatory backdoor capability requirements that could affect a wide range of service providers well beyond traditional telecoms.

---

## Warrantless Access: The Core Legal Problem

The Supreme Court of Canada was clear in *R v Spencer* (2014): obtaining subscriber information tied to an IP address constitutes a search under Section 8 of the *Charter of Rights and Freedoms*. Law enforcement needs a warrant. The ruling forced a rollback of informal RCMP and CSIS data requests to ISPs.

Bill C-22 Part 2 attempts to thread a needle. It doesn't fully restore the pre-*Spencer* regime, but it creates a carve-out for "basic subscriber information" that critics argue is broad enough to expose significant personal data without judicial authorization. An IP address combined with a name and timestamp isn't basic. It's identity.

For developers, this matters directly. If your application logs IP addresses — and most do, by default — you may be operating infrastructure that becomes a disclosure target. No court order required. No user notification mandated. Just a government request to the underlying telecom or hosting provider.

## The Backdoor Mandate: Systemic Infrastructure Risk

Part 2 also requires designated operators to maintain interception capabilities. This is the technical backdoor problem security engineers have warned about for decades.

The argument against backdoors isn't ideological. It's architectural. A system designed to allow government access can't distinguish between a legitimate law enforcement request and a malicious actor who has discovered — or stolen — the access mechanism. The 2024 Salt Typhoon breach, where Chinese state actors accessed U.S. carrier lawful interception systems according to the U.S. Cybersecurity and Infrastructure Security Agency, demonstrates the real-world cost of mandated interception infrastructure. That breach wasn't theoretical. Attackers walked straight through a door that was built to stay open.

The developer privacy risk becomes concrete the moment a cloud provider or CDN operating under Canadian law is designated under C-22. Your application traffic could route through infrastructure with built-in interception capabilities you didn't architect and can't audit.

## Scope Ambiguity: Who's Actually Covered?

The bill's definition of covered entities is broad. Traditional ISPs are obviously included. But the language in C-22 Part 2 — following the *Telecommunications Act* definition — could extend to VoIP providers, messaging platforms, and potentially API-layer services that transmit communications data.

This scope ambiguity is a genuine risk because compliance obligations may arrive before legal clarity does. A startup operating a communications-adjacent SaaS product in Canada might discover it's a designated provider through a government notice, not a published regulatory list.

## How Canada Compares Internationally

| Criteria | Canada C-22 Part 2 | UK Investigatory Powers Act (2016) | EU e-Privacy Directive |
|---|---|---|---|
| Warrant required for subscriber data | No (basic info exempt) | Yes for content; No for metadata in some cases | Generally yes, with exceptions |
| Backdoor/interception mandate | Yes | Yes (Technical Capability Notices) | No mandatory backdoor |
| Independent judicial oversight | Limited | Investigatory Powers Commissioner | National data protection authorities |
| Provider notification to users | Not required | Prohibited (gag orders) | Required in some cases |
| Scope of covered entities | Broad (Telecom Act definition) | Broad (CSPs) | Narrower (electronic comms) |
| Constitutional challenge history | *R v Spencer* (2014) | *Big Brother Watch v UK* (ECtHR, 2021) | *Digital Rights Ireland* (CJEU, 2014) |

The pattern is consistent across jurisdictions: mandated interception infrastructure without strong judicial oversight creates both civil liberties exposure and security vulnerabilities. Canada's C-22 sits closer to the UK model than the EU model — and the UK's framework has faced sustained legal challenges at the European Court of Human Rights.

---

## Practical Implications for Engineering Teams

The immediate action is a data audit. Map what subscriber-adjacent data your application collects — IP logs, session identifiers, account metadata — and understand which layer of your infrastructure stack might be subject to C-22 Part 2 obligations. If you're using a Canadian cloud region or a Canadian CDN provider, that provider may receive disclosure demands you'll never see.

Three scenarios worth thinking through:

**SaaS product with Canadian users.** Your application stores IP addresses at login. Your hosting provider is designated under C-22. Law enforcement requests that data without a warrant. You're not notified. Your privacy policy almost certainly promises more protection than this outcome delivers. That's a legal and reputational gap worth closing now — either through infrastructure decisions or updated disclosures.

**API platform transmitting communications data.** Your service might fall under the broad "telecommunications service provider" definition. Getting designated triggers interception capability obligations. The cost and security implications of building and maintaining that infrastructure aren't trivial, and they may arrive with limited lead time.

**Open-source tool deployed by Canadian operators.** You're not directly subject to C-22, but your downstream operators are. If your tool doesn't support the audit logging or access control mechanisms that compliance demands, you're creating friction for your users in a regulated market.

This approach can also fail when legal definitions lag technical reality. The *Telecommunications Act* definitions weren't written with modern API architecture in mind. Regulatory guidance interpreting those definitions may not arrive until well after the bill passes — which means developers face a compliance gap with no clear answers.

**What to watch:** The bill's committee review process will determine whether the scope definitions tighten. Geist and the CCLA have both signaled they'll push for judicial authorization requirements on subscriber data. Amendments in Q2 2026 are where the technical definitions either get fixed or get locked in. That's the window that matters.

---

## What Comes Next

The warrantless access problem didn't disappear when C-26 died. It reappeared in C-22 Part 2, dressed in slightly different language but carrying the same structural issues: warrantless subscriber data access, mandatory interception infrastructure, and scope definitions broad enough to catch a lot of software companies off guard.

The core findings hold regardless of how the committee process plays out:

- Warrantless access to subscriber data survives the legislative rewrite, despite *R v Spencer*
- Mandatory backdoor requirements create systemic security risks independent of government intent
- Scope ambiguity means many non-telecom developers may face unexpected compliance obligations
- Canada's framework offers weaker judicial oversight than the EU standard

Expect constitutional challenges if C-22 passes as written — the *Spencer* precedent gives challengers solid footing. Watch for amendments narrowing the subscriber data carve-out, and for Privacy Commissioner intervention on notification requirements in the months ahead.

The practical shift for technical teams: treat Canadian infrastructure the same way you'd treat any jurisdiction with mandatory interception law. Document your data flows. Audit your hosting decisions. And make sure your privacy commitments actually match the legal reality your users live in.

That last part is the one most teams skip. It's also the one that creates liability.

## References

1. [Backgrounder – Securing Access to Information (Bill C-22 – Part 2) - Canada.ca](https://www.canada.ca/en/public-safety-canada/news/2026/03/backgrounder--securing-access-to-information-in-bill-c-22.html)
2. [A Tale of Two Bills: Lawful Access Returns With Changes to Warrantless Access But Dangerous Backdoor](https://mgeist.substack.com/p/a-tale-of-two-bills-lawful-access)
3. [A Tale of Two Bills: Lawful Access Returns With Changes to Warrantless Access But Dangerous Backdoor](https://www.michaelgeist.ca/2026/03/a-tale-of-two-bills-lawful-access-returns-with-changes-to-warrantless-access-but-dangerous-backdoor-surveillance-risks-remains/)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-woman-sitting-on-a-bed-using-a-laptop-xSiQBSq-I0M)*
