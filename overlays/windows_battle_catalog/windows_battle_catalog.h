#ifndef VEGA_WINDOWS_BATTLE_CATALOG_H
#define VEGA_WINDOWS_BATTLE_CATALOG_H

/* T29 adds a second, explicitly IDLE-only context to the T28 transaction
 * owner.  Payloads intentionally remain byte-identical to reward item/mon so
 * one canonical validator and one normal bag/party/PC delivery path own both
 * use cases. */
#define WINDOWS_BATTLE_CATALOG_COMMAND_ITEM 15u
#define WINDOWS_BATTLE_CATALOG_COMMAND_MON 16u
#define WINDOWS_BATTLE_CATALOG_CAPABILITY 0x00002000u
#define WINDOWS_BATTLE_CATALOG_PROTOCOL_MAJOR 1u
#define WINDOWS_BATTLE_CATALOG_PROTOCOL_MINOR 0u

#endif
