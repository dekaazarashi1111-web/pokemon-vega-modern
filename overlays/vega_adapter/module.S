/*
 * T03 rebuild harness module.
 *
 * This module is deliberately inert: it exports one Thumb entry point whose
 * only instruction is ``bx lr``.  Nothing in the Vega-owned ROM region points
 * at it during T03.  Later tasks may add declared hooks through the allocator
 * and expected-byte assertion pipeline.
 */

    .syntax unified
    .cpu arm7tdmi
    .thumb

    .section .vega_adapter.header, "a", %progbits
    .balign 4
    .global gVegaAdapterModuleHeader
    .type gVegaAdapterModuleHeader, %object
gVegaAdapterModuleHeader:
    /* Fixed 16-byte marker: ASCII "PVADAPTER_V1" followed by four NULs. */
    .ascii "PVADAPTER_V1"
    .space 4, 0
    .word 1
    /* Linker assertions keep this fixed ABI size honest. */
    .word 34
    .word vega_adapter_entry
    .word 0
    .size gVegaAdapterModuleHeader, . - gVegaAdapterModuleHeader

    .section .vega_adapter.text, "ax", %progbits
    .balign 2
    .global vega_adapter_entry
    .type vega_adapter_entry, %function
    .thumb_func
vega_adapter_entry:
    bx lr
    .size vega_adapter_entry, . - vega_adapter_entry

    .section .note.GNU-stack, "", %progbits
