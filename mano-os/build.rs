use std::path::PathBuf;

fn main() {
    let out_dir = PathBuf::from(std::env::var_os("OUT_DIR").expect("OUT_DIR missing"));
    let kernel_bin = PathBuf::from(
        std::env::var_os("CARGO_BIN_FILE_MANO_KERNEL_mano_kernel")
            .expect("CARGO_BIN_FILE_MANO_KERNEL_mano_kernel missing"),
    );

    let mut cfg = bootloader::BootConfig::default();
    cfg.frame_buffer_logging = false;
    cfg.serial_logging = true;

    let uefi_img = out_dir.join("mano-uefi.img");
    let mut uefi = bootloader::UefiBoot::new(&kernel_bin);
    uefi.set_boot_config(&cfg);
    uefi.create_disk_image(&uefi_img).expect("UEFI image build failed");

    let bios_img = out_dir.join("mano-bios.img");
    let mut bios = bootloader::BiosBoot::new(&kernel_bin);
    bios.set_boot_config(&cfg);
    bios.create_disk_image(&bios_img).expect("BIOS image build failed");

    println!("cargo:rustc-env=MANO_UEFI_IMG={}", uefi_img.display());
    println!("cargo:rustc-env=MANO_BIOS_IMG={}", bios_img.display());
}
