param(
    [Parameter(Mandatory = $true)]
    [string]$DriveLetter,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedSerial,
    [switch]$ForceConfirm
)

$ErrorActionPreference = "Stop"

$letter = $DriveLetter.TrimEnd(':', '\').ToUpper()
if ($letter -eq "C") {
    throw "SAFETY ABORT: Refusing to touch system drive C:!"
}

$vol = Get-Volume -DriveLetter $letter -ErrorAction Stop
$part = Get-Partition -DriveLetter $letter -ErrorAction Stop
$disk = Get-Disk -Number $part.DiskNumber -ErrorAction Stop

if ($disk.BusType -ne "USB" -or $disk.Number -eq 0) {
    throw "SAFETY ABORT: Drive ${letter}: is NOT a removable USB drive (Disk $($disk.Number), BusType=$($disk.BusType))!"
}

if ($disk.SerialNumber.Trim() -ne $ExpectedSerial.Trim()) {
    throw "SAFETY ABORT: USB Serial mismatch! Found '$($disk.SerialNumber)', expected '$ExpectedSerial'."
}

$StageDir = "C:\Users\shres\OneDrive\Desktop\MANO_OS_PROJECT\mano-os-hybrid\out\usb_stage"
if (-not (Test-Path "$StageDir\live\filesystem.squashfs")) {
    throw "MANO OS USB stage not found at $StageDir"
}

Write-Host "============================================================"
Write-Host "  MANO OS SAFE USB DEPLOYMENT"
Write-Host "  Target Disk  : Disk $($disk.Number) — $($disk.FriendlyName)"
Write-Host "  USB Serial   : $($disk.SerialNumber)"
Write-Host "  Drive Letter : ${letter}: ($([math]::Round($disk.Size/1GB, 2)) GB)"
Write-Host "============================================================"

if (-not $ForceConfirm) {
    $ans = Read-Host "Type YES_FORMAT_MANO to format ${letter}: as FAT32 MANO_OS and deploy"
    if ($ans -ne "YES_FORMAT_MANO") {
        throw "Cancelled by user."
    }
}

Write-Host "[1/3] Formatting ${letter}: as FAT32 with label MANO_OS..."
Format-Volume -DriveLetter $letter -FileSystem FAT32 -NewFileSystemLabel "MANO_OS" -Confirm:$false -Force | Out-Null

Write-Host "[2/3] Copying Microsoft-signed UEFI Secure Boot MANO OS layout to ${letter}:\..."
robocopy $StageDir "${letter}:\" /E /R:2 /W:1 /NFL /NDL /NP | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    throw "Robocopy failed with exit code $rc"
}

Write-Host "[3/3] Verifying SHA-256 checksums on ${letter}:\..."
$critical = @(
    "EFI\BOOT\BOOTX64.EFI",
    "EFI\BOOT\grubx64.efi",
    "EFI\BOOT\mmx64.efi",
    "EFI\BOOT\grub.cfg",
    "EFI\debian\grub.cfg",
    "boot\grub\grub.cfg",
    "live\vmlinuz",
    "live\initrd.img",
    "live\filesystem.squashfs"
)
foreach ($rel in $critical) {
    $srcFile = Join-Path $StageDir $rel
    if (-not (Test-Path $srcFile)) { continue }
    $dstFile = Join-Path "${letter}:\" $rel
    $hSrc = (Get-FileHash -Algorithm SHA256 $srcFile).Hash
    $hDst = (Get-FileHash -Algorithm SHA256 $dstFile).Hash
    if ($hSrc -ne $hDst) {
        throw "SHA-256 MISMATCH on $rel!"
    }
    Write-Host "  [OK] $rel  ($($hDst.Substring(0, 16))...)"
}

Write-Host "============================================================"
Write-Host "  ✓ MANO OS DEPLOYED & VERIFIED ON ${letter}: (FAT32 MANO_OS)"
Write-Host "============================================================"
