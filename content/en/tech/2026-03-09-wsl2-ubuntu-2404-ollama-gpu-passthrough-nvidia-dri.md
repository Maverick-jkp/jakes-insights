---
title: "WSL2 Ubuntu 24.04 Ollama GPU Passthrough NVIDIA Driver Mismatch Fix"
date: 2026-03-09T20:01:23+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "wsl2", "ubuntu", "24.04", "Python"]
description: "Fix WSL2 Ubuntu 24.04 Ollama GPU passthrough killed by NVIDIA driver mismatch — the RTX 4090 blocker engineers hit most in early 2026, solved."
image: "/images/20260309-wsl2-ubuntu-2404-ollama-gpu-pa.webp"
technologies: ["Python", "Docker", "Linux", "Rust", "Go"]
faq:
  - question: "wsl2 ubuntu 24.04 ollama gpu passthrough nvidia driver mismatch error solved how to fix"
    answer: "The fix for the WSL2 Ubuntu 24.04 Ollama GPU passthrough NVIDIA driver mismatch error is to never install NVIDIA drivers inside WSL2 itself. You should only install the CUDA Toolkit (without driver components) inside Ubuntu 24.04, and ensure your Windows host has NVIDIA driver version 560 or higher installed. The Windows host driver handles passthrough automatically via the dxgkrnl paravirtualized kernel module."
  - question: "why is ollama using cpu instead of gpu in wsl2 ubuntu 24.04"
    answer: "Ollama silently falls back to CPU inference when it detects a broken or mismatched CUDA stub library, which is a common result of incorrectly installing NVIDIA drivers inside the WSL2 environment. This is a known issue tied to the WSL2 Ubuntu 24.04 Ollama GPU passthrough NVIDIA driver mismatch error, where the corrupted libcuda.so prevents a valid CUDA context from forming. The symptom is noticeably slow inference speeds, typically 3–4 tokens per second instead of 60+, with no obvious error message."
  - question: "can you install nvidia drivers inside wsl2 ubuntu 24.04"
    answer: "You should not install NVIDIA drivers inside WSL2 Ubuntu 24.04, even though the apt repository makes nvidia-driver packages appear available and installable. Installing them corrupts the stub libcuda.so file that the WSL2 GPU passthrough architecture depends on, causing driver version mismatch errors. Only the CUDA Toolkit without driver components should be installed inside the WSL2 Linux environment."
  - question: "nvidia-smi shows gpu but cuda not working wsl2 ubuntu 24.04"
    answer: "When nvidia-smi detects the GPU but CUDA fails in WSL2 Ubuntu 24.04, it typically means the libcuda.so stub library has been corrupted, usually by installing NVIDIA drivers directly inside the WSL2 environment. Ubuntu 24.04's kernel 6.8 changed how the CUDA stub library maps to the Windows-side driver, making it more sensitive to this misconfiguration than previous Ubuntu versions. Removing any NVIDIA driver packages installed inside WSL2 and relying solely on the Windows host driver (version 560+) resolves the issue."
  - question: "minimum nvidia driver version for wsl2 ubuntu 24.04 cuda 12"
    answer: "As of early 2026, NVIDIA driver version 560 or higher on the Windows host is the minimum required for stable CUDA 12.x passthrough to WSL2 running Ubuntu 24.04. Older driver versions can cause the GPU passthrough to fail or produce driver mismatch errors even when nvidia-smi appears to detect the GPU correctly. Keeping the Windows host driver up to date is one of the most important steps when troubleshooting the WSL2 Ubuntu 24.04 Ollama GPU passthrough NVIDIA driver mismatch error."
---

The setup looked perfect on paper. WSL2 running Ubuntu 24.04, Ollama installed, NVIDIA RTX 4090 sitting idle — and a `nvidia-smi` inside WSL2 throwing back a driver version mismatch error that killed GPU passthrough entirely. This specific failure pattern has become one of the most common blockers for engineers running local LLMs on Windows in early 2026, and the fix isn't obvious unless you understand *why* the WSL2 driver architecture works the way it does.

> **Key Takeaways**
> - The WSL2 Ubuntu 24.04 Ollama GPU passthrough NVIDIA driver mismatch error is almost always caused by installing NVIDIA drivers *inside* the WSL2 environment instead of relying on the Windows host driver to pass through.
> - Ubuntu 24.04 ships with a newer kernel (6.8) that changed how the CUDA stub library maps to the Windows-side NVIDIA driver, creating version conflicts that didn't exist on Ubuntu 22.04.
> - The correct fix requires zero NVIDIA driver installation inside WSL2 — only the CUDA Toolkit (without driver components) belongs in the Linux environment.
> - As of March 2026, NVIDIA driver version 560+ on the Windows host side is the minimum required for stable CUDA 12.x passthrough to WSL2 with Ubuntu 24.04.

---

## Why Ubuntu 24.04 Changed Everything for WSL2 GPU Passthrough

WSL2 GPU passthrough has existed since Microsoft and NVIDIA partnered on the feature in 2020. The architecture is elegant in principle: Windows manages the physical GPU driver, and WSL2 accesses it through a paravirtualized kernel module called `dxgkrnl`. A stub `libcuda.so` inside the Linux VM forwards CUDA calls back to the Windows driver.

It worked well through Ubuntu 20.04 and 22.04. Then Ubuntu 24.04 LTS shipped in April 2024 with kernel 6.8, and two things changed. First, the default NVIDIA open-kernel-module interface shifted. Second, `apt` repositories for Ubuntu 24.04 started offering `nvidia-driver-*` packages that *appear* installable inside WSL2 — but installing them corrupts the stub library that the passthrough architecture depends on.

By late 2024 and into 2025, NVIDIA's developer forums started logging consistent reports of the exact failure mode: `nvidia-smi` showing the GPU but reporting a driver mismatch, Ollama defaulting to CPU inference despite a capable GPU, and `nvidia-container-toolkit` failing with cryptic errors. A prominent thread on NVIDIA's developer forums covering WSL2 + Ubuntu 24.04 LTS documented users reporting OpenGL falling back to `llvmpipe` (software rendering) even when `nvidia-smi` confirmed GPU detection.

The Ollama angle made it worse. Ollama's auto-detection logic checks for `libcuda.so` and a working CUDA context. A broken stub library means Ollama silently falls back to CPU — no loud error, just models running at 3–4 tokens/second instead of 60+. You won't see a failure message. The GPU just sits there, doing nothing.

---

## Why the Driver Mismatch Actually Happens

The root cause is an architectural mismatch most documentation glosses over. WSL2 doesn't need — and *can't* use — a full NVIDIA Linux driver inside the VM. The Windows host driver (560.x or higher for CUDA 12.x) exposes GPU access through the `/dev/dxg` device. Microsoft ships a minimal kernel-mode driver (`nvidia.ko`) as part of WSL2 automatically. That's the entire driver layer.

When you run `sudo apt install nvidia-driver-535` inside Ubuntu 24.04 on WSL2, you're installing a full Linux GPU driver that tries to load its own kernel module — which conflicts with the already-loaded Microsoft/NVIDIA paravirtualized one. The `libcuda.so` stub in `/usr/lib/wsl/lib/` gets shadowed or overwritten, and the version numbers no longer match. `nvidia-smi` can still see the device (because `dxgkrnl` is still active), but it reports the version mismatch because the userspace library version doesn't match the kernel module version.

On Ubuntu 22.04, this was harder to trigger accidentally. The NVIDIA packages in the Jammy repos were older and less likely to clobber the stub. On Ubuntu 24.04 (Noble Numbat), the repos are more aggressive and the kernel changes make the collision more likely. The install appears to succeed. Nothing warns you. The breakage only surfaces when Ollama runs inference and quietly falls back to CPU.

---

## The Correct WSL2 + Ubuntu 24.04 + Ollama Stack

The working configuration as of March 2026:

**Windows host side:**
- NVIDIA Game Ready or Studio driver 560.81 or newer (560+ is the hard floor for CUDA 12.x in WSL2)
- WSL2 with kernel version 5.15.167+ (check with `wsl --update`)

**Inside Ubuntu 24.04 WSL2 — what you install:**
- CUDA Toolkit only, using the CUDA network installer with the `--override` flag to skip driver installation
- `nvidia-cuda-toolkit` from the CUDA repo, *not* from Ubuntu's default apt mirror
- Ollama via the official `curl` install script

**Inside Ubuntu 24.04 WSL2 — what you never install:**
- Any `nvidia-driver-*` package
- `nvidia-kernel-*` packages
- The full CUDA runfile installer without the `--no-kernel-module` flag

According to the ITECS NVIDIA/WSL2 driver guide, the single most common mistake is running `ubuntu-drivers autoinstall` inside WSL2 — a command that works correctly on bare metal but causes immediate passthrough breakage in a WSL2 context. It's the kind of muscle memory command that feels right and breaks everything.

---

## Diagnosing and Repairing an Existing Broken Setup

If you're already hitting the mismatch error, the repair path is methodical.

First, check what's broken:

```bash
ls -la /usr/lib/wsl/lib/libcuda.so*
nvidia-smi
python3 -c "import ctypes; ctypes.CDLL('libcuda.so.1')"
```

If `libcuda.so` in `/usr/lib/wsl/lib/` is missing, or if `nvidia-smi` outputs `Driver/library version mismatch`, proceed with cleanup.

Remove the conflicting packages:

```bash
sudo apt purge nvidia-*
sudo apt autoremove
```

Then verify the WSL stub is intact:

```bash
ls /usr/lib/wsl/lib/
```

You should see `libcuda.so.1`, `libcudadebugger.so.1`, and related files. These are injected by Windows/WSL2 automatically — don't touch them. If they're missing, run `wsl --shutdown` from PowerShell and relaunch WSL2; they'll be remounted.

After cleanup, reinstall only the CUDA Toolkit using NVIDIA's official CUDA 12.x network installer for Ubuntu 24.04, selecting `cuda-toolkit-12-x` specifically — not `cuda`, which pulls in drivers. Then reinstall Ollama. On next launch, `ollama run llama3.1:8b` should immediately show GPU utilization via `nvidia-smi` in a parallel terminal.

---

## Setup Approach Comparison

| Approach | Driver Inside WSL2 | CUDA Toolkit | Ollama GPU Detection | Stability |
|---|---|---|---|---|
| **Correct (passthrough only)** | None | Toolkit only (no driver) | ✅ Works | High |
| **Broken (full driver install)** | nvidia-driver-535/545 | Full CUDA package | ❌ Mismatch error | Fails |
| **CUDA runfile (no-driver flag)** | None | Manual, precise | ✅ Works | High |
| **Ubuntu autoinstall** | Auto-selected, wrong | Included | ❌ Corrupts stub | Fails |
| **Docker + nvidia-container-toolkit** | None in container | In container image | ✅ Works (separate fix needed) | Medium |

The contrast between the correct and broken approaches is the frustrating part. Both *feel* correct during setup — `apt install` gives no warnings, everything appears to install cleanly. The failure only surfaces when Ollama runs inference and silently falls back to CPU.

The Docker path deserves a separate note. Running Ollama inside a Docker container on WSL2 requires `nvidia-container-toolkit` configured correctly with `nvidia-ctk runtime configure --runtime=docker`. The same core rule applies: no NVIDIA drivers inside the container or the WSL2 environment itself.

---

## Three Scenarios Worth Walking Through

**Scenario 1: Fresh Ubuntu 24.04 WSL2 install in 2026.**
Don't follow tutorials that predate the Ubuntu 24.04 + CUDA 12.x era. The NVIDIA CUDA on WSL User Guide (updated Q4 2025) is the ground truth. Install the CUDA network repo, pin `cuda-toolkit-12-6` or current, skip driver components entirely. Takes about 15 minutes and passthrough works on the first try.

**Scenario 2: Existing setup that broke after a Windows NVIDIA driver update.**
Windows driver updates don't touch `/usr/lib/wsl/lib/` directly — they update files on the Windows side. But if your WSL2 environment had a manually installed NVIDIA driver, the version delta between the old installed driver and new Windows-side driver widens after the update, making the mismatch error reappear. Full purge → toolkit reinstall → done.

**Scenario 3: Running multiple WSL2 distros with different CUDA requirements.**
Ubuntu 22.04 and Ubuntu 24.04 can coexist as WSL2 distros, but they share the same Windows-side NVIDIA driver. CUDA Toolkit versions inside each distro need to be compatible with that single driver version. As of NVIDIA driver 560, CUDA 11.x through 12.6 are supported. Installing CUDA 12.8 toolkit against a 555.x Windows driver will hit the version ceiling.

**One thing to watch:** NVIDIA's open-kernel-module transition — now default in driver 560+ — is gradually simplifying the WSL2 passthrough story. By Q3 2026, the distinction between "full driver" and "stub driver" in WSL2 contexts may be handled more gracefully by installer tooling. Until then, the manual approach above is the reliable path.

---

## What Comes Next

The driver mismatch error is solvable in under 30 minutes once you understand the actual architecture. Windows owns the driver. WSL2 gets a stub. Installing drivers inside Ubuntu 24.04 doesn't help — it breaks what already works.

The short version:

- NVIDIA driver 560+ on Windows is the minimum for CUDA 12.x WSL2 passthrough in 2026
- Never run `ubuntu-drivers autoinstall` or install `nvidia-driver-*` inside WSL2
- Purge conflicting packages, verify `/usr/lib/wsl/lib/` stub integrity, reinstall toolkit only
- Ollama silently falls back to CPU when CUDA context fails — always verify with `nvidia-smi` during active inference

NVIDIA's open-kernel-module rollout and ongoing WSL2 kernel updates should reduce friction over the next 6–12 months. Microsoft has been iterating on WSL2 GPU support consistently, and NVIDIA's installer tooling is slowly becoming WSL2-aware.

For now, the rule is simple: bookmark the NVIDIA CUDA on WSL User Guide and ignore any tutorial telling you to install GPU drivers inside the Linux environment. That single rule prevents the mismatch entirely.

Running Ollama through Docker instead of directly in WSL2? The container path has its own quirks — and they're worth covering separately.

## References

1. [Ollama Ubuntu 24.04 NVIDIA Install: Driver Pitfalls Guide | Blog // ITECS](https://itecsonline.com/post/ollama-ubuntu-nvidia)
2. [[WSL2 + Ubuntu 24.04 LTS] NVIDIA GPU detected but WSLg not working (OpenGL = llvmpipe) - Drivers - L](https://forums.developer.nvidia.com/t/wsl2-ubuntu-24-04-lts-nvidia-gpu-detected-but-wslg-not-working-opengl-llvmpipe/347383)
3. [WSL2 + Ollama on Windows: Complete Setup Guide (GPU Passthrough Included) | InsiderLLM](https://insiderllm.com/guides/wsl2-ollama-windows-setup-guide/)


---

*Photo by [BoliviaInteligente](https://unsplash.com/@boliviainteligente) on [Unsplash](https://unsplash.com/photos/a-number-of-cubes-with-the-word-swi-in-the-middle-tGkitDsOmmg)*
