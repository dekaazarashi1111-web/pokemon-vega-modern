OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(Stage74_RuntimeProbe)

SECTIONS
{
    . = STAGE74_LOAD_ADDRESS;
    .text : ALIGN(4)
    {
        KEEP(*(.text.Stage74_RuntimeProbe))
        *(.text*)
        *(.rodata*)
    }
    . = ALIGN(4);
    STAGE74_PAYLOAD_END = .;
    /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) }
}
