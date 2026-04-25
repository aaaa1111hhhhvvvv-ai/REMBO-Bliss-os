# Changelog

## [1.0.0] — 2025-04-25

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
