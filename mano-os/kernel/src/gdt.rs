use core::ptr::addr_of;
use spin::Lazy;
use x86_64::instructions::segmentation::{CS, DS, ES, SS, Segment};
use x86_64::instructions::tables::load_tss;
use x86_64::structures::gdt::{Descriptor, GlobalDescriptorTable, SegmentSelector};
use x86_64::structures::tss::TaskStateSegment;
use x86_64::VirtAddr;

pub const DOUBLE_FAULT_IST_IDX: u16 = 0;

#[repr(C, align(16))]
struct IstStack([u8; 4096 * 5]);

static DF_STACK: IstStack = IstStack([0; 4096 * 5]);

static TSS: Lazy<TaskStateSegment> = Lazy::new(|| {
    let mut tss = TaskStateSegment::new();
    let stack_start = VirtAddr::from_ptr(addr_of!(DF_STACK.0));
    tss.interrupt_stack_table[DOUBLE_FAULT_IST_IDX as usize] = stack_start + (4096 * 5) as u64;
    tss
});

struct GdtBundle {
    table: GlobalDescriptorTable,
    code_sel: SegmentSelector,
    data_sel: SegmentSelector,
    tss_sel: SegmentSelector,
}

static GDT: Lazy<GdtBundle> = Lazy::new(|| {
    let mut table = GlobalDescriptorTable::new();
    let code_sel = table.append(Descriptor::kernel_code_segment());
    let data_sel = table.append(Descriptor::kernel_data_segment());
    let tss_sel = table.append(Descriptor::tss_segment(&TSS));
    GdtBundle {
        table,
        code_sel,
        data_sel,
        tss_sel,
    }
});

pub fn init_gdt() {
    GDT.table.load();
    unsafe {
        CS::set_reg(GDT.code_sel);
        DS::set_reg(GDT.data_sel);
        ES::set_reg(GDT.data_sel);
        SS::set_reg(GDT.data_sel);
        load_tss(GDT.tss_sel);
    }
}
