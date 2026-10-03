OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage75_RuntimeProbe)

SECTIONS
{
    . = STAGE75_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage75_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE75_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
