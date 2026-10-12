"""保存zero byte専用モデル。外部callは境界停止、指定した仮定だけで継続する。"""
from __future__ import annotations

MASK = 0xffffffff
ENTRY, SELECTOR, SAVE_PTR, HALFWORD = 0x0806DDBD, 0x03005ED8, 0x03005048, 0x030050BC
CALL1, CALL2, CALL3 = 0x08113889, 0x0806DD1D, 0x081138F9
HELPER_LR = 0x09097113


def need(ok, text):
    if not ok:
        raise ValueError(text)


def plus(a, b):
    if type(a) is int and type(b) is int:
        return (a + b) & MASK
    if type(a) is tuple and type(b) is int:
        return (a[0], (a[1] + b) & MASK)
    if type(b) is tuple and type(a) is int:
        return plus(b, a)
    raise ValueError('unknown arithmetic')


def cmp_flags(a, b):
    if a == ('call1_nonzero', 0) and b == 0:
        return (None, False, None, None)
    need(type(a) is int and type(b) is int, 'unknown comparison')
    value = (a - b) & MASK
    return (bool(value >> 31), value == 0, a >= b, bool(((a ^ b) & (a ^ value)) >> 31))


def condition(code, flags):
    need(flags is not None, 'unknown flags')
    uses = {0: (1,), 1: (1,), 8: (1, 2), 13: (0, 1, 3)}
    need(code in uses and all(type(flags[i]) is bool for i in uses[code]), 'unknown/unsupported condition')
    n, z, c, v = flags
    return {0: z, 1: not z, 8: c and not z, 13: z or n != v}[code]


def branch_target(at, half):
    if half & 0xf000 == 0xd000:
        off = half & 255
        return at + 4 + (off - 256 if off & 128 else off) * 2
    need(half & 0xf800 == 0xe000, 'not branch')
    off = half & 0x7ff
    return at + 4 + (off - 0x800 if off & 0x400 else off) * 2


def bl_target(at, raw):
    need(len(raw) == 4, 'BL width')
    hi, lo = int.from_bytes(raw[:2], 'little'), int.from_bytes(raw[2:], 'little')
    need(hi & 0xf800 == 0xf000 and lo & 0xf800 == 0xf800, 'not Thumb-1 BL')
    off = hi & 0x7ff
    return (at + 4 + ((off - 0x800 if off & 0x400 else off) << 12) + ((lo & 0x7ff) << 1)) | 1


def execute(nodes, literals, ident, selector=0, returns=None):
    """returnsは実測値でなく、SP/r4-r11/保存slotを保つ仮想call契約。"""
    need(type(ident) is int and 0 <= ident <= 65535, 'not u16')
    need(type(selector) is int and 0 <= selector <= 255, 'not u8 selector')
    returns = {} if returns is None else dict(returns)
    need(set(returns) <= {CALL1, CALL2}, 'unmodelled call assumption')
    regs = {r: 'unknown_r' + str(r) for r in range(16)}
    regs.update({0: ENTRY, 4: ident, 5: ident << 16, 6: ident, 13: -24, 14: HELPER_LR})
    pc, flags, coverage, reads, writes, calls = ENTRY & ~1, None, [], [], [], []

    def load(address, width):
        reads.append({'address': address, 'width': width})
        if address == SELECTOR and width == 1:
            return selector
        if address == SAVE_PTR and width == 4:
            return ('save_base', 0)
        need(width == 1 and type(address) is tuple and address[0] in ('save_base', 'call1_nonzero'), 'unmodelled read')
        return {'read_width': 1, 'address': address}

    def result(boundary, site=None):
        return {'boundary': boundary, 'site': site, 'registers': regs, 'coverage': coverage,
                'reads': reads, 'writes': writes, 'calls': calls}

    for _ in range(100):
        if pc not in nodes:
            return result(pc | 1)
        need(pc not in coverage, 'cycle')
        coverage.append(pc)
        raw = nodes[pc]
        h, at = int.from_bytes(raw[:2], 'little'), pc
        pc += len(raw)
        if len(raw) == 4:
            target = bl_target(at, raw)
            regs[14] = pc | 1
            calls.append({'site': at, 'target': target, 'args': [regs[r] for r in (0, 1, 2)],
                          'return_thumb': regs[14], 'return_assumed': target in returns})
            if target not in returns:
                return result(target, at)
            for r in (1, 2, 3, 12):
                regs[r] = 'unknown_after_call_r' + str(r)
            regs[0], flags = returns[target], None
        elif h & 0xf800 == 0x4800:
            address = ((at + 4) & ~3) + (h & 255) * 4
            need(address in literals, 'missing literal')
            regs[(h >> 8) & 7] = literals[address]
        elif h & 0xf800 in (0x6800, 0x7800):
            width = 4 if h & 0xf800 == 0x6800 else 1
            rd, rb, off = h & 7, (h >> 3) & 7, ((h >> 6) & 31) * width
            regs[rd] = load(plus(regs[rb], off), width)
        elif h & 0xf800 in (0x7000, 0x8000):
            width = 1 if h & 0xf800 == 0x7000 else 2
            address = plus(regs[(h >> 3) & 7], ((h >> 6) & 31) * width)
            value = regs[h & 7]
            if type(value) is int:
                value &= (1 << (8 * width)) - 1
            else:
                need(width == 1 and type(value) is dict and value.get('read_width') == 1, 'unknown store value')
            writes.append({'site': at, 'address': address, 'width': width, 'value': value})
        elif h & 0xf800 == 0x2000:
            regs[(h >> 8) & 7] = h & 255
            flags = (False, (h & 255) == 0, None, None)
        elif h & 0xf800 == 0x2800:
            flags = cmp_flags(regs[(h >> 8) & 7], h & 255)
        elif h & 0xffc0 == 0x4280:
            flags = cmp_flags(regs[h & 7], regs[(h >> 3) & 7])
        elif h & 0xf800 in (0x0000, 0x0800):
            amount, value = (h >> 6) & 31, regs[(h >> 3) & 7]
            need(type(value) is int, 'unknown shift')
            regs[h & 7] = (value << amount) & MASK if h & 0xf800 == 0 else value >> (amount or 32)
            flags = None
        elif h & 0xfa00 == 0x1800:
            rhs = ((h >> 6) & 7) if h & 0x400 else regs[(h >> 6) & 7]
            regs[h & 7] = plus(regs[(h >> 3) & 7], rhs)
            flags = None
        elif h & 0xf000 == 0xd000:
            if condition((h >> 8) & 15, flags):
                pc = branch_target(at, h)
        elif h & 0xf800 == 0xe000:
            pc = branch_target(at, h)
        else:
            raise ValueError('unsupported opcode at ' + hex(at))
    raise ValueError('instruction budget')
