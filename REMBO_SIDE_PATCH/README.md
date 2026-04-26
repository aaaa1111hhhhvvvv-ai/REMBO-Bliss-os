# REMBO Sovereign Side-Patch

**Lead Architect:** FERAS-AL-ABBADI
**Version:** 1.0.0
**Target Hardware:** Intel i5-12400F (Alder Lake) + NVIDIA RTX 4060 Ti (AD106)

---

## What is this?

A self-contained injection suite that transforms a stock BlissOS 16.9.7 installation into the REMBO-Bliss-os Sovereign Edition. It uses the **initrd Line 390 Hook** — a script auto-sourcing mechanism in the BlissOS init process — to apply OverlayFS-based modifications before Android's own init takes over.

**Mode:** Fully Offline — Zero Internet Dependency

---

## How It Works

```
BlissOS initrd /init (line 390-393):
    for s in `ls /scripts/* /src/scripts/*`; do
        test -e "$s" && source $s
    done

→ Our script at scripts/99-rembo-atomic-patch is auto-sourced here
→ "99-" prefix ensures it runs LAST (after 0-auto-detect, 2-mount, etc.)
→ Full root access, Android /system already mounted at /android/system
→ OverlayFS applied BEFORE switch_root to Android init
```

---

## Directory Structure

```
REMBO_SIDE_PATCH/
├── scripts/
│   └── 99-rembo-atomic-patch        ← Trigger script (Line 390 hook)
├── overlay/                          ← OverlayFS upper directory
│   ├── bin/
│   │   ├── rembo-sovereign-init.sh   ← 6-layer boot optimizer
│   │   └── rembo-sentinel.sh         ← Background update daemon
│   ├── lib64/
│   │   ├── hw/vulkan.nouveau.so      ← NVK Vulkan driver (user-supplied)
│   │   ├── dri/nouveau_dri.so        ← DRI driver (user-supplied)
│   │   └── libzstd.so.1              ← Dependency (user-supplied)
│   ├── lib/
│   │   ├── firmware/nvidia/ad106/gsp/ ← 8 GSP firmware binaries (user-supplied)
│   │   └── modules/                   ← Kernel modules (user-supplied)
│   └── priv-app/
│       └── REMBOHealthCheck/          ← Health check APK (user-supplied)
├── configs/
│   ├── sovereign_build.prop          ← System properties (180Hz, 8000Hz, BBR, KVM mask)
│   └── grub_sovereign.cfg           ← Sovereign GRUB configuration
├── verify/
│   ├── verify-integrity.sh           ← Pre-deployment verification tool
│   └── SHA256SUMS.txt                ← Generated hash manifest
└── README.md                         ← This file
```

---

## Deployment

### Step 1: Supply Binary Assets

The following files must be compiled/acquired and placed in the overlay:

| File | Source | Required |
|------|--------|----------|
| `overlay/lib64/hw/vulkan.nouveau.so` | Mesa NVK build (`-march=alderlake`) | Recommended |
| `overlay/lib64/dri/nouveau_dri.so` | Mesa Gallium build | Recommended |
| `overlay/lib/firmware/nvidia/ad106/gsp/*.bin` | linux-firmware repo | Required for GPU |
| `overlay/lib/modules/` | Kernel 6.14.0 build | If upgrading kernel |
| `overlay/priv-app/REMBOHealthCheck/REMBOHealthCheck.apk` | AAPT2 build | Optional |

### Step 2: Verify Integrity

```bash
chmod +x verify/verify-integrity.sh
./verify/verify-integrity.sh
```

### Step 3: Copy to Boot Device

```
USB_ROOT/
├── kernel                    ← Sovereign kernel 6.14.0 (optional upgrade)
├── initrd.img
├── system.efs
├── scripts/
│   └── 99-rembo-atomic-patch ← Copy from REMBO_SIDE_PATCH/scripts/
└── REMBO_SIDE_PATCH/         ← Copy entire directory
    ├── overlay/
    ├── configs/
    └── ...
```

### Step 4: Boot

Boot from the USB drive. The `99-rembo-atomic-patch` script will automatically:
1. Verify the REMBO_SIDE_PATCH directory exists
2. Set up OverlayFS (RAM-backed if data partition unavailable)
3. Inject GPU drivers and GSP firmware
4. Merge Sovereign properties into build.prop
5. Stage Sovereign init and Sentinel scripts
6. Mount OverlayFS over /android/system
7. Run 10-point boot flow verification
8. Hand off to Android init with all modifications active

---

## GRUB Configuration

For the full Sovereign experience, replace the boot device's GRUB config with `configs/grub_sovereign.cfg`. This adds:

- `nouveau.config=NvGspRm=1` — Enable GSP firmware
- `video=1920x1080@180` — Force 180Hz
- `usbhid.mousepoll=1` — 8000Hz USB polling
- `VULKAN=1 HWACCEL=1` — Hardware acceleration
- `HWC=drm_minigbm GRALLOC=minigbm` — Display compositor

---

*Lead Architect: FERAS-AL-ABBADI*
