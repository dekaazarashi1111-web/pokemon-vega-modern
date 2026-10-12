OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage73_RuntimeProbe)

SECTIONS
{
    . = STAGE73_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage73_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE73_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
