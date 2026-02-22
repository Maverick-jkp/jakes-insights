---
title: "**Keep Android Open: Developers Push Back on Google's 2026 Rule**"
date: 2026-02-22T13:28:45+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["Keep", "Android", "Open"]
description: "Discover why keeping Android open matters for innovation, user freedom, and app diversity. Learn how openness shapes the future of mobile tech."
image: "/images/20260222-keep-android-open.jpg"
technologies: ["Linux", "Rust", "Go"]
faq:
  - question: "What is the Keep Android Open movement and what does it want?"
    answer: "Keep Android Open is a developer-led movement centered at keepandroidopen.org, led by F-Droid board member Marc Prud'hommeaux, pushing back against Google's mandatory developer verification policy set to begin enforcement in 2026. The movement frames Google's verification requirements as an antitrust issue rather than a legitimate security measure, arguing it extends Google's control over app distribution beyond just the Play Store. Prud'hommeaux has contacted antitrust officials in four US states as well as Brazilian and EU regulators."
  - question: "What does Google's mandatory developer verification require starting March 2026?"
    answer: "Starting March 2026, all apps installed on certified Android devices — including sideloaded apps — must come from verified developers who have supplied government ID, a Google payment profile, and proof of app signing key ownership, in addition to paying a one-time $25 fee. The enforcement rollout begins in September 2026 across Brazil, Indonesia, Singapore, and Thailand, with more regions to follow. This policy applies to over 95% of Android devices worldwide, with only alternative builds like LineageOS and GrapheneOS excluded."
  - question: "Does Keep Android Open have a valid point about Google's security argument being weak?"
    answer: "Critics of Google's policy point out that Google's own Play Store distributed 77 malicious apps that accumulated over 19 million downloads, which directly undermines Google's claim that sideloading carries 50 times more malware risk than using the Play Store. The Keep Android Open movement argues the verification requirement is about extending platform control rather than genuinely improving user security. Marc Prud'hommeaux estimates that 90-95% of Android developers oppose the policy."
  - question: "How does Google's developer verification policy affect F-Droid and open-source app stores?"
    answer: "Open-source app stores like F-Droid face an existential distribution threat on certified Android devices under Google's new verification policy, since apps distributed outside of verified channels would be blocked on the vast majority of Android devices. F-Droid is a free, open-source app repository that distributes apps Google does not carry, and the new policy removes sideloading as a practical workaround for developers and users who rely on alternative distribution channels. Only users running alternative Android builds like LineageOS or GrapheneOS would remain unaffected."
  - question: "Can you still sideload apps on Android after the 2026 verification deadline?"
    answer: "After Google's verification enforcement begins in 2026, sideloaded apps on certified Android devices will still need to come from verified developers who have completed Google's identity and payment verification process, meaning unrestricted sideloading effectively ends on mainstream Android hardware. Users who want to avoid these restrictions would need to switch to alternative Android builds like LineageOS or GrapheneOS, which are not subject to Google's certified device requirements. This represents a major structural change to how Android app distribution has historically worked."
---

Google's March 2026 developer verification deadline is weeks away. And the developer community is pushing back hard.

[According to The Register](https://www.theregister.com/2025/10/29/keep_android_open_movement/), Google announced in August 2025 that all apps installed on certified Android devices — including sideloaded ones — must come from verified developers starting this month. The enforcement rollout begins in September 2026 across Brazil, Indonesia, Singapore, and Thailand. More regions follow after that.

This isn't a minor policy tweak. It's a structural change that reshapes who controls Android's app distribution layer. The Keep Android Open movement — centered at keepandroidopen.org and led by F-Droid board member Marc Prud'hommeaux — frames this as an antitrust issue, not a security upgrade. Prud'hommeaux estimates 90-95% of Android developers oppose the policy.

The core tension is real: Google controls the dominant mobile OS while simultaneously operating the dominant app store. Tightening verification requirements for *all* certified devices — not just Play Store installs — extends that control well beyond what most users understand. And the security rationale? It doesn't hold up well under scrutiny.

**This analysis covers:**
- What verification actually requires and who it excludes
- Why Google's security argument has credibility problems
- How alternative Android ecosystems compare under this policy
- What developers and organizations should do right now

> **Key Takeaways**
> - Google's mandatory developer verification starts March 2026 and covers over 95% of Android devices worldwide, excluding only alternative builds like LineageOS and GrapheneOS.
> - The one-time $25 fee is the smallest barrier — developers must also supply government ID, a Google payment profile, and proof of app signing key ownership.
> - Marc Prud'hommeaux (F-Droid board member) estimates 90-95% of Android developers oppose the policy, and has contacted US antitrust officials in four states plus Brazilian and EU regulators.
> - Google's own platform distributed 77 malicious apps that accumulated over 19 million downloads, directly undermining the "50x more sideload malware" security claim.
> - Open-source app stores like F-Droid face an existential distribution threat on certified Android devices under this policy.

---

## Android's Openness Was Always Conditional

Android launched in 2008 under the Apache License, which theoretically meant anyone could build on it. In practice, "Android" as most users experience it — with Google Play, the Play Protect framework, and Google Mobile Services — has always required a separate licensing agreement with Google. The open-source AOSP (Android Open Source Project) is the foundation. The commercial product is something different.

That distinction mattered less when sideloading remained a practical escape valve. If Google Play rejected your app, or if users wanted software Google didn't distribute, they could install APKs directly. F-Droid, the open-source app repository, built an entire ecosystem on this capability. Privacy-focused distributions like GrapheneOS and CalyxOS depended on it. Small developers in markets where Google payment infrastructure doesn't work relied on it.

The August 2025 announcement changes that calculus for certified devices. The timeline is aggressive:

- **March 2026**: Mandatory verification begins for all certified Android device app installs
- **September 2026**: Active enforcement starts in Brazil, Indonesia, Singapore, and Thailand
- **2026–2027**: Additional regional rollouts follow

The verification requirements go beyond a simple fee. [According to The Register](https://www.theregister.com/2025/10/29/keep_android_open_movement/), developers must pay a $25 one-time fee, create a Google payment profile, provide government-issued ID, agree to Google's Terms and Conditions, prove ownership of app signing keys, and declare current and future app identifiers. That last requirement — pre-declaring future app identifiers — is particularly binding. It creates a registration dependency before software even exists.

The Keep Android Open petition emerged directly from this announcement. Prud'hommeaux has since made contact with Brazilian regulators, US antitrust officials across four states, and EU policy bodies. No formal investigation has opened as of February 2026, but the regulatory interest is real.

---

## The Security Rationale Has a Credibility Problem

Google's stated justification for the policy is malware reduction. The company claims sideloaded sources produce 50 times more malware than Play Store distributions. That number sounds decisive. It isn't.

[According to The Register's reporting](https://www.theregister.com/2025/10/29/keep_android_open_movement/), 77 malicious apps on Google Play itself accumulated over 19 million downloads. That's not a minor footnote — that's a significant malware distribution event through the very platform Google positions as the safe alternative. And Google offers no warranty or user compensation when this happens through its own store.

The structural problem runs deeper than bad actors slipping past review. Verified developers can still integrate compromised third-party SDKs. SDK supply chain attacks — where a legitimate developer unknowingly includes malicious library code — bypass developer verification entirely. The verification system checks who built the app. It can't verify the full dependency graph that shipped inside it.

This reveals what the policy actually controls: distribution channels, not security outcomes. A verified developer can ship malware. An unverified open-source developer on F-Droid typically can't, because the code is publicly auditable.

---

## Who This Locks Out — and Who It Doesn't

The policy applies to certified Android devices. That's the critical qualifier. [According to The Register](https://www.theregister.com/2025/10/29/keep_android_open_movement/), certified devices represent over 95% of Android installations outside China. The exclusions — LineageOS, GrapheneOS, /e/OS — are real but serve a tiny fraction of users.

GrapheneOS is worth examining specifically. Its security architecture, discussed at length in [Hacker News technical threads](https://news.ycombinator.com/item?id=45742488), deliberately excludes app-level root grants because unconstrained root access eliminates SELinux containment guarantees. GrapheneOS treats security as a design constraint, not a feature toggle. Its users are already self-selecting for technical sophistication.

The developers losing the most aren't GrapheneOS users. They're:

- **F-Droid contributors** building open-source apps distributed outside Play Store
- **Small developers in emerging markets** where Google payment profiles are difficult or impossible to create
- **Enterprise developers** distributing internal apps without going through public Play Store infrastructure
- **Researchers and security professionals** who need to distribute testing tools without formal verification

The $25 fee isn't the hard barrier. Government ID requirements and mandatory Google payment profiles exclude significant developer populations in markets Google is simultaneously trying to grow — including Brazil and Indonesia, two of the first enforcement targets.

---

## The Antitrust Angle Is the One to Watch

Prud'hommeaux's regulatory outreach strategy is deliberate. The EU has already shown it'll act on mobile platform competition — Apple's response to the Digital Markets Act resulted in real, if imperfect, sideloading changes in Europe. Android, as the dominant mobile OS in most global markets, faces similar scrutiny.

Developer communities are actively comparing this to Microsoft Teams bundling behavior — users sticking with a platform due to ecosystem lock-in rather than genuine preference. [Community discussions at Hacker News](https://news.ycombinator.com/item?id=45742488) draw that comparison explicitly. The implication: Google may be underestimating how much developer goodwill it's burning, on the assumption that users stay for Android quality rather than inertia.

Australian developers specifically have a practical lever: the ACCC has precedent on platform overreach, having successfully forced Steam into refund compliance and actively pursuing Microsoft. Filing complaints through national competition authorities is a concrete action, not just symbolic protest.

A smaller cohort is already migrating to PostmarketOS and Mobian — Linux-based smartphone distributions. Battery life and software stability are genuinely poor on these platforms right now. Developers making this move are accepting real trade-offs as a protest position. That's not mainstream adoption, but it signals how seriously some technical users view where this is heading.

---

## Comparing Android Distribution Paths Under the New Policy

| Criteria | Google Play (Verified) | F-Droid | GrapheneOS/LineageOS | PostmarketOS/Mobian |
|---|---|---|---|---|
| **Affected by March 2026 policy** | No (already verified) | Yes — existential threat on certified devices | No — exempt as alternative builds | No — not Android |
| **Developer cost** | $25 one-time | Free | Free | Free |
| **Government ID required** | Yes | No | No | No |
| **Malware review process** | Automated + manual (77 malicious apps still got through) | Community review + open-source auditing | N/A (user-installed) | Package maintainer review |
| **Market reach (certified devices)** | ~95% of non-China Android | Severely restricted post-March 2026 | <1% of Android users | Niche/experimental |
| **SDK supply chain transparency** | Low | High (open source) | Variable | High (open source) |
| **Regulatory exposure** | High (active EU, US, AU scrutiny) | Low | Low | None |
| **Best for** | Commercial apps, broad distribution | Privacy-focused, open-source projects | Security-conscious power users | Developer experimentation |

The trade-off picture is stark. Google Play wins on reach — by a large margin. But it's the only distribution path that requires government ID and creates a permanent dependency on Google's payment infrastructure. F-Droid's open-source audit model arguably produces more verifiable security outcomes than automated Play Store review, yet the new policy treats it as higher-risk by default.

GrapheneOS threads the needle by opting out of certification entirely. Its security architecture — particularly the decision not to grant app-level root and to keep network management in SELinux-constrained `netd` rather than allowing competing firewall apps — reflects a coherent design philosophy. But it serves a technical audience willing to manage their own device trust chain.

---

## Practical Implications

### Who Should Care?

**Developers and engineers** need to act immediately. If you distribute APKs outside the Play Store — internal enterprise tools, beta builds, open-source utilities — your March 2026 compliance status needs a review now. The verification process takes time, and government ID verification isn't instant.

**Organizations** running internal Android app fleets face a quieter version of the same problem. Enterprise Mobile Device Management (MDM) deployments that rely on sideloading for internal tooling may need to route through Play Store private channels or managed Google Play, which adds complexity and Google dependency to previously self-contained workflows.

**End users** who rely on F-Droid for privacy-respecting software face shrinking options on their existing certified Android devices. The policy doesn't block F-Droid itself — it blocks installing apps from F-Droid on certified hardware. That's a meaningful distinction.

### How to Prepare or Respond

**Short-term actions (now through May 2026):**
- Complete Google developer verification if you distribute Android apps at all — even outside Play Store
- Audit any internal enterprise apps for distribution method and compliance status
- If you're in Australia, Brazil, or the EU: document your use cases for regulator contact (ACCC complaints are free to file)
- Check whether your app signing keys meet Google's new ownership proof requirements

**Long-term strategy (through early 2027):**
- If open-source distribution is core to your project, track EU Digital Markets Act developments — Android may face DMA obligations that create legal sideloading carve-outs
- Monitor F-Droid's technical response to the policy; the project has survived platform pressure before
- Evaluate whether GrapheneOS or similar exempt builds serve your user base — it's a small audience, but a technically sophisticated and privacy-conscious one

### Opportunities and Challenges

**Opportunity #1: Regulatory carve-outs may open.**
The DMA and active US antitrust attention create real possibility that verification requirements face legal constraints. Developers who've formally registered opposition — through petitions or regulator contact — have standing in those proceedings.

**Challenge #1: F-Droid's distribution model faces structural threat.**
The open-source ecosystem around F-Droid may fragment. Some projects will register with Google to maintain reach. Others won't — or can't, due to payment infrastructure barriers. The likely result is a bifurcated developer community, not a unified response.

**Opportunity #2: Alternative ecosystems get a narrative boost.**
PostmarketOS and Mobian are rough right now. Battery management is poor, app compatibility is limited. But every time Google tightens certified Android, these projects pick up developer interest. Better hardware support takes time, but developer attention accelerates it.

---

## What Comes Next

The Keep Android Open movement has surfaced something that was always true but rarely stated directly: Android's openness was always conditional. The AOSP license is open. The certified Android ecosystem — the one shipping on 95% of non-China devices — never was.

**Key insights from this analysis:**

- Google's security rationale is undermined by its own platform's malware record: 19 million downloads of malicious apps distributed through Play Store
- The verification requirements are structurally exclusionary for developers in markets Google is actively trying to grow
- Alternative Android builds are exempt but serve a tiny fraction of users
- Regulatory pressure is real but slow — no formal investigations as of February 2026

**What to expect in the next 6–12 months:**

- March 2026 verification enforcement will generate the first real compliance data — how many small developers simply don't qualify
- September 2026 enforcement in Brazil and Indonesia will test whether emerging market developers can meet the requirements in practice
- EU DMA proceedings may create explicit obligations around Android sideloading before year-end
- F-Droid will announce a formal technical or legal response; watch keepandroidopen.org for updates

The bottom line is straightforward. If you build or distribute Android apps outside the Play Store, your window to act without pressure is closing. Get verified, document your objections through official regulatory channels, and watch what the EU does. That's where the most meaningful constraint on this policy is most likely to emerge first — and fastest.

---

*Photo by [Luis Andrés Villalón Vega](https://unsplash.com/@avillalonv) on [Unsplash](https://unsplash.com/photos/a-large-green-object-with-a-yellow-cloth-on-it-XJD9JwFqdDk)*
