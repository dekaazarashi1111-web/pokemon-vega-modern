OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage72_RuntimeProbe)

SECTIONS
{
    . = STAGE72_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage72_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE72_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
