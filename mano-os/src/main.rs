fn main() {
    println!("MANO OS Bare-Metal Rust Microkernel Images Built Successfully:");
    println!("  UEFI Image : {}", env!("MANO_UEFI_IMG"));
    println!("  BIOS Image : {}", env!("MANO_BIOS_IMG"));
}
