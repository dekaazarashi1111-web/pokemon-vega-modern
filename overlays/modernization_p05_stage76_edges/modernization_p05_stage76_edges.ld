OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage76_RuntimeProbe)

SECTIONS
{
    . = STAGE76_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage76_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE76_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
