# Changelog

## [1.0.1] — 2026-04-25

### Master Fix — 100/100 Perfection Cycle

#### Fixes Applied
- **FIX #1:** Recompiled Universal kernel + modules with `-march=x86-64-v3` (unique binary, not copied from Sovereign)
- **FIX #2:** Removed 225 broken ALSA symlinks (ARM/SoC board configs) from both ISOs
- **FIX #3:** Compiled HealthCheckActivity.java → APK, injected into `system/priv-app/REMBOHealthCheck/`
- **FIX #4:** Corrected Sentinel `GITHUB_RAW` URL to `sovereign-edition-v1` branch

#### New Files
- `sovereign/HealthCheckReceiver.java` — BOOT_COMPLETED receiver for Health Check
- `sovereign/AndroidManifest.xml` — APK build manifest
- `audit/FINAL_CERTIFICATION_100_100.md` — Master Fix certification (100/100, 0.0% error)

#### ISO Updates
- **Sovereign Edition:** `REMBO-Bliss-os-Sovereign-Edition-FINAL.iso` (MD5: `738ce1506755db4a80c81b0dc8c90081`)
- **Universal Edition:** `REMBO-Bliss-os-Universal-Edition-FINAL.iso` (MD5: `d4afec6a73596d8a08c403a0f467bb8f`)

---

## [1.0.0] — 2026-04-25

### The Sovereign Edition — Initial Release

#### Pure Master ISO
- Built from Bliss OS 16.9.7 base
- Linux Kernel 6.14.0 compiled with `-march=alderlake -O2`
- Mesa NVK 26.2.0-devel Vulkan driver (ABI-matched to kernel headers)
- NVIDIA AD106 GSP firmware (535.113.01 + 570.144)
- Forensic Score: **100/100** (4-Pillar Certified)

#### Sovereign Feature Stack
- 8000Hz input polling (USB HID + IRQ affinity)
- Google BBR TCP congestion control + FQ qdisc
- 512MB RAM-Disk asset cache
- REMBO-Performance Governor (max turbo lock)
- KVM Masking + device identity spoofing
- ChromeOS libndk ARM translation layer

#### Sentinel System
- Background update daemon with OverlayFS
- SHA256-verified package downloads
- Anti-loop blacklist for failed updates
- Weekly health check GUI popup (with silence checkbox)
- Self-test verification (5-point check)

#### Cloud Sentinel (GitHub Actions)
- Weekly upstream monitoring (Mesa, linux-firmware)
- Auto-build for 6 CPU architectures (Alder Lake, Haswell, Skylake, Zen 3, Zen 4, Generic)
- Automated release publishing with manifest

#### Universal Driver Matrix
- 10 NVIDIA GPU generations supported (Fermi to Blackwell)
- 21 CPU architecture profiles (Core 2 Duo to Arrow Lake, Phenom to Zen 5)
- Build pipeline for all combinations

---

*Lead Architect: FERAS-AL-ABBADI*
