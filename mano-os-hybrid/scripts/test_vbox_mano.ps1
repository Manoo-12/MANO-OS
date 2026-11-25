$ErrorActionPreference = "Stop"

$VBox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$VmName = "MANO_OS_UEFI_Verify"
$ImgPath = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os-hybrid\out\mano_usb_test.img"
$VdiPath = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os-hybrid\out\mano_usb_test.vdi"
$ShotDir = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os-hybrid\screenshots"

if (-not (Test-Path $ImgPath)) {
    throw "FAT32 USB test image not found at $ImgPath"
}
New-Item -ItemType Directory -Force -Path $ShotDir | Out-Null

Write-Host "[VBOX] Cleaning any previous VM $VmName..."
$ErrorActionPreference = "Continue"
& $VBox controlvm $VmName poweroff 2>&1 | Out-Null
Start-Sleep -Seconds 2
& $VBox unregistervm $VmName --delete 2>&1 | Out-Null
if (Test-Path $VdiPath) { Remove-Item -Force $VdiPath }
$ErrorActionPreference = "Stop"

Write-Host "[VBOX] Converting exact FAT32 Signed-UEFI USB image to VDI..."
& $VBox convertfromraw $ImgPath $VdiPath --format VDI | Out-Null

Write-Host "[VBOX] Creating UEFI VM $VmName (2 GB RAM, 2 vCPU, NAT Internet)..."
& $VBox createvm --name $VmName --ostype Debian_64 --register | Out-Null
& $VBox modifyvm $VmName `
    --memory 2048 `
    --cpus 2 `
    --vram 64 `
    --graphicscontroller vmsvga `
    --firmware efi `
    --nic1 nat `
    --nictype1 82540EM `
    --audio-driver none `
    --mouse ps2 `
    --keyboard ps2 `
    --boot1 disk --boot2 none --boot3 none --boot4 none

& $VBox storagectl $VmName --name "SATA" --add sata --controller IntelAhci | Out-Null
& $VBox storageattach $VmName --storagectl "SATA" --port 0 --device 0 --type hdd --medium $VdiPath

Write-Host "[VBOX] Booting MANO OS FAT32 Signed-UEFI Live Image..."
& $VBox startvm $VmName --type headless | Out-Null

# Wait for GRUB + Linux 6.1 LTS + systemd + Xorg + Welcome Splash -> Clean Desktop
Start-Sleep -Seconds 110
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_01_desktop.png"
Write-Host "[VBOX] Captured mano_01_desktop.png"

# Press F6 -> Launch MANO Snap Store (live Canonical snapd)
& $VBox controlvm $VmName keyboardputscancode 40 c0
Start-Sleep -Seconds 18
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_02_snap_store.png"
Write-Host "[VBOX] Captured mano_02_snap_store.png"

# Close Snap Store (Alt+F4)
& $VBox controlvm $VmName keyboardputscancode 38 3e be b8
Start-Sleep -Seconds 3

# Press F4 -> Open Top-Right MANO Wi-Fi Control Center
& $VBox controlvm $VmName keyboardputscancode 3e be
Start-Sleep -Seconds 5
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_03_wifi_panel.png"
Write-Host "[VBOX] Captured mano_03_wifi_panel.png"

# Close Wi-Fi Control Center (Escape)
& $VBox controlvm $VmName keyboardputscancode 01 81
Start-Sleep -Seconds 2

# Press F5 -> Open MANO System Telemetry Dashboard
& $VBox controlvm $VmName keyboardputscancode 3f bf
Start-Sleep -Seconds 6
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_04_telemetry.png"
Write-Host "[VBOX] Captured mano_04_telemetry.png"

# Close Telemetry (Alt+F4)
& $VBox controlvm $VmName keyboardputscancode 38 3e be b8
Start-Sleep -Seconds 3

# Press F3 -> Launch Sandboxed Chromium to Google
& $VBox controlvm $VmName keyboardputscancode 3d bd
Start-Sleep -Seconds 22
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_05_google.png"
Write-Host "[VBOX] Captured mano_05_google.png"

# Navigate to YouTube (Ctrl+L -> https://www.youtube.com -> Enter)
& $VBox controlvm $VmName keyboardputscancode 1d 26 a6 9d
Start-Sleep -Milliseconds 600
& $VBox controlvm $VmName keyboardputstring "https://www.youtube.com"
Start-Sleep -Milliseconds 400
& $VBox controlvm $VmName keyboardputscancode 1c 9c
Start-Sleep -Seconds 24
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_06_youtube.png"
Write-Host "[VBOX] Captured mano_06_youtube.png"

# Clean shutdown & unregister temporary VM
Write-Host "[VBOX] Powering off and cleaning temporary VM..."
$ErrorActionPreference = "Continue"
& $VBox controlvm $VmName poweroff 2>&1 | Out-Null
Start-Sleep -Seconds 3
& $VBox unregistervm $VmName --delete 2>&1 | Out-Null
if (Test-Path $VdiPath) { Remove-Item -Force $VdiPath }
Write-Host "[VBOX] MANO OS 6-screen UEFI verification complete!"
