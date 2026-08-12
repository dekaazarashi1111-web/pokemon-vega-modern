OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(vega_adapter_entry)

/*
 * The build driver supplies __vega_adapter_rom_origin.  The permitted window
 * is the audited gap after the largest T01 CFRU payload and before DPE's fixed
 * insertion region.
 */
MEMORY
{
    ROM (rx) : ORIGIN = __vega_adapter_rom_origin,
               LENGTH = 0x09600000 - __vega_adapter_rom_origin
}

SECTIONS
{
    .vega_adapter.header ORIGIN(ROM) : ALIGN(4)
    {
        __vega_adapter_start = .;
        KEEP(*(.vega_adapter.header))
        __vega_adapter_header_end = .;
    } > ROM

    .vega_adapter.text : ALIGN(2)
    {
        __vega_adapter_text_start = .;
        KEEP(*(.vega_adapter.text))
        __vega_adapter_text_end = .;
        __vega_adapter_end = .;
    } > ROM

    __vega_adapter_size = __vega_adapter_end - __vega_adapter_start;
    __vega_adapter_hook_count = 0;

    /DISCARD/ :
    {
        *(.comment)
        *(.note*)
        *(.data*)
        *(.bss*)
        *(.rodata*)
    }
}

ASSERT(__vega_adapter_rom_origin >= 0x09200000,
       "vega_adapter origin is outside the allocator integration_modules region")
ASSERT(__vega_adapter_rom_origin < 0x09600000,
       "vega_adapter origin overlaps the fixed DPE insertion region")
ASSERT((__vega_adapter_rom_origin & 3) == 0,
       "vega_adapter origin must be 4-byte aligned")
ASSERT(__vega_adapter_end <= 0x09600000,
       "vega_adapter exceeds the integration_modules region")
ASSERT(SIZEOF(.vega_adapter.header) == 32,
       "vega_adapter ABI header must remain exactly 32 bytes")
ASSERT(SIZEOF(.vega_adapter.text) == 2,
       "T03 no-op entry must remain one 16-bit Thumb instruction")
ASSERT(__vega_adapter_hook_count == 0,
       "T03 no-op adapter must not declare hooks")
