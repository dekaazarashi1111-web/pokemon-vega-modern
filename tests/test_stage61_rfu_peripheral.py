from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_stage61_rfu_peripheral.c"
HEADER = ROOT / "tools/mgba_stage61_rfu_peripheral.h"
MGBA_INCLUDE = ROOT / ".local/stage61-mgba-0.10.2/include"


HARNESS = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mgba_stage61_rfu_peripheral.h"
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/io.h>
#include <mgba/internal/gba/sio.h>

/* Link-only mGBA shims.  Isolated exchange never calls timing or IRQ. */
static struct mTimingEvent *gScheduledEvent;
static int32_t gScheduledWhen;
static unsigned gIrqCount;
void mTimingSchedule(struct mTiming *timing, struct mTimingEvent *event,
                     int32_t when) {
    (void) timing;
    gScheduledEvent = event;
    gScheduledWhen = when;
}
void mTimingDeschedule(struct mTiming *timing, struct mTimingEvent *event) {
    (void) timing;
    if (gScheduledEvent == event) gScheduledEvent = NULL;
}
void GBARaiseIRQ(struct GBA *gba, enum GBAIRQ irq, uint32_t cyclesLate) {
    (void) gba; (void) cyclesLate;
    assert(irq == GBA_IRQ_SIO);
    ++gIrqCount;
}
void GBASIOSetDriver(struct GBASIO *sio, struct GBASIODriver *driver,
                     enum GBASIOMode mode) {
    struct GBASIODriver *old;
    assert(mode == SIO_NORMAL_8 || mode == SIO_NORMAL_32);
    old = sio->drivers.normal;
    if (old) {
        if (old->unload) old->unload(old);
        if (old->deinit) old->deinit(old);
    }
    if (driver) {
        driver->p = sio;
        if (driver->init) assert(driver->init(driver));
    }
    if (sio->activeDriver == old) {
        sio->activeDriver = driver;
        if (driver && driver->load) assert(driver->load(driver));
    }
    sio->drivers.normal = driver;
}

static uint32_t transfer(struct Stage61RfuPeripheral *p, uint32_t tx,
                         bool *polarity) {
    uint32_t rx = 0;
    assert(Stage61RfuPeripheralExchangeIsolated(p, tx, &rx, polarity));
    return rx;
}

static void completeScheduled(struct GBA *gba) {
    struct mTimingEvent *event = gScheduledEvent;
    assert(event != NULL);
    gScheduledEvent = NULL;
    event->callback(&gba->timing, event->context, 0);
}

static void login(struct Stage61RfuPeripheral *p) {
    bool polarity = true;
    assert(transfer(p, 0x0000494EU, &polarity) == 0x494E0000U);
    assert(!polarity);
    assert(transfer(p, 0xB6B1544EU, &polarity) == 0x544EB6B1U);
    assert(transfer(p, 0xB0BB8001U, &polarity) == 0x8001B0BBU);
    assert(!polarity);
}

static uint32_t command(struct Stage61RfuPeripheral *p, uint8_t cmd,
                        const uint32_t *payload, uint8_t payloadLen,
                        uint32_t *response, uint8_t *responseLen,
                        bool *polarityAfterHeader) {
    uint32_t header;
    uint8_t i;
    bool polarity = false;
    assert(transfer(p, 0x99660000U | ((uint32_t) payloadLen << 8) | cmd,
                    &polarity) == 0x80000000U);
    for (i = 0; i < payloadLen; ++i) {
        assert(transfer(p, payload[i], &polarity) == 0x80000000U);
    }
    header = transfer(p, 0x80000000U, &polarity);
    assert((header & 0xFFFF0000U) == 0x99660000U);
    *responseLen = (uint8_t) (header >> 8);
    if (polarityAfterHeader) *polarityAfterHeader = polarity;
    for (i = 0; i < *responseLen; ++i) {
        response[i] = transfer(p, 0x80000000U, &polarity);
    }
    return header;
}

static uint8_t externalRequest(struct Stage61RfuPeripheral *p,
                               uint8_t expectedCommand,
                               uint32_t *payload) {
    uint32_t header;
    uint8_t length;
    uint8_t i;
    bool polarity = false;
    header = transfer(p, 0x80000000U, &polarity);
    assert((header & 0xFFFF00FFU)
           == (0x99660000U | expectedCommand));
    assert(polarity);
    length = (uint8_t) (header >> 8);
    for (i = 0; i < length; ++i) {
        payload[i] = transfer(p, 0x80000000U, &polarity);
        assert(polarity);
    }
    assert(transfer(p, 0x99660000U | (expectedCommand ^ 0x80U),
                    &polarity) == 0x80000000U);
    assert(!polarity);
    return length;
}

static void destroyPair(struct Stage61RfuHub *hub,
                        struct Stage61RfuPeripheral *a,
                        struct Stage61RfuPeripheral *b) {
    Stage61RfuPeripheralDestroy(b);
    Stage61RfuPeripheralDestroy(a);
    assert(Stage61RfuHubDestroy(hub));
}

static void testLoginAndPresence(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuScenario scenario = {
        false, STAGE61_RFU_FAULT_NONE, 0, 0
    };
    uint32_t rx = 0;
    uint32_t response[64];
    uint8_t responseLen = 0;
    bool polarity = false;
    assert(hub && p);
    assert(Stage61RfuPeripheralConfigure(p, &scenario));
    assert(!Stage61RfuPeripheralExchangeIsolated(
        p, 0x0000494EU, &rx, &polarity));
    scenario.adapterPresent = true;
    assert(Stage61RfuPeripheralConfigure(p, &scenario));
    assert(Stage61RfuPeripheralReset(p));
    login(p);
    assert(command(p, 0x13, NULL, 0, response, &responseLen, NULL)
           == 0x99660193U);
    assert(responseLen == 1);
    assert(response[0] == Stage61RfuPeripheralStationId(p));
    assert(Stage61RfuPeripheralTraceCount(p) == 6);
    assert(Stage61RfuPeripheralTraceHash(p) != 0);
    assert(!Stage61RfuPeripheralSupportsSavestate());
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testDiscoverJoinFifoPolarityDisconnect(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *host = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client2 = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint32_t gameData[6] = {
        0x11223344U, 0x55667788U, 0x01020304U,
        0xAABBCCDDU, 0x13572468U, 0xCAFEBABEU
    };
    uint32_t join[1];
    uint32_t packet[2] = { 0xDEADBEEFU, 0x12345678U };
    uint32_t disconnect[1];
    uint32_t externalData[64];
    uint32_t asyncHeader;
    uint8_t responseLen;
    bool polarity;
    assert(hub && host && client && client2);
    assert(Stage61RfuHubEndpointCount(hub) == 3);
    login(host);
    login(client);
    login(client2);

    assert(command(host, 0x16, gameData, 6, response, &responseLen, NULL)
           == 0x99660096U);
    assert(responseLen == 0);
    assert(command(host, 0x19, NULL, 0, response, &responseLen, NULL)
           == 0x99660099U);

    assert(command(client, 0x1E, NULL, 0, response, &responseLen, NULL)
           == 0x9966079EU);
    assert(responseLen == 7);
    assert(response[0] == Stage61RfuPeripheralStationId(host));
    assert(!memcmp(&response[1], gameData, sizeof(gameData)));

    join[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, join, 1, response, &responseLen, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &responseLen, NULL)
           == 0x9966019AU);
    assert(responseLen == 1);
    assert((response[0] & 0xFFFFU)
           == Stage61RfuPeripheralStationId(client));
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x01);
    assert(Stage61RfuPeripheralSignal(host) == 0xFFU);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);

    assert(command(client2, 0x1E, NULL, 0, response, &responseLen, NULL)
           == 0x9966079EU);
    join[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client2, 0x1F, join, 1, response, &responseLen, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &responseLen, NULL)
           == 0x9966019AU);
    assert((response[0] >> 16) == 1);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x03);
    assert(Stage61RfuPeripheralSignal(host) == 0xFFFFU);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFFFU);
    assert(Stage61RfuPeripheralSignal(client2) == 0xFFFFU);

    /* A child's non-matching logical bitmap is a successful no-op. */
    disconnect[0] = 0x02;
    assert(command(client, 0x30, disconnect, 1,
                   response, &responseLen, NULL)
           == 0x996600B0U);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x03);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFFFU);

    assert(command(client, 0x24, packet, 2, response, &responseLen, NULL)
           == 0x996600A4U);
    assert(command(host, 0x26, NULL, 0, response, &responseLen, NULL)
           == 0x996602A6U);
    assert(responseLen == 2);
    assert(response[0] == packet[0] && response[1] == packet[1]);

    packet[0] = 0x0BADF00DU;
    assert(command(client, 0x24, packet, 1, response, &responseLen, NULL)
           == 0x996600A4U);
    assert(command(host, 0x27, NULL, 0, response, &responseLen, &polarity)
           == 0x996600A7U);
    assert(polarity);
    asyncHeader = transfer(host, 0x80000000U, &polarity);
    assert(asyncHeader == 0x99660128U);
    assert(polarity);
    assert(transfer(host, 0x80000000U, &polarity) == packet[0]);
    assert(polarity);
    assert(transfer(host, 0x996600A8U, &polarity) == 0x80000000U);
    assert(!polarity);

    disconnect[0] = 0x01;
    assert(command(host, 0x30, disconnect, 1,
                   response, &responseLen, NULL)
           == 0x996600B0U);
    assert(externalRequest(client, 0x29, externalData) == 1);
    assert(externalData[0] == 0x01);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x02);
    assert(Stage61RfuPeripheralSignal(client) == 0);
    assert(Stage61RfuPeripheralSignal(host) == 0xFFU);
    assert(Stage61RfuPeripheralSignal(client2) == 0xFFU);

    /* Host role and advertising survive; the hole is reused as logical 0. */
    assert(command(client, 0x1E, NULL, 0, response, &responseLen, NULL)
           == 0x9966079EU);
    join[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, join, 1, response, &responseLen, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &responseLen, NULL)
           == 0x9966019AU);
    assert((response[0] >> 16) == 0);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x03);

    /* Disconnecting logical 1 preserves logical 0 and its signal. */
    disconnect[0] = 0x02;
    assert(command(host, 0x30, disconnect, 1,
                   response, &responseLen, NULL)
           == 0x996600B0U);
    assert(externalRequest(client2, 0x29, externalData) == 1);
    assert(externalData[0] == 0x02);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0x01);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);
    assert(Stage61RfuPeripheralSignal(client2) == 0);

    /* A child may select its own stable logical slot; the host gets 0x29. */
    disconnect[0] = 0x01;
    assert(command(client, 0x30, disconnect, 1,
                   response, &responseLen, NULL)
           == 0x996600B0U);
    assert(externalRequest(host, 0x29, externalData) == 1);
    assert(externalData[0] == 0x01);
    assert(Stage61RfuPeripheralHostBitmap(host) == 0);
    Stage61RfuPeripheralDestroy(client2);
    destroyPair(hub, host, client);
}

static void testSupportedCommandSurface(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint32_t six[6] = { 1, 2, 3, 4, 5, 6 };
    uint32_t one[1] = { 0x12345678U };
    uint32_t zero[1] = { 0 };
    uint8_t length;
    bool polarity;
    assert(hub && p);
    login(p);
    assert(command(p, 0x10, NULL, 0, response, &length, NULL)
           == 0x99660090U);
    assert(command(p, 0x3D, NULL, 0, response, &length, NULL)
           == 0x996600BDU);
    assert(command(p, 0x11, NULL, 0, response, &length, NULL)
           == 0x99660191U && length == 1 && response[0] == 0);
    assert(command(p, 0x13, NULL, 0, response, &length, NULL)
           == 0x99660193U);
    assert(command(p, 0x14, NULL, 0, response, &length, NULL)
           == 0x99660194U && response[0] == 0);
    assert(command(p, 0x16, six, 6, response, &length, NULL)
           == 0x99660096U);
    assert(command(p, 0x17, one, 1, response, &length, NULL)
           == 0x99660097U);
    assert(command(p, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    assert(command(p, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966009AU);
    assert(command(p, 0x1B, NULL, 0, response, &length, NULL)
           == 0x9966009BU);
    assert(command(p, 0x1C, NULL, 0, response, &length, NULL)
           == 0x9966009CU);
    assert(command(p, 0x1D, NULL, 0, response, &length, NULL)
           == 0x9966009DU);
    assert(command(p, 0x1E, NULL, 0, response, &length, NULL)
           == 0x9966009EU);
    assert(command(p, 0x20, NULL, 0, response, &length, NULL)
           == 0x996601A0U);
    assert(command(p, 0x21, NULL, 0, response, &length, NULL)
           == 0x996601A1U);
    assert(command(p, 0x24, one, 1, response, &length, NULL)
           == 0x996600A4U);
    assert(command(p, 0x25, one, 1, response, &length, &polarity)
           == 0x996600A5U && !polarity);
    assert(command(p, 0x26, NULL, 0, response, &length, NULL)
           == 0x996600A6U);
    assert(command(p, 0x27, NULL, 0, response, &length, &polarity)
           == 0x996600A7U && !polarity);
    /* 0x28/0x29 are adapter-initiated slave requests, never master REQs. */
    assert(command(p, 0x28, NULL, 0, response, &length, NULL)
           == 0x996601EEU && response[0] == 1);
    assert(command(p, 0x29, one, 1, response, &length, NULL)
           == 0x996601EEU && response[0] == 1);
    assert(command(p, 0x30, NULL, 0, response, &length, NULL)
           == 0x996601EEU && response[0] == 1);
    assert(command(p, 0x30, zero, 1, response, &length, NULL)
           == 0x996600B0U);
    assert(command(p, 0x32, six, 1, response, &length, NULL)
           == 0x996601EEU && response[0] == 1);
    assert(command(p, 0x33, NULL, 0, response, &length, NULL)
           == 0x996601B3U && response[0] == UINT32_MAX);
    assert(command(p, 0x34, NULL, 0, response, &length, NULL)
           == 0x996600B4U);
    assert(command(p, 0x35, one, 1, response, &length, &polarity)
           == 0x996600B5U && !polarity);
    assert(command(p, 0x36, NULL, 0, response, &length, NULL)
           == 0x996600B6U);
    assert(command(p, 0x37, NULL, 0, response, &length, &polarity)
           == 0x996600B7U && !polarity);
    assert(command(p, 0xEE, NULL, 0, response, &length, NULL)
           == 0x9966006EU);
    assert(command(p, 0x16, six, 5, response, &length, NULL)
           == 0x996601EEU && response[0] == 1);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testFaultAndUnknownReject(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuScenario scenario = {
        true, STAGE61_RFU_FAULT_REJECT_NEXT, 0, 0
    };
    uint32_t response[64];
    uint8_t responseLen;
    assert(hub && p);
    assert(Stage61RfuPeripheralConfigure(p, &scenario));
    login(p);
    assert(command(p, 0x13, NULL, 0, response, &responseLen, NULL)
           == 0x996601EEU);
    assert(responseLen == 1 && response[0] == 1);
    assert(Stage61RfuPeripheralHealthy(p));
    assert(command(p, 0x13, NULL, 0, response, &responseLen, NULL)
           == 0x99660193U);
    assert(command(p, 0x12, NULL, 0, response, &responseLen, NULL)
           == 0x996601EEU);
    assert(response[0] == 1);
    assert(command(p, 0x7F, NULL, 0, response, &responseLen, NULL)
           == 0x996601EEU);
    assert(response[0] == 2);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testTraceOverflowAndHash(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuTraceEntry entry;
    uint32_t rx;
    uint64_t firstHash;
    size_t i;
    assert(hub && p);
    assert(Stage61RfuPeripheralTraceCapacity()
           == STAGE61_RFU_TRACE_CAPACITY);
    for (i = 0; i < Stage61RfuPeripheralTraceCapacity(); ++i) {
        assert(Stage61RfuPeripheralExchangeIsolated(p, 0, &rx, NULL));
        assert(rx == 0);
    }
    firstHash = Stage61RfuPeripheralTraceHash(p);
    assert(firstHash != 0);
    assert(Stage61RfuPeripheralTraceRead(p, 0, &entry));
    assert(entry.sequence == 0 && entry.txWord == 0 && entry.rxWord == 0);
    assert(!Stage61RfuPeripheralTraceRead(
        p, Stage61RfuPeripheralTraceCapacity(), &entry));
    assert(!Stage61RfuPeripheralExchangeIsolated(p, 0, &rx, NULL));
    assert(Stage61RfuPeripheralTraceOverflowed(p));
    assert(!Stage61RfuPeripheralHealthy(p));
    assert(Stage61RfuPeripheralTraceCount(p)
           == Stage61RfuPeripheralTraceCapacity());

    assert(Stage61RfuPeripheralReset(p));
    for (i = 0; i < Stage61RfuPeripheralTraceCapacity(); ++i) {
        assert(Stage61RfuPeripheralExchangeIsolated(p, 0, &rx, NULL));
    }
    assert(Stage61RfuPeripheralTraceHash(p) == firstHash);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testEndpointLimitAndReset(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p0 = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *p1 = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *p2 = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *p3 = Stage61RfuPeripheralCreate(hub);
    assert(hub && p0 && p1 && p2 && p3);
    assert(Stage61RfuPeripheralCreate(hub) == NULL);
    assert(!Stage61RfuHubDestroy(hub));
    assert(Stage61RfuHubReset(hub));
    Stage61RfuPeripheralDestroy(p3);
    Stage61RfuPeripheralDestroy(p2);
    Stage61RfuPeripheralDestroy(p1);
    Stage61RfuPeripheralDestroy(p0);
    assert(Stage61RfuHubEndpointCount(hub) == 0);
    assert(Stage61RfuHubDestroy(hub));
}

static void testDriverTimingLifecycle(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct GBA *gba = calloc(1, sizeof(*gba));
    struct GBASIO sio;
    struct GBASIODriver *driver;
    uint16_t siocnt;
    uint32_t isolatedRx = 0xA5A5A5A5U;
    bool isolatedPolarity = false;
    size_t traceBeforeDuplicate;
    assert(hub && p && gba);
    memset(&sio, 0, sizeof(sio));
    sio.p = gba;
    sio.mode = SIO_NORMAL_32;
    assert(Stage61RfuPeripheralAttach(p, &sio));
    assert(Stage61RfuPeripheralIsAttached(p));
    driver = sio.drivers.normal;
    assert(driver && sio.activeDriver == driver);

    gba->memory.io[REG_SIODATA32_LO >> 1] = 0x8001;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0xB0BB;
    siocnt = driver->writeRegister(driver, REG_SIOCNT, 0x4083);
    sio.siocnt = siocnt;
    assert(gScheduledEvent != NULL);
    assert(gScheduledWhen == 256);
    assert(siocnt & 0x0080);
    assert(siocnt & 0x0004);

    /* Test-only transport cannot race the scheduled physical transfer. */
    traceBeforeDuplicate = Stage61RfuPeripheralTraceCount(p);
    assert(!Stage61RfuPeripheralExchangeIsolated(
        p, 0x99660013U, &isolatedRx, &isolatedPolarity));
    assert(isolatedRx == 0xA5A5A5A5U);
    assert(Stage61RfuPeripheralTraceCount(p) == traceBeforeDuplicate);

    traceBeforeDuplicate = Stage61RfuPeripheralTraceCount(p);
    assert(driver->writeRegister(driver, REG_SIOCNT, 0x4083) & 0x0080);
    assert(Stage61RfuPeripheralHealthy(p));
    assert(Stage61RfuPeripheralTraceCount(p) == traceBeforeDuplicate + 1);

    completeScheduled(gba);
    assert(gba->memory.io[REG_SIODATA32_LO >> 1] == 0xB0BB);
    assert(gba->memory.io[REG_SIODATA32_HI >> 1] == 0x8001);
    assert(!(sio.siocnt & 0x0080));
    assert(sio.siocnt & 0x0008);
    assert(sio.siocnt & 0x0004);
    assert(gIrqCount == 1);

    assert(transfer(p, 0x99660013U, NULL) == 0x80000000U);
    assert(driver->unload(driver));
    assert(driver->load(driver));
    assert(transfer(p, 0x1234494EU, NULL) == 0x494E1234U);
    Stage61RfuPeripheralDetach(p);
    assert(!Stage61RfuPeripheralIsAttached(p));
    assert(sio.drivers.normal == NULL && sio.activeDriver == NULL);
    free(gba);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testDriverExternalClockDelivery(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *host = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    struct GBA *gba = calloc(1, sizeof(*gba));
    struct GBASIO sio;
    struct GBASIODriver *driver;
    uint32_t response[64];
    uint32_t gameData[6] = { 1, 2, 3, 4, 5, 6 };
    uint32_t join[1];
    uint32_t packet[1] = { 0xC001D00DU };
    uint8_t length;
    uint16_t value;
    bool polarity;
    assert(hub && host && client && gba);
    memset(&sio, 0, sizeof(sio));
    sio.p = gba;
    sio.mode = SIO_NORMAL_32;
    assert(Stage61RfuPeripheralAttach(host, &sio));
    driver = sio.drivers.normal;
    login(host);
    login(client);
    assert(command(host, 0x16, gameData, 6, response, &length, NULL)
           == 0x99660096U);
    assert(command(host, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    join[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, join, 1, response, &length, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966019AU);
    assert(command(host, 0x27, NULL, 0, response, &length, &polarity)
           == 0x996600A7U && !polarity);

    gScheduledEvent = NULL;
    gIrqCount = 0;
    gba->memory.io[REG_SIODATA32_LO >> 1] = 0;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0x8000;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x5082);
    sio.siocnt = value;
    assert(gScheduledEvent == NULL); /* Slave waits for virtual air. */

    assert(command(client, 0x24, packet, 1, response, &length, NULL)
           == 0x996600A4U);
    assert(gScheduledEvent != NULL && gScheduledWhen == 256);
    completeScheduled(gba);
    assert(gba->memory.io[REG_SIODATA32_LO >> 1] == 0x0128);
    assert(gba->memory.io[REG_SIODATA32_HI >> 1] == 0x9966);
    value = driver->writeRegister(driver, REG_SIOCNT, 0x500A);
    assert(value & 0x0004); /* Reversed polarity: SO=1 presents SI=1. */
    sio.siocnt = value;

    gba->memory.io[REG_SIODATA32_LO >> 1] = 0;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0x8000;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x5082);
    sio.siocnt = value;
    assert(gScheduledEvent != NULL);
    completeScheduled(gba);
    assert(gba->memory.io[REG_SIODATA32_LO >> 1]
           == (uint16_t) packet[0]);
    assert(gba->memory.io[REG_SIODATA32_HI >> 1]
           == (uint16_t) (packet[0] >> 16));

    gba->memory.io[REG_SIODATA32_LO >> 1] = 0x00A8;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0x9966;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x5082);
    sio.siocnt = value;
    assert(gScheduledEvent != NULL);
    completeScheduled(gba);
    assert(gba->memory.io[REG_SIODATA32_LO >> 1] == 0);
    assert(gba->memory.io[REG_SIODATA32_HI >> 1] == 0x8000);
    assert(gIrqCount == 3);
    assert(Stage61RfuPeripheralHealthy(host));

    Stage61RfuPeripheralDetach(host);
    free(gba);
    Stage61RfuPeripheralDestroy(client);
    Stage61RfuPeripheralDestroy(host);
    assert(Stage61RfuHubDestroy(hub));
}

static void testMalformedCommAbortsPendingRequest(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint8_t length;
    assert(hub && p);
    assert(Stage61RfuHubIsQuiescent(hub));
    login(p);
    assert(Stage61RfuPeripheralIsQuiescent(p));

    /* An idle-looking word with any payload bits is not a finalizer. */
    assert(transfer(p, 0x99660019U, NULL) == 0x80000000U);
    assert(!Stage61RfuPeripheralIsQuiescent(p));
    assert(transfer(p, 0x80000001U, NULL) == 0x996601EEU);
    assert(transfer(p, 0x80000000U, NULL) == 2);
    assert(Stage61RfuPeripheralIsQuiescent(p));

    /* 0x19 would advertise if its pending finalize survived a random word. */
    assert(transfer(p, 0x99660019U, NULL) == 0x80000000U);
    assert(!Stage61RfuPeripheralIsQuiescent(p));
    assert(transfer(p, 0x12345678U, NULL) == 0x996601EEU);
    assert(transfer(p, 0x80000000U, NULL) == 2);
    assert(Stage61RfuPeripheralIsQuiescent(p));
    assert(command(p, 0x13, NULL, 0, response, &length, NULL)
           == 0x99660193U);
    assert(response[0] == Stage61RfuPeripheralStationId(p));
    assert(Stage61RfuPeripheralHostBitmap(p) == 0);

    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testMalformedExternalReceiveFailsClosed(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *host = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint32_t payload[1];
    uint32_t rx = 0xA5A5A5A5U;
    uint8_t length;
    bool polarity;
    assert(hub && host && client);
    login(host);
    login(client);
    assert(command(host, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    payload[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, payload, 1, response, &length, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966019AU);
    assert(command(host, 0x27, NULL, 0, response, &length, &polarity)
           == 0x996600A7U && !polarity);
    payload[0] = 0xC001D00DU;
    assert(command(client, 0x24, payload, 1, response, &length, NULL)
           == 0x996600A4U);
    assert(transfer(host, 0x80000000U, &polarity) == 0x99660128U);
    assert(polarity);

    /* A non-idle payload clock is fatal and must erase the old async state. */
    assert(!Stage61RfuPeripheralExchangeIsolated(
        host, 0x12345678U, &rx, &polarity));
    assert(rx == 0x80000000U);
    assert(!Stage61RfuPeripheralHealthy(host));
    assert(Stage61RfuPeripheralHostBitmap(host) == 0);
    assert(Stage61RfuPeripheralSignal(client) == 0);

    destroyPair(hub, host, client);
}

static void testConnectRecoveryCommands(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *host = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint32_t gameData[6] = { 1, 2, 3, 4, 5, 6 };
    uint32_t payload[2];
    uint32_t externalData[64];
    uint8_t length;
    assert(hub && host && client);
    login(host);
    login(client);
    assert(command(host, 0x16, gameData, 6, response, &length, NULL)
           == 0x99660096U);
    assert(command(host, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    payload[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, payload, 1, response, &length, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966019AU);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);

    payload[0] = 1;
    assert(command(host, 0x30, payload, 1, response, &length, NULL)
           == 0x996600B0U);
    assert(externalRequest(client, 0x29, externalData) == 1);
    assert(externalData[0] == 1);

    payload[0] = ((uint32_t) Stage61RfuPeripheralStationId(host) << 16)
        | Stage61RfuPeripheralStationId(client);
    payload[1] = 1;
    assert(command(client, 0x32, payload, 2, response, &length, NULL)
           == 0x996600B2U);
    assert(!Stage61RfuPeripheralIsQuiescent(client));
    assert(command(client, 0x33, NULL, 0, response, &length, NULL)
           == 0x996601B3U);
    assert(length == 1 && response[0] == 0);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);
    assert(command(client, 0x34, NULL, 0, response, &length, NULL)
           == 0x996600B4U);
    assert(Stage61RfuHubIsQuiescent(hub));

    destroyPair(hub, host, client);
}

static void testContradictoryRolesAreRejected(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *host = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *otherHost = Stage61RfuPeripheralCreate(hub);
    uint32_t response[64];
    uint32_t payload[2];
    uint8_t length;
    assert(hub && host && client && otherHost);
    login(host);
    login(client);
    login(otherHost);

    assert(command(host, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    payload[0] = Stage61RfuPeripheralStationId(host);
    assert(command(client, 0x1F, payload, 1, response, &length, NULL)
           == 0x9966009FU);
    assert(command(host, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966019AU);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);

    /* A connected child cannot become a host without disconnecting first. */
    assert(command(client, 0x19, NULL, 0, response, &length, NULL)
           == 0x996601EEU);
    assert(length == 1 && response[0] == 1);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);

    assert(command(otherHost, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    payload[0] = Stage61RfuPeripheralStationId(otherHost);
    /* A host cannot simultaneously become another host's child. */
    assert(command(host, 0x1F, payload, 1, response, &length, NULL)
           == 0x996601EEU);
    assert(length == 1 && response[0] == 1);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);

    payload[0] =
        ((uint32_t) Stage61RfuPeripheralStationId(otherHost) << 16)
        | Stage61RfuPeripheralStationId(host);
    payload[1] = 1;
    /* Recovery is also a client role and is rejected for an active host. */
    assert(command(host, 0x32, payload, 2, response, &length, NULL)
           == 0x996601EEU);
    assert(length == 1 && response[0] == 1);
    assert(Stage61RfuPeripheralHostBitmap(host) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);

    Stage61RfuPeripheralDestroy(otherHost);
    Stage61RfuPeripheralDestroy(client);
    Stage61RfuPeripheralDestroy(host);
    assert(Stage61RfuHubDestroy(hub));
}

static void testDriverOwnershipNormal8AndAbsent(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuScenario scenario = {
        false, STAGE61_RFU_FAULT_NONE, 0, 0
    };
    struct GBA *gba = calloc(1, sizeof(*gba));
    struct GBASIO sio;
    struct GBASIODriver *driver;
    uint32_t response[64];
    uint8_t length;
    uint16_t value;
    size_t traceBefore;
    assert(hub && p && gba);
    memset(&sio, 0, sizeof(sio));
    sio.mode = SIO_NORMAL_32;
    assert(!Stage61RfuPeripheralAttach(p, &sio));
    sio.p = gba;
    assert(Stage61RfuPeripheralConfigure(p, &scenario));
    assert(Stage61RfuPeripheralAttach(p, &sio));
    driver = sio.drivers.normal;
    assert(driver != NULL);

    gScheduledEvent = NULL;
    gIrqCount = 0;
    traceBefore = Stage61RfuPeripheralTraceCount(p);
    gba->memory.io[REG_SIODATA32_LO >> 1] = 0;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x4083);
    assert(!(value & 0x0080) && (value & 0x0008) && (value & 0x0004));
    assert(gba->memory.io[REG_SIODATA32_LO >> 1] == UINT16_MAX);
    assert(gba->memory.io[REG_SIODATA32_HI >> 1] == UINT16_MAX);
    assert(gScheduledEvent == NULL && gIrqCount == 1);
    assert(Stage61RfuPeripheralTraceCount(p) == traceBefore);
    value = driver->writeRegister(driver, REG_SIOCNT, 0x5083);
    assert(!(value & 0x0080) && (value & 0x0008) && (value & 0x0004));
    assert(gScheduledEvent == NULL && gIrqCount == 2);
    assert(Stage61RfuPeripheralTraceCount(p) == traceBefore);

    scenario.adapterPresent = true;
    assert(Stage61RfuPeripheralConfigure(p, &scenario));
    assert(Stage61RfuPeripheralReset(p));
    login(p);
    sio.mode = SIO_NORMAL_8;
    assert(driver->load(driver));
    traceBefore = Stage61RfuPeripheralTraceCount(p);
    assert(driver->writeRegister(driver, REG_SIOCNT, 0x4083) == 0x4083);
    assert(gScheduledEvent == NULL);
    assert(Stage61RfuPeripheralTraceCount(p) == traceBefore);
    assert(command(p, 0x13, NULL, 0, response, &length, NULL)
           == 0x99660193U); /* NORMAL8 load did not steal/reset protocol. */

    sio.mode = SIO_NORMAL_32;
    GBASIOSetDriver(&sio, NULL, SIO_NORMAL_32);
    assert(!Stage61RfuPeripheralIsAttached(p));
    assert(driver->p == NULL);
    assert(sio.drivers.normal == NULL && sio.activeDriver == NULL);
    free(gba); /* Destroy must not follow the now-dead core through driver.p. */
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testClockSlaveStartIsPendingUntilReset(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuScenario scenario = {
        true, STAGE61_RFU_FAULT_NONE, 0, 0
    };
    struct GBA *gba = calloc(1, sizeof(*gba));
    struct GBASIO sio;
    struct GBASIODriver *driver;
    uint32_t rx = 0xA5A5A5A5U;
    uint16_t value;
    size_t traceBefore;
    assert(hub && p && gba);
    memset(&sio, 0, sizeof(sio));
    sio.p = gba;
    sio.mode = SIO_NORMAL_32;
    assert(Stage61RfuPeripheralAttach(p, &sio));
    driver = sio.drivers.normal;
    login(p);

    gScheduledEvent = NULL;
    gba->memory.io[REG_SIODATA32_LO >> 1] = 0;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0x8000;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x5082);
    sio.siocnt = value;
    gba->memory.io[REG_SIOCNT >> 1] = value;
    assert(value & 0x0080);
    assert(gScheduledEvent == NULL);
    assert(!Stage61RfuPeripheralIsQuiescent(p));
    assert(!Stage61RfuPeripheralConfigure(p, &scenario));
    traceBefore = Stage61RfuPeripheralTraceCount(p);
    assert(!Stage61RfuPeripheralExchangeIsolated(
        p, 0x99660013U, &rx, NULL));
    assert(rx == 0xA5A5A5A5U);
    assert(Stage61RfuPeripheralTraceCount(p) == traceBefore);

    assert(Stage61RfuHubReset(hub));
    assert(!(sio.siocnt & 0x0080));
    assert(gba->memory.io[REG_SIOCNT >> 1] == sio.siocnt);
    assert(Stage61RfuPeripheralIsQuiescent(p));
    assert(Stage61RfuPeripheralConfigure(p, &scenario));

    Stage61RfuPeripheralDetach(p);
    free(gba);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

static void testScheduledTraceOverflowFailsClosed(void) {
    struct Stage61RfuHub *hub = Stage61RfuHubCreate();
    struct Stage61RfuPeripheral *p = Stage61RfuPeripheralCreate(hub);
    struct Stage61RfuPeripheral *client = Stage61RfuPeripheralCreate(hub);
    struct GBA *gba = calloc(1, sizeof(*gba));
    struct GBASIO sio;
    struct GBASIODriver *driver;
    uint32_t rx;
    uint32_t response[64];
    uint32_t join[1];
    uint8_t length;
    uint16_t value;
    size_t i;
    assert(hub && p && client && gba);
    memset(&sio, 0, sizeof(sio));
    sio.p = gba;
    sio.mode = SIO_NORMAL_32;
    assert(Stage61RfuPeripheralAttach(p, &sio));
    driver = sio.drivers.normal;
    login(p);
    login(client);
    assert(command(p, 0x19, NULL, 0, response, &length, NULL)
           == 0x99660099U);
    join[0] = Stage61RfuPeripheralStationId(p);
    assert(command(client, 0x1F, join, 1, response, &length, NULL)
           == 0x9966009FU);
    assert(command(p, 0x1A, NULL, 0, response, &length, NULL)
           == 0x9966019AU);
    assert(Stage61RfuPeripheralHostBitmap(p) == 1);
    assert(Stage61RfuPeripheralSignal(client) == 0xFFU);
    for (i = Stage61RfuPeripheralTraceCount(p);
         i + 1 < Stage61RfuPeripheralTraceCapacity(); ++i) {
        assert(Stage61RfuPeripheralExchangeIsolated(p, 0, &rx, NULL));
    }
    assert(Stage61RfuPeripheralTraceCount(p) == 511);
    gScheduledEvent = NULL;
    gIrqCount = 0;
    gba->memory.io[REG_SIODATA32_LO >> 1] = 0;
    gba->memory.io[REG_SIODATA32_HI >> 1] = 0;
    value = driver->writeRegister(driver, REG_SIOCNT, 0x4083);
    sio.siocnt = value;
    assert(gScheduledEvent != NULL);
    assert(Stage61RfuPeripheralTraceCount(p) == 512);
    value = driver->writeRegister(driver, REG_SIOCNT, 0x4083);
    sio.siocnt = value;
    assert(gScheduledEvent == NULL);
    assert(!(value & 0x0080) && (value & 0x0008));
    assert(Stage61RfuPeripheralTraceOverflowed(p));
    assert(!Stage61RfuPeripheralHealthy(p));
    assert(Stage61RfuPeripheralHostBitmap(p) == 0);
    assert(Stage61RfuPeripheralSignal(p) == 0);
    assert(Stage61RfuPeripheralSignal(client) == 0);
    assert(gIrqCount == 0);

    Stage61RfuPeripheralDetach(p);
    free(gba);
    Stage61RfuPeripheralDestroy(client);
    Stage61RfuPeripheralDestroy(p);
    assert(Stage61RfuHubDestroy(hub));
}

int main(int argc, char **argv) {
    if (argc != 2) return 64;
    if (!strcmp(argv[1], "login")) testLoginAndPresence();
    else if (!strcmp(argv[1], "hub")) testDiscoverJoinFifoPolarityDisconnect();
    else if (!strcmp(argv[1], "fault")) testFaultAndUnknownReject();
    else if (!strcmp(argv[1], "trace")) testTraceOverflowAndHash();
    else if (!strcmp(argv[1], "limit")) testEndpointLimitAndReset();
    else if (!strcmp(argv[1], "driver")) testDriverTimingLifecycle();
    else if (!strcmp(argv[1], "commands")) testSupportedCommandSurface();
    else if (!strcmp(argv[1], "external")) testDriverExternalClockDelivery();
    else if (!strcmp(argv[1], "malformed")) testMalformedCommAbortsPendingRequest();
    else if (!strcmp(argv[1], "malformed_external")) testMalformedExternalReceiveFailsClosed();
    else if (!strcmp(argv[1], "recovery")) testConnectRecoveryCommands();
    else if (!strcmp(argv[1], "roles")) testContradictoryRolesAreRejected();
    else if (!strcmp(argv[1], "driver_edges")) testDriverOwnershipNormal8AndAbsent();
    else if (!strcmp(argv[1], "slave_pending")) testClockSlaveStartIsPendingUntilReset();
    else if (!strcmp(argv[1], "scheduled_overflow")) testScheduledTraceOverflowFailsClosed();
    else return 65;
    puts("PASS");
    return 0;
}
"""


class Stage61RfuPeripheralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MGBA_INCLUDE.is_dir():
            raise unittest.SkipTest("pinned mGBA 0.10.2 source is unavailable")
        cls._temporary = tempfile.TemporaryDirectory()
        directory = Path(cls._temporary.name)
        harness = directory / "rfu_peripheral_harness.c"
        cls.binary = directory / "rfu_peripheral_harness"
        harness.write_text(textwrap.dedent(HARNESS), encoding="utf-8")
        command = [
            "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
            "-isystem", str(MGBA_INCLUDE), "-I", str(ROOT / "tools"),
            str(SOURCE), str(harness), "-o", str(cls.binary),
        ]
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if completed.returncode:
            raise AssertionError(
                "strict RFU peripheral compile failed:\n"
                + completed.stdout + completed.stderr
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def _run_case(self, name: str) -> None:
        completed = subprocess.run(
            [str(self.binary), name], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(
            completed.returncode, 0,
            msg=completed.stdout + completed.stderr,
        )
        self.assertEqual(completed.stdout, "PASS\n")

    def test_login_and_cancelable_adapter_presence(self) -> None:
        self._run_case("login")

    def test_two_endpoint_discover_join_fifo_and_polarity(self) -> None:
        self._run_case("hub")

    def test_fault_and_unknown_command_are_ack_rejected(self) -> None:
        self._run_case("fault")

    def test_trace_hash_is_deterministic_and_overflow_fails_closed(self) -> None:
        self._run_case("trace")

    def test_four_endpoint_limit_and_explicit_reset(self) -> None:
        self._run_case("limit")

    def test_normal32_driver_timing_polarity_and_load_reset(self) -> None:
        self._run_case("driver")

    def test_supported_command_surface_and_length_rejection(self) -> None:
        self._run_case("commands")

    def test_driver_external_clock_delivers_async_data_and_ack(self) -> None:
        self._run_case("external")

    def test_malformed_comm_aborts_pending_side_effect(self) -> None:
        self._run_case("malformed")

    def test_malformed_external_receive_fails_closed(self) -> None:
        self._run_case("malformed_external")

    def test_connect_recovery_32_33_34_uses_stable_slot(self) -> None:
        self._run_case("recovery")

    def test_contradictory_host_and_client_roles_are_rejected(self) -> None:
        self._run_case("roles")

    def test_driver_ownership_normal8_and_absent_completion(self) -> None:
        self._run_case("driver_edges")

    def test_clock_slave_start_is_nonquiescent_until_hub_reset(self) -> None:
        self._run_case("slave_pending")

    def test_scheduled_transfer_is_canceled_on_trace_overflow(self) -> None:
        self._run_case("scheduled_overflow")

    def test_source_has_only_sio_timing_runtime_surface(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        self.assertIn("struct GBASIODriver", source)
        self.assertIn("struct mTimingEvent", source)
        self.assertIn("GBASIOSetDriver(sio, &peripheral->driver", source)
        self.assertIn("SIO_NORMAL_32", source)
        self.assertIn("mTimingSchedule", source)
        self.assertNotIn("memory.wram", source)
        self.assertNotIn("memory.rom", source)
        self.assertNotIn("savedata", source.lower())
        self.assertIn("not part of\n * mGBA savestates", header)
        self.assertIn("MUST call Stage61RfuHubReset", header)
        self.assertIn("quiescence does NOT serialize or restore RFU state", header)
        self.assertIn("Stage61RfuPeripheralIsQuiescent", header)
        self.assertIn("Always false", header)


if __name__ == "__main__":
    unittest.main()
