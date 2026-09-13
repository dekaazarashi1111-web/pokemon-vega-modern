OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage77_RuntimeProbe)

SECTIONS
{
    . = STAGE77_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage77_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE77_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
