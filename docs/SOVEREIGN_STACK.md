# REMBO-Bliss-os Sovereign Stack — Technical Documentation

## Overview

The Sovereign Stack is a layered performance and security architecture that transforms a standard Bliss OS 16.9.7 installation into a gaming-optimized, self-evolving platform. Each layer is applied at boot time via the `rembo-sovereign-init.sh` script.

---

## Layer 1: Input Optimization (8000Hz Polling)

### Implementation
- USB HID `mousepoll` parameter set to 1ms (kernel module parameter)
- GRUB boot parameter: `usbhid.mousepoll=1`
- IRQ affinity pinned to performance cores (bitmask `0x3f` for 6 P-cores on i5-12400F)
- Kernel scheduler granularity reduced to 100us
- Timer migration disabled to prevent latency spikes from core-to-core handoff

### Technical Notes
- True 8000Hz requires hardware support (mouse firmware)
- Kernel-side polling at 1ms (1000Hz) is the maximum supported by USB HID spec
- Combined with 1000Hz kernel tick rate (`CONFIG_HZ=1000`) for sub-ms response

---

## Layer 2: Network Optimization (BBR + eBPF)

### BBR (Bottleneck Bandwidth and Round-trip propagation time)
Google's TCP congestion control algorithm, designed for:
- Higher throughput on lossy networks
- Lower latency than CUBIC (Linux default)
- Better queue management (reduces bufferbloat)

### Configuration
```
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_low_latency = 1
net.ipv4.tcp_fastopen = 1
net.ipv4.tcp_slow_start_after_idle = 0
```

### Buffer Tuning
- `rmem_max` / `wmem_max` = 16MB (prevents buffer starvation on fast networks)
- TCP window scaling enabled by default in kernel 6.14.0

---

## Layer 3: Storage Optimization (RAM-Disk Asset Loader)

### Implementation
- 512MB `tmpfs` mounted at `/data/ramdisk_cache`
- Games/apps can use this as a fast cache for frequently accessed assets
- I/O scheduler set to `none` for NVMe (bypasses unnecessary scheduling overhead)
- Read-ahead reduced to 128KB (optimized for random I/O patterns in games)

### Dirty Page Tuning
```
vm.dirty_ratio = 80          (allow 80% of RAM for dirty pages before forced writeback)
vm.dirty_background_ratio = 50 (start background writeback at 50%)
vm.vfs_cache_pressure = 100    (balanced inode/dentry cache reclaim)
```

---

## Layer 4: REMBO-Performance Governor

### CPU Configuration
- All cores locked to `performance` governor (no frequency scaling)
- Intel P-state: `min_perf_pct = 100`, `no_turbo = 0` (turbo boost enabled, always at max)
- Deep C-states (C1E, C3, C6) disabled via `cpuidle/state[1-9]/disable`
- Result: CPU never drops below max turbo frequency

### GPU Configuration
- `power_dpm_force_performance_level = high`
- Nouveau pstate forced to maximum
- VULKAN=1 and HWACCEL=1 boot flags ensure hardware acceleration path

---

## Layer 5: Stealth Shield (KVM Masking)

### Device Identity Spoofing
The following Android system properties are overridden at boot:

| Property | Spoofed Value |
|----------|--------------|
| `ro.product.model` | REMBO-Gaming-PC |
| `ro.product.manufacturer` | REMBO-Systems |
| `ro.product.brand` | REMBO |
| `ro.build.fingerprint` | REMBO/rembo_x86_64/... |
| `ro.kernel.qemu` | 0 |
| `ro.hardware.virtual_device` | 0 |

### Purpose
- Prevents app-side detection of Android-x86 as an "emulator"
- Bypasses games that block emulator environments
- EDID spoofing masks monitor identification via DRM subsystem

---

## Layer 6: ARM Translation Layer

### libndk_translation (ChromeOS)
- Translates ARM native code to x86_64 at runtime
- Enables ARM-only games and apps to run on x86 hardware
- JIT cache size increased to 512MB for better translation performance
- DEX2OAT compilation threads set to 6 (matching i5-12400F P-core count)

### Fallback: Houdini
- Intel's proprietary ARM translation layer
- Used as fallback if libndk is not present in the system image

---

## Boot Parameter Reference

| Parameter | Purpose |
|-----------|---------|
| `nouveau.config=NvGspRm=1` | Enable GSP firmware for NVIDIA GPU |
| `nouveau.debug=info,VBIOS=info,PWR=debug` | Verbose GPU debugging |
| `video=1920x1080@180` | Force 180Hz display mode |
| `VULKAN=1` | Enable Vulkan rendering path |
| `HWACCEL=1` | Enable hardware acceleration |
| `HWC=drm_minigbm` | Use minigbm Hardware Composer |
| `GRALLOC=minigbm` | Use minigbm graphics allocator |
| `usbhid.mousepoll=1` | Maximum USB polling rate |
| `androidboot.selinux=permissive` | SELinux in permissive mode |
| `androidboot.selinux=0` | Disable SELinux enforcement |

---

*Documentation by FERAS-AL-ABBADI*
