OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage78_RuntimeProbe)

SECTIONS
{
    . = STAGE78_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage78Entries))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE78_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
