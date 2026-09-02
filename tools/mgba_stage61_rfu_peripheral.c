#include "mgba_stage61_rfu_peripheral.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/io.h>
#include <mgba/internal/gba/sio.h>

/*
 * Protocol provenance:
 *   - pokefirered/src/librfu_sio32id.c (NINTENDO login and RFU_ID)
 *   - pokefirered/src/librfu_intr.c (0x9966 framing and 0xEE rejection)
 *   - VBA-M src/core/gba/gbaLink.cpp at commit 2acf41f (command effects)
 *   - mGBA src/gba/sio.c at commit 2fb5545 (GBASIODriver lifecycle)
 */

#define STAGE61_RFU_LOGIN_COMPLETE UINT32_C(0xB0BB8001)
#define STAGE61_RFU_IDLE_WORD UINT32_C(0x80000000)
#define STAGE61_RFU_HEADER UINT32_C(0x99660000)

enum {
	STAGE61_RFU_STATION_BASE = 0x61F1,
	STAGE61_RFU_MESSAGE_CAPACITY = 16,
	STAGE61_RFU_BROADCAST_WORDS = 7,
	STAGE61_RFU_DEFAULT_FAST_CYCLES = 256,
	STAGE61_RFU_DEFAULT_SLOW_CYCLES = 2048,
};

enum {
	STAGE61_RFU_TRACE_FLAG_POLARITY = 1U << 0,
	STAGE61_RFU_TRACE_FLAG_PRESENT = 1U << 1,
	STAGE61_RFU_TRACE_FLAG_REJECTED = 1U << 2,
	STAGE61_RFU_TRACE_FLAG_ASYNC = 1U << 3,
	STAGE61_RFU_TRACE_FLAG_DUPLICATE_START = 1U << 4,
};

struct Stage61RfuMessage {
	uint32_t data[STAGE61_RFU_MAX_PAYLOAD_WORDS];
	uint8_t senderSlot;
	uint8_t length;
	uint8_t important;
};

struct Stage61RfuHub {
	struct Stage61RfuPeripheral *endpoints[STAGE61_RFU_MAX_ENDPOINTS];
	size_t endpointCount;
};

struct Stage61RfuPeripheral {
	/* Keep the driver first: mGBA peripheral callbacks cast from it. */
	struct GBASIODriver driver;
	struct mTimingEvent event;
	struct Stage61RfuHub *hub;
	struct GBASIO *attachedSio;
	struct Stage61RfuScenario scenario;

	struct Stage61RfuTraceEntry trace[STAGE61_RFU_TRACE_CAPACITY];
	size_t traceCount;
	uint32_t traceSequence;
	bool traceOverflow;
	bool failed;

	uint32_t requestData[STAGE61_RFU_MAX_PAYLOAD_WORDS];
	uint32_t responseData[STAGE61_RFU_MAX_PAYLOAD_WORDS];
	uint8_t requestLength;
	uint8_t requestNext;
	uint8_t responseLength;
	uint8_t responseNext;
	uint8_t command;
	uint8_t responseCommand;
	uint8_t rejectionReason;
	enum Stage61RfuProtocolPhase phase;
	bool commandPending;
	bool polarity;
	bool awaitingAsync;
	uint8_t asyncCommand;
	bool externalTransfer;
	bool externalAwaitAck;
	uint8_t externalCommand;
	uint32_t pendingExternalData[2];
	uint8_t pendingExternalLength;

	uint32_t pendingReply;
	bool transferBusy;
	bool attached;
	uint8_t slot;

	bool roleHost;
	bool advertising;
	uint8_t hostBitmap;
	uint8_t pendingJoinBitmap;
	int8_t logicalSlotByEndpoint[STAGE61_RFU_MAX_ENDPOINTS];
	int8_t connectedHost;
	int8_t requestedHost;
	int8_t logicalChildSlot;
	int8_t recoveryHost;
	int8_t recoveryLogicalSlot;
	bool recoveryPending;
	bool recoverySucceeded;
	uint32_t broadcast[STAGE61_RFU_BROADCAST_WORDS];
	uint32_t systemConfig;

	struct Stage61RfuMessage fifo[STAGE61_RFU_MESSAGE_CAPACITY];
	uint8_t fifoFront;
	uint8_t fifoCount;
};

static bool _driverInit(struct GBASIODriver *driver);
static void _driverDeinit(struct GBASIODriver *driver);
static bool _driverLoad(struct GBASIODriver *driver);
static bool _driverUnload(struct GBASIODriver *driver);
static uint16_t _driverWriteRegister(struct GBASIODriver *driver,
	uint32_t address, uint16_t value);
static void _transferEvent(struct mTiming *timing, void *context,
	uint32_t cyclesLate);
static bool _armExternalTransfer(struct Stage61RfuPeripheral *peripheral);
static bool _queueExternalControl(struct Stage61RfuPeripheral *peripheral,
	uint8_t command, uint32_t data, uint8_t length);
static void _clearSession(struct Stage61RfuPeripheral *peripheral);
static void _clearProtocol(struct Stage61RfuPeripheral *peripheral,
	enum Stage61RfuProtocolPhase phase);

static bool _physicalStartPending(
	const struct Stage61RfuPeripheral *peripheral) {
	const struct GBASIO *sio = peripheral ? peripheral->driver.p : NULL;
	return sio && sio->p && sio->mode == SIO_NORMAL_32
		&& GBASIONormalIsStart(sio->siocnt);
}

static void _cancelPhysicalTransfer(
	struct Stage61RfuPeripheral *peripheral) {
	struct GBASIO *sio;
	if (!peripheral) {
		return;
	}
	sio = peripheral->driver.p;
	if (peripheral->transferBusy && sio && sio->p) {
		mTimingDeschedule(&sio->p->timing, &peripheral->event);
	}
	if (_physicalStartPending(peripheral)) {
		sio->siocnt = GBASIONormalClearStart(sio->siocnt);
		sio->siocnt = GBASIONormalFillIdleSo(sio->siocnt);
		sio->p->memory.io[REG_SIOCNT >> 1] = sio->siocnt;
	}
	peripheral->transferBusy = false;
}

static void _failClosed(struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral) {
		return;
	}
	_cancelPhysicalTransfer(peripheral);
	/* A failed endpoint must disappear from the virtual air immediately. */
	_clearSession(peripheral);
	_clearProtocol(peripheral, STAGE61_RFU_PHASE_FAILED);
	peripheral->failed = true;
}

static uint16_t _stationIdForSlot(uint8_t slot) {
	return (uint16_t) (STAGE61_RFU_STATION_BASE + ((uint16_t) slot << 3));
}

static unsigned _popcount8(uint8_t value) {
	unsigned count = 0;
	while (value) {
		count += value & 1U;
		value >>= 1;
	}
	return count;
}

static bool _tracePush(struct Stage61RfuPeripheral *peripheral,
	uint8_t kind, uint8_t command, enum Stage61RfuProtocolPhase phaseBefore,
	uint32_t txWord, uint32_t rxWord, uint8_t flags) {
	struct Stage61RfuTraceEntry *entry;
	if (!peripheral || peripheral->traceCount >= STAGE61_RFU_TRACE_CAPACITY) {
		if (peripheral) {
			peripheral->traceOverflow = true;
			_failClosed(peripheral);
		}
		return false;
	}
	entry = &peripheral->trace[peripheral->traceCount++];
	memset(entry, 0, sizeof(*entry));
	entry->sequence = peripheral->traceSequence++;
	entry->txWord = txWord;
	entry->rxWord = rxWord;
	entry->stationId = _stationIdForSlot(peripheral->slot);
	entry->kind = kind;
	entry->command = command;
	entry->phaseBefore = (uint8_t) phaseBefore;
	entry->phaseAfter = (uint8_t) peripheral->phase;
	entry->flags = flags;
	return true;
}

static void _clearFifo(struct Stage61RfuPeripheral *peripheral) {
	peripheral->fifoFront = 0;
	peripheral->fifoCount = 0;
	memset(peripheral->fifo, 0, sizeof(peripheral->fifo));
}

static void _disconnectLinks(struct Stage61RfuPeripheral *peripheral) {
	unsigned i;
	struct Stage61RfuHub *hub;
	if (!peripheral || !peripheral->hub) {
		return;
	}
	hub = peripheral->hub;
	for (i = 0; i < STAGE61_RFU_MAX_ENDPOINTS; ++i) {
		struct Stage61RfuPeripheral *peer = hub->endpoints[i];
		if (!peer || peer == peripheral) {
			continue;
		}
		peer->hostBitmap &= (uint8_t) ~(1U << peripheral->slot);
		peer->pendingJoinBitmap &= (uint8_t) ~(1U << peripheral->slot);
		peer->logicalSlotByEndpoint[peripheral->slot] = -1;
		if (peer->connectedHost == (int8_t) peripheral->slot) {
			peer->connectedHost = -1;
			peer->logicalChildSlot = -1;
			peer->polarity = false;
			peer->awaitingAsync = false;
			peer->asyncCommand = 0;
		}
		if (peer->requestedHost == (int8_t) peripheral->slot) {
			peer->requestedHost = -1;
		}
		if (peer->recoveryHost == (int8_t) peripheral->slot) {
			peer->recoveryHost = -1;
			peer->recoveryLogicalSlot = -1;
			peer->recoveryPending = false;
			peer->recoverySucceeded = false;
		}
	}
	peripheral->hostBitmap = 0;
	peripheral->pendingJoinBitmap = 0;
	for (i = 0; i < STAGE61_RFU_MAX_ENDPOINTS; ++i) {
		peripheral->logicalSlotByEndpoint[i] = -1;
	}
	peripheral->connectedHost = -1;
	peripheral->requestedHost = -1;
	peripheral->logicalChildSlot = -1;
	peripheral->recoveryHost = -1;
	peripheral->recoveryLogicalSlot = -1;
	peripheral->recoveryPending = false;
	peripheral->recoverySucceeded = false;
}

static void _clearSession(struct Stage61RfuPeripheral *peripheral) {
	_disconnectLinks(peripheral);
	peripheral->roleHost = false;
	peripheral->advertising = false;
	peripheral->systemConfig = 0;
	peripheral->polarity = false;
	peripheral->awaitingAsync = false;
	peripheral->asyncCommand = 0;
	peripheral->externalTransfer = false;
	peripheral->externalAwaitAck = false;
	peripheral->externalCommand = 0;
	peripheral->pendingExternalLength = 0;
	memset(peripheral->pendingExternalData, 0,
		sizeof(peripheral->pendingExternalData));
	memset(peripheral->broadcast, 0, sizeof(peripheral->broadcast));
	_clearFifo(peripheral);
}

static void _clearProtocol(struct Stage61RfuPeripheral *peripheral,
	enum Stage61RfuProtocolPhase phase) {
	peripheral->phase = phase;
	peripheral->requestLength = 0;
	peripheral->requestNext = 0;
	peripheral->responseLength = 0;
	peripheral->responseNext = 0;
	peripheral->command = 0;
	peripheral->responseCommand = 0;
	peripheral->rejectionReason = 0;
	peripheral->commandPending = false;
	peripheral->polarity = false;
	peripheral->awaitingAsync = false;
	peripheral->asyncCommand = 0;
	peripheral->externalTransfer = false;
	peripheral->externalAwaitAck = false;
	peripheral->externalCommand = 0;
	peripheral->pendingExternalLength = 0;
	memset(peripheral->pendingExternalData, 0,
		sizeof(peripheral->pendingExternalData));
	peripheral->pendingReply = STAGE61_RFU_IDLE_WORD;
	peripheral->transferBusy = false;
	memset(peripheral->requestData, 0, sizeof(peripheral->requestData));
	memset(peripheral->responseData, 0, sizeof(peripheral->responseData));
}

static void _loadLoginReset(struct Stage61RfuPeripheral *peripheral) {
	/* GPIO soft reset is observed by mGBA as unload followed by this load. */
	_clearSession(peripheral);
	_clearProtocol(peripheral, STAGE61_RFU_PHASE_LOGIN);
}

static struct Stage61RfuPeripheral *_endpointAt(
	const struct Stage61RfuPeripheral *peripheral, unsigned slot) {
	if (!peripheral || !peripheral->hub || slot >= STAGE61_RFU_MAX_ENDPOINTS) {
		return NULL;
	}
	return peripheral->hub->endpoints[slot];
}

static int _slotForStation(const struct Stage61RfuPeripheral *peripheral,
	uint16_t stationId) {
	unsigned slot;
	for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
		struct Stage61RfuPeripheral *candidate = _endpointAt(peripheral, slot);
		if (candidate && _stationIdForSlot(candidate->slot) == stationId) {
			return (int) slot;
		}
	}
	return -1;
}

static uint32_t _signalFor(const struct Stage61RfuPeripheral *peripheral) {
	unsigned peers;
	struct Stage61RfuPeripheral *host;
	if (!peripheral) {
		return 0;
	}
	if (peripheral->roleHost) {
		peers = _popcount8(peripheral->hostBitmap);
	} else {
		host = peripheral->connectedHost < 0 ? NULL
			: _endpointAt(peripheral,
				(unsigned) peripheral->connectedHost);
		if (!host || !host->roleHost
			|| !(host->hostBitmap & (1U << peripheral->slot))) {
			return 0;
		}
		peers = _popcount8(host->hostBitmap);
	}
	if (!peers) {
		return 0;
	}
	if (peers >= 3) {
		return 0x00FFFFFFU;
	}
	return (1U << (peers * 8U)) - 1U;
}

static uint8_t _logicalHostBitmap(
	const struct Stage61RfuPeripheral *peripheral) {
	uint8_t bitmap = 0;
	unsigned slot;
	if (!peripheral || !peripheral->roleHost) {
		return 0;
	}
	for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
		int logicalSlot;
		if (!(peripheral->hostBitmap & (1U << slot))) {
			continue;
		}
		logicalSlot = peripheral->logicalSlotByEndpoint[slot];
		if (logicalSlot >= 0 && logicalSlot < 4) {
			bitmap |= (uint8_t) (1U << (unsigned) logicalSlot);
		}
	}
	return bitmap;
}

static int _allocateLogicalSlot(
	const struct Stage61RfuPeripheral *host) {
	uint8_t bitmap = _logicalHostBitmap(host);
	unsigned logicalSlot;
	for (logicalSlot = 0; logicalSlot < 4; ++logicalSlot) {
		if (!(bitmap & (1U << logicalSlot))) {
			return (int) logicalSlot;
		}
	}
	return -1;
}

static unsigned _clientIndex(const struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral || peripheral->logicalChildSlot < 0
		|| peripheral->logicalChildSlot >= 4) {
		return 0;
	}
	return (unsigned) peripheral->logicalChildSlot;
}

static bool _fifoCanPush(const struct Stage61RfuPeripheral *peripheral) {
	return peripheral && peripheral->fifoCount < STAGE61_RFU_MESSAGE_CAPACITY;
}

static bool _fifoPush(struct Stage61RfuPeripheral *peripheral,
	uint8_t senderSlot, const uint32_t *data, uint8_t length,
	bool important) {
	unsigned index;
	struct Stage61RfuMessage *message;
	if (!_fifoCanPush(peripheral)
		|| length > STAGE61_RFU_MAX_PAYLOAD_WORDS
		|| (length && !data)) {
		return false;
	}
	index = (unsigned) (peripheral->fifoFront + peripheral->fifoCount)
		% STAGE61_RFU_MESSAGE_CAPACITY;
	message = &peripheral->fifo[index];
	memset(message, 0, sizeof(*message));
	message->senderSlot = senderSlot;
	message->length = length;
	message->important = important ? 1 : 0;
	if (length) {
		memcpy(message->data, data, (size_t) length * sizeof(uint32_t));
	}
	++peripheral->fifoCount;
	if (peripheral->awaitingAsync) {
		peripheral->asyncCommand = peripheral->command >= 0x35 ? 0x36 : 0x28;
		peripheral->polarity = true;
		(void) _armExternalTransfer(peripheral);
	}
	return true;
}

static bool _fifoPop(struct Stage61RfuPeripheral *peripheral,
	struct Stage61RfuMessage *messageOut) {
	if (!peripheral || !messageOut || !peripheral->fifoCount) {
		return false;
	}
	*messageOut = peripheral->fifo[peripheral->fifoFront];
	memset(&peripheral->fifo[peripheral->fifoFront], 0,
		sizeof(peripheral->fifo[peripheral->fifoFront]));
	peripheral->fifoFront = (uint8_t) ((peripheral->fifoFront + 1U)
		% STAGE61_RFU_MESSAGE_CAPACITY);
	--peripheral->fifoCount;
	return true;
}

static bool _routeMessage(struct Stage61RfuPeripheral *peripheral,
	const uint32_t *data, uint8_t length, bool important) {
	struct Stage61RfuPeripheral *recipients[STAGE61_RFU_MAX_ENDPOINTS];
	unsigned count = 0;
	unsigned slot;
	if (!peripheral || length > STAGE61_RFU_MAX_PAYLOAD_WORDS) {
		return false;
	}
	if (peripheral->roleHost) {
		for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
			if (peripheral->hostBitmap & (1U << slot)) {
				struct Stage61RfuPeripheral *peer = _endpointAt(peripheral, slot);
				if (peer) {
					recipients[count++] = peer;
				}
			}
		}
	} else if (peripheral->connectedHost >= 0) {
		struct Stage61RfuPeripheral *host = _endpointAt(peripheral,
			(unsigned) peripheral->connectedHost);
		if (host && (host->hostBitmap & (1U << peripheral->slot))) {
			recipients[count++] = host;
		}
	}
	/* Sending while disconnected is a successful no-recipient air frame. */
	for (slot = 0; slot < count; ++slot) {
		if (!_fifoCanPush(recipients[slot])) {
			return false;
		}
	}
	for (slot = 0; slot < count; ++slot) {
		if (!_fifoPush(recipients[slot], peripheral->slot, data, length,
			important)) {
			return false;
		}
	}
	return true;
}

static bool _commandAllowed(uint8_t command) {
	switch (command) {
	case 0x10:
	case 0x11:
	case 0x13:
	case 0x14:
	case 0x16:
	case 0x17:
	case 0x19:
	case 0x1A:
	case 0x1B:
	case 0x1C:
	case 0x1D:
	case 0x1E:
	case 0x1F:
	case 0x20:
	case 0x21:
	case 0x24:
	case 0x25:
	case 0x26:
	case 0x27:
	case 0x30:
	case 0x32:
	case 0x33:
	case 0x34:
	case 0x35:
	case 0x36:
	case 0x37:
	case 0x3D:
	case 0xEE:
		return true;
	default:
		return false;
	}
}

static bool _commandLengthValid(uint8_t command, uint8_t length) {
	switch (command) {
	case 0x16:
		return length == 6;
	case 0x17:
	case 0x1F:
	case 0x30:
		return length == 1;
	case 0x32:
		return length == 2;
	case 0x24:
	case 0x25:
	case 0x35:
		return length <= STAGE61_RFU_MAX_PAYLOAD_WORDS;
	case 0x10:
	case 0x11:
	case 0x13:
	case 0x14:
	case 0x19:
	case 0x1A:
	case 0x1B:
	case 0x1C:
	case 0x1D:
	case 0x1E:
	case 0x20:
	case 0x21:
	case 0x26:
	case 0x27:
	case 0x33:
	case 0x34:
	case 0x36:
	case 0x37:
	case 0x3D:
	case 0xEE:
		return length == 0;
	default:
		return false;
	}
}

static void _setResponse(struct Stage61RfuPeripheral *peripheral,
	uint8_t responseCommand, const uint32_t *data, uint8_t length) {
	peripheral->responseCommand = responseCommand;
	peripheral->responseLength = length;
	peripheral->responseNext = 0;
	memset(peripheral->responseData, 0, sizeof(peripheral->responseData));
	if (length && data) {
		memcpy(peripheral->responseData, data,
			(size_t) length * sizeof(uint32_t));
	}
}

static void _setRejection(struct Stage61RfuPeripheral *peripheral,
	uint8_t reason) {
	uint32_t detail = reason;
	peripheral->rejectionReason = reason;
	_setResponse(peripheral, 0xEE, &detail, 1);
}

static void _abortPendingRequest(struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral) {
		return;
	}
	peripheral->commandPending = false;
	peripheral->requestLength = 0;
	peripheral->requestNext = 0;
	peripheral->command = 0;
	peripheral->rejectionReason = 0;
	memset(peripheral->requestData, 0, sizeof(peripheral->requestData));
}

static bool _canQueueExternalControl(
	const struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral) {
		return false;
	}
	if (!peripheral->scenario.adapterPresent) {
		return true;
	}
	return !peripheral->failed && !peripheral->asyncCommand
		&& !peripheral->externalTransfer
		&& !peripheral->externalAwaitAck
		&& !peripheral->transferBusy
		&& !peripheral->commandPending
		&& peripheral->phase == STAGE61_RFU_PHASE_COMM
		&& peripheral->responseLength == 0;
}

static void _clearClientLink(struct Stage61RfuPeripheral *host,
	struct Stage61RfuPeripheral *client) {
	if (!host || !client || client->slot >= STAGE61_RFU_MAX_ENDPOINTS) {
		return;
	}
	host->hostBitmap &= (uint8_t) ~(1U << client->slot);
	host->pendingJoinBitmap &= (uint8_t) ~(1U << client->slot);
	host->logicalSlotByEndpoint[client->slot] = -1;
	client->connectedHost = -1;
	client->requestedHost = -1;
	client->logicalChildSlot = -1;
	client->recoveryHost = -1;
	client->recoveryLogicalSlot = -1;
	client->recoveryPending = false;
	client->recoverySucceeded = false;
	client->awaitingAsync = false;
	client->asyncCommand = 0;
	client->externalTransfer = false;
	client->externalAwaitAck = false;
	client->externalCommand = 0;
	client->pendingExternalLength = 0;
	memset(client->pendingExternalData, 0,
		sizeof(client->pendingExternalData));
	client->polarity = false;
	_clearFifo(client);
}

static bool _disconnectSelected(struct Stage61RfuPeripheral *peripheral,
	uint8_t bitmap) {
	unsigned slot;
	if (!peripheral) {
		return false;
	}
	if (peripheral->roleHost) {
		/* Validate all notifications before making the operation observable. */
		for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
			struct Stage61RfuPeripheral *client;
			int logicalSlot = peripheral->logicalSlotByEndpoint[slot];
			if (!(peripheral->hostBitmap & (1U << slot))
				|| logicalSlot < 0 || logicalSlot >= 4
				|| !(bitmap & (1U << (unsigned) logicalSlot))) {
				continue;
			}
			client = _endpointAt(peripheral, slot);
			if (!client || client->connectedHost
				!= (int8_t) peripheral->slot
				|| !_canQueueExternalControl(client)) {
				return false;
			}
		}
		for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
			struct Stage61RfuPeripheral *client;
			int logicalSlot = peripheral->logicalSlotByEndpoint[slot];
			uint32_t notification;
			if (!(peripheral->hostBitmap & (1U << slot))
				|| logicalSlot < 0 || logicalSlot >= 4
				|| !(bitmap & (1U << (unsigned) logicalSlot))) {
				continue;
			}
			client = _endpointAt(peripheral, slot);
			notification = 1U << (unsigned) logicalSlot;
			_clearClientLink(peripheral, client);
			if (client->scenario.adapterPresent
				&& !_queueExternalControl(client, 0x29,
					notification, 1)) {
				_failClosed(peripheral);
				return false;
			}
		}
		return true;
	}
	if (peripheral->connectedHost >= 0
		&& peripheral->logicalChildSlot >= 0
		&& peripheral->logicalChildSlot < 4
		&& (bitmap & (1U << (unsigned) peripheral->logicalChildSlot))) {
		struct Stage61RfuPeripheral *host = _endpointAt(peripheral,
			(unsigned) peripheral->connectedHost);
		uint32_t notification = 1U
			<< (unsigned) peripheral->logicalChildSlot;
		if (!host || !host->roleHost || !_canQueueExternalControl(host)) {
			return false;
		}
		_clearClientLink(host, peripheral);
		if (host->scenario.adapterPresent
			&& !_queueExternalControl(host, 0x29, notification, 1)) {
			_failClosed(peripheral);
			return false;
		}
	}
	return true;
}

static void _disconnectCommand(struct Stage61RfuPeripheral *peripheral) {
	_disconnectLinks(peripheral);
	peripheral->roleHost = false;
	peripheral->advertising = false;
	peripheral->pendingJoinBitmap = 0;
	peripheral->polarity = false;
	peripheral->awaitingAsync = false;
	peripheral->asyncCommand = 0;
	peripheral->externalTransfer = false;
	peripheral->externalAwaitAck = false;
	peripheral->externalCommand = 0;
	peripheral->pendingExternalLength = 0;
	memset(peripheral->pendingExternalData, 0,
		sizeof(peripheral->pendingExternalData));
	memset(peripheral->broadcast, 0, sizeof(peripheral->broadcast));
	_clearFifo(peripheral);
}

static bool _executeCommand(struct Stage61RfuPeripheral *peripheral) {
	uint32_t response[STAGE61_RFU_MAX_PAYLOAD_WORDS];
	uint8_t responseLength = 0;
	uint8_t responseCommand = (uint8_t) (peripheral->command ^ 0x80U);
	unsigned slot;
	memset(response, 0, sizeof(response));

	if (peripheral->rejectionReason) {
		_setRejection(peripheral, peripheral->rejectionReason);
		return false;
	}
	if (peripheral->scenario.faultMode == STAGE61_RFU_FAULT_REJECT_NEXT
		|| (peripheral->scenario.faultMode
			== STAGE61_RFU_FAULT_REJECT_COMMAND
			&& peripheral->scenario.rejectCommand == peripheral->command)) {
		if (peripheral->scenario.faultMode == STAGE61_RFU_FAULT_REJECT_NEXT) {
			peripheral->scenario.faultMode = STAGE61_RFU_FAULT_NONE;
		}
		_setRejection(peripheral, 1);
		return false;
	}
	if (peripheral->scenario.faultMode
		== STAGE61_RFU_FAULT_DISCONNECT_NEXT) {
		peripheral->scenario.faultMode = STAGE61_RFU_FAULT_NONE;
		_disconnectCommand(peripheral);
		_setRejection(peripheral, 1);
		return false;
	}

	switch (peripheral->command) {
	case 0x10:
	case 0x3D:
		_clearSession(peripheral);
		break;
	case 0x11:
		response[0] = _signalFor(peripheral);
		responseLength = 1;
		break;
	case 0x13:
		response[0] = _stationIdForSlot(peripheral->slot);
		if (peripheral->roleHost) {
			response[0] |= 0x01000000U;
		} else if (peripheral->connectedHost >= 0) {
			response[0] |= (uint32_t) _clientIndex(peripheral) << 16;
		}
		responseLength = 1;
		break;
	case 0x14:
		response[0] = 0;
		responseLength = 1;
		break;
	case 0x16:
		if (peripheral->requestLength > STAGE61_RFU_BROADCAST_WORDS - 1) {
			_setRejection(peripheral, 1);
			return false;
		}
		memset(&peripheral->broadcast[1], 0,
			(STAGE61_RFU_BROADCAST_WORDS - 1) * sizeof(uint32_t));
		memcpy(&peripheral->broadcast[1], peripheral->requestData,
			(size_t) peripheral->requestLength * sizeof(uint32_t));
		break;
	case 0x17:
		if (peripheral->requestLength != 1) {
			_setRejection(peripheral, 1);
			return false;
		}
		peripheral->systemConfig = peripheral->requestData[0];
		break;
	case 0x19:
		if (peripheral->connectedHost >= 0
			|| peripheral->requestedHost >= 0
			|| peripheral->recoveryPending) {
			_setRejection(peripheral, 1);
			return false;
		}
		peripheral->roleHost = true;
		peripheral->advertising = true;
		peripheral->broadcast[0] = _stationIdForSlot(peripheral->slot);
		break;
	case 0x1A:
		if (!peripheral->roleHost) {
			break;
		}
		for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
			struct Stage61RfuPeripheral *client;
			int logicalSlot;
			if (!(peripheral->pendingJoinBitmap & (1U << slot))) {
				continue;
			}
			client = _endpointAt(peripheral, slot);
			if (!client || client == peripheral
				|| client->requestedHost != (int8_t) peripheral->slot) {
				continue;
			}
			logicalSlot = _allocateLogicalSlot(peripheral);
			if (logicalSlot < 0) {
				_setRejection(peripheral, 1);
				return false;
			}
			peripheral->hostBitmap |= (uint8_t) (1U << slot);
			peripheral->logicalSlotByEndpoint[slot] =
				(int8_t) logicalSlot;
			client->connectedHost = (int8_t) peripheral->slot;
			client->requestedHost = -1;
			client->logicalChildSlot = (int8_t) logicalSlot;
			response[responseLength++] = _stationIdForSlot(client->slot)
				| ((uint32_t) logicalSlot << 16);
		}
		peripheral->pendingJoinBitmap = 0;
		break;
	case 0x1B:
		peripheral->advertising = false;
		peripheral->broadcast[0] = 0;
		break;
	case 0x1C:
		_disconnectCommand(peripheral);
		break;
	case 0x1D:
	case 0x1E:
		_disconnectCommand(peripheral);
		for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
			struct Stage61RfuPeripheral *host = _endpointAt(peripheral, slot);
			if (!host || host == peripheral || !host->roleHost
				|| !host->advertising || !host->broadcast[0]) {
				continue;
			}
			if ((unsigned) responseLength + STAGE61_RFU_BROADCAST_WORDS
				> STAGE61_RFU_MAX_PAYLOAD_WORDS) {
				_setRejection(peripheral, 1);
				return false;
			}
			memcpy(&response[responseLength], host->broadcast,
				sizeof(host->broadcast));
			responseLength += STAGE61_RFU_BROADCAST_WORDS;
		}
		break;
	case 0x1F: {
		int hostSlot;
		struct Stage61RfuPeripheral *host;
		if (peripheral->requestLength != 1
			|| peripheral->roleHost || peripheral->advertising
			|| peripheral->hostBitmap
			|| peripheral->pendingJoinBitmap) {
			_setRejection(peripheral, 1);
			return false;
		}
		hostSlot = _slotForStation(peripheral,
			(uint16_t) peripheral->requestData[0]);
		host = hostSlot < 0 ? NULL : _endpointAt(peripheral,
			(unsigned) hostSlot);
		if (!host || host == peripheral || !host->roleHost
			|| !host->advertising) {
			_setRejection(peripheral, 1);
			return false;
		}
		_disconnectLinks(peripheral);
		peripheral->requestedHost = (int8_t) hostSlot;
		host->pendingJoinBitmap |= (uint8_t) (1U << peripheral->slot);
		break;
	}
	case 0x20:
	case 0x21:
		response[0] = _stationIdForSlot(peripheral->slot)
			| ((uint32_t) _clientIndex(peripheral) << 16);
		responseLength = 1;
		break;
	case 0x24:
	case 0x25:
	case 0x35:
		if (!_routeMessage(peripheral, peripheral->requestData,
			peripheral->requestLength, peripheral->command != 0x24)) {
			_setRejection(peripheral, 1);
			return false;
		}
		if (peripheral->command == 0x25 || peripheral->command == 0x35) {
			peripheral->awaitingAsync = true;
			if (peripheral->fifoCount) {
				peripheral->asyncCommand = peripheral->command == 0x35
					? 0x36 : 0x28;
				peripheral->polarity = true;
			}
		}
		break;
	case 0x26:
	case 0x36: {
		struct Stage61RfuMessage message;
		if (_fifoPop(peripheral, &message)) {
			responseLength = message.length;
			if (responseLength) {
				memcpy(response, message.data,
					(size_t) responseLength * sizeof(uint32_t));
			}
		}
		peripheral->awaitingAsync = false;
		peripheral->asyncCommand = 0;
		peripheral->polarity = false;
		break;
	}
	case 0x27:
	case 0x37:
		peripheral->awaitingAsync = true;
		if (peripheral->fifoCount) {
			peripheral->asyncCommand = peripheral->command == 0x37
				? 0x36 : 0x28;
			peripheral->polarity = true;
		}
		break;
	case 0x30:
		if (peripheral->requestData[0] & ~UINT32_C(0x0F)
			|| !_disconnectSelected(peripheral,
				(uint8_t) peripheral->requestData[0])) {
			_setRejection(peripheral, 1);
			return false;
		}
		break;
	case 0x32: {
		uint16_t hostId = (uint16_t) (peripheral->requestData[0] >> 16);
		uint16_t selfId = (uint16_t) peripheral->requestData[0];
		uint8_t bitmap = (uint8_t) peripheral->requestData[1];
		int hostSlot;
		int logicalSlot;
		struct Stage61RfuPeripheral *host;
		if (peripheral->requestData[1] & ~UINT32_C(0x0F)
			|| _popcount8(bitmap) != 1
			|| selfId != _stationIdForSlot(peripheral->slot)
			|| peripheral->roleHost || peripheral->advertising
			|| peripheral->hostBitmap
			|| peripheral->pendingJoinBitmap
			|| peripheral->connectedHost >= 0
			|| peripheral->requestedHost >= 0) {
			_setRejection(peripheral, 1);
			return false;
		}
		hostSlot = _slotForStation(peripheral, hostId);
		host = hostSlot < 0 ? NULL : _endpointAt(peripheral,
			(unsigned) hostSlot);
		for (logicalSlot = 0; logicalSlot < 4; ++logicalSlot) {
			if (bitmap & (1U << (unsigned) logicalSlot)) {
				break;
			}
		}
		if (!host || host == peripheral || !host->roleHost
			|| logicalSlot >= 4
			|| (_logicalHostBitmap(host)
				& (1U << (unsigned) logicalSlot))) {
			_setRejection(peripheral, 1);
			return false;
		}
		peripheral->recoveryHost = (int8_t) hostSlot;
		peripheral->recoveryLogicalSlot = (int8_t) logicalSlot;
		peripheral->recoveryPending = true;
		peripheral->recoverySucceeded = false;
		break;
	}
	case 0x33:
		response[0] = UINT32_MAX;
		if (peripheral->recoveryPending) {
			struct Stage61RfuPeripheral *host =
				peripheral->recoveryHost < 0 ? NULL
				: _endpointAt(peripheral,
					(unsigned) peripheral->recoveryHost);
			int logicalSlot = peripheral->recoveryLogicalSlot;
			if (peripheral->recoverySucceeded) {
				response[0] = 0;
			} else if (host && host->roleHost && logicalSlot >= 0
				&& logicalSlot < 4
				&& !(_logicalHostBitmap(host)
					& (1U << (unsigned) logicalSlot))) {
				host->hostBitmap |= (uint8_t) (1U << peripheral->slot);
				host->pendingJoinBitmap &=
					(uint8_t) ~(1U << peripheral->slot);
				host->logicalSlotByEndpoint[peripheral->slot] =
					(int8_t) logicalSlot;
				peripheral->connectedHost =
					peripheral->recoveryHost;
				peripheral->requestedHost = -1;
				peripheral->logicalChildSlot = (int8_t) logicalSlot;
				peripheral->recoverySucceeded = true;
				response[0] = 0;
			}
		}
		responseLength = 1;
		break;
	case 0x34:
		peripheral->recoveryHost = -1;
		peripheral->recoveryLogicalSlot = -1;
		peripheral->recoveryPending = false;
		peripheral->recoverySucceeded = false;
		break;
	case 0xEE:
		responseCommand = 0x6E;
		peripheral->polarity = false;
		break;
	default:
		_setRejection(peripheral, 2);
		return false;
	}

	_setResponse(peripheral, responseCommand, response, responseLength);
	return true;
}

static uint32_t _responseHeader(const struct Stage61RfuPeripheral *peripheral) {
	return STAGE61_RFU_HEADER
		| ((uint32_t) peripheral->responseLength << 8)
		| peripheral->responseCommand;
}

static bool _beginCommand(struct Stage61RfuPeripheral *peripheral,
	uint32_t txWord) {
	peripheral->command = (uint8_t) txWord;
	peripheral->requestLength = (uint8_t) (txWord >> 8);
	peripheral->requestNext = 0;
	peripheral->commandPending = true;
	peripheral->rejectionReason = 0;
	memset(peripheral->requestData, 0, sizeof(peripheral->requestData));
	if (!_commandAllowed(peripheral->command)) {
		peripheral->rejectionReason = peripheral->command >= 0x10
			&& peripheral->command <= 0x3D ? 1 : 2;
	} else if (!_commandLengthValid(peripheral->command,
		peripheral->requestLength)) {
		peripheral->rejectionReason = 1;
	}
	peripheral->phase = peripheral->requestLength
		? STAGE61_RFU_PHASE_SEND : STAGE61_RFU_PHASE_COMM;
	return peripheral->rejectionReason == 0;
}

static bool _emitAsyncHeader(struct Stage61RfuPeripheral *peripheral,
	uint32_t *rxWordOut) {
	struct Stage61RfuMessage message;
	uint8_t command = peripheral->asyncCommand;
	memset(&message, 0, sizeof(message));
	if (!command) {
		return false;
	}
	if (command == 0x29) {
		if (peripheral->pendingExternalLength != 1) {
			return false;
		}
		message.length = peripheral->pendingExternalLength;
		memcpy(message.data, peripheral->pendingExternalData,
			(size_t) message.length * sizeof(uint32_t));
		peripheral->pendingExternalLength = 0;
		memset(peripheral->pendingExternalData, 0,
			sizeof(peripheral->pendingExternalData));
	} else if (!_fifoPop(peripheral, &message)) {
		return false;
	}
	_setResponse(peripheral, command, message.data, message.length);
	peripheral->awaitingAsync = false;
	peripheral->asyncCommand = 0;
	peripheral->polarity = true;
	peripheral->externalTransfer = true;
	peripheral->externalAwaitAck = message.length == 0;
	peripheral->externalCommand = command;
	peripheral->phase = message.length
		? STAGE61_RFU_PHASE_RECV : STAGE61_RFU_PHASE_COMM;
	*rxWordOut = _responseHeader(peripheral);
	return true;
}

static bool _exchangeWord(struct Stage61RfuPeripheral *peripheral,
	uint32_t txWord, uint32_t *rxWordOut) {
	enum Stage61RfuProtocolPhase phaseBefore;
	uint32_t rxWord = STAGE61_RFU_IDLE_WORD;
	uint8_t traceKind = STAGE61_RFU_TRACE_TRANSFER;
	uint8_t traceCommand;
	uint8_t flags = 0;
	bool accepted = true;

	if (!peripheral || !rxWordOut || !peripheral->scenario.adapterPresent
		|| peripheral->failed) {
		return false;
	}
	if (peripheral->traceCount >= STAGE61_RFU_TRACE_CAPACITY) {
		peripheral->traceOverflow = true;
		_failClosed(peripheral);
		return false;
	}
	phaseBefore = peripheral->phase;
	traceCommand = peripheral->command;

	switch (peripheral->phase) {
	case STAGE61_RFU_PHASE_LOGIN:
		rxWord = (txWord << 16) | (txWord >> 16);
		if (txWord == STAGE61_RFU_LOGIN_COMPLETE) {
			peripheral->phase = STAGE61_RFU_PHASE_COMM;
			peripheral->polarity = false;
		}
		break;
	case STAGE61_RFU_PHASE_COMM:
		if (peripheral->asyncCommand && txWord == STAGE61_RFU_IDLE_WORD) {
			if (!_emitAsyncHeader(peripheral, &rxWord)) {
				_setRejection(peripheral, 1);
				rxWord = _responseHeader(peripheral);
				peripheral->phase = STAGE61_RFU_PHASE_RECV;
				accepted = false;
			}
			traceCommand = peripheral->responseCommand;
			flags |= STAGE61_RFU_TRACE_FLAG_ASYNC;
			break;
		}
		if ((txWord & 0xFFFF0000U) == STAGE61_RFU_HEADER) {
			traceKind = STAGE61_RFU_TRACE_COMMAND;
			accepted = _beginCommand(peripheral, txWord);
			traceCommand = peripheral->command;
			rxWord = STAGE61_RFU_IDLE_WORD;
			break;
		}
		if (txWord == STAGE61_RFU_IDLE_WORD
			&& peripheral->commandPending) {
			traceCommand = peripheral->command;
			accepted = _executeCommand(peripheral);
			rxWord = _responseHeader(peripheral);
			peripheral->commandPending = false;
			peripheral->phase = peripheral->responseLength
				? STAGE61_RFU_PHASE_RECV : STAGE61_RFU_PHASE_COMM;
			if (!accepted) {
				traceKind = STAGE61_RFU_TRACE_REJECTION;
				flags |= STAGE61_RFU_TRACE_FLAG_REJECTED;
			}
			break;
		}
		if ((txWord & 0xFFFFU) == 0x494EU) {
			_loadLoginReset(peripheral);
			rxWord = (txWord << 16) | (txWord >> 16);
			break;
		}
		_abortPendingRequest(peripheral);
		_setRejection(peripheral, 2);
		rxWord = _responseHeader(peripheral);
		peripheral->phase = STAGE61_RFU_PHASE_RECV;
		traceKind = STAGE61_RFU_TRACE_REJECTION;
		flags |= STAGE61_RFU_TRACE_FLAG_REJECTED;
		accepted = false;
		break;
	case STAGE61_RFU_PHASE_SEND:
		if (peripheral->requestNext < STAGE61_RFU_MAX_PAYLOAD_WORDS) {
			peripheral->requestData[peripheral->requestNext] = txWord;
		}
		++peripheral->requestNext;
		if (peripheral->requestNext >= peripheral->requestLength) {
			peripheral->phase = STAGE61_RFU_PHASE_COMM;
		}
		rxWord = STAGE61_RFU_IDLE_WORD;
		break;
	case STAGE61_RFU_PHASE_RECV:
		if (txWord != STAGE61_RFU_IDLE_WORD
			|| peripheral->responseNext >= peripheral->responseLength) {
			if (peripheral->externalTransfer) {
				traceCommand = peripheral->externalCommand;
				_failClosed(peripheral);
				flags |= STAGE61_RFU_TRACE_FLAG_PRESENT
					| STAGE61_RFU_TRACE_FLAG_REJECTED
					| STAGE61_RFU_TRACE_FLAG_ASYNC;
				*rxWordOut = STAGE61_RFU_IDLE_WORD;
				(void) _tracePush(peripheral,
					STAGE61_RFU_TRACE_REJECTION, traceCommand,
					phaseBefore, txWord, *rxWordOut, flags);
				return false;
			}
			_setRejection(peripheral, 2);
			rxWord = _responseHeader(peripheral);
			peripheral->phase = STAGE61_RFU_PHASE_RECV;
			traceKind = STAGE61_RFU_TRACE_REJECTION;
			flags |= STAGE61_RFU_TRACE_FLAG_REJECTED;
			accepted = false;
			break;
		}
		rxWord = peripheral->responseData[peripheral->responseNext++];
		if (peripheral->responseNext >= peripheral->responseLength) {
			peripheral->phase = STAGE61_RFU_PHASE_COMM;
			peripheral->responseLength = 0;
			peripheral->responseNext = 0;
			if (peripheral->externalTransfer) {
				peripheral->externalAwaitAck = true;
			}
		}
		break;
	case STAGE61_RFU_PHASE_FAILED:
	default:
		return false;
	}

	if (peripheral->scenario.adapterPresent) {
		flags |= STAGE61_RFU_TRACE_FLAG_PRESENT;
	}
	if (peripheral->polarity) {
		flags |= STAGE61_RFU_TRACE_FLAG_POLARITY;
	}
	*rxWordOut = rxWord;
	if (!_tracePush(peripheral, traceKind, traceCommand, phaseBefore,
		txWord, rxWord, flags)) {
		return false;
	}
	/* A protocol NACK is a successful physical transfer. */
	(void) accepted;
	return true;
}

static bool _prepareExternalWord(struct Stage61RfuPeripheral *peripheral,
	uint32_t txWord, uint32_t *rxWordOut) {
	uint8_t flags = STAGE61_RFU_TRACE_FLAG_PRESENT
		| STAGE61_RFU_TRACE_FLAG_ASYNC
		| STAGE61_RFU_TRACE_FLAG_POLARITY;
	uint8_t command;
	uint32_t expectedAck;
	if (!peripheral || !rxWordOut || peripheral->failed) {
		return false;
	}
	if (peripheral->externalAwaitAck) {
		command = peripheral->externalCommand;
		expectedAck = STAGE61_RFU_HEADER | (uint8_t) (command ^ 0x80U);
		if (txWord != expectedAck) {
			_failClosed(peripheral);
			flags |= STAGE61_RFU_TRACE_FLAG_REJECTED;
			(void) _tracePush(peripheral, STAGE61_RFU_TRACE_REJECTION,
				command, STAGE61_RFU_PHASE_COMM, txWord,
				STAGE61_RFU_IDLE_WORD, flags);
			return false;
		}
		*rxWordOut = STAGE61_RFU_IDLE_WORD;
		peripheral->externalTransfer = false;
		peripheral->externalAwaitAck = false;
		peripheral->externalCommand = 0;
		peripheral->polarity = false;
		return _tracePush(peripheral, STAGE61_RFU_TRACE_COMMAND,
			command, STAGE61_RFU_PHASE_COMM, txWord, *rxWordOut, flags);
	}
	if (peripheral->asyncCommand
		|| peripheral->phase == STAGE61_RFU_PHASE_RECV) {
		return _exchangeWord(peripheral, txWord, rxWordOut);
	}
	return false;
}

static bool _queueExternalControl(struct Stage61RfuPeripheral *peripheral,
	uint8_t command, uint32_t data, uint8_t length) {
	if (!peripheral || command != 0x29 || length != 1
		|| !_canQueueExternalControl(peripheral)) {
		return false;
	}
	peripheral->pendingExternalData[0] = data;
	peripheral->pendingExternalData[1] = 0;
	peripheral->pendingExternalLength = length;
	peripheral->awaitingAsync = false;
	peripheral->asyncCommand = command;
	peripheral->polarity = true;
	(void) _armExternalTransfer(peripheral);
	return true;
}

static bool _armExternalTransfer(struct Stage61RfuPeripheral *peripheral) {
	struct GBASIO *sio;
	uint32_t txWord;
	int32_t cycles;
	if (!peripheral || !peripheral->attached || !peripheral->driver.p
		|| !peripheral->driver.p->p
		|| peripheral->transferBusy || !peripheral->scenario.adapterPresent) {
		return false;
	}
	sio = peripheral->driver.p;
	if (sio->mode != SIO_NORMAL_32
		|| !GBASIONormalIsStart(sio->siocnt)
		|| GBASIONormalIsSc(sio->siocnt)) {
		return false;
	}
	txWord = sio->p->memory.io[REG_SIODATA32_LO >> 1]
		| ((uint32_t) sio->p->memory.io[REG_SIODATA32_HI >> 1] << 16);
	if (!_prepareExternalWord(peripheral, txWord,
		&peripheral->pendingReply)) {
		return false;
	}
	/* Reversed RFU polarity presents SI=SO while the adapter owns the clock. */
	sio->siocnt = GBASIONormalSetSi(sio->siocnt,
		GBASIONormalGetIdleSo(sio->siocnt));
	sio->p->memory.io[REG_SIOCNT >> 1] = sio->siocnt;
	cycles = peripheral->scenario.transferCycles
		? (int32_t) peripheral->scenario.transferCycles
		: STAGE61_RFU_DEFAULT_FAST_CYCLES;
	peripheral->transferBusy = true;
	mTimingDeschedule(&sio->p->timing, &peripheral->event);
	mTimingSchedule(&sio->p->timing, &peripheral->event, cycles);
	return true;
}

struct Stage61RfuHub *Stage61RfuHubCreate(void) {
	return calloc(1, sizeof(struct Stage61RfuHub));
}

bool Stage61RfuHubDestroy(struct Stage61RfuHub *hub) {
	if (!hub || hub->endpointCount) {
		return false;
	}
	free(hub);
	return true;
}

bool Stage61RfuHubReset(struct Stage61RfuHub *hub) {
	unsigned slot;
	if (!hub) {
		return false;
	}
	for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
		if (hub->endpoints[slot]
			&& !Stage61RfuPeripheralReset(hub->endpoints[slot])) {
			return false;
		}
	}
	return true;
}

size_t Stage61RfuHubEndpointCount(const struct Stage61RfuHub *hub) {
	return hub ? hub->endpointCount : 0;
}

bool Stage61RfuHubIsQuiescent(const struct Stage61RfuHub *hub) {
	unsigned slot;
	if (!hub) {
		return false;
	}
	for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
		if (hub->endpoints[slot]
			&& !Stage61RfuPeripheralIsQuiescent(hub->endpoints[slot])) {
			return false;
		}
	}
	return true;
}

struct Stage61RfuPeripheral *Stage61RfuPeripheralCreate(
	struct Stage61RfuHub *hub) {
	struct Stage61RfuPeripheral *peripheral;
	unsigned slot;
	if (!hub || hub->endpointCount >= STAGE61_RFU_MAX_ENDPOINTS) {
		return NULL;
	}
	for (slot = 0; slot < STAGE61_RFU_MAX_ENDPOINTS; ++slot) {
		if (!hub->endpoints[slot]) {
			break;
		}
	}
	if (slot >= STAGE61_RFU_MAX_ENDPOINTS) {
		return NULL;
	}
	peripheral = calloc(1, sizeof(*peripheral));
	if (!peripheral) {
		return NULL;
	}
	peripheral->hub = hub;
	peripheral->slot = (uint8_t) slot;
	peripheral->scenario.adapterPresent = true;
	peripheral->scenario.faultMode = STAGE61_RFU_FAULT_NONE;
	peripheral->driver.init = _driverInit;
	peripheral->driver.deinit = _driverDeinit;
	peripheral->driver.load = _driverLoad;
	peripheral->driver.unload = _driverUnload;
	peripheral->driver.writeRegister = _driverWriteRegister;
	peripheral->event.context = peripheral;
	peripheral->event.callback = _transferEvent;
	peripheral->event.name = "Stage61 RFU Wireless Adapter";
	peripheral->event.priority = 0x80;
	hub->endpoints[slot] = peripheral;
	++hub->endpointCount;
	if (!Stage61RfuPeripheralReset(peripheral)) {
		hub->endpoints[slot] = NULL;
		--hub->endpointCount;
		free(peripheral);
		return NULL;
	}
	return peripheral;
}

void Stage61RfuPeripheralDestroy(struct Stage61RfuPeripheral *peripheral) {
	struct Stage61RfuHub *hub;
	if (!peripheral) {
		return;
	}
	Stage61RfuPeripheralDetach(peripheral);
	_disconnectLinks(peripheral);
	hub = peripheral->hub;
	if (hub && peripheral->slot < STAGE61_RFU_MAX_ENDPOINTS
		&& hub->endpoints[peripheral->slot] == peripheral) {
		hub->endpoints[peripheral->slot] = NULL;
		if (hub->endpointCount) {
			--hub->endpointCount;
		}
	}
	memset(peripheral, 0, sizeof(*peripheral));
	free(peripheral);
}

bool Stage61RfuPeripheralReset(struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral) {
		return false;
	}
	_cancelPhysicalTransfer(peripheral);
	_clearSession(peripheral);
	_clearProtocol(peripheral, STAGE61_RFU_PHASE_LOGIN);
	peripheral->failed = false;
	peripheral->traceOverflow = false;
	peripheral->traceCount = 0;
	peripheral->traceSequence = 0;
	memset(peripheral->trace, 0, sizeof(peripheral->trace));
	return true;
}

bool Stage61RfuPeripheralAttach(struct Stage61RfuPeripheral *peripheral,
	struct GBASIO *sio) {
	if (!peripheral || !sio || !sio->p || peripheral->attached
		|| (sio->drivers.normal
			&& sio->drivers.normal != &peripheral->driver)) {
		return false;
	}
	peripheral->attachedSio = sio;
	GBASIOSetDriver(sio, &peripheral->driver, SIO_NORMAL_32);
	if (sio->drivers.normal != &peripheral->driver) {
		peripheral->attachedSio = NULL;
		return false;
	}
	peripheral->attached = true;
	return true;
}

void Stage61RfuPeripheralDetach(struct Stage61RfuPeripheral *peripheral) {
	struct GBASIO *sio;
	if (!peripheral || !peripheral->attached) {
		return;
	}
	sio = peripheral->attachedSio;
	if (sio && sio->drivers.normal == &peripheral->driver) {
		GBASIOSetDriver(sio, NULL, SIO_NORMAL_32);
	}
	peripheral->attached = false;
	peripheral->attachedSio = NULL;
	peripheral->driver.p = NULL;
}

bool Stage61RfuPeripheralIsAttached(
	const struct Stage61RfuPeripheral *peripheral) {
	return peripheral && peripheral->attached;
}

bool Stage61RfuPeripheralConfigure(
	struct Stage61RfuPeripheral *peripheral,
	const struct Stage61RfuScenario *scenario) {
	if (!peripheral || !scenario || peripheral->transferBusy
		|| _physicalStartPending(peripheral)
		|| scenario->faultMode < STAGE61_RFU_FAULT_NONE
		|| scenario->faultMode > STAGE61_RFU_FAULT_DISCONNECT_NEXT
		|| (scenario->faultMode == STAGE61_RFU_FAULT_REJECT_COMMAND
			&& !scenario->rejectCommand)
		|| scenario->transferCycles > INT_MAX) {
		return false;
	}
	peripheral->scenario = *scenario;
	if (!scenario->adapterPresent) {
		_disconnectCommand(peripheral);
		_clearProtocol(peripheral, STAGE61_RFU_PHASE_LOGIN);
	}
	return true;
}

bool Stage61RfuPeripheralGetScenario(
	const struct Stage61RfuPeripheral *peripheral,
	struct Stage61RfuScenario *scenarioOut) {
	if (!peripheral || !scenarioOut) {
		return false;
	}
	*scenarioOut = peripheral->scenario;
	return true;
}

uint16_t Stage61RfuPeripheralStationId(
	const struct Stage61RfuPeripheral *peripheral) {
	return peripheral ? _stationIdForSlot(peripheral->slot) : 0;
}

uint8_t Stage61RfuPeripheralHostBitmap(
	const struct Stage61RfuPeripheral *peripheral) {
	return _logicalHostBitmap(peripheral);
}

uint32_t Stage61RfuPeripheralSignal(
	const struct Stage61RfuPeripheral *peripheral) {
	return _signalFor(peripheral);
}

bool Stage61RfuPeripheralHealthy(
	const struct Stage61RfuPeripheral *peripheral) {
	return peripheral && !peripheral->failed && !peripheral->traceOverflow;
}

bool Stage61RfuPeripheralIsQuiescent(
	const struct Stage61RfuPeripheral *peripheral) {
	if (!peripheral || peripheral->failed || peripheral->traceOverflow
		|| peripheral->transferBusy || _physicalStartPending(peripheral)
		|| peripheral->commandPending
		|| peripheral->awaitingAsync || peripheral->asyncCommand
		|| peripheral->externalTransfer || peripheral->externalAwaitAck
		|| peripheral->pendingExternalLength || peripheral->polarity
		|| peripheral->fifoCount || peripheral->pendingJoinBitmap
		|| peripheral->requestedHost >= 0
		|| peripheral->recoveryPending) {
		return false;
	}
	return peripheral->phase == STAGE61_RFU_PHASE_LOGIN
		|| (peripheral->phase == STAGE61_RFU_PHASE_COMM
			&& peripheral->responseLength == 0);
}

bool Stage61RfuPeripheralExchangeIsolated(
	struct Stage61RfuPeripheral *peripheral, uint32_t txWord,
	uint32_t *rxWordOut, bool *polarityOut) {
	bool result;
	if (!peripheral || peripheral->transferBusy
		|| _physicalStartPending(peripheral)) {
		if (polarityOut) {
			*polarityOut = peripheral && peripheral->polarity;
		}
		return false;
	}
	result = peripheral->externalAwaitAck
		? _prepareExternalWord(peripheral, txWord, rxWordOut)
		: _exchangeWord(peripheral, txWord, rxWordOut);
	if (polarityOut) {
		*polarityOut = peripheral && peripheral->polarity;
	}
	return result;
}

size_t Stage61RfuPeripheralTraceCount(
	const struct Stage61RfuPeripheral *peripheral) {
	return peripheral ? peripheral->traceCount : 0;
}

size_t Stage61RfuPeripheralTraceCapacity(void) {
	return STAGE61_RFU_TRACE_CAPACITY;
}

bool Stage61RfuPeripheralTraceRead(
	const struct Stage61RfuPeripheral *peripheral, size_t index,
	struct Stage61RfuTraceEntry *entryOut) {
	if (!peripheral || !entryOut || index >= peripheral->traceCount) {
		return false;
	}
	*entryOut = peripheral->trace[index];
	return true;
}

static uint64_t _hashByte(uint64_t hash, uint8_t value) {
	hash ^= value;
	return hash * UINT64_C(1099511628211);
}

static uint64_t _hashU32(uint64_t hash, uint32_t value) {
	unsigned i;
	for (i = 0; i < 4; ++i) {
		hash = _hashByte(hash, (uint8_t) (value >> (i * 8U)));
	}
	return hash;
}

uint64_t Stage61RfuPeripheralTraceHash(
	const struct Stage61RfuPeripheral *peripheral) {
	uint64_t hash = UINT64_C(14695981039346656037);
	size_t i;
	if (!peripheral) {
		return 0;
	}
	for (i = 0; i < peripheral->traceCount; ++i) {
		const struct Stage61RfuTraceEntry *entry = &peripheral->trace[i];
		hash = _hashU32(hash, entry->sequence);
		hash = _hashU32(hash, entry->txWord);
		hash = _hashU32(hash, entry->rxWord);
		hash = _hashByte(hash, (uint8_t) entry->stationId);
		hash = _hashByte(hash, (uint8_t) (entry->stationId >> 8));
		hash = _hashByte(hash, entry->kind);
		hash = _hashByte(hash, entry->command);
		hash = _hashByte(hash, entry->phaseBefore);
		hash = _hashByte(hash, entry->phaseAfter);
		hash = _hashByte(hash, entry->flags);
	}
	hash = _hashByte(hash, peripheral->traceOverflow ? 1 : 0);
	return hash;
}

bool Stage61RfuPeripheralTraceOverflowed(
	const struct Stage61RfuPeripheral *peripheral) {
	return peripheral && peripheral->traceOverflow;
}

bool Stage61RfuPeripheralSupportsSavestate(void) {
	return false;
}

static bool _driverInit(struct GBASIODriver *driver) {
	return driver != NULL;
}

static void _driverDeinit(struct GBASIODriver *driver) {
	struct Stage61RfuPeripheral *peripheral;
	if (!driver) {
		return;
	}
	peripheral = (struct Stage61RfuPeripheral *) driver;
	_cancelPhysicalTransfer(peripheral);
	if (peripheral->attachedSio == driver->p) {
		peripheral->attached = false;
		peripheral->attachedSio = NULL;
	}
	driver->p = NULL;
}

static bool _driverLoad(struct GBASIODriver *driver) {
	struct Stage61RfuPeripheral *peripheral;
	if (!driver || !driver->p || !driver->p->p) {
		return false;
	}
	if (driver->p->mode != SIO_NORMAL_32) {
		return true;
	}
	peripheral = (struct Stage61RfuPeripheral *) driver;
	_loadLoginReset(peripheral);
	return true;
}

static bool _driverUnload(struct GBASIODriver *driver) {
	struct Stage61RfuPeripheral *peripheral;
	if (!driver || !driver->p || !driver->p->p) {
		return false;
	}
	peripheral = (struct Stage61RfuPeripheral *) driver;
	_cancelPhysicalTransfer(peripheral);
	return true;
}

static uint16_t _driverWriteRegister(struct GBASIODriver *driver,
	uint32_t address, uint16_t value) {
	struct Stage61RfuPeripheral *peripheral;
	uint32_t txWord;
	int32_t cycles;
	if (!driver || !driver->p || !driver->p->p) {
		return value;
	}
	if (driver->p->mode != SIO_NORMAL_32) {
		return value;
	}
	peripheral = (struct Stage61RfuPeripheral *) driver;
	if (address != REG_SIOCNT) {
		return value;
	}
	/* Normal SI=!SO; reversed RFU polarity presents SI=SO on every write. */
	value = GBASIONormalSetSi(value, peripheral->polarity
		? GBASIONormalGetIdleSo(value) : !GBASIONormalGetIdleSo(value));
	if (!peripheral->scenario.adapterPresent) {
		value = GBASIONormalFillSi(value);
		if (!GBASIONormalIsStart(value) || !GBASIONormalIsSc(value)) {
			return value;
		}
		driver->p->p->memory.io[REG_SIODATA32_LO >> 1] = UINT16_MAX;
		driver->p->p->memory.io[REG_SIODATA32_HI >> 1] = UINT16_MAX;
		value = GBASIONormalClearStart(value);
		value = GBASIONormalFillIdleSo(value);
		if (GBASIONormalIsIrq(value)) {
			GBARaiseIRQ(driver->p->p, GBA_IRQ_SIO, 0);
		}
		return value;
	}
	if (!GBASIONormalIsStart(value)) {
		return value;
	}
	txWord = driver->p->p->memory.io[REG_SIODATA32_LO >> 1]
		| ((uint32_t) driver->p->p->memory.io[REG_SIODATA32_HI >> 1] << 16);
	if (peripheral->transferBusy) {
		uint8_t flags = STAGE61_RFU_TRACE_FLAG_PRESENT
			| STAGE61_RFU_TRACE_FLAG_DUPLICATE_START;
		if (peripheral->polarity) {
			flags |= STAGE61_RFU_TRACE_FLAG_POLARITY;
		}
		if (!_tracePush(peripheral, STAGE61_RFU_TRACE_TRANSFER,
			peripheral->command, peripheral->phase, txWord,
			peripheral->pendingReply, flags)) {
			return GBASIONormalFillIdleSo(
				GBASIONormalClearStart(value));
		}
		/* Hardware ignores another Start until the scheduled edge finishes. */
		return value;
	}
	if (!GBASIONormalIsSc(value)) {
		/*
		 * In clock-slave mode, leave Start pending until virtual air has an
		 * adapter-initiated 0x28/0x36 word (or its final ACK transfer).
		 */
		if (!_prepareExternalWord(peripheral, txWord,
			&peripheral->pendingReply)) {
			return value;
		}
		value = GBASIONormalSetSi(value,
			GBASIONormalGetIdleSo(value));
		cycles = peripheral->scenario.transferCycles
			? (int32_t) peripheral->scenario.transferCycles
			: STAGE61_RFU_DEFAULT_FAST_CYCLES;
		peripheral->transferBusy = true;
		mTimingDeschedule(&driver->p->p->timing, &peripheral->event);
		mTimingSchedule(&driver->p->p->timing, &peripheral->event, cycles);
		return value;
	}
	if (!_exchangeWord(peripheral, txWord, &peripheral->pendingReply)) {
		return GBASIONormalFillIdleSo(GBASIONormalClearStart(value));
	}
	value = GBASIONormalSetSi(value, peripheral->polarity
		? GBASIONormalGetIdleSo(value) : !GBASIONormalGetIdleSo(value));
	cycles = peripheral->scenario.transferCycles
		? (int32_t) peripheral->scenario.transferCycles
		: (GBASIONormalIsInternalSc(value) && GBASIONormalIsSc(value)
			? STAGE61_RFU_DEFAULT_FAST_CYCLES
			: STAGE61_RFU_DEFAULT_SLOW_CYCLES);
	peripheral->transferBusy = true;
	mTimingDeschedule(&driver->p->p->timing, &peripheral->event);
	mTimingSchedule(&driver->p->p->timing, &peripheral->event, cycles);
	return value;
}

static void _transferEvent(struct mTiming *timing, void *context,
	uint32_t cyclesLate) {
	struct Stage61RfuPeripheral *peripheral = context;
	struct GBASIO *sio;
	(void) timing;
	if (!peripheral || !peripheral->transferBusy || !peripheral->driver.p
		|| !peripheral->driver.p->p) {
		return;
	}
	sio = peripheral->driver.p;
	sio->p->memory.io[REG_SIODATA32_LO >> 1] =
		(uint16_t) peripheral->pendingReply;
	sio->p->memory.io[REG_SIODATA32_HI >> 1] =
		(uint16_t) (peripheral->pendingReply >> 16);
	sio->siocnt = GBASIONormalClearStart(sio->siocnt);
	sio->siocnt = GBASIONormalSetSi(sio->siocnt,
		GBASIONormalGetSc(sio->siocnt));
	sio->siocnt = GBASIONormalFillIdleSo(sio->siocnt);
	sio->p->memory.io[REG_SIOCNT >> 1] = sio->siocnt;
	peripheral->transferBusy = false;
	if (GBASIONormalIsIrq(sio->siocnt)) {
		GBARaiseIRQ(sio->p, GBA_IRQ_SIO, cyclesLate);
	}
}
