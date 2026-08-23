#ifndef VEGA_WINDOWS_BOX14_VAULT_H
#define VEGA_WINDOWS_BOX14_VAULT_H

#include <stddef.h>
#include <stdint.h>

#ifndef CODEX_VAULT_TRANSFER_ADDRESS
#define CODEX_VAULT_TRANSFER_ADDRESS 0x0203D880u
#endif

#ifndef CODEX_VAULT_ABI_CRC32
#define CODEX_VAULT_ABI_CRC32 0u
#endif

#define WINDOWS_BOX14_VAULT_CAPABILITY 0x00004000u
#define WINDOWS_BOX14_VAULT_MAGIC 0x31564257u
#define WINDOWS_BOX14_VAULT_VERSION 1u
#define WINDOWS_BOX14_VAULT_TRANSFER_SIZE 128u
#define WINDOWS_BOX14_VAULT_RECORD_SIZE 80u
#define WINDOWS_BOX14_VAULT_BOX_INDEX 13u
#define WINDOWS_BOX14_VAULT_SLOT_COUNT 30u

enum WindowsBox14VaultCommand {
    WINDOWS_BOX14_VAULT_COMMAND_SCAN = 17,
    WINDOWS_BOX14_VAULT_COMMAND_EXPORT = 18,
    WINDOWS_BOX14_VAULT_COMMAND_REMOVE = 19,
    WINDOWS_BOX14_VAULT_COMMAND_IMPORT = 20,
};

enum WindowsBox14VaultTransferStatus {
    WINDOWS_BOX14_VAULT_TRANSFER_EMPTY = 0,
    WINDOWS_BOX14_VAULT_TRANSFER_OUTPUT = 1,
    WINDOWS_BOX14_VAULT_TRANSFER_INPUT = 2,
};

typedef struct __attribute__((packed)) WindowsBox14VaultTransferV1 {
    uint32_t magic;
    uint32_t magic_inverse;
    uint16_t version;
    uint16_t struct_size;
    uint32_t generation;
    uint32_t generation_inverse;
    uint16_t command;
    uint16_t status;
    uint8_t box;
    uint8_t slot;
    uint16_t record_size;
    uint32_t occupancy_mask;
    uint32_t record_crc32;
    uint32_t abi_crc32;
    uint32_t session_nonce;
    uint8_t record[WINDOWS_BOX14_VAULT_RECORD_SIZE];
    uint32_t block_crc32;
} WindowsBox14VaultTransferV1;

_Static_assert(sizeof(WindowsBox14VaultTransferV1)
                   == WINDOWS_BOX14_VAULT_TRANSFER_SIZE,
               "Box 14 transfer ABI differs");
_Static_assert(offsetof(WindowsBox14VaultTransferV1, record) == 44u,
               "Box 14 raw record offset differs");
_Static_assert(offsetof(WindowsBox14VaultTransferV1, block_crc32) == 124u,
               "Box 14 transfer CRC offset differs");

#define gWindowsBox14VaultTransfer \
    ((volatile WindowsBox14VaultTransferV1 *)(uintptr_t) \
        CODEX_VAULT_TRANSFER_ADDRESS)

#endif
