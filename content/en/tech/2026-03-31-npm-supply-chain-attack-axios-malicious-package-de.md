---
title: "How the Axios npm Supply Chain Attack Worked and How to Stay Safe"
date: 2026-03-31T19:56:56+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-security", "npm", "supply", "chain", "JavaScript"]
description: "Axios npm supply chain attack injected a RAT into auto-updated projects. Discover exactly how attackers compromised millions of installs and how to protect yours."
image: "/images/20260331-npm-supply-chain-attack-axios-.webp"
technologies: ["JavaScript", "Node.js", "GitHub Actions", "Rust", "Go"]
faq:
  - question: "what happened in the axios npm supply chain attack"
    answer: "In early 2026, the Axios npm package was compromised through a malicious nested dependency that delivered a remote access Trojan (RAT) to any project that auto-updated. Attackers gained publish access to a lower-level package in Axios's dependency tree and pushed a poisoned version, which propagated to millions of projects because Axios used version ranges instead of exact pins. Researchers at Socket.dev and StepSecurity detected the attack and confirmed that affected builds would send data to an attacker-controlled server."
  - question: "npm supply chain attack axios malicious package developer guide how to protect your dependencies"
    answer: "The fastest mitigation is pinning exact dependency versions using a lockfile and running 'npm ci' instead of 'npm install' in CI pipelines to prevent unexpected updates. You should also add security tooling like 'socket' or 'npm audit' to catch compromised packages before they reach your build. Enabling two-factor authentication on npm accounts and using granular publish tokens further reduces the risk of your own packages being hijacked."
  - question: "how do npm supply chain attacks work through transitive dependencies"
    answer: "Rather than attacking a popular package directly, threat actors compromise a lower-level dependency in that package's tree, which then gets pulled in automatically during installs. Because developers rarely review every package in a dependency tree that can be dozens of levels deep, the malicious code reaches production builds largely undetected. The Axios attack exploited this gap by targeting a transitive dependency, allowing the payload to spread to any project using Axios with a version range specifier."
  - question: "npm supply chain attack axios malicious package developer guide best tools to detect compromised packages"
    answer: "Tools like Socket.dev, 'npm audit', and StepSecurity's GitHub Actions hardening are specifically designed to flag suspicious or compromised packages before they enter your build. Socket.dev in particular analyzes package behavior and network activity, which is how the Axios attack was identified and reported in 2026. Integrating these tools into your CI pipeline adds an automated layer of protection that manual code review alone cannot provide."
  - question: "should I use npm ci instead of npm install in production"
    answer: "Yes, 'npm ci' is strongly recommended over 'npm install' in CI and production environments because it installs dependencies strictly from the lockfile, preventing unexpected version updates. Using 'npm install' with range specifiers like '^' or '~' can silently pull in updated transitive dependencies, which is exactly how the Axios supply chain attack reached affected projects. Treating 'npm ci' as non-negotiable in automated pipelines is one of the simplest and most effective supply chain security practices available."
---

A trusted HTTP library used by millions of projects was quietly compromised — and most developers didn't notice until the damage was done. The Axios npm package was hit by a supply chain attack that injected a remote access Trojan into published versions, exposing any project that auto-updated. This tutorial walks through exactly what happened, how attackers pulled it off, and the concrete steps you can take today to protect your own dependencies.

**Who should read this?** Frontend developers, backend engineers, DevOps practitioners — anyone who runs `npm install` and trusts the output.

By the end, you'll know:
- How the Axios attack was structured and why it worked
- How to audit your current dependency tree for malicious packages
- How to lock and verify dependencies at the CI level
- What tooling to add *before* the next attack lands

---

> **Key Takeaways**
> - The Axios npm package was compromised via a supply chain attack that introduced a malicious nested dependency delivering a remote access Trojan (RAT) to affected projects.
> - Malicious versions were live on the npm registry long enough to reach production builds before Socket.dev and StepSecurity researchers detected them in early 2026.
> - Pinning exact dependency versions with a lockfile is the single fastest mitigation — `npm ci` over `npm install` is non-negotiable in CI pipelines.
> - Tools like `socket`, `npm audit`, and StepSecurity's GitHub Actions hardening can catch compromised packages *before* they hit your build.
> - Compromised maintainer credentials remain the most common attack vector — enabling 2FA on npm accounts and using granular publish tokens eliminates a major risk surface.

---

## Background & Context

Supply chain attacks on npm are not new. The `event-stream` incident in 2018 exposed how fragile transitive trust could be across the JavaScript ecosystem. But the Axios attack in 2026 hit differently — Axios sits at roughly 50 million weekly downloads, making it one of the most widely installed packages in existence.

The attack worked by compromising a dependency *of* Axios rather than Axios itself directly. A malicious actor gained publish access to a lower-level package in the dependency tree, pushed a version containing a RAT payload, and waited for the update to propagate upward. Because Axios specified a range (`^` or `~`) rather than an exact version pin, any fresh `npm install` pulled the poisoned transitive dependency automatically.

Socket.dev and StepSecurity both published technical breakdowns confirming that affected builds would phone home to an attacker-controlled server — giving the attacker remote code execution capability on any machine that ran the compromised install.

The current landscape makes this harder to stop than it sounds. The npm registry holds over 2.5 million packages. Most of them have dependency trees dozens of levels deep. No developer is manually reviewing every transitive package on every install. That's exactly the gap this class of attack exploits.

**Prerequisites for this tutorial:**
- Node.js 20+ and npm 10+
- Basic familiarity with `package.json` and lockfiles
- A GitHub or GitLab repo with a CI pipeline (optional but recommended)

---

## Comparing Your Defense Options

Different approaches exist for catching supply chain threats. They're not mutually exclusive — the strongest posture layers all of them.

| Feature | Socket.dev | npm audit | Snyk | Manual Lockfile Pinning |
|---|---|---|---|---|
| **Cost** | Free tier + paid plans | Free (built-in) | Free tier + paid | Free |
| **Detects known CVEs** | Yes | Yes | Yes | No |
| **Detects behavior anomalies** | Yes (network calls, obfuscation) | No | Partial | No |
| **CI/CD integration** | GitHub App, CLI | Native npm | CLI + IDE plugin | Manual `npm ci` enforcement |
| **Transitive dep analysis** | Deep (real-time) | Shallow | Deep | Lockfile-dependent |
| **Response speed** | Near real-time | Post-CVE publication | Post-CVE publication | Immediate (blocks updates) |
| **Maintainer compromise detection** | Yes | No | No | Partial |

**Why this matters:** `npm audit` only catches packages with published CVEs. The Axios attack used a freshly compromised package with *no existing CVE* — it would have passed a standard `npm audit` clean. Socket.dev's behavioral analysis, which flags things like unexpected outbound network calls in install scripts, caught it earlier. Lockfile pinning doesn't detect malice, but it prevents you from silently pulling in new versions without an explicit, reviewable change.

This isn't a case where one tool wins. Each layer catches something the others miss. The teams that got hit were running only one layer — usually the free, built-in one.

---

## Step-by-Step: Hardening Your npm Supply Chain

### Prerequisites
- Node.js 20+ installed
- `npm` 10.x or later (`npm --version` to check)
- Access to your project's CI configuration
- npm account with 2FA enabled (critical — do this first)

---

### Step 1: Audit Your Current Lockfile State

Before adding new tooling, understand what's already in your tree.

```bash
# Check if a lockfile exists and is committed to source control
ls -la package-lock.json

# Generate a full dependency tree — pipe to a file for easier review
npm ls --all > dependency-tree.txt

# Run the built-in audit (catches known CVEs — necessary but not sufficient)
npm audit

# If you find high/critical issues, attempt auto-fix
npm audit fix
```

If you don't have a `package-lock.json` committed to git, that's your first problem. Without it, every `npm install` can silently resolve to a different version than the one you last tested. That silent drift is exactly what supply chain attackers depend on.

---

### Step 2: Switch CI Pipelines from `npm install` to `npm ci`

`npm ci` is strict — it installs *exactly* what's in your lockfile and fails if there's any discrepancy. It doesn't resolve ranges. It doesn't fetch newer patch versions.

```yaml
# .github/workflows/build.yml
name: Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies (strict lockfile enforcement)
        run: npm ci  # NOT npm install — this fails if lockfile is out of sync

      - name: Run tests
        run: npm test
```

The key difference: `npm install` updates `package-lock.json` silently. `npm ci` treats any drift as a hard error, so a tampered or unexpected lockfile change stops the build before it can do damage.

---

### Step 3: Add Socket.dev for Behavioral Analysis

`npm audit` wouldn't have caught the Axios attack. Socket's CLI analyzes packages for suspicious behaviors — obfuscated code, unexpected network calls in `postinstall` scripts, newly published versions with unusual changes.

```bash
# Install the Socket CLI globally
npm install -g @socketsecurity/cli

# Scan your current project dependencies
socket scan npm .

# Example: check a specific package before installing it
socket npm install axios
# This proxies through Socket's analysis before the install completes
```

Expected output for a clean package:
```
✓ axios@1.8.4 — No issues detected
  · No install scripts
  · No new maintainers
  · No obfuscated code
```

For GitHub repos, install the [Socket GitHub App](https://socket.dev). It reviews every PR that touches `package.json` or `package-lock.json` and flags suspicious dependency changes before they merge — not after production is already affected.

---

### Step 4: Pin Exact Versions and Enable Lockfile-Only Installs

Remove range specifiers (`^`, `~`) from critical production dependencies.

```json
// package.json — before (vulnerable to silent updates)
{
  "dependencies": {
    "axios": "^1.7.0",
    "express": "~4.18.0"
  }
}
```

```json
// package.json — after (explicit version pins)
{
  "dependencies": {
    "axios": "1.8.4",
    "express": "4.19.2"
  }
}
```

Then add an `.npmrc` to enforce lockfile-only installs across the team:

```ini
# .npmrc
save-exact=true
package-lock=true
```

`save-exact=true` means every future `npm install <package>` writes an exact version rather than a range. One line of config. Blocks an entire class of silent update attacks.

---

### Step 5: Harden Your npm Account and Publish Tokens

The Axios attack vector involved compromised maintainer credentials. These two steps eliminate most of that risk:

```bash
# Enable 2FA on your npm account (do this in the npm web UI, not CLI)
# Then verify it's active:
npm profile get

# If you publish packages, use granular access tokens
# Create a publish-only token scoped to a single package
npm token create --type=granular-access

# List active tokens and revoke any you don't recognize
npm token list
npm token revoke <token-id>
```

For teams, switch to [npm Organizations](https://docs.npmjs.com/organizations) with role-based access. No single compromised account should have publish rights across all your packages. That's the kind of blast radius that turns one phished credential into an ecosystem-wide incident.

---

## Code Examples & Real-World Use Cases

### Basic Example: Pre-Install Verification Script

Add this to your project's `Makefile` or `package.json` scripts to run before any install:

```javascript
// scripts/verify-deps.js
// Run with: node scripts/verify-deps.js
// Checks that package-lock.json is committed and matches package.json

const fs = require('fs');
const { execSync } = require('child_process');

function verifyLockfile() {
  // Fail if lockfile is missing entirely
  if (!fs.existsSync('package-lock.json')) {
    console.error('ERROR: package-lock.json not found. Run npm install and commit it.');
    process.exit(1);
  }

  // Check for lockfile/package.json drift using npm's built-in check
  try {
    execSync('npm ci --dry-run', { stdio: 'pipe' });
    console.log('✓ Lockfile is in sync with package.json');
  } catch (err) {
    console.error('ERROR: Lockfile is out of sync. Review changes before proceeding.');
    console.error(err.stdout?.toString());
    process.exit(1);
  }
}

verifyLockfile();
```

**Explanation:** `npm ci --dry-run` validates that your lockfile matches `package.json` without actually installing anything. This script fails loudly in CI if someone committed a `package.json` change without updating the lockfile — exactly the scenario that lets supply chain attacks slip through unnoticed.

---

### Advanced Example: Automated Dependency Review in GitHub Actions

```yaml
# .github/workflows/dependency-review.yml
# Runs on every PR that touches package files
name: Dependency Review

on:
  pull_request:
    paths:
      - 'package.json'
      - 'package-lock.json'

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write  # allows posting review comments

    steps:
      - uses: actions/checkout@v4

      - name: GitHub Dependency Review
        # Built into GitHub — flags newly added packages with known vulnerabilities
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-2.0, LGPL-2.0  # block unexpected license changes too

      - name: Socket Security Scan
        uses: nicolo-ribaudo/socket-security-action@v1
        with:
          socket-security-api-key: ${{ secrets.SOCKET_API_KEY }}
```

**Use Case:** Every developer on your team opens a PR to update a dependency. This workflow runs automatically, checks the diff against known vulnerabilities *and* behavioral signals, and posts a comment if anything looks suspicious — before the merge, not after production breaks.

---

## Best Practices & Pitfalls

### Common Pitfalls to Avoid

**Pitfall 1: Trusting `npm audit` alone**
The Axios attack had no CVE when it was first live. `npm audit` passed clean. Behavioral analysis tools catch what CVE databases can't — and the gap between "attack is live" and "CVE is published" is exactly when the damage happens.
- Solution: Layer `npm audit` with Socket or equivalent real-time behavioral scanning.

**Pitfall 2: Committing node_modules to source control**
Some teams skip lockfiles and commit `node_modules` directly, thinking it's more reliable. It bloats repos and obscures changes in transitive deps — the opposite of safer.
- Solution: Commit `package-lock.json`, add `node_modules/` to `.gitignore`, use `npm ci` in CI.

**Pitfall 3: Shared npm publish tokens with broad permissions**
One compromised CI secret with broad publish access can affect every package in your org. That's not a hypothetical — it's the documented pattern in the Axios incident.
- Solution: Granular access tokens, one per package, rotated quarterly.

**When this approach has limits:** These controls protect your consume-side posture well. But if you're a package maintainer with downstream users who *don't* pin versions, your security hygiene alone can't protect them. Publish provenance attestations using npm's built-in provenance support and encourage downstream consumers to adopt the same lockfile discipline. The ecosystem problem only shrinks when both sides tighten up.

### Production Readiness Checklist

- [ ] `package-lock.json` committed to git and reviewed on every PR
- [ ] CI uses `npm ci` exclusively — `npm install` is banned in pipelines
- [ ] Socket.dev GitHub App installed and blocking suspicious PRs
- [ ] All npm accounts have 2FA enabled
- [ ] Publish tokens are granular-access and scoped per package
- [ ] `save-exact=true` set in `.npmrc`
- [ ] Dependency review action runs on every PR touching package files
- [ ] Team has a documented response plan if a dependency is flagged

---

## Conclusion & Next Steps

The Axios supply chain attack is a clear signal: the npm ecosystem's trust model has real gaps, and "it's a popular package, it's fine" is not a security posture. Popularity is actually what makes a package a better target.

The fixes aren't complicated. Lock your versions. Use `npm ci` in every pipeline. Add behavioral analysis tooling that catches what CVE databases miss. Secure the publish credentials for any package your team maintains. None of these steps require a security team or a big budget — they require about an hour and a decision to treat dependency updates as a trust boundary, not a convenience.

**Start today:** Run `socket scan npm .` in your current project. See what comes back. Then enforce `npm ci` in your next CI pipeline update. Those two steps close the most common attack surface before your next deploy.

- Official npm security docs: [docs.npmjs.com/threats-and-mitigations](https://docs.npmjs.com/threats-and-mitigations)
- Socket.dev analysis of the Axios attack: [socket.dev/blog/axios-npm-package-compromised](https://socket.dev/blog/axios-npm-package-compromised)
- StepSecurity technical breakdown: [stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan](https://www.stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan)

Next topic worth learning: **SLSA (Supply-chain Levels for Software Artifacts)** — the framework Google and the OpenSSF built specifically for this class of attack. It gives you a structured vocabulary for what "verified" actually means across your entire software supply chain, not just npm.

## References

1. [Supply Chain Attack on Axios Pulls Malicious Dependency from...](https://socket.dev/blog/axios-npm-package-compromised)
2. [axios Compromised on npm - Malicious Versions Drop Remote Access Trojan - StepSecurity](https://www.stepsecurity.io/blog/axios-compromised-on-npm-malicious-versions-drop-remote-access-trojan)
3. [r/cybersecurity on Reddit: Supply Chain attack on Axios NPM Package](https://www.reddit.com/r/cybersecurity/comments/1s8cbkh/supply_chain_attack_on_axios_npm_package/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-desk-with-coffee-8UnGiO4yesk)*
