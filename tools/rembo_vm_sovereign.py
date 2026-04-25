#!/usr/bin/env python3
"""
REMBO-VM Sovereign Emulator
============================
A standalone GUI application that uses QEMU to create a hardware-accurate
simulation of the REMBO-Bliss-os Sovereign Edition target platform.

Target Hardware:
  - CPU: Intel Core i5-12400F (Alder Lake, 6C/12T)
  - GPU: NVIDIA RTX 4060 Ti (AD106, PCI 0x10de:0x2803)

Lead Architect: FERAS-AL-ABBADI
Project: REMBO-Bliss-os (Sovereign Edition)
"""

import ctypes
import datetime
import os
import platform
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

# ---------------------------------------------------------------------------
# Dependency bootstrap — install customtkinter if absent
# ---------------------------------------------------------------------------
try:
    import customtkinter as ctk
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_TITLE = "REMBO-VM Sovereign Emulator"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
DEFAULT_RAM_MB = 8192
DISK_NAME = "rembo_sovereign_drive.qcow2"
DISK_SIZE = "32G"
LOG_FILE = "rembo_vm_sovereign.log"

# QEMU well-known install locations on Windows
QEMU_WIN_PATHS = [
    Path(r"C:\Program Files\qemu"),
    Path(r"C:\Program Files (x86)\qemu"),
    Path(os.environ.get("LOCALAPPDATA", ""), "Programs", "qemu"),
]

# Hardware spoof flags (Sovereign Master Target)
CPU_FLAGS = "host,+avx2,+fma,+vaes,+vpclmulqdq"
GPU_DEVICE = "virtio-gpu-pci,vendorid=0x10de,deviceid=0x2803"
SMP_CONFIG = "cores=6,threads=2"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def is_windows() -> bool:
    return platform.system() == "Windows"


def is_admin() -> bool:
    if not is_windows():
        return os.geteuid() == 0
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _find_qemu_binary() -> str | None:
    """Locate qemu-system-x86_64 on the host, checking PATH and common dirs."""
    # 1. Check PATH
    binary = "qemu-system-x86_64.exe" if is_windows() else "qemu-system-x86_64"
    found = shutil.which(binary)
    if found:
        return found

    # 2. Check well-known Windows directories
    if is_windows():
        for base in QEMU_WIN_PATHS:
            candidate = base / binary
            if candidate.is_file():
                return str(candidate)

    return None


def _find_qemu_img() -> str | None:
    """Locate qemu-img on the host."""
    binary = "qemu-img.exe" if is_windows() else "qemu-img"
    found = shutil.which(binary)
    if found:
        return found

    if is_windows():
        for base in QEMU_WIN_PATHS:
            candidate = base / binary
            if candidate.is_file():
                return str(candidate)

    return None


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class REMBOEmulatorApp(ctk.CTk):
    """Main GUI window for the REMBO-VM Sovereign Emulator."""

    def __init__(self) -> None:
        super().__init__()

        # -- Window setup ------------------------------------------------
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(900, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # -- State -------------------------------------------------------
        self.iso_path: str = ""
        self.qemu_bin: str | None = None
        self.qemu_img: str | None = None
        self.qemu_process: subprocess.Popen | None = None
        self.log_file_handle = open(LOG_FILE, "a", encoding="utf-8")

        # -- Build UI ----------------------------------------------------
        self._build_ui()

        # -- Pre-flight --------------------------------------------------
        self.after(300, self._preflight_check)

    # ===================================================================
    # UI Construction
    # ===================================================================

    def _build_ui(self) -> None:
        # Root grid: left panel (controls) + right panel (telemetry)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ----- Left Panel -----------------------------------------------
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")

        # Header
        ctk.CTkLabel(
            left,
            text="REMBO-VM\nSovereign Emulator",
            font=ctk.CTkFont(size=22, weight="bold"),
            justify="center",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            left,
            text="Lead Architect: FERAS-AL-ABBADI",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(0, 20))

        # Separator
        ctk.CTkFrame(left, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=4)

        # --- ISO Picker -------------------------------------------------
        ctk.CTkLabel(left, text="ISO File", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=24, pady=(16, 4)
        )

        iso_frame = ctk.CTkFrame(left, fg_color="transparent")
        iso_frame.pack(fill="x", padx=24)

        self.iso_entry = ctk.CTkEntry(iso_frame, placeholder_text="Select REMBO ISO…")
        self.iso_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(iso_frame, text="Browse", width=80, command=self._browse_iso).pack(
            side="right"
        )

        # --- RAM Allocation ---------------------------------------------
        ctk.CTkLabel(left, text="RAM (MB)", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 4)
        )

        self.ram_entry = ctk.CTkEntry(left, placeholder_text="8192")
        self.ram_entry.insert(0, str(DEFAULT_RAM_MB))
        self.ram_entry.pack(fill="x", padx=24)

        # --- Hardware Info Box ------------------------------------------
        ctk.CTkLabel(left, text="Hardware Spoof", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 4)
        )

        hw_info = ctk.CTkTextbox(left, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        hw_info.pack(fill="x", padx=24)
        hw_info.insert(
            "1.0",
            f"CPU: Alder Lake i5-12400F\n"
            f"     -cpu {CPU_FLAGS}\n"
            f"GPU: RTX 4060 Ti (AD106)\n"
            f"     -device {GPU_DEVICE}\n"
            f"SMP: {SMP_CONFIG}\n"
            f"Disk: {DISK_SIZE} qcow2",
        )
        hw_info.configure(state="disabled")

        # --- Launch Button ----------------------------------------------
        self.launch_btn = ctk.CTkButton(
            left,
            text="LAUNCH SOVEREIGN\nSIMULATION",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=64,
            corner_radius=10,
            command=self._on_launch,
        )
        self.launch_btn.pack(fill="x", padx=24, pady=(28, 8))

        # --- Stop Button ------------------------------------------------
        self.stop_btn = ctk.CTkButton(
            left,
            text="STOP EMULATOR",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color="#8B0000",
            hover_color="#B22222",
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(fill="x", padx=24, pady=(0, 8))

        # --- Status Label -----------------------------------------------
        self.status_label = ctk.CTkLabel(
            left, text="Status: Initializing…", font=ctk.CTkFont(size=12), text_color="orange"
        )
        self.status_label.pack(pady=(8, 16))

        # --- Version footer ---------------------------------------------
        ctk.CTkLabel(
            left,
            text=f"v{APP_VERSION} | REMBO-Bliss-os Sovereign Edition",
            font=ctk.CTkFont(size=10),
            text_color="gray40",
        ).pack(side="bottom", pady=8)

        # ----- Right Panel (Telemetry) ----------------------------------
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")

        ctk.CTkLabel(
            right,
            text="Telemetry Console",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))

        self.console = ctk.CTkTextbox(
            right, font=ctk.CTkFont(family="Consolas", size=12), wrap="word"
        )
        self.console.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # ===================================================================
    # Logging
    # ===================================================================

    def _log(self, message: str, level: str = "INFO") -> None:
        line = f"[{timestamp()}] [{level}] {message}"
        self.console.insert("end", line + "\n")
        self.console.see("end")
        self.log_file_handle.write(line + "\n")
        self.log_file_handle.flush()

    def _set_status(self, text: str, color: str = "white") -> None:
        self.status_label.configure(text=f"Status: {text}", text_color=color)

    # ===================================================================
    # Pre-Flight Check
    # ===================================================================

    def _preflight_check(self) -> None:
        self._log("=" * 60)
        self._log(f"REMBO-VM Sovereign Emulator v{APP_VERSION}")
        self._log(f"Lead Architect: FERAS-AL-ABBADI")
        self._log(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
        self._log("=" * 60)
        self._log("")
        self._log("Running pre-flight checks…")

        self.qemu_bin = _find_qemu_binary()
        self.qemu_img = _find_qemu_img()

        if self.qemu_bin:
            self._log(f"qemu-system-x86_64 found: {self.qemu_bin}", "OK")
        else:
            self._log("qemu-system-x86_64 NOT found on this system.", "WARN")

        if self.qemu_img:
            self._log(f"qemu-img found: {self.qemu_img}", "OK")
        else:
            self._log("qemu-img NOT found on this system.", "WARN")

        if not self.qemu_bin or not self.qemu_img:
            if is_windows():
                self._log("")
                self._log("QEMU is not installed. Attempting automatic installation via winget…")
                self._set_status("Installing QEMU…", "orange")
                threading.Thread(target=self._install_qemu_windows, daemon=True).start()
                return
            else:
                self._log("Install QEMU manually: sudo apt install qemu-system-x86 qemu-utils", "ERROR")
                self._set_status("QEMU not found", "red")
                self.launch_btn.configure(state="disabled")
                return

        self._set_status("Ready", "#00CC66")
        self._log("")
        self._log("Pre-flight checks PASSED. Ready to launch.")

    def _install_qemu_windows(self) -> None:
        try:
            self._log("Executing: winget install --id SoftwareFreedomConservancy.QEMU -e --silent")
            result = subprocess.run(
                ["winget", "install", "--id", "SoftwareFreedomConservancy.QEMU", "-e", "--silent"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                self._log("QEMU installation completed successfully.", "OK")
            else:
                self._log(f"winget output: {result.stdout}", "WARN")
                if result.stderr:
                    self._log(f"winget stderr: {result.stderr}", "WARN")

            # Re-check
            self.qemu_bin = _find_qemu_binary()
            self.qemu_img = _find_qemu_img()

            if self.qemu_bin and self.qemu_img:
                self._log(f"Verified: {self.qemu_bin}", "OK")
                self.after(0, lambda: self._set_status("Ready", "#00CC66"))
            else:
                self._log(
                    "QEMU binaries not found after install. "
                    "Please install manually from https://www.qemu.org/download/#windows "
                    "and restart this application.",
                    "ERROR",
                )
                self.after(0, lambda: self._set_status("QEMU install failed", "red"))
                self.after(0, lambda: self.launch_btn.configure(state="disabled"))

        except FileNotFoundError:
            self._log(
                "winget not found. Please install QEMU manually from "
                "https://www.qemu.org/download/#windows",
                "ERROR",
            )
            self.after(0, lambda: self._set_status("winget not available", "red"))
            self.after(0, lambda: self.launch_btn.configure(state="disabled"))
        except subprocess.TimeoutExpired:
            self._log("QEMU installation timed out (>5 min). Please install manually.", "ERROR")
            self.after(0, lambda: self._set_status("Install timeout", "red"))
            self.after(0, lambda: self.launch_btn.configure(state="disabled"))

    # ===================================================================
    # ISO Picker
    # ===================================================================

    def _browse_iso(self) -> None:
        path = filedialog.askopenfilename(
            title="Select REMBO-Bliss-os ISO",
            filetypes=[("ISO Images", "*.iso"), ("All Files", "*.*")],
        )
        if path:
            self.iso_path = path
            self.iso_entry.delete(0, "end")
            self.iso_entry.insert(0, path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self._log(f"ISO selected: {path} ({size_mb:.1f} MB)")

    # ===================================================================
    # Launch Logic
    # ===================================================================

    def _on_launch(self) -> None:
        # Validate ISO
        iso = self.iso_entry.get().strip()
        if not iso or not os.path.isfile(iso):
            self._log("No valid ISO file selected. Please browse for an ISO.", "ERROR")
            self._set_status("No ISO selected", "red")
            return

        # Validate RAM
        try:
            ram = int(self.ram_entry.get().strip())
            if ram < 1024:
                raise ValueError("RAM too low")
        except ValueError:
            self._log("Invalid RAM value. Must be an integer >= 1024 MB.", "ERROR")
            self._set_status("Invalid RAM", "red")
            return

        if not self.qemu_bin or not self.qemu_img:
            self._log("QEMU not found. Cannot launch.", "ERROR")
            return

        self.iso_path = iso
        self.launch_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("Launching…", "orange")
        threading.Thread(target=self._run_qemu, args=(iso, ram), daemon=True).start()

    def _run_qemu(self, iso_path: str, ram_mb: int) -> None:
        try:
            disk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DISK_NAME)

            # Create virtual disk if needed
            if not os.path.isfile(disk_path):
                self._log(f"Creating virtual disk: {disk_path} ({DISK_SIZE})…")
                subprocess.run(
                    [self.qemu_img, "create", "-f", "qcow2", disk_path, DISK_SIZE],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self._log(f"Virtual disk created: {DISK_SIZE} qcow2", "OK")
            else:
                size_mb = os.path.getsize(disk_path) / (1024 * 1024)
                self._log(f"Existing virtual disk found: {disk_path} ({size_mb:.1f} MB)")

            # Build QEMU command
            cmd = [
                self.qemu_bin,
                # Machine & firmware
                "-machine", "q35,accel=whpx,kernel-irqchip=on",
                "-bios", self._find_ovmf(),
                # CPU spoof: Alder Lake i5-12400F
                "-cpu", CPU_FLAGS,
                "-smp", SMP_CONFIG,
                # Memory
                "-m", str(ram_mb),
                # GPU spoof: RTX 4060 Ti (AD106)
                "-device", GPU_DEVICE,
                # Storage
                "-drive", f"file={disk_path},format=qcow2,if=virtio,cache=writeback",
                "-drive", f"file={iso_path},format=raw,media=cdrom,readonly=on",
                "-boot", "order=d,menu=on",
                # Network
                "-netdev", "user,id=net0",
                "-device", "virtio-net-pci,netdev=net0",
                # USB
                "-usb",
                "-device", "usb-tablet",
                # Audio
                "-audiodev", "sdl,id=audio0",
                "-device", "intel-hda",
                "-device", "hda-duplex,audiodev=audio0",
                # Display
                "-display", "gtk,gl=on",
                # UEFI variables (NVRAM)
                "-global", "driver=cfi.pflash01,property=secure,value=off",
                # Misc
                "-name", "REMBO-VM Sovereign",
            ]

            # Fallback: if WHPX not available, try other accelerators
            if not is_windows():
                cmd[cmd.index("q35,accel=whpx,kernel-irqchip=on")] = "q35,accel=kvm"

            self._log("")
            self._log("=" * 60)
            self._log("SOVEREIGN SIMULATION — BOOT PARAMETERS")
            self._log("=" * 60)
            self._log(f"  ISO:        {iso_path}")
            self._log(f"  Disk:       {disk_path}")
            self._log(f"  RAM:        {ram_mb} MB")
            self._log(f"  CPU Spoof:  Alder Lake i5-12400F")
            self._log(f"              -cpu {CPU_FLAGS}")
            self._log(f"  GPU Spoof:  RTX 4060 Ti (AD106)")
            self._log(f"              -device {GPU_DEVICE}")
            self._log(f"  SMP:        {SMP_CONFIG}")
            self._log(f"  Display:    GTK with OpenGL")
            self._log(f"  Firmware:   OVMF (UEFI)")
            self._log("=" * 60)
            self._log("")
            self._log("Full QEMU command:")
            self._log(" ".join(cmd))
            self._log("")
            self._log("Starting QEMU process…")

            self.qemu_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self.after(0, lambda: self._set_status("Running", "#00CC66"))
            self._log(f"QEMU started (PID: {self.qemu_process.pid})", "OK")

            # Stream output
            for line in self.qemu_process.stdout:
                stripped = line.rstrip()
                if stripped:
                    self._log(f"[QEMU] {stripped}")

            self.qemu_process.wait()
            exit_code = self.qemu_process.returncode
            self._log(f"QEMU process exited with code {exit_code}")

            if exit_code == 0:
                self.after(0, lambda: self._set_status("Stopped", "gray"))
            else:
                self._log(f"QEMU exited abnormally (code {exit_code})", "WARN")
                self.after(0, lambda: self._set_status(f"Exited ({exit_code})", "orange"))

        except FileNotFoundError as e:
            self._log(f"Binary not found: {e}", "ERROR")
            self.after(0, lambda: self._set_status("QEMU binary error", "red"))
        except subprocess.CalledProcessError as e:
            self._log(f"Disk creation failed: {e}", "ERROR")
            self.after(0, lambda: self._set_status("Disk error", "red"))
        except Exception as e:
            self._log(f"Unexpected error: {e}", "ERROR")
            self.after(0, lambda: self._set_status("Error", "red"))
        finally:
            self.qemu_process = None
            self.after(0, lambda: self.launch_btn.configure(state="normal"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _find_ovmf(self) -> str:
        """Locate an OVMF UEFI firmware file for QEMU."""
        candidates = []

        if is_windows():
            for base in QEMU_WIN_PATHS:
                candidates.append(base / "share" / "OVMF.fd")
                candidates.append(base / "share" / "edk2-x86_64-code.fd")
                candidates.append(base / "share" / "OVMF_CODE.fd")
            # Also check alongside the binary
            if self.qemu_bin:
                qemu_dir = Path(self.qemu_bin).parent
                candidates.append(qemu_dir / "share" / "OVMF.fd")
                candidates.append(qemu_dir / "OVMF.fd")
        else:
            candidates = [
                Path("/usr/share/OVMF/OVMF_CODE.fd"),
                Path("/usr/share/ovmf/OVMF.fd"),
                Path("/usr/share/edk2/ovmf/OVMF_CODE.fd"),
                Path("/usr/share/qemu/OVMF.fd"),
                Path("/usr/share/OVMF/OVMF_CODE_4M.fd"),
            ]

        for p in candidates:
            if p.is_file():
                self._log(f"OVMF firmware found: {p}", "OK")
                return str(p)

        # Fallback: let QEMU use its default BIOS
        self._log("OVMF firmware not found — using QEMU default BIOS (legacy mode).", "WARN")
        return ""

    # ===================================================================
    # Stop Logic
    # ===================================================================

    def _on_stop(self) -> None:
        if self.qemu_process and self.qemu_process.poll() is None:
            self._log("Sending termination signal to QEMU…")
            self.qemu_process.terminate()
            self._set_status("Stopping…", "orange")
        else:
            self._log("No running QEMU process to stop.")

    # ===================================================================
    # Cleanup
    # ===================================================================

    def destroy(self) -> None:
        if self.qemu_process and self.qemu_process.poll() is None:
            self.qemu_process.terminate()
        if self.log_file_handle:
            self.log_file_handle.close()
        super().destroy()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    app = REMBOEmulatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
