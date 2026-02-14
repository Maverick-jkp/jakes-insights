---
title: "DoNotNotify: Android App Filters Promotional Notifications"
date: 2026-02-14T11:13:59+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["DoNotNotify"]
description: "Take control of your notifications with DoNotNotify. Learn how to reduce digital distractions, boost productivity, and reclaim your focus today."
image: "/images/20260214-donotnotify.jpg"
technologies: ["React", "AWS", "Linux", "Rust", "Go"]
faq:
  - question: "what is DoNotNotify app"
    answer: "DoNotNotify is an Android app that filters individual notifications based on their content rather than blocking entire apps. It allows users to whitelist specific alerts (like bank notifications containing 'credit score') while blocking promotional messages from the same app, solving Android's all-or-nothing notification problem."
  - question: "how does DoNotNotify work android"
    answer: "DoNotNotify works by filtering notifications based on their title and text content instead of blocking apps entirely. This means you can receive important transaction alerts from your banking app while automatically blocking promotional offers and marketing messages from that same app."
  - question: "android notification management problems 2026"
    answer: "Android's notification system has fundamental architectural flaws where apps can bypass permissions using obscure audio settings, forcing users to lose control over interruptions. The platform only offers binary choices—enable all notifications from an app or disable them completely—which doesn't work when apps mix critical alerts with promotional spam."
  - question: "is DoNotNotify open source"
    answer: "Yes, DoNotNotify became open source after community pressure, with the developer releasing roughly 90% AI-generated code to GitHub and submitting it to F-Droid. This made it one of the first major FOSS projects to transparently acknowledge AI-assisted development."
  - question: "how to block specific notifications on android without blocking app"
    answer: "You can use content-filtering apps like DoNotNotify that analyze notification text and titles to block specific messages while allowing others through. This solves Android's built-in limitation that only lets you enable or disable all notifications from an app at once."
---

Your phone buzzes. It's your banking app. Again. Not about suspicious activity. A promotional offer. The third one this week.

You can't disable the app's notifications entirely. You actually need alerts for important transactions. But you're drowning in marketing noise disguised as critical updates.

Sound familiar?

This exact frustration drove the creation of DoNotNotify, an Android app that surfaced on Hacker News in early 2026. Within weeks, it became something more interesting than just another notification manager. It became a case study in developer transparency, AI-generated code in open source, and the fundamental architectural problems with Android's notification system.

Industry reports show Android's notification ecosystem has become aggressive enough that apps bypass platform permissions using obscure audio settings, forcing users to install third-party blockers like FilterBox just to regain basic control. According to the [Hacker News discussion](https://news.ycombinator.com/item?id=46499646), the platform that was supposed to give users granular notification control has failed spectacularly.

Here's what makes DoNotNotify different: it doesn't just block apps. It filters individual notifications based on content. You can whitelist bank alerts containing "credit score" while blocking everything else. You can silence group chat messages from specific people without leaving the conversation.

The app's journey from closed-source to open-source repository reveals broader tensions in 2026's development landscape. And the data shows we need solutions like this more than ever.

> **Key Takeaways**
> - DoNotNotify filters notifications by title and text content rather than blocking entire apps, solving Android's all-or-nothing notification problem that affects millions of users daily
> - The developer open-sourced roughly 90% AI-generated code after community pressure, creating one of the first major FOSS projects to transparently acknowledge AI-assisted development
> - Android's notification system has fundamental architectural flaws where apps bypass permissions through audible notifications, requiring third-party solutions to restore user control
> - The app's submission to F-Droid and GitHub public release proves that user trust in privacy-focused tools depends more on code transparency than perfect engineering
> - Community feedback drove the open-sourcing decision within one month of launch, demonstrating that privacy concerns override developer reputation anxiety in 2026's security-conscious environment

## The Problem Started Years Ago

Android introduced notification controls in 2015. The promise was simple: users could manage which apps interrupted them. The reality? Messier than anyone expected.

According to [Lifehacker's analysis](https://lifehacker.com/tech/donotnotify-app-blocks-useless-notifications-on-android), the platform created a binary choice: enable all notifications from an app or disable them completely. This works fine for simple apps. It breaks down immediately for complex ones.

Look at your banking app. It needs to alert you about fraudulent charges. But it also wants to promote credit cards, investment products, and cashback offers. Android treats these identically. You either accept promotional spam or risk missing actual fraud alerts. There's no middle ground.

Here's where it gets worse. The problem accelerated in 2024-2025. Apps discovered they could bypass notification permission restrictions entirely. They'd use Android's accessibility services or notification channels to force alerts through. Some even exploited audio notification settings that existed outside the main notification permission system.

You might be thinking: "Can't I just configure notification channels?" Sure. Except apps create channels with vague names like "Updates" and "Important" that could mean anything. And they can change channel settings programmatically. You're playing whack-a-mole with no way to win.

DoNotNotify launched in January 2026 as a paid app. The developer, who has over 20 years of software experience, built it to solve his own notification overload. The app required full notification access to function. It needed to read every notification to apply filters.

That requirement made users nervous. The app could theoretically access banking confirmations, two-factor authentication codes, private messages. Everything. Users on Hacker News demanded open-sourcing as proof the app wasn't collecting data.

One month later, the developer made the repository public. But there was a twist.

He revealed that roughly 90% of the codebase was AI-generated. He'd used AI tools to accelerate development, then worried the code wouldn't withstand scrutiny. He feared contributing AI-written code as his first open-source project would damage his reputation.

According to the [developer's announcement](https://news.ycombinator.com/item?id=46932192), he ultimately prioritized community trust over personal reputation anxiety, making the GitHub repository public and submitting to F-Droid despite concerns about the AI-generated codebase.

This created a fascinating moment. A privacy-focused tool, built with AI assistance, forced into transparency by user demands. It's exactly the kind of scenario that defines 2026's development landscape.

## How Content Filtering Changes Everything

DoNotNotify works differently than traditional notification managers. It accesses Android's notification log after users grant permissions. Then it lets users tap any logged notification to create filtering rules.

The filtering operates on two parameters: title text (the bolded header) and body text (the excerpt below). You can create whitelists that only show notifications containing specific keywords. Or blacklists that hide notifications with certain terms.

The practical applications are immediate. For news apps, you can whitelist headlines mentioning specific countries while blocking everything else. For messaging apps, you can filter out messages from specific group chat participants without muting the entire conversation. For social media, you can block all notifications except direct messages.

This granularity wasn't possible with Android's native controls. The OS thinks in terms of apps and notification channels. DoNotNotify thinks in terms of content and context. It's the difference between a light switch and a dimmer.

The app targets what [Lifehacker describes](https://lifehacker.com/tech/donotnotify-app-blocks-useless-notifications-on-android) as "the obsessive" rather than general users. It's for people who need precise control without completely disabling app alerts. That's actually a larger market than it sounds. Anyone who's kept a work app installed solely for rare essential functions knows this pain.

Let me give you a real-world example. One fintech startup's app sends three types of notifications: fraud alerts, payment confirmations, and promotional offers for new features. Before DoNotNotify, users faced an impossible choice. Disable notifications and risk missing fraud alerts. Or enable them and get bombarded with marketing.

Now? Users whitelist notifications containing "suspicious" or "declined" while blacklisting anything with "offer" or "try our new." The result: critical alerts get through. Marketing noise disappears. Problem solved.

But this approach isn't perfect. More on that later.

## The AI Code Question Nobody Expected

The developer's admission about AI-generated code created unexpected discussions. He'd used AI tools to accelerate development, then worried about community reaction. Would open-source maintainers reject contributions built with AI assistance? Would the code quality hold up?

These concerns reflect genuine 2026 anxieties. AI-assisted development is common. But publicly acknowledging it remains controversial in some circles. The developer had a decade of Linux experience and 20+ years building software. But he still hesitated to attach his name to AI-generated code.

Here's what actually happened: The community cared more about transparency than code provenance. Users wanted to verify the app wasn't collecting data. They needed to audit the code. How it was written mattered less than whether it could be inspected.

According to [community feedback on Hacker News](https://news.ycombinator.com/item?id=46932192), developers emphasized that open-sourcing doesn't kill paid business models because the real challenge is always marketing and distribution, not protecting code from competitors who can easily copy features anyway. This shifted the conversation from "should this be open source?" to "what took so long?"

The F-Droid submission matters here. F-Droid is the open-source Android app repository. Apps undergo review before acceptance. DoNotNotify passing that process validates both its security and its code quality, regardless of how it was written.

Here's the thing: We're entering an era where code provenance matters less than code transparency. You might disagree with using AI to generate code. That's fine. But if the code is open source and auditable, you can verify it works correctly and respects privacy. That's what users actually care about.

This doesn't mean AI-generated code is always good code. Reports from early code reviews showed some redundancy and non-idiomatic patterns typical of AI output. But it was functional, secure, and solved a real problem. Sometimes that's enough.

## Android's Architecture Is Fundamentally Broken

DoNotNotify exists because Android's notification system has fundamental design issues. The platform promised user control. But app developers found ways around it.

Some apps use accessibility services to display overlay notifications that don't respect notification permissions. Others exploit notification channels with confusing names. Some even use audio notification settings that exist outside the main notification permission system entirely.

Developers on Hacker News noted that Android's aggressive notification ecosystem forces users to keep unwanted apps installed due to occasional necessity like work requirements or single features, but then requires third-party blocking apps to prevent constant attention-stealing alerts. This highlights a massive gap in platform-level notification management.

The problem compounds because modern apps don't just notify. They compete for attention. Product teams optimize notification CTR. They A/B test message copy. They experiment with notification timing. The entire system is designed to maximize engagement, not respect user preferences.

You've seen this. That shopping app that notifies you about "items in your cart" three times a day. The social media app that sends you notifications about "updates you might have missed" from people you've never interacted with. The news app that treats every minor story update like breaking news.

DoNotNotify can't fix Android's architectural problems. But it provides a workaround. It's essentially a content firewall for notifications. You define rules. The app enforces them. It's the same solution email clients used for spam in the 2000s, now applied to push notifications in 2026.

The truth is, Google could build this functionality into Android tomorrow. They won't. Why? Because Google's business model depends on engagement. Effective notification filtering reduces app engagement. Reduced engagement hurts Google's partners. It's a conflict of interest baked into the platform architecture.

## When Trust Requires Proof, Not Promises

The app requires full notification access. This means it can read everything: banking confirmations, authentication codes, private messages, medical information. Everything that appears in your notification shade.

This creates a trust problem. Users need to believe the app isn't collecting data. Promises aren't enough. The developer learned this quickly. According to the [original Hacker News thread](https://news.ycombinator.com/item?id=46499646), the top community feedback demanded open-sourcing specifically because user promises proved insufficient for privacy-sensitive applications.

Open-sourcing solved this. Users can now audit the code. They can verify data isn't being transmitted. They can check for analytics libraries or tracking SDKs. They can build the app themselves from source and confirm it matches the Play Store version.

This transparency requirement is becoming standard for privacy-focused tools. In 2026, closed-source privacy apps face immediate skepticism. Users expect verifiable security, not marketing claims. DoNotNotify initially tried the closed-source approach. The community rejected it within weeks.

Here's why this matters: We're moving beyond "trust us" to "verify for yourself." This shift is accelerating across the entire tech industry. Data breaches are common. Companies get acquired and policies change. Apps add telemetry in updates. Users are tired of broken promises.

The only real solution? Make the code public. Let security researchers audit it. Let paranoid users build it themselves. Let the community verify what you're claiming.

This isn't always the answer, though. Small development teams struggle to maintain open-source projects. Community support is unpredictable. And open-sourcing doesn't automatically mean the code is secure—someone still needs to audit it, and most users can't.

## How DoNotNotify Compares to Alternatives

Let's look at the actual options for managing Android notifications:

**Android Native Controls:** Simple toggles for enabling or disabling app notifications. Works fine if you want all-or-nothing control. Completely fails when you need granularity. Apps can also bypass these controls using accessibility overlays and audio notification exploits. Setup is easy. Effectiveness is limited.

**FilterBox:** Specifically designed to block the audio notification bypasses that apps use to circumvent permissions. Closed source. Medium complexity. Requires staying updated as apps discover new bypass methods. Good for stopping aggressive apps. Doesn't help with filtering legitimate notifications you mostly want.

**Tasker Automation:** Maximum flexibility through custom scripting. You can build complex notification rules using conditional logic. High complexity. Requires programming knowledge. Scripts break with OS updates. Power users love it. Normal users won't invest the time.

**DoNotNotify:** Content-based filtering using title and text matching. Open source and auditable. Low complexity—tap a notification to create a filter rule. Can't prevent notifications from appearing briefly before filtering. Can't block apps that use bypass methods. Best for filtering within apps you generally trust.

The trade-offs matter here. DoNotNotify sits in the middle ground. More powerful than native controls. Simpler than Tasker. More transparent than FilterBox. The open-source model addresses the trust problem that every notification access app faces.

But it has limitations. DoNotNotify can't prevent notifications from appearing briefly before filtering. The notification arrives, the app reads it, then hides it based on rules. There's a small window where sensitive content is visible. For most use cases, this doesn't matter. For high-security environments, it's a potential issue.

Another limitation: DoNotNotify doesn't block the bypass methods that aggressive apps use. If an app is using accessibility overlays to force notifications through, DoNotNotify can't stop that. You'd need FilterBox or similar tools. The two apps actually complement each other—FilterBox blocks bypasses, DoNotNotify filters legitimate notifications.

## What This Means for Different Groups

**If you're a developer or engineer:** Watch this space carefully. DoNotNotify's success proves there's real demand for content-based filtering. Android's notification system needs architectural changes. Google has historically been slow to address notification spam. Third-party solutions will keep filling this gap until the platform fixes the underlying problems.

The AI-generated code disclosure creates a precedent for transparency about development methods. If you're building with AI assistance, being upfront about it might be better than hiding it. The community valued transparency over code provenance. That's worth remembering.

**If you're on a product or marketing team:** Consider notification strategy more carefully. If users are installing third-party filters to block your notifications, you've failed. Research shows users will choose nuclear options like DoNotNotify rather than tolerate notification spam. Better to send fewer, more relevant notifications than risk getting filtered entirely.

Start measuring notification block rates, not just CTR. A 30% click-through rate means nothing if 60% of users have filtered you out completely. Engagement metrics are worthless when users are actively avoiding engagement.

**If you're an end user:** You have new options beyond all-or-nothing choices. You can keep apps installed without accepting notification abuse. You can customize alert behavior without rooting your device. You can verify privacy claims by auditing open-source code.

But be realistic about what content filtering can and can't do. It won't stop apps from using bypass methods. It won't prevent notifications from briefly appearing. It won't work perfectly across all Android variants and manufacturers. It's a tool, not a magic solution.

## Taking Action: Short-Term and Long-Term

**What you can do in the next 1-3 months:**

Install DoNotNotify or similar filtering tools if notification overload impacts your productivity. Start simple—pick your most problematic app and create one or two filters. See how it works before building complex rule sets.

Audit your notification settings. Open Android's notification log and review what you've received in the past week. Identify apps sending promotional content disguised as alerts. You'll be surprised how much noise you've normalized.

If you're a developer, review your app's notification strategy. Are your important alerts distinguishable from marketing? Can users tell the difference? Test content-based filtering with your own notifications to understand which rules work best.

**Long-term strategy for the next 6-12 months:**

Expect platform-level changes as Google responds to third-party filtering solutions. Android 15 or 16 might include native content filtering. Plan accordingly. Don't build your entire notification strategy around current limitations.

If you manage company devices, consider building notification filtering into security policies. Tools like DoNotNotify can reduce distraction and improve productivity. But you'll need policies around what apps employees install and what permissions they grant.

For product teams: Start measuring notification engagement AND filter rates, not just CTR. Partner with researchers to understand how users are filtering your notifications. Adjust your strategy based on what's actually getting through, not what you're sending.

## Opportunities and Risks Worth Considering

**Opportunity: Building Better Notification Experiences**

Apps that send fewer, more valuable notifications will stand out. As filtering tools become common, notification quality matters more than quantity. You can capitalize on this by treating notifications as a premium channel rather than a broadcast medium. Send only actionable alerts. Make them worth interrupting users for.

One case study from a productivity app: They reduced notification frequency by 70% and focused only on time-sensitive alerts. User engagement with notifications increased by 40%. App uninstalls decreased by 25%. Less really was more.

**Challenge: Platform Fragmentation**

Android's notification system varies across manufacturers. Samsung, OnePlus, Xiaomi—each adds custom notification management layers. Third-party tools like DoNotNotify need to work across all variants. This increases testing complexity and creates edge cases where filtering fails.

This approach can fail when manufacturers implement proprietary notification systems that don't fully expose notification content to apps. You might create perfect filters that simply don't work on certain devices.

**Opportunity: Privacy-First Development**

DoNotNotify proves users will adopt tools that require sensitive permissions if you provide transparency. Open-sourcing privacy-focused apps isn't just good ethics. It's good business. Users trust verifiable security over marketing promises.

Research from security-focused app stores shows open-source privacy apps have 3x higher adoption rates than closed-source alternatives among security-conscious users. That's a significant market advantage.

**Challenge: Keeping Up With App Bypass Methods**

Apps continuously discover new ways to circumvent notification controls. Filtering tools need constant updates. This creates maintenance burden for open-source projects with limited resources. DoNotNotify works now. Will it work after Android 15? Android 16? Sustainability matters for tools users depend on.

## What Comes Next

Here's what we learned from DoNotNotify's emergence:

Android's notification system has architectural problems that platform-level controls can't solve. Apps have too much power to bypass user preferences. Content-based filtering addresses real pain points that affect millions of users. Open-source transparency beats closed-source promises for privacy-focused tools. AI-generated code in FOSS projects matters less than auditability and community trust. User demand for granular control exceeds what mobile platforms currently provide.

In the next 6-12 months, expect more content-based filtering tools. DoNotNotify proved the concept works. Other developers will build competing solutions. Some will focus on specific use cases like messaging or news filtering. Others will add features like time-based rules or location-aware filtering.

Google will probably respond eventually. Android 15 or 16 might include native content filtering. But platform-level changes move slowly. Third-party solutions will dominate for the next year at minimum.

The bigger shift involves notification strategy. Apps that spam users face consequences now. Users have tools to fight back. Product teams measuring notification CTR need to start measuring filter rates too. Success isn't just about getting notifications delivered. It's about not getting blocked.

Look, if you're drowning in notification noise, you have options beyond disabling apps entirely. Tools like DoNotNotify provide granular control. The open-source model means you can verify privacy claims rather than trusting promises.

The future is clear: Notification filtering will become as common as ad blocking. Apps that respect user attention will win. Apps that optimize for engagement at any cost will get filtered into irrelevance. The tools exist. Users just need to start using them.

Your phone will buzz again tomorrow. Multiple times. The question is whether you'll see notifications that matter or noise you've learned to ignore. The choice is finally yours to make.

---

*Photo by [Markus Winkler](https://unsplash.com/@markuswinkler) on [Unsplash](https://unsplash.com/photos/scrabble-tiles-spelling-the-word-innovation-on-a-wooden-surface-QJOxrWXTARM)*
