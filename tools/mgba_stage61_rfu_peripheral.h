#ifndef MGBA_STAGE61_RFU_PERIPHERAL_H
#define MGBA_STAGE61_RFU_PERIPHERAL_H

/*
 * Stage61 RFU Wireless Adapter peripheral for mGBA 0.10.2.
 *
 * The peripheral is external emulator state.  It is deliberately not part of
 * mGBA savestates: a harness MUST call Stage61RfuHubReset (or reset every
 * endpoint) after every core reset or savestate load, before execution resumes.
 * A savestate may only be captured at the quiescent boundary reported below;
 * quiescence does NOT serialize or restore RFU state and does not remove that
 * mandatory post-load reset.
 *
 * Runtime attachment uses only mGBA's NORMAL_32 GBASIODriver interface and an
 * mTimingEvent.  This API has no ROM, EWRAM, save-block, or VAR_RESULT access.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct GBASIO;

enum {
	STAGE61_RFU_MAX_ENDPOINTS = 4,
	STAGE61_RFU_MAX_PAYLOAD_WORDS = 64,
	STAGE61_RFU_TRACE_CAPACITY = 512,
};

enum Stage61RfuFaultMode {
	STAGE61_RFU_FAULT_NONE = 0,
	/* Reject matching commands with the protocol-defined 0xEE ACK. */
	STAGE61_RFU_FAULT_REJECT_COMMAND = 1,
	/* Reject the next otherwise valid command, then consume the fault. */
	STAGE61_RFU_FAULT_REJECT_NEXT = 2,
	/* Disconnect this endpoint immediately before its next command. */
	STAGE61_RFU_FAULT_DISCONNECT_NEXT = 3,
};

struct Stage61RfuScenario {
	bool adapterPresent;
	enum Stage61RfuFaultMode faultMode;
	uint8_t rejectCommand;
	/* 0 selects the hardware-derived 256/2048-cycle delay. */
	uint32_t transferCycles;
};

enum Stage61RfuTraceKind {
	STAGE61_RFU_TRACE_TRANSFER = 1,
	STAGE61_RFU_TRACE_COMMAND = 2,
	STAGE61_RFU_TRACE_HUB = 3,
	STAGE61_RFU_TRACE_REJECTION = 4,
	STAGE61_RFU_TRACE_RESET = 5,
};

enum Stage61RfuProtocolPhase {
	STAGE61_RFU_PHASE_LOGIN = 0,
	STAGE61_RFU_PHASE_COMM = 1,
	STAGE61_RFU_PHASE_SEND = 2,
	STAGE61_RFU_PHASE_RECV = 3,
	STAGE61_RFU_PHASE_FAILED = 4,
};

struct Stage61RfuTraceEntry {
	uint32_t sequence;
	uint32_t txWord;
	uint32_t rxWord;
	uint16_t stationId;
	uint8_t kind;
	uint8_t command;
	uint8_t phaseBefore;
	uint8_t phaseAfter;
	uint8_t flags;
	uint8_t reserved;
};

struct Stage61RfuHub;
struct Stage61RfuPeripheral;

struct Stage61RfuHub *Stage61RfuHubCreate(void);

/* Returns false, without freeing the hub, while endpoints are still live. */
bool Stage61RfuHubDestroy(struct Stage61RfuHub *hub);

/* Resets virtual air plus every registered endpoint. */
bool Stage61RfuHubReset(struct Stage61RfuHub *hub);

size_t Stage61RfuHubEndpointCount(const struct Stage61RfuHub *hub);

/*
 * True only when every endpoint is at a safe capture/reset boundary: no word,
 * command, external request, queued air frame, join, or recovery is pending.
 * Existing idle link topology may remain.  This is an inspection API, not
 * savestate support; Stage61RfuHubReset is still mandatory after a load.
 */
bool Stage61RfuHubIsQuiescent(const struct Stage61RfuHub *hub);

/* Creation reserves the lowest free virtual-air slot; a fifth endpoint fails. */
struct Stage61RfuPeripheral *Stage61RfuPeripheralCreate(
	struct Stage61RfuHub *hub);
void Stage61RfuPeripheralDestroy(struct Stage61RfuPeripheral *peripheral);

/*
 * Mandatory lifecycle reset.  It clears protocol/session/FIFO/trace state but
 * preserves hub membership, mGBA attachment, and the configured scenario.
 */
bool Stage61RfuPeripheralReset(struct Stage61RfuPeripheral *peripheral);

/* Attach/detach the GBASIODriver in NORMAL_32 mode. */
bool Stage61RfuPeripheralAttach(struct Stage61RfuPeripheral *peripheral,
	struct GBASIO *sio);
void Stage61RfuPeripheralDetach(struct Stage61RfuPeripheral *peripheral);
bool Stage61RfuPeripheralIsAttached(
	const struct Stage61RfuPeripheral *peripheral);

/* Configuration is rejected while a transfer is in flight. */
bool Stage61RfuPeripheralConfigure(
	struct Stage61RfuPeripheral *peripheral,
	const struct Stage61RfuScenario *scenario);
bool Stage61RfuPeripheralGetScenario(
	const struct Stage61RfuPeripheral *peripheral,
	struct Stage61RfuScenario *scenarioOut);

uint16_t Stage61RfuPeripheralStationId(
	const struct Stage61RfuPeripheral *peripheral);
uint8_t Stage61RfuPeripheralHostBitmap(
	const struct Stage61RfuPeripheral *peripheral);
uint32_t Stage61RfuPeripheralSignal(
	const struct Stage61RfuPeripheral *peripheral);
bool Stage61RfuPeripheralHealthy(
	const struct Stage61RfuPeripheral *peripheral);

/* Per-endpoint form of the quiescent capture/reset-boundary inspection. */
bool Stage61RfuPeripheralIsQuiescent(
	const struct Stage61RfuPeripheral *peripheral);

/*
 * Isolated protocol transport for deterministic module tests and harness
 * preflight.  It executes the exact same word state machine as GBASIODriver;
 * it does not write emulator memory.  False means adapter absent, a physical
 * driver transfer or clock-slave Start is already pending, or an internal
 * fail-closed condition.
 */
bool Stage61RfuPeripheralExchangeIsolated(
	struct Stage61RfuPeripheral *peripheral, uint32_t txWord,
	uint32_t *rxWordOut, bool *polarityOut);

size_t Stage61RfuPeripheralTraceCount(
	const struct Stage61RfuPeripheral *peripheral);
size_t Stage61RfuPeripheralTraceCapacity(void);
bool Stage61RfuPeripheralTraceRead(
	const struct Stage61RfuPeripheral *peripheral, size_t index,
	struct Stage61RfuTraceEntry *entryOut);
uint64_t Stage61RfuPeripheralTraceHash(
	const struct Stage61RfuPeripheral *peripheral);
bool Stage61RfuPeripheralTraceOverflowed(
	const struct Stage61RfuPeripheral *peripheral);

/* Always false: external RFU state is intentionally not serialized. */
bool Stage61RfuPeripheralSupportsSavestate(void);

#ifdef __cplusplus
}
#endif

#endif /* MGBA_STAGE61_RFU_PERIPHERAL_H */
