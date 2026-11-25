#!/usr/bin/env bash
set -euo pipefail

# MANO OS Hybrid — Standalone Reproducible Live OS Builder (Debian 12 + Linux 6.1 LTS)
# Engineered by MANO M.
# Run as root inside WSL2 (Ubuntu/Debian) or native Linux.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ROOT="/root/mano-hybrid-build"
CHROOT="$BUILD_ROOT/chroot"
ISO_DIR="$BUILD_ROOT/iso"
OUT_DIR="$SCRIPT_DIR/out"
USB_STAGE="$OUT_DIR/usb_stage"

echo "============================================================"
echo "   MANO OS HYBRID — STANDALONE LIVE USB & ISO BUILDER       "
echo "   Engineered by MANO M.                                    "
echo "============================================================"

rm -rf "$BUILD_ROOT"
mkdir -p "$CHROOT" "$ISO_DIR/live" "$ISO_DIR/boot/grub" "$OUT_DIR" \
         "$USB_STAGE/EFI/BOOT" "$USB_STAGE/EFI/debian" "$USB_STAGE/boot/grub" "$USB_STAGE/live"

echo "[1/6] Bootstrapping Debian 12 (Bookworm) minimal rootfs..."
debootstrap --arch=amd64 --variant=minbase bookworm "$CHROOT" http://deb.debian.org/debian

cat > "$CHROOT/etc/apt/sources.list" << 'EOF'
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
EOF

echo "mano-os" > "$CHROOT/etc/hostname"
cat > "$CHROOT/etc/hosts" << 'EOF'
127.0.0.1 localhost mano-os
::1       localhost
EOF

cat > "$CHROOT/usr/lib/os-release" << 'EOF'
PRETTY_NAME="MANO OS 1.0 (Obsidian Emerald)"
NAME="MANO OS"
VERSION_ID="1.0"
VERSION="1.0 (Obsidian Emerald)"
VERSION_CODENAME=bookworm
ID=mano-os
ID_LIKE=debian
EOF
ln -sfn ../usr/lib/os-release "$CHROOT/etc/os-release"

mount --bind /dev "$CHROOT/dev"
mount --bind /dev/pts "$CHROOT/dev/pts"
mount -t proc proc "$CHROOT/proc"
mount -t sysfs sysfs "$CHROOT/sys"

cleanup_mounts() {
    umount -lf "$CHROOT/dev/pts" 2>/dev/null || true
    umount -lf "$CHROOT/dev" 2>/dev/null || true
    umount -lf "$CHROOT/proc" 2>/dev/null || true
    umount -lf "$CHROOT/sys" 2>/dev/null || true
}
trap cleanup_mounts EXIT

echo "[2/6] Installing Linux 6.1 LTS, Universal Wi-Fi Firmware, NetworkManager, Chromium, snapd & Signed UEFI..."
cat > "$CHROOT/tmp/install_packages.sh" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends \
    linux-image-amd64 live-boot systemd-sysv dbus udev kmod sudo \
    pciutils usbutils rfkill iw wireless-tools \
    firmware-realtek firmware-iwlwifi firmware-atheros firmware-brcm80211 \
    firmware-amd-graphics firmware-misc-nonfree firmware-sof-signed \
    shim-signed grub-efi-amd64-signed \
    network-manager wpasupplicant iproute2 iputils-ping ca-certificates curl \
    xserver-xorg-core xserver-xorg-video-fbdev xserver-xorg-video-vesa \
    xserver-xorg-input-libinput xinit x11-xserver-utils openbox feh \
    fonts-dejavu-core fonts-liberation alsa-utils pulseaudio \
    chromium snapd squashfs-tools fuse3 apparmor \
    python3 python3-gi gir1.2-gtk-3.0 pcmanfm lxterminal libgtk-3-0

useradd -m -s /bin/bash -G sudo,netdev,audio,video,plugdev mano || true
echo "mano:mano" | chpasswd
echo "root:mano" | chpasswd
echo "mano ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/mano
chmod 0440 /etc/sudoers.d/mano
systemctl enable NetworkManager snapd.socket snapd.service || true
systemctl disable snapd.seeded.service 2>/dev/null || true
ln -sfn /var/lib/snapd/snap /snap
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/* /usr/share/man/*
EOF
chmod +x "$CHROOT/tmp/install_packages.sh"
chroot "$CHROOT" /bin/bash /tmp/install_packages.sh
rm -f "$CHROOT/tmp/install_packages.sh"

echo "[3/6] Installing MANO OS Obsidian-Emerald Shell, Snap Store, Telemetry & Wallpaper..."
mkdir -p "$CHROOT/opt/mano" "$CHROOT/etc/sysctl.d" "$CHROOT/etc/modprobe.d" \
         "$CHROOT/etc/NetworkManager" "$CHROOT/etc/X11/xorg.conf.d" \
         "$CHROOT/etc/systemd/system/getty@tty1.service.d" "$CHROOT/etc/profile.d"

sed 's/\r$//' "$SCRIPT_DIR/shell/mano_shell.py" > "$CHROOT/opt/mano/mano_shell.py"
sed 's/\r$//' "$SCRIPT_DIR/shell/mano_store.py" > "$CHROOT/opt/mano/mano_store.py"
sed 's/\r$//' "$SCRIPT_DIR/shell/mano_telemetry.py" > "$CHROOT/opt/mano/mano_telemetry.py"
sed 's/\r$//' "$SCRIPT_DIR/shell/mano_wallpaper.py" > "$CHROOT/opt/mano/mano_wallpaper.py"
chmod +x "$CHROOT/opt/mano/"*.py
python3 "$CHROOT/opt/mano/mano_wallpaper.py" "$CHROOT/opt/mano/emerald_aurora.png"

echo "kernel.unprivileged_userns_clone=1" > "$CHROOT/etc/sysctl.d/99-chromium-sandbox.conf"
printf 'export PATH="$PATH:/snap/bin"\n' > "$CHROOT/etc/profile.d/mano_snap_path.sh"
printf 'options rtw88_pci disable_aspm=y\noptions rtw88_core disable_lps_deep=y\n' > "$CHROOT/etc/modprobe.d/rtw88_8821ce.conf"
printf '[main]\nplugins=ifupdown,keyfile\n\n[ifupdown]\nmanaged=true\n' > "$CHROOT/etc/NetworkManager/NetworkManager.conf"

cat > "$CHROOT/etc/systemd/system/getty@tty1.service.d/autologin.conf" << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin mano --skip-login --noissue --noclear %I $TERM
StandardInput=tty
StandardOutput=null
EOF
: > "$CHROOT/etc/motd"
: > "$CHROOT/etc/issue"

mkdir -p "$CHROOT/home/mano/.config/openbox"
cat > "$CHROOT/home/mano/.config/openbox/rc.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <desktops><number>1</number></desktops>
  <theme><name>Nightmare</name><titleLayout>NLIMC</titleLayout><keepBorder>yes</keepBorder></theme>
  <keyboard>
    <keybind key="A-F4"><action name="Close"/></keybind>
    <keybind key="A-Tab"><action name="NextWindow"/></keybind>
    <keybind key="F1"><action name="Execute"><command>pcmanfm</command></action></keybind>
    <keybind key="F2"><action name="Execute"><command>lxterminal</command></action></keybind>
    <keybind key="F3"><action name="Execute"><command>chromium --no-first-run https://www.google.com</command></action></keybind>
    <keybind key="F4"><action name="Execute"><command>bash -c 'kill -USR1 $(cat /tmp/mano_shell.pid) 2>/dev/null || true'</command></action></keybind>
    <keybind key="F5"><action name="Execute"><command>python3 /opt/mano/mano_telemetry.py</command></action></keybind>
    <keybind key="F6"><action name="Execute"><command>python3 /opt/mano/mano_store.py</command></action></keybind>
    <keybind key="F7"><action name="Execute"><command>bash -c 'kill -USR2 $(cat /tmp/mano_shell.pid) 2>/dev/null || true'</command></action></keybind>
  </keyboard>
</openbox_config>
EOF

cat > "$CHROOT/home/mano/.xinitrc" << 'EOF'
#!/bin/sh
xsetroot -solid "#040A08"
xrandr --auto 2>/dev/null || true
feh --bg-fill /opt/mano/emerald_aurora.png &
pulseaudio --start 2>/dev/null || true
openbox-session &
sleep 0.6
exec python3 /opt/mano/mano_shell.py
EOF
chmod +x "$CHROOT/home/mano/.xinitrc"

cat > "$CHROOT/home/mano/.bash_profile" << 'EOF'
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx -- -keeptty > /tmp/xorg.log 2>&1
fi
EOF
touch "$CHROOT/home/mano/.hushlogin"
chroot "$CHROOT" chown -R mano:mano /home/mano

echo "[4/6] Exporting signed UEFI shim, kernel & XZ-compressed initrd..."
cp "$CHROOT/usr/lib/shim/shimx64.efi.signed" "$USB_STAGE/EFI/BOOT/BOOTX64.EFI"
cp "$CHROOT/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" "$USB_STAGE/EFI/BOOT/grubx64.efi"
[ -f "$CHROOT/usr/lib/shim/mmx64.efi" ] && cp "$CHROOT/usr/lib/shim/mmx64.efi" "$USB_STAGE/EFI/BOOT/mmx64.efi"
cp "$CHROOT/boot/vmlinuz-"* "$ISO_DIR/live/vmlinuz"
cp "$ISO_DIR/live/vmlinuz" "$USB_STAGE/live/vmlinuz"
zcat "$CHROOT/boot/initrd.img-"* | xz --check=crc32 -9 -T0 > "$ISO_DIR/live/initrd.img"
cp "$ISO_DIR/live/initrd.img" "$USB_STAGE/live/initrd.img"

cleanup_mounts
trap - EXIT

echo "[5/6] Packing SquashFS (ZSTD level 15) & GRUB configuration..."
mksquashfs "$CHROOT" "$ISO_DIR/live/filesystem.squashfs" -comp zstd -Xcompression-level 15 -noappend -quiet
cp "$ISO_DIR/live/filesystem.squashfs" "$USB_STAGE/live/filesystem.squashfs"

cat > "$ISO_DIR/boot/grub/grub.cfg" << 'EOF'
insmod part_gpt
insmod part_msdos
insmod fat
insmod iso9660
insmod search
insmod search_fs_file
insmod search_label
insmod linux
insmod all_video
insmod efi_gop
insmod efi_uga
set default="0"
set timeout="2"
menuentry "MANO OS — Obsidian Emerald Live Desktop (Real Wi-Fi + Chromium + Snap Store)" {
    search --no-floppy --set=root --file /live/vmlinuz
    linux /live/vmlinuz boot=live components quiet loglevel=0 rd.systemd.show_status=false rd.udev.log_level=3 vt.global_cursor_default=0
    initrd /live/initrd.img
}
menuentry "MANO OS — Safe Graphics / Verbose Mode (nomodeset)" {
    search --no-floppy --set=root --file /live/vmlinuz
    linux /live/vmlinuz boot=live components nomodeset
    initrd /live/initrd.img
}
EOF
cp "$ISO_DIR/boot/grub/grub.cfg" "$USB_STAGE/boot/grub/grub.cfg"
cp "$ISO_DIR/boot/grub/grub.cfg" "$USB_STAGE/EFI/BOOT/grub.cfg"
cp "$ISO_DIR/boot/grub/grub.cfg" "$USB_STAGE/EFI/debian/grub.cfg"

echo "[6/6] Building Universal UEFI+BIOS ISO + SHA-256..."
grub-mkrescue -o "$OUT_DIR/mano-os-hybrid-universal.iso" "$ISO_DIR" -- -volid MANO_OS
(cd "$OUT_DIR" && sha256sum mano-os-hybrid-universal.iso > mano-os-hybrid-universal.iso.sha256)
echo "✓ MANO OS Hybrid build finished cleanly!"
