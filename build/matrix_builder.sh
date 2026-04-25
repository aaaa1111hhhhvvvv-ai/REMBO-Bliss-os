#!/bin/bash
# ============================================================================
#  REMBO Universal Matrix Builder
#  Lead Architect: FERAS-AL-ABBADI
#  Description: Builds specialized driver packages for all GPU/CPU combinations
# ============================================================================

MATRIX_DIR="$(dirname "$(readlink -f "$0")")/.."
OUTPUT_DIR="$MATRIX_DIR/output"
MESA_SRC="/home/ubuntu/nvk-automation/mesa"
KERNEL_SRC="/home/ubuntu/REMBO_OS/kernel-zenith"

mkdir -p "$OUTPUT_DIR"

# ============================================================================
# NVIDIA GPU Profiles (Fermi → RTX 5090)
# ============================================================================
declare -A NVIDIA_PROFILES=(
    # [codename]="chip_family|vulkan_driver|gsp_support|firmware_dir"
    ["fermi"]="NVC0|nouveau|no|"
    ["kepler"]="NVE0|nouveau|no|"
    ["maxwell"]="NV110|nouveau|no|"
    ["pascal"]="NV130|nouveau|no|"
    ["volta"]="NV140|nouveau|no|"
    ["turing_1650"]="TU117|nouveau|yes|nvidia/tu117/gsp"
    ["turing_2060"]="TU106|nouveau|yes|nvidia/tu106/gsp"
    ["turing_2070"]="TU104|nouveau|yes|nvidia/tu104/gsp"
    ["turing_2080"]="TU102|nouveau|yes|nvidia/tu102/gsp"
    ["ampere_3060"]="GA106|nouveau|yes|nvidia/ga106/gsp"
    ["ampere_3070"]="GA104|nouveau|yes|nvidia/ga104/gsp"
    ["ampere_3080"]="GA102|nouveau|yes|nvidia/ga102/gsp"
    ["ampere_3090"]="GA102|nouveau|yes|nvidia/ga102/gsp"
    ["ada_4060"]="AD107|nouveau|yes|nvidia/ad107/gsp"
    ["ada_4060ti"]="AD106|nouveau|yes|nvidia/ad106/gsp"
    ["ada_4070"]="AD104|nouveau|yes|nvidia/ad104/gsp"
    ["ada_4080"]="AD103|nouveau|yes|nvidia/ad103/gsp"
    ["ada_4090"]="AD102|nouveau|yes|nvidia/ad102/gsp"
    ["blackwell_5070"]="GB205|nouveau|yes|nvidia/gb205/gsp"
    ["blackwell_5080"]="GB203|nouveau|yes|nvidia/gb203/gsp"
    ["blackwell_5090"]="GB202|nouveau|yes|nvidia/gb202/gsp"
)

# ============================================================================
# CPU Architecture Profiles
# ============================================================================
declare -A CPU_PROFILES=(
    # [name]="march_flag|description"
    ["core2"]="core2|Intel Core 2 Duo/Quad (Conroe/Penryn)"
    ["nehalem"]="nehalem|Intel 1st Gen Core i (Nehalem/Westmere)"
    ["sandybridge"]="sandybridge|Intel 2nd Gen (Sandy Bridge)"
    ["ivybridge"]="ivybridge|Intel 3rd Gen (Ivy Bridge)"
    ["haswell"]="haswell|Intel 4th Gen (Haswell)"
    ["broadwell"]="broadwell|Intel 5th Gen (Broadwell)"
    ["skylake"]="skylake|Intel 6th/7th Gen (Skylake/Kaby Lake)"
    ["cannonlake"]="cannonlake|Intel 8th Gen (Coffee Lake)"
    ["icelake"]="icelake-client|Intel 10th Gen (Ice Lake)"
    ["tigerlake"]="tigerlake|Intel 11th Gen (Tiger Lake)"
    ["alderlake"]="alderlake|Intel 12th Gen (Alder Lake)"
    ["raptorlake"]="raptorlake|Intel 13th/14th Gen (Raptor Lake)"
    ["arrowlake"]="arrowlake|Intel 15th Gen (Arrow Lake)"
    ["znver1"]="znver1|AMD Zen 1 (Ryzen 1000/2000)"
    ["znver2"]="znver2|AMD Zen 2 (Ryzen 3000)"
    ["znver3"]="znver3|AMD Zen 3 (Ryzen 5000)"
    ["znver4"]="znver4|AMD Zen 4 (Ryzen 7000)"
    ["znver5"]="znver5|AMD Zen 5 (Ryzen 9000)"
    ["bdver1"]="bdver1|AMD Bulldozer (FX Series)"
    ["btver2"]="btver2|AMD Jaguar (APU)"
    ["k8"]="k8|AMD Athlon 64 / Phenom"
    ["generic"]="x86-64-v3|Generic x86-64 v3 (AVX2)"
)

# ============================================================================
# Build Functions
# ============================================================================
build_mesa_for_cpu() {
    local cpu_name="$1"
    local march_flag="$2"
    local gpu_name="$3"

    echo "[MATRIX] Building Mesa NVK for CPU=$cpu_name (${march_flag}) GPU=$gpu_name"

    local build_dir="$MESA_SRC/build_matrix_${cpu_name}_${gpu_name}"
    local install_dir="$OUTPUT_DIR/mesa_${cpu_name}_${gpu_name}"

    cd "$MESA_SRC"

    meson setup "$build_dir" \
        -Dplatforms=x11,wayland \
        -Dvulkan-drivers=nouveau \
        -Dgallium-drivers=nouveau \
        -Dbuildtype=release \
        -Db_ndebug=true \
        -Dc_args="-O2 -march=${march_flag}" \
        -Dcpp_args="-O2 -march=${march_flag}" \
        --prefix=/usr/local 2>/dev/null

    if [ $? -eq 0 ]; then
        ninja -C "$build_dir" -j$(nproc) 2>/dev/null
        if [ $? -eq 0 ]; then
            DESTDIR="$install_dir" ninja -C "$build_dir" install 2>/dev/null
            echo "[MATRIX] SUCCESS: Mesa built for ${cpu_name}+${gpu_name}"

            # Create package
            create_package "$cpu_name" "$gpu_name" "$install_dir"
            return 0
        fi
    fi

    echo "[MATRIX] FAILED: Mesa build for ${cpu_name}+${gpu_name}"
    return 1
}

create_package() {
    local cpu_name="$1"
    local gpu_name="$2"
    local install_dir="$3"
    local pkg_name="rembo-drivers-${gpu_name}-${cpu_name}"
    local pkg_dir="$OUTPUT_DIR/packages/${pkg_name}"
    local pkg_file="$OUTPUT_DIR/packages/${pkg_name}.zip"

    mkdir -p "$pkg_dir/system/lib64/hw"
    mkdir -p "$pkg_dir/system/lib64/dri"
    mkdir -p "$pkg_dir/META-INF"

    # Copy driver files
    find "$install_dir" -name "libvulkan_nouveau.so" -exec cp {} "$pkg_dir/system/lib64/hw/vulkan.nouveau.so" \;
    find "$install_dir" -name "nouveau_dri.so" -exec cp {} "$pkg_dir/system/lib64/dri/" \;

    # Create package metadata
    cat > "$pkg_dir/META-INF/package.json" << EOF
{
    "name": "$pkg_name",
    "version": "1.0.0",
    "cpu_arch": "$cpu_name",
    "gpu_target": "$gpu_name",
    "mesa_version": "26.2.0-devel",
    "build_date": "$(date -Iseconds)",
    "architect": "FERAS-AL-ABBADI"
}
EOF

    # Create zip package
    cd "$pkg_dir" && zip -r "$pkg_file" . 2>/dev/null
    local hash=$(sha256sum "$pkg_file" 2>/dev/null | awk '{print $1}')
    echo "[MATRIX] Package created: $pkg_file (SHA256: $hash)"
}

generate_manifest() {
    echo "[MATRIX] Generating Universal Matrix manifest..."

    local manifest="$OUTPUT_DIR/packages/manifest.json"
    echo '{"packages":[' > "$manifest"

    local first=true
    for pkg in "$OUTPUT_DIR/packages"/*.zip; do
        [ -f "$pkg" ] || continue
        local name=$(basename "$pkg" .zip)
        local hash=$(sha256sum "$pkg" | awk '{print $1}')
        local size=$(stat -c %s "$pkg")

        [ "$first" = true ] && first=false || echo ',' >> "$manifest"

        cat >> "$manifest" << EOF
{
    "name": "$name",
    "file": "$(basename $pkg)",
    "sha256": "$hash",
    "size": $size,
    "url": "https://github.com/$GITHUB_REPO/releases/download/v1.0/$name.zip"
}
EOF
    done

    echo ']}' >> "$manifest"
    echo "[MATRIX] Manifest generated: $manifest"
}

# ============================================================================
# Main Build Matrix
# ============================================================================
build_pure_master() {
    echo "============================================"
    echo "  Building Pure Master (i5-12400F + RTX 4060 Ti)"
    echo "============================================"
    build_mesa_for_cpu "alderlake" "alderlake" "ada_4060ti"
}

build_universal_matrix() {
    echo "============================================"
    echo "  Building Universal Matrix"
    echo "============================================"

    local total=0
    local success=0
    local failed=0

    # Build for each CPU profile with the nouveau driver
    for cpu_key in "${!CPU_PROFILES[@]}"; do
        IFS='|' read -r march desc <<< "${CPU_PROFILES[$cpu_key]}"

        echo ""
        echo "--- Building for $desc ($march) ---"
        build_mesa_for_cpu "$cpu_key" "$march" "nouveau_universal"

        if [ $? -eq 0 ]; then
            success=$((success+1))
        else
            failed=$((failed+1))
        fi
        total=$((total+1))
    done

    echo ""
    echo "============================================"
    echo "  Universal Matrix Build Summary"
    echo "  Total: $total | Success: $success | Failed: $failed"
    echo "============================================"

    generate_manifest
}

# ============================================================================
# Entry Point
# ============================================================================
case "$1" in
    master)   build_pure_master ;;
    matrix)   build_universal_matrix ;;
    package)  create_package "$2" "$3" "$4" ;;
    manifest) generate_manifest ;;
    *)
        echo "REMBO Universal Matrix Builder v1.0"
        echo "Usage: $0 {master|matrix|package|manifest}"
        echo "  master   - Build Pure Master (i5-12400F + RTX 4060 Ti)"
        echo "  matrix   - Build Universal Matrix (all CPU/GPU combos)"
        echo "  package  - Create package from build output"
        echo "  manifest - Generate package manifest"
        ;;
esac
