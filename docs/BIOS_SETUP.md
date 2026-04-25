# REMBO-Bliss-os — Optimal BIOS Configuration Guide

**Project:** REMBO-Bliss-os (Sovereign Edition)
**Lead Architect:** FERAS-AL-ABBADI
**Purpose:** Mandatory BIOS settings to achieve 100/100 Forensic Score and unlock full Sovereign Stack performance (180Hz display, 8000Hz input, Re-Size BAR GPU acceleration).

---

> **Warning:** These settings must be applied BEFORE booting the REMBO-Bliss-os ISO. Incorrect BIOS configuration will result in degraded performance, boot failures, or disabled hardware features.

---

## 1. Boot Configuration

These settings ensure the ISO boots correctly in pure UEFI mode without legacy interference.

| Setting | Value | Reason |
|---------|-------|--------|
| **Fast Boot** | **Disabled** | Fast Boot skips USB device initialization — the USB drive will not be detected if enabled |
| **Secure Boot** | **Disabled** | REMBO-Bliss-os uses a custom kernel (6.14.0) with unsigned modules. Secure Boot will block the kernel from loading |
| **CSM Support** | **Disabled** | CSM (Compatibility Support Module) forces legacy BIOS mode. REMBO requires pure UEFI for GPT partition support and EFI bootloader |

### How to find these settings:
- **ASUS:** Advanced → Boot → Fast Boot / Secure Boot / CSM
- **MSI:** Settings → Boot → Fast Boot / Settings → Security → Secure Boot
- **Gigabyte:** Boot → Fast Boot / Boot → CSM Support / Boot → Secure Boot
- **ASRock:** Boot → Fast Boot / Security → Secure Boot / Boot → CSM

---

## 2. CPU & Memory Optimization

These settings unlock the full potential of your CPU and memory for the Sovereign Performance Governor.

| Setting | Value | Reason |
|---------|-------|--------|
| **XMP / D.O.C.P** | **Enabled** | Activates the rated speed of your RAM (e.g., DDR4-3200 / DDR5-6000). Without this, RAM runs at base JEDEC speed (2133/4800 MHz), reducing performance by 20-40% |
| **Intel Virtualization (VT-x)** | **Enabled** | Required for KVM-Masking in the Stealth Stack. Also needed for Android's ART runtime optimizations |
| **VT-d (Directed I/O)** | **Enabled** | Enables IOMMU for direct GPU passthrough and secure DMA. Required for the KVM Masking identity spoof to function correctly |

### XMP/D.O.C.P Location by Motherboard:
- **ASUS:** AI Tweaker → XMP (Intel) / D.O.C.P (AMD)
- **MSI:** OC → Memory → XMP
- **Gigabyte:** Tweaker → Extreme Memory Profile (XMP)
- **ASRock:** OC Tweaker → DRAM Configuration → Load XMP Setting

### For Intel i5-12400F (Pure Master Target):
- VT-x: Advanced → CPU Configuration → Intel Virtualization Technology → **Enabled**
- VT-d: Advanced → System Agent Configuration → VT-d → **Enabled**

---

## 3. Graphics & PCIe Configuration

These settings are **critical** for NVIDIA RTX 4060 Ti (AD106) GPU acceleration with Mesa NVK.

| Setting | Value | Reason |
|---------|-------|--------|
| **Re-Size BAR Support** | **Enabled** | Allows the CPU to access the full GPU VRAM (8 GB) directly instead of 256 MB windows. Provides 5-15% performance improvement in GPU-intensive workloads |
| **Above 4G Decoding** | **Enabled** | **Required** for Re-Size BAR to work. Maps GPU VRAM above the 4 GB address space. Must be enabled FIRST before Re-Size BAR appears as an option |
| **Primary Display** | **PCIE** | Forces the system to use the discrete GPU (RTX 4060 Ti) instead of integrated graphics. The i5-12400F has no iGPU, but this setting prevents fallback to non-existent integrated graphics |

### Important Notes:
- **Above 4G Decoding** must be enabled BEFORE **Re-Size BAR** becomes visible in BIOS
- If Re-Size BAR is not visible, enable Above 4G Decoding first, save & reboot, then Re-Size BAR will appear
- These settings directly affect how `nouveau.ko` and `vulkan.nouveau.so` interact with the GPU VRAM

### Location by Motherboard:
- **ASUS:** Advanced → PCI Subsystem Settings → Above 4G Decoding / Re-Size BAR
- **MSI:** Settings → Advanced → PCI Subsystem Settings → Above 4G / Re-Size BAR
- **Gigabyte:** Settings → IO Ports → Above 4G Decoding / Re-Size BAR
- **ASRock:** Advanced → PCI Configuration → Above 4G Decoding / Re-Size BAR

---

## 4. USB & Peripherals

These settings ensure 8000Hz USB polling and proper peripheral detection in Android-x86.

| Setting | Value | Reason |
|---------|-------|--------|
| **XHCI Hand-off** | **Enabled** | Transfers USB 3.x controller ownership from BIOS to the OS. Without this, USB devices may not work after Android boots because BIOS retains control |
| **Legacy USB Support** | **Enabled** | Ensures USB keyboard/mouse work during GRUB boot menu and early boot stages before the kernel loads XHCI drivers |

### Why This Matters for 8000Hz Polling:
The Sovereign Stack sets `usbhid.mousepoll=1` (1000Hz base) and uses IRQ affinity + FIQ for 8000Hz effective polling. XHCI Hand-off is mandatory — without it, the kernel cannot access the USB controller to apply these optimizations.

### Location by Motherboard:
- **ASUS:** Advanced → USB Configuration → XHCI Hand-off / Legacy USB
- **MSI:** Settings → Advanced → USB Configuration → XHCI Hand-off
- **Gigabyte:** Settings → IO Ports → USB Configuration → XHCI Hand-off
- **ASRock:** Advanced → USB Configuration → XHCI Hand-off

---

## Quick Reference — Complete BIOS Checklist

Copy this checklist and verify each setting before booting REMBO-Bliss-os:

```
[ ] Fast Boot ..................... Disabled
[ ] Secure Boot .................. Disabled
[ ] CSM Support .................. Disabled
[ ] XMP / D.O.C.P ............... Enabled
[ ] Intel VT-x .................. Enabled
[ ] VT-d ........................ Enabled
[ ] Above 4G Decoding ........... Enabled
[ ] Re-Size BAR Support ......... Enabled
[ ] Primary Display .............. PCIE
[ ] XHCI Hand-off ............... Enabled
[ ] Legacy USB Support ........... Enabled
```

> After applying all settings, press **F10** to save and exit BIOS.

---

## Relationship to Forensic Score

These BIOS settings are directly linked to the **100/100 Forensic Certification**:

| BIOS Setting | Forensic Pillar | Impact if Wrong |
|-------------|----------------|-----------------|
| Secure Boot OFF | Pillar 3 (ABI Sync) | Kernel modules blocked from loading → GPU driver fails |
| CSM OFF | Pillar 1 (Firmware) | Legacy boot mode skips EFI partition → GSP firmware not found |
| Re-Size BAR ON | Pillar 2 (Optimization) | GPU limited to 256 MB BAR → NVK performance drops 15% |
| Above 4G ON | Pillar 2 (Optimization) | Required for Re-Size BAR → same impact as above |
| XHCI Hand-off ON | Sovereign Stack | USB controller locked by BIOS → 8000Hz polling disabled |
| XMP/D.O.C.P ON | Sovereign Stack | RAM at JEDEC base speed → Performance Governor cannot reach full turbo |
| VT-x + VT-d ON | Sovereign Stack | KVM Masking fails → device identity exposed |

---

## Troubleshooting

### USB Drive Not Detected
1. Verify **Fast Boot** is disabled
2. Verify **Legacy USB Support** is enabled
3. Try a different USB port (use rear USB 3.0 ports, not front panel)

### Black Screen After Boot
1. Verify **CSM Support** is disabled (must be pure UEFI)
2. Verify **Primary Display** is set to PCIE
3. Verify **Secure Boot** is disabled

### GPU Not Detected / Low Performance
1. Enable **Above 4G Decoding** first, save & reboot
2. Then enable **Re-Size BAR Support**
3. Verify GPU is in the top PCIe x16 slot

### Keyboard/Mouse Not Working in GRUB Menu
1. Enable **Legacy USB Support**
2. Enable **XHCI Hand-off**

---

<div align="center">

**REMBO-Bliss-os Sovereign Edition**
**BIOS Configuration Guide v1.0**

Lead Architect: **FERAS-AL-ABBADI** | [@684ao](https://instagram.com/684ao)

</div>
