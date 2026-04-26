#!/bin/bash
# ============================================================================
#  REMBO Side-Patch Integrity Verification
#  Lead Architect: FERAS-AL-ABBADI
#  Purpose: Verify all patch files are present and intact before deployment
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass=0
warn=0
fail=0
total=0

check_file() {
    local path="$1"
    local desc="$2"
    local required="$3"  # "required" or "optional"
    total=$((total + 1))

    if [ -f "$PATCH_ROOT/$path" ]; then
        local size=$(stat -c%s "$PATCH_ROOT/$path" 2>/dev/null || stat -f%z "$PATCH_ROOT/$path" 2>/dev/null || echo "?")
        local hash=$(sha256sum "$PATCH_ROOT/$path" 2>/dev/null | cut -d' ' -f1 || echo "N/A")
        echo -e "  ${GREEN}[OK]${NC}   $desc"
        echo "         Path: $path"
        echo "         Size: $size bytes"
        echo "         SHA256: ${hash:0:16}..."
        pass=$((pass + 1))
    elif [ "$required" = "required" ]; then
        echo -e "  ${RED}[FAIL]${NC} $desc"
        echo "         Missing: $path"
        fail=$((fail + 1))
    else
        echo -e "  ${YELLOW}[WARN]${NC} $desc"
        echo "         Optional, not found: $path"
        warn=$((warn + 1))
    fi
}

check_dir() {
    local path="$1"
    local desc="$2"
    total=$((total + 1))

    if [ -d "$PATCH_ROOT/$path" ]; then
        local count=$(find "$PATCH_ROOT/$path" -type f | wc -l)
        echo -e "  ${GREEN}[OK]${NC}   $desc ($count files)"
        pass=$((pass + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} $desc"
        echo "         Missing directory: $path"
        fail=$((fail + 1))
    fi
}

echo ""
echo "============================================"
echo " REMBO Side-Patch Integrity Verification"
echo " Lead Architect: FERAS-AL-ABBADI"
echo "============================================"
echo ""

# --- Structure ---
echo -e "${CYAN}[1/6] Directory Structure${NC}"
check_dir  "scripts"                        "Trigger scripts directory"
check_dir  "overlay"                        "Overlay data directory"
check_dir  "configs"                        "Configuration directory"
check_dir  "verify"                         "Verification directory"
echo ""

# --- Trigger Script ---
echo -e "${CYAN}[2/6] Trigger Script (Line 390 Hook)${NC}"
check_file "scripts/99-rembo-atomic-patch"  "Atomic patch trigger script" "required"
echo ""

# --- Configs ---
echo -e "${CYAN}[3/6] Sovereign Configuration${NC}"
check_file "configs/sovereign_build.prop"   "Sovereign system properties" "required"
check_file "configs/grub_sovereign.cfg"     "Sovereign GRUB config" "required"
echo ""

# --- Overlay: GPU Stack ---
echo -e "${CYAN}[4/6] GPU Stack (Mesa NVK + GSP)${NC}"
check_file "overlay/lib64/hw/vulkan.nouveau.so"              "NVK Vulkan driver" "optional"
check_file "overlay/lib64/hw/DRIVER_MANIFEST.txt"            "NVK build instructions" "required"
check_file "overlay/lib64/dri/nouveau_dri.so"                "DRI Gallium driver" "optional"
check_dir  "overlay/lib/firmware/nvidia/ad106/gsp"           "GSP firmware directory"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/FIRMWARE_MANIFEST.txt" "GSP firmware manifest" "required"
# Individual firmware binaries (optional — user must supply from linux-firmware)
check_file "overlay/lib/firmware/nvidia/ad106/gsp/booter_load-535.113.01.bin"   "GSP booter_load 535"   "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/booter_load-570.144.bin"      "GSP booter_load 570"   "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/booter_unload-535.113.01.bin" "GSP booter_unload 535" "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/booter_unload-570.144.bin"    "GSP booter_unload 570" "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/bootloader-535.113.01.bin"    "GSP bootloader 535"    "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/bootloader-570.144.bin"       "GSP bootloader 570"    "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/gsp-535.113.01.bin"           "GSP main 535"          "optional"
check_file "overlay/lib/firmware/nvidia/ad106/gsp/scrubber-570.144.bin"         "GSP scrubber 570"      "optional"
echo ""

# --- Overlay: Sovereign Scripts ---
echo -e "${CYAN}[5/6] Sovereign Stack Scripts${NC}"
check_file "overlay/bin/rembo-sovereign-init.sh"              "Boot-time optimizer (6 layers)" "required"
check_file "overlay/bin/rembo-sentinel.sh"                    "Background update daemon" "required"
check_file "overlay/priv-app/REMBOHealthCheck/REMBOHealthCheck.apk" "Health Check APK" "optional"
echo ""

# --- Readme ---
echo -e "${CYAN}[6/6] Documentation${NC}"
check_file "README.md"                                        "Side-Patch README" "required"
echo ""

# --- Summary ---
echo "============================================"
echo -e " Results: ${GREEN}$pass passed${NC}, ${YELLOW}$warn warnings${NC}, ${RED}$fail failed${NC} (total: $total)"

if [ "$fail" -eq 0 ]; then
    echo -e " ${GREEN}STATUS: VERIFIED — Ready for deployment${NC}"
    echo ""
    echo " To deploy: Copy REMBO_SIDE_PATCH/ to USB root alongside"
    echo "            system.efs, kernel, and initrd.img."
    echo "            Copy scripts/99-rembo-atomic-patch to the"
    echo "            boot device's scripts/ directory."
else
    echo -e " ${RED}STATUS: INCOMPLETE — $fail required file(s) missing${NC}"
    echo ""
    echo " Review the [FAIL] items above and supply missing files."
fi
echo "============================================"

# --- Generate hash manifest ---
echo ""
echo "Generating SHA256 manifest..."
MANIFEST="$PATCH_ROOT/verify/SHA256SUMS.txt"
find "$PATCH_ROOT" -type f -not -path "*/verify/SHA256SUMS.txt" -not -path "*/.git/*" | sort | while read -r f; do
    sha256sum "$f" 2>/dev/null
done > "$MANIFEST"
echo "Manifest written to: verify/SHA256SUMS.txt"
echo "Package hash: $(sha256sum "$MANIFEST" 2>/dev/null | cut -d' ' -f1)"
echo ""

exit $fail
