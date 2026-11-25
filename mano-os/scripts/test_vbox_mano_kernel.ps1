$ErrorActionPreference = "Stop"

$VBox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$VmName = "MANO_OS_Kernel_UEFI_Verify"
$ImgPath = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os\build_artifacts\mano-uefi.img"
$VdiPath = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os\build_artifacts\mano-uefi.vdi"
$ShotDir = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os\screenshots"
$SerialLog = "$ShotDir\kernel_serial_tc1_tc6.log"

New-Item -ItemType Directory -Force -Path $ShotDir | Out-Null

$ErrorActionPreference = "Continue"
& $VBox controlvm $VmName poweroff 2>&1 | Out-Null
Start-Sleep -Seconds 2
& $VBox unregistervm $VmName --delete 2>&1 | Out-Null
if (Test-Path $VdiPath) { Remove-Item -Force $VdiPath }
if (Test-Path $SerialLog) { Remove-Item -Force $SerialLog }
$ErrorActionPreference = "Stop"

& $VBox convertfromraw $ImgPath $VdiPath --format VDI | Out-Null
& $VBox createvm --name $VmName --ostype Other_64 --register | Out-Null
& $VBox modifyvm $VmName `
    --memory 512 --cpus 1 --vram 32 --graphicscontroller vmsvga `
    --firmware efi --uart1 0x3F8 4 --uartmode1 file $SerialLog `
    --boot1 disk --boot2 none --boot3 none --boot4 none

& $VBox storagectl $VmName --name "SATA" --add sata --controller IntelAhci | Out-Null
& $VBox storageattach $VmName --storagectl "SATA" --port 0 --device 0 --type hdd --medium $VdiPath

Write-Host "[VBOX-KERNEL] Booting MANO OS Bare-Metal Rust Microkernel (UEFI)..."
& $VBox startvm $VmName --type headless | Out-Null
Start-Sleep -Seconds 15
& $VBox controlvm $VmName screenshotpng "$ShotDir\mano_kernel_uefi_dashboard.png"
Write-Host "[VBOX-KERNEL] Captured mano_kernel_uefi_dashboard.png"

$ErrorActionPreference = "Continue"
& $VBox controlvm $VmName poweroff 2>&1 | Out-Null
Start-Sleep -Seconds 2
& $VBox unregistervm $VmName --delete 2>&1 | Out-Null
if (Test-Path $VdiPath) { Remove-Item -Force $VdiPath }

Write-Host "=== COM1 SERIAL TELEMETRY ==="
if (Test-Path $SerialLog) { Get-Content $SerialLog }
