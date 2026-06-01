---
title: "NPM Supply Chain Attack Prevention Checklist for Open Source Maintainers"
date: 2026-05-12T20:59:16+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "npm", "supply", "chain", "React"]
description: "Protect your npm packages from supply chain attacks like the April 2025 worm that compromised 160+ packages. A prevention checklist for maintainers."
image: "/images/20260512-npm-supply-chain-attack-preven.webp"
technologies: ["React", "AWS", "GitHub Actions", "Rust", "Go"]
faq:
  - question: "NPM supply chain attack prevention checklist for open source maintainers — what should it include?"
    answer: "An effective NPM supply chain attack prevention checklist for open source maintainers should cover three core areas: identity and token security, publishing pipeline controls, and dependency hygiene. Token compromise is the leading initial attack vector, so rotating tokens, using granular access tokens, and enabling two-factor authentication are foundational steps. Provenance attestations and lockfile integrity checks should also be included, as automated worms can exploit publish permissions to spread across dozens of packages before any manual response is possible."
  - question: "how did the April 2025 npm worm spread to so many packages so fast"
    answer: "The April 2025 npm worm compromised a single npm publish token, then autonomously mapped the account's publish access across the dependency graph to spread malicious code to over 160 packages, including TanStack and Mistral's npm presence. It was the first documented case of automated lateral movement within the npm permission system at scale, moving faster than any human incident response team could contain. This confirmed that manual monitoring alone is no longer a sufficient defense for open source maintainers."
  - question: "what percentage of npm packages use provenance attestations"
    answer: "As of Q1 2026, fewer than 12% of the top 1,000 npm packages have adopted provenance attestations, despite the feature being generally available since late 2023, according to Chainguard's ecosystem analysis. Provenance attestations are npm's built-in signing feature that cryptographically links a published package to its source code and build pipeline. Low adoption means the vast majority of npm packages still lack a verifiable chain of custody from source to registry."
  - question: "best tools to prevent npm supply chain attacks in 2025 2026"
    answer: "Tools like Socket.dev, Aikido Security, and pnpm's built-in lockfile integrity checks each address different parts of the npm supply chain threat model, but none of them replace foundational security controls. Socket.dev focuses on detecting malicious package behavior, Aikido provides broader supply chain monitoring, and lockfile integrity checks prevent silent dependency tampering. Following a comprehensive NPM supply chain attack prevention checklist for open source maintainers — covering tokens, pipeline signing, and dependency hygiene — is still required alongside any automated tooling."
  - question: "how do npm supply chain attacks start — stolen tokens or malicious code"
    answer: "Token compromise, not direct package code tampering, is the leading initial attack vector for npm supply chain breaches. Tokens are most commonly stolen from CI environments or dotfiles accidentally committed to public repositories, giving attackers publish rights without ever needing to touch the source code directly. Once a valid token is obtained, attackers can inject malicious code into a release or, as seen in 2025, use automated worms to propagate across every package the compromised account has publish access to."
---

The April 2025 npm worm didn't ask for permission. It found a compromised token, injected malicious code, mapped the account's publish access across the dependency graph, and spread to 160+ packages — including TanStack and Mistral's npm presence — faster than any human incident response team could react.

Aikido Security's researchers called it "mini Shai-Hulud." The name fits. It moved through the npm ecosystem the way a sandworm moves through Arrakis: autonomously, at scale, and without warning.

That's the threat model in 2026. Not a lone attacker manually swapping files. An automated worm exploiting the trust relationships baked into the npm publish pipeline.

According to Sonatype's 2025 State of the Software Supply Chain report, malicious package uploads to open source registries grew 156% year-over-year. The npm ecosystem — 2.5 million packages and counting — remains the largest single attack surface in software distribution. Every maintainer without a formal prevention checklist is operating on trust and luck.

Neither scales.

---

**Key Takeaways**

> - The April 2025 npm worm spread to 160+ packages autonomously, confirming that manual monitoring is no longer sufficient for open source maintainers.
> - Token compromise remains the leading initial attack vector for npm supply chain breaches — not package code tampering.
> - Provenance attestations (npm's built-in signing feature, GA since late 2023) are still adopted by fewer than 12% of top-1,000 npm packages as of Q1 2026, per Chainguard's ecosystem analysis.
> - An effective prevention checklist must cover identity, publishing pipeline, and dependency hygiene — not just code review.
> - Automated tooling like Socket.dev, Aikido, and pnpm's built-in lockfile integrity checks each address different parts of the threat model — and none of them replace foundational controls.

---

## The Attack Pattern Has a Lineage

The TanStack compromise wasn't exotic. Per TanStack's own postmortem, it started with a stolen npm token — likely harvested from a CI environment or a dotfile accidentally committed to a public repo. Once the attacker had publish rights, they injected malicious code into a release. Downstream dependents started pulling compromised versions before any human noticed.

This pattern goes back further. The 2021 `ua-parser-js` hijack. The 2022 `node-ipc` sabotage, where the maintainer *intentionally* shipped malicious code. The 2024 `polyfill.io` CDN compromise. Each incident exposed a different weak point in the trust chain.

But the 2025 worm is qualitatively different. It's the first documented case of automated lateral movement within the npm permission graph at scale. The payload actively sought out other packages the compromised account had publish access to. It didn't stop at one target. It propagated.

The ecosystem's response has been incremental. npm added granular access tokens and two-factor enforcement for high-impact packages in late 2023. GitHub introduced npm provenance attestations — cryptographically linking a package to its source repo and CI run — around the same time. Adoption has been slow. Maintainers are volunteers or small teams. Security work competes with shipping features.

That gap between available tooling and actual adoption is exactly where attackers operate.

## Token Security Is the First Domino

Every major npm compromise in the past three years started the same way. Token leaked. Game over.

The attack surface is larger than most maintainers realize. An npm publish token can live in `.npmrc` files accidentally committed to public repos, CI environment variables exposed through forked PRs, leaked workflow logs, or compromised third-party CI integrations. According to GitGuardian's 2025 State of Secrets Sprawl report, npm tokens were the third most commonly leaked secret type on GitHub — behind AWS keys and generic API tokens.

The fix isn't complicated. It requires discipline.

**Use granular access tokens** — not the old "automation" or "publish" tokens with full account scope. Npm's granular tokens let you restrict a token to a single package and a specific IP CIDR range. **Enable 2FA for publishing** on every package. npm has made this mandatory for the top 500 most-downloaded packages, but it's opt-in for everyone else. **Rotate tokens quarterly at minimum.** Most maintainers set one up and forget it exists. **Audit active tokens** via `npm token list` regularly and revoke anything unfamiliar.

The TanStack postmortem explicitly identified a compromised token as the initial vector. That's a preventable failure.

## The Publishing Pipeline Is an Attack Surface

CI/CD pipelines have made publishing easier. They've also made it possible for an attacker with code execution inside your pipeline to ship malicious packages without anyone noticing.

GitHub Actions workflows that auto-publish on tag or push are particularly exposed. If a workflow uses `npm publish` with a stored secret and that workflow file is writable by a contributor, you have a problem. pnpm's supply chain security documentation specifically recommends treating the publish step as a high-trust operation requiring separate, isolated permissions — not bundled into the same workflow that runs tests.

The controls here are concrete:

**Pin CI action versions to commit SHAs, not floating tags.** `actions/checkout@v4` can be silently updated by the action author. `actions/checkout@abc123...` can't. **Use environment protection rules** in GitHub Actions to require manual approval before any workflow can access the `NPM_TOKEN` secret. **Enable npm provenance attestations.** Adding `--provenance` to your publish command generates a cryptographically verifiable link between the published package, the source commit, and the CI run. Consumers can verify it. Attackers can't fake it without access to your repo *and* your CI. **Restrict who can trigger publish workflows.** Not every contributor needs that access.

This approach can fail when teams treat pipeline security as a one-time setup. Workflow files drift. Permissions accumulate. Review your publish pipeline every quarter, not just when something breaks.

## Dependency Hygiene — Your Attack Surface Grows With Every `npm install`

Your own token security doesn't matter if one of your dependencies gets compromised and starts executing code during your build.

Lockfiles are the first line of defense. A `package-lock.json` or `pnpm-lock.yaml` pins exact resolved versions including integrity hashes. Without one, `npm install` in CI can silently pull a newer, compromised minor version. With one, that install fails if the hash doesn't match.

Beyond lockfiles: **audit your `postinstall` scripts**. These run automatically on install and are a common execution vector for malicious packages. In your own package, minimize or eliminate them. For dependencies, use `npm install --ignore-scripts` in CI contexts where you don't need them. **Use `npm audit` as a gate, not a report** — block deploys on high-severity findings. **Watch for dependency confusion attacks.** If your org uses private packages, make sure your npm config explicitly scopes them to your private registry. Aikido's analysis of the 2025 worm showed it attempted to exploit publish-access relationships. Scoping prevents lateral spread.

## How the Main Tooling Options Compare

No checklist survives contact with a complex monorepo without tooling. Here's how the main options stack up on criteria that actually matter:

| Criteria | Socket.dev | Aikido Security | Snyk | pnpm built-in |
|---|---|---|---|---|
| **Malicious package detection** | Yes (behavior analysis) | Yes (SAST + runtime) | Limited (CVE-based) | No |
| **Provenance verification** | Yes | Partial | No | Via lockfile integrity |
| **CI/CD integration** | GitHub App + Actions | GitHub + GitLab | GitHub + Jenkins + more | Native (pnpm only) |
| **False positive rate** | Low (policy-configurable) | Medium | Low-Medium | N/A |
| **Cost (open source)** | Free tier available | Free tier available | Free tier (limited) | Free |
| **Token/secret scanning** | No | Yes | No | No |
| **Best for** | Package-level threat detection | Full-stack security posture | CVE/compliance workflows | Lockfile-strict teams |

Socket.dev focuses specifically on supply chain threats — it analyzes package behavior, not just known CVEs. That makes it better at catching novel malicious packages like those in the 2025 worm. Aikido catches a broader threat surface including secrets. Snyk is strong for compliance-driven orgs that need CVE reporting.

None of these replace the foundational checklist work on tokens and pipelines. They're a detection layer. Not a prevention layer.

## Who Needs What

**For solo maintainers and small teams**, priority order matters because time is the constraint. Start with tokens. Revoke old ones, enable 2FA, switch to granular tokens. That's an afternoon of work and it eliminates the most common initial attack vector. Then add a lockfile if you don't have one. Then enable provenance attestations on your next release. Each step is independent.

**For organizations managing internal packages or monorepos**, a compromised internal package doesn't just affect your users — it affects every team depending on it internally. Environment protection rules on GitHub Actions and scoped private registries are non-negotiable at this scale. Run Socket.dev or Aikido on every PR that touches `package.json` or lockfiles.

**For package consumers** — which is everyone — check whether packages you depend on publish provenance attestations. Prefer packages with active security policies and 2FA-enforced publishing. Treat `postinstall` scripts in transitive dependencies as potential execution vectors, because they are.

## What's Coming in the Next Six Months

Three things worth watching:

npm's planned enforcement of provenance attestations for high-impact packages is expected around Q3 2026, per GitHub's public roadmap discussions. SLSA (Supply-chain Levels for Software Artifacts) framework adoption is expanding beyond Google and large enterprises into the open source maintainer community. And automated worm detection at the npm registry itself — still an open problem — is something GitHub and npm's security teams have been publicly discussing since late 2025.

The 2025 worm was a signal, not an anomaly. Most of the effective defenses are known, documented, and available right now. Token compromise is still the most common entry point — granular tokens and 2FA close it. CI pipeline hardening eliminates the publish-step attack surface. Lockfile integrity and `postinstall` script auditing address upstream poisoning. Tooling like Socket.dev and Aikido provides detection on top of that foundation.

This isn't a one-time audit. It's an operational posture. Every token rotation, every pipeline review, every lockfile commit is part of that posture.

One concrete next step: run `npm token list` right now and revoke anything you don't recognize. Three minutes. Highest leverage action on the list.

---

*References: TanStack npm supply chain compromise postmortem (tanstack.com); Aikido Security analysis of the 2025 npm worm (aikido.dev); pnpm supply chain security documentation (pnpm.io); Sonatype 2025 State of the Software Supply Chain; GitGuardian 2025 State of Secrets Sprawl; Chainguard npm provenance adoption analysis Q1 2026.*

## References

1. [Mitigating supply chain attacks | pnpm](https://pnpm.io/supply-chain-security)
2. [Postmortem: TanStack npm supply-chain compromise | TanStack Blog](https://tanstack.com/blog/npm-supply-chain-compromise-postmortem)
3. [Mini Shai-Hulud Is Back: npm Worm Hits over 160 Packages, including Mistral and Tanstack](https://www.aikido.dev/blog/mini-shai-hulud-is-back-tanstack-compromised)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
