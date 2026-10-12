"""全constructor/setupの直接CFGと限定callee効果証明。根/lifetime未閉鎖を昇格しない。"""
from collections import deque
import copy
import hashlib
import pr16_dex_hof_callback_party as inherited
import pr16_dex_hof_callback_party_task as inherited_task
block=inherited.block
BLOCKS={}
def put(name,address,specs):BLOCKS[name]=tuple(block(address,specs))

put('constructor_1', 0x0811f24c, [
    ('push', 240, True), # 0x0811f24c
    ('movhi', 7, 10), # 0x0811f24e
    ('movhi', 6, 9), # 0x0811f250
    ('movhi', 5, 8), # 0x0811f252
    ('push', 224, False), # 0x0811f254
    ('spadd', -4), # 0x0811f256
    ('spmem', True, 4, 36), # 0x0811f258
    ('shift', 'lsl', 0, 0, 24), # 0x0811f25a
    ('shift', 'lsr', 0, 0, 24), # 0x0811f25c
    ('movhi', 9, 0), # 0x0811f25e
    ('shift', 'lsl', 1, 1, 24), # 0x0811f260
    ('shift', 'lsr', 1, 1, 24), # 0x0811f262
    ('movhi', 10, 1), # 0x0811f264
    ('shift', 'lsl', 2, 2, 24), # 0x0811f266
    ('shift', 'lsr', 2, 2, 24), # 0x0811f268
    ('movhi', 8, 2), # 0x0811f26a
    ('shift', 'lsl', 3, 3, 24), # 0x0811f26c
    ('shift', 'lsr', 3, 3, 24), # 0x0811f26e
    ('spmem', False, 3, 0), # 0x0811f270
    ('shift', 'lsl', 4, 4, 24), # 0x0811f272
    ('shift', 'lsr', 7, 4, 24), # 0x0811f274
    ('call', 135394992), # 0x0811f276
    ('literal', 6, 135393940), # 0x0811f27a
    ('imm', 'mov', 0, 142), # 0x0811f27c
    ('shift', 'lsl', 0, 0, 2), # 0x0811f27e
    ('call', 134228892), # 0x0811f280
    ('addi', 5, 0, 0), # 0x0811f284
    ('mem', False, 'word', 5, 6, 0), # 0x0811f286
    ('imm', 'cmp', 5, 0), # 0x0811f288
    ('branch', 1, 135393944), # 0x0811f28a
    ('spmem', True, 0, 44), # 0x0811f28c
    ('call', 134219076), # 0x0811f28e
    ('jump', 135394184), # 0x0811f292
])

put('constructor_2', 0x0811f298, [
    ('literal', 3, 135394024), # 0x0811f298
    ('imm', 'mov', 1, 15), # 0x0811f29a
    ('movhi', 0, 9), # 0x0811f29c
    ('alu', 'and', 1, 0), # 0x0811f29e
    ('mem', True, 'byte', 2, 3, 8), # 0x0811f2a0
    ('imm', 'mov', 0, 16), # 0x0811f2a2
    ('alu', 'neg', 0, 0), # 0x0811f2a4
    ('alu', 'and', 0, 2), # 0x0811f2a6
    ('alu', 'orr', 0, 1), # 0x0811f2a8
    ('mem', False, 'byte', 0, 3, 8), # 0x0811f2aa
    ('spmem', True, 1, 44), # 0x0811f2ac
    ('mem', False, 'word', 1, 3, 0), # 0x0811f2ae
    ('imm', 'mov', 4, 0), # 0x0811f2b0
    ('movhi', 0, 8), # 0x0811f2b2
    ('mem', False, 'byte', 0, 3, 11), # 0x0811f2b4
    ('shift', 'lsl', 2, 7, 2), # 0x0811f2b6
    ('mem', True, 'half', 1, 5, 10), # 0x0811f2b8
    ('imm', 'mov', 0, 3), # 0x0811f2ba
    ('alu', 'and', 0, 1), # 0x0811f2bc
    ('alu', 'orr', 0, 2), # 0x0811f2be
    ('mem', False, 'half', 0, 5, 10), # 0x0811f2c0
    ('spmem', True, 0, 40), # 0x0811f2c2
    ('mem', False, 'word', 0, 5, 0), # 0x0811f2c4
    ('mem', False, 'word', 4, 5, 4), # 0x0811f2c6
    ('mem', True, 'byte', 1, 5, 8), # 0x0811f2c8
    ('imm', 'mov', 0, 15), # 0x0811f2ca
    ('alu', 'neg', 0, 0), # 0x0811f2cc
    ('alu', 'and', 0, 1), # 0x0811f2ce
    ('mem', False, 'byte', 0, 5, 8), # 0x0811f2d0
    ('addi', 7, 3, 0), # 0x0811f2d2
    ('movhi', 1, 9), # 0x0811f2d4
    ('imm', 'cmp', 1, 4), # 0x0811f2d6
    ('branch', 1, 135394028), # 0x0811f2d8
    ('mem', True, 'word', 0, 6, 0), # 0x0811f2da
    ('mem', True, 'byte', 1, 0, 8), # 0x0811f2dc
    ('imm', 'mov', 2, 1), # 0x0811f2de
    ('alu', 'orr', 1, 2), # 0x0811f2e0
    ('mem', False, 'byte', 1, 0, 8), # 0x0811f2e2
    ('jump', 135394040), # 0x0811f2e4
])

put('constructor_3', 0x0811f2ec, [
    ('mem', True, 'word', 2, 6, 0), # 0x0811f2ec
    ('mem', True, 'byte', 1, 2, 8), # 0x0811f2ee
    ('imm', 'mov', 0, 2), # 0x0811f2f0
    ('alu', 'neg', 0, 0), # 0x0811f2f2
    ('alu', 'and', 0, 1), # 0x0811f2f4
    ('mem', False, 'byte', 0, 2, 8), # 0x0811f2f6
    ('movhi', 5, 10), # 0x0811f2f8
    ('imm', 'cmp', 5, 255), # 0x0811f2fa
    ('branch', 0, 135394064), # 0x0811f2fc
    ('imm', 'mov', 0, 3), # 0x0811f2fe
    ('alu', 'and', 0, 5), # 0x0811f300
    ('shift', 'lsl', 0, 0, 4), # 0x0811f302
    ('mem', True, 'byte', 2, 7, 8), # 0x0811f304
    ('imm', 'mov', 1, 49), # 0x0811f306
    ('alu', 'neg', 1, 1), # 0x0811f308
    ('alu', 'and', 1, 2), # 0x0811f30a
    ('alu', 'orr', 1, 0), # 0x0811f30c
    ('mem', False, 'byte', 1, 7, 8), # 0x0811f30e
    ('imm', 'mov', 2, 0), # 0x0811f310
    ('literal', 5, 135394200), # 0x0811f312
    ('imm', 'mov', 4, 134), # 0x0811f314
    ('shift', 'lsl', 4, 4, 2), # 0x0811f316
    ('imm', 'mov', 3, 0), # 0x0811f318
    ('mem', True, 'word', 0, 5, 0), # 0x0811f31a
    ('shift', 'lsl', 1, 2, 1), # 0x0811f31c
    ('add', 0, 0, 4), # 0x0811f31e
    ('add', 0, 0, 1), # 0x0811f320
    ('mem', False, 'half', 3, 0, 0), # 0x0811f322
    ('addi', 0, 2, 1), # 0x0811f324
    ('shift', 'lsl', 0, 0, 16), # 0x0811f326
    ('shift', 'lsr', 2, 0, 16), # 0x0811f328
    ('imm', 'cmp', 2, 15), # 0x0811f32a
    ('branch', 9, 135394074), # 0x0811f32c
    ('imm', 'mov', 2, 0), # 0x0811f32e
    ('literal', 4, 135394200), # 0x0811f330
    ('imm', 'mov', 3, 255), # 0x0811f332
    ('mem', True, 'word', 0, 4, 0), # 0x0811f334
    ('imm', 'add', 0, 12), # 0x0811f336
    ('add', 0, 0, 2), # 0x0811f338
    ('mem', True, 'byte', 1, 0, 0), # 0x0811f33a
    ('alu', 'orr', 1, 3), # 0x0811f33c
    ('mem', False, 'byte', 1, 0, 0), # 0x0811f33e
    ('addi', 0, 2, 1), # 0x0811f340
    ('shift', 'lsl', 0, 0, 16), # 0x0811f342
    ('shift', 'lsr', 2, 0, 16), # 0x0811f344
    ('imm', 'cmp', 2, 2), # 0x0811f346
    ('branch', 9, 135394100), # 0x0811f348
    ('spmem', True, 0, 0), # 0x0811f34a
    ('imm', 'cmp', 0, 0), # 0x0811f34c
    ('branch', 0, 135394160), # 0x0811f34e
    ('addi', 1, 7, 0), # 0x0811f350
    ('imm', 'mov', 0, 9), # 0x0811f352
    ('signed_load', 'byte', 0, 1, 0), # 0x0811f354
    ('imm', 'cmp', 0, 5), # 0x0811f356
    ('branch', 12, 135394158), # 0x0811f358
    ('addi', 1, 0, 0), # 0x0811f35a
    ('imm', 'mov', 0, 100), # 0x0811f35c
    ('alu', 'mul', 0, 1), # 0x0811f35e
    ('literal', 1, 135394204), # 0x0811f360
    ('add', 0, 0, 1), # 0x0811f362
    ('imm', 'mov', 1, 11), # 0x0811f364
    ('call', 134476628), # 0x0811f366
    ('imm', 'cmp', 0, 0), # 0x0811f36a
    ('branch', 1, 135394162), # 0x0811f36c
    ('imm', 'mov', 0, 0), # 0x0811f36e
    ('mem', False, 'byte', 0, 7, 9), # 0x0811f370
    ('literal', 2, 135394208), # 0x0811f372
    ('mem', True, 'byte', 1, 2, 0), # 0x0811f374
    ('imm', 'mov', 0, 5), # 0x0811f376
    ('alu', 'neg', 0, 0), # 0x0811f378
    ('alu', 'and', 0, 1), # 0x0811f37a
    ('mem', False, 'byte', 0, 2, 0), # 0x0811f37c
    ('call', 134480688), # 0x0811f37e
    ('literal', 0, 135394212), # 0x0811f382
    ('call', 134219076), # 0x0811f384
    ('spadd', 4), # 0x0811f388
    ('pop', 56, False), # 0x0811f38a
    ('movhi', 8, 3), # 0x0811f38c
    ('movhi', 9, 4), # 0x0811f38e
    ('movhi', 10, 5), # 0x0811f390
    ('pop', 240, False), # 0x0811f392
    ('pop', 1, False), # 0x0811f394
    ('bx', 0), # 0x0811f396
])

put('setup_selector', 0x0811f404, [
    ('push', 16, True), # 0x0811f404
    ('spadd', -4), # 0x0811f406
    ('literal', 0, 135394340), # 0x0811f408
    ('imm', 'mov', 1, 135), # 0x0811f40a
    ('shift', 'lsl', 1, 1, 3), # 0x0811f40c
    ('add', 0, 0, 1), # 0x0811f40e
    ('mem', True, 'byte', 0, 0, 0), # 0x0811f410
    ('imm', 'cmp', 0, 22), # 0x0811f412
    ('branch', 9, 135394328), # 0x0811f414
    ('jump', 135394844), # 0x0811f416
    ('shift', 'lsl', 0, 0, 2), # 0x0811f418
    ('literal', 1, 135394344), # 0x0811f41a
    ('add', 0, 0, 1), # 0x0811f41c
    ('mem', True, 'word', 0, 0, 0), # 0x0811f41e
    ('movhi', 15, 0), # 0x0811f420
])

put('setup_0_2', 0x0811f488, [
    ('call', 135006520), # 0x0811f488
    ('call', 135006540), # 0x0811f48c
    ('call', 135231464), # 0x0811f490
    ('jump', 135394820), # 0x0811f494
    ('call', 134773320), # 0x0811f496
    ('jump', 135394820), # 0x0811f49a
    ('call', 134675660), # 0x0811f49c
    ('literal', 2, 135394476), # 0x0811f4a0
    ('mem', True, 'byte', 0, 2, 8), # 0x0811f4a2
    ('imm', 'mov', 1, 128), # 0x0811f4a4
    ('alu', 'orr', 0, 1), # 0x0811f4a6
    ('jump', 135394818), # 0x0811f4a8
])

put('setup_3_7', 0x0811f4b0, [
    ('call', 134243980), # 0x0811f4b0
    ('jump', 135394820), # 0x0811f4b4
    ('call', 134251628), # 0x0811f4b6
    ('jump', 135394820), # 0x0811f4ba
    ('call', 135006424), # 0x0811f4bc
    ('shift', 'lsl', 0, 0, 24), # 0x0811f4c0
    ('imm', 'cmp', 0, 0), # 0x0811f4c2
    ('branch', 0, 135394504), # 0x0811f4c4
    ('jump', 135394820), # 0x0811f4c6
    ('call', 134703956), # 0x0811f4c8
    ('jump', 135394820), # 0x0811f4cc
    ('call', 135401684), # 0x0811f4ce
    ('jump', 135394820), # 0x0811f4d2
    ('call', 135395028), # 0x0811f4d4
    ('shift', 'lsl', 0, 0, 24), # 0x0811f4d8
    ('imm', 'cmp', 0, 0), # 0x0811f4da
    ('branch', 1, 135394534), # 0x0811f4dc
    ('call', 135394880), # 0x0811f4de
    ('imm', 'mov', 0, 1), # 0x0811f4e2
    ('jump', 135394870), # 0x0811f4e4
    ('literal', 0, 135394552), # 0x0811f4e6
    ('mem', True, 'word', 0, 0, 0), # 0x0811f4e8
    ('imm', 'mov', 1, 134), # 0x0811f4ea
    ('shift', 'lsl', 1, 1, 2), # 0x0811f4ec
    ('add', 0, 0, 1), # 0x0811f4ee
    ('imm', 'mov', 1, 0), # 0x0811f4f0
    ('mem', False, 'half', 1, 0, 0), # 0x0811f4f2
    ('jump', 135394820), # 0x0811f4f4
])

put('setup_8_9', 0x0811f4fc, [
    ('call', 135395148), # 0x0811f4fc
    ('shift', 'lsl', 0, 0, 24), # 0x0811f500
    ('imm', 'cmp', 0, 0), # 0x0811f502
    ('branch', 1, 135394568), # 0x0811f504
    ('jump', 135394868), # 0x0811f506
    ('jump', 135394820), # 0x0811f508
    ('literal', 0, 135394584), # 0x0811f50a
    ('mem', True, 'byte', 0, 0, 8), # 0x0811f50c
    ('shift', 'lsl', 0, 0, 26), # 0x0811f50e
    ('shift', 'lsr', 0, 0, 30), # 0x0811f510
    ('call', 135403600), # 0x0811f512
    ('jump', 135394820), # 0x0811f516
])

put('setup_10', 0x0811f51c, [
    ('literal', 0, 135394616), # 0x0811f51c
    ('mem', True, 'byte', 0, 0, 8), # 0x0811f51e
    ('shift', 'lsl', 0, 0, 26), # 0x0811f520
    ('shift', 'lsr', 0, 0, 30), # 0x0811f522
    ('call', 135395524), # 0x0811f524
    ('literal', 0, 135394620), # 0x0811f528
    ('mem', True, 'word', 0, 0, 0), # 0x0811f52a
    ('imm', 'mov', 1, 134), # 0x0811f52c
    ('shift', 'lsl', 1, 1, 2), # 0x0811f52e
    ('add', 0, 0, 1), # 0x0811f530
    ('imm', 'mov', 1, 0), # 0x0811f532
    ('mem', False, 'half', 1, 0, 0), # 0x0811f534
    ('jump', 135394820), # 0x0811f536
])

put('setup_11_15', 0x0811f540, [
    ('call', 135408940), # 0x0811f540
    ('jump', 135394820), # 0x0811f544
    ('call', 135409724), # 0x0811f546
    ('jump', 135394820), # 0x0811f54a
    ('call', 135410012), # 0x0811f54c
    ('jump', 135394820), # 0x0811f550
    ('call', 134834856), # 0x0811f552
    ('jump', 135394820), # 0x0811f556
    ('call', 135397168), # 0x0811f558
    ('shift', 'lsl', 0, 0, 24), # 0x0811f55c
    ('imm', 'cmp', 0, 0), # 0x0811f55e
    ('branch', 0, 135394868), # 0x0811f560
    ('literal', 0, 135394676), # 0x0811f562
    ('mem', True, 'word', 0, 0, 0), # 0x0811f564
    ('imm', 'mov', 1, 134), # 0x0811f566
    ('shift', 'lsl', 1, 1, 2), # 0x0811f568
    ('add', 0, 0, 1), # 0x0811f56a
    ('imm', 'mov', 1, 0), # 0x0811f56c
    ('mem', False, 'half', 1, 0, 0), # 0x0811f56e
    ('jump', 135394820), # 0x0811f570
])

put('setup_16', 0x0811f578, [
    ('call', 135396828), # 0x0811f578
    ('shift', 'lsl', 0, 0, 24), # 0x0811f57c
    ('imm', 'cmp', 0, 0), # 0x0811f57e
    ('branch', 0, 135394868), # 0x0811f580
    ('literal', 0, 135394708), # 0x0811f582
    ('mem', True, 'word', 0, 0, 0), # 0x0811f584
    ('imm', 'mov', 1, 134), # 0x0811f586
    ('shift', 'lsl', 1, 1, 2), # 0x0811f588
    ('add', 0, 0, 1), # 0x0811f58a
    ('imm', 'mov', 1, 0), # 0x0811f58c
    ('mem', False, 'half', 1, 0, 0), # 0x0811f58e
    ('jump', 135394820), # 0x0811f590
])

put('setup_17_18', 0x0811f598, [
    ('call', 135397220), # 0x0811f598
    ('jump', 135394820), # 0x0811f59c
    ('literal', 0, 135394736), # 0x0811f59e
    ('mem', True, 'word', 0, 0, 0), # 0x0811f5a0
    ('mem', True, 'byte', 0, 0, 8), # 0x0811f5a2
    ('shift', 'lsl', 0, 0, 31), # 0x0811f5a4
    ('shift', 'lsr', 0, 0, 31), # 0x0811f5a6
    ('call', 135403752), # 0x0811f5a8
    ('jump', 135394820), # 0x0811f5ac
])

put('setup_19_20', 0x0811f5b4, [
    ('imm', 'mov', 0, 5), # 0x0811f5b4
    ('call', 135444980), # 0x0811f5b6
    ('jump', 135394820), # 0x0811f5ba
    ('literal', 4, 135394772), # 0x0811f5bc
    ('mem', True, 'word', 0, 4, 0), # 0x0811f5be
    ('mem', True, 'word', 0, 0, 0), # 0x0811f5c0
    ('imm', 'mov', 1, 0), # 0x0811f5c2
    ('call', 134704052), # 0x0811f5c4
    ('mem', True, 'word', 0, 4, 0), # 0x0811f5c8
    ('mem', True, 'half', 0, 0, 10), # 0x0811f5ca
    ('shift', 'lsr', 0, 0, 2), # 0x0811f5cc
    ('call', 135406808), # 0x0811f5ce
    ('jump', 135394820), # 0x0811f5d2
])

put('setup_21_22_increment', 0x0811f5d8, [
    ('imm', 'mov', 0, 1), # 0x0811f5d8
    ('alu', 'neg', 0, 0), # 0x0811f5da
    ('imm', 'mov', 1, 16), # 0x0811f5dc
    ('imm', 'mov', 2, 0), # 0x0811f5de
    ('call', 134679672), # 0x0811f5e0
    ('jump', 135394820), # 0x0811f5e4
    ('imm', 'mov', 0, 1), # 0x0811f5e6
    ('alu', 'neg', 0, 0), # 0x0811f5e8
    ('imm', 'mov', 1, 2), # 0x0811f5ea
    ('alu', 'neg', 1, 1), # 0x0811f5ec
    ('imm', 'mov', 2, 0), # 0x0811f5ee
    ('spmem', False, 2, 0), # 0x0811f5f0
    ('imm', 'mov', 2, 16), # 0x0811f5f2
    ('imm', 'mov', 3, 0), # 0x0811f5f4
    ('call', 134675756), # 0x0811f5f6
    ('literal', 2, 135394836), # 0x0811f5fa
    ('mem', True, 'byte', 1, 2, 8), # 0x0811f5fc
    ('imm', 'mov', 0, 127), # 0x0811f5fe
    ('alu', 'and', 0, 1), # 0x0811f600
    ('mem', False, 'byte', 0, 2, 8), # 0x0811f602
    ('literal', 1, 135394840), # 0x0811f604
    ('imm', 'mov', 0, 135), # 0x0811f606
    ('shift', 'lsl', 0, 0, 3), # 0x0811f608
    ('add', 1, 1, 0), # 0x0811f60a
    ('mem', True, 'byte', 0, 1, 0), # 0x0811f60c
    ('imm', 'add', 0, 1), # 0x0811f60e
    ('mem', False, 'byte', 0, 1, 0), # 0x0811f610
    ('jump', 135394868), # 0x0811f612
])

put('setup_default', 0x0811f61c, [
    ('literal', 0, 135394860), # 0x0811f61c
    ('call', 134219508), # 0x0811f61e
    ('literal', 0, 135394864), # 0x0811f622
    ('call', 134219076), # 0x0811f624
    ('imm', 'mov', 0, 1), # 0x0811f628
    ('jump', 135394870), # 0x0811f62a
])

put('setup_return', 0x0811f634, [
    ('imm', 'mov', 0, 0), # 0x0811f634
    ('spadd', 4), # 0x0811f636
    ('pop', 16, False), # 0x0811f638
    ('pop', 2, False), # 0x0811f63a
    ('bx', 1), # 0x0811f63c
])

put('init_callback', 0x0811f3d8, [
    ('push', 0, True), # 0x0811f3d8
    ('call', 135006488), # 0x0811f3da
    ('shift', 'lsl', 0, 0, 24), # 0x0811f3de
    ('shift', 'lsr', 0, 0, 24), # 0x0811f3e0
    ('imm', 'cmp', 0, 1), # 0x0811f3e2
    ('branch', 0, 135394302), # 0x0811f3e4
    ('call', 135394308), # 0x0811f3e6
    ('shift', 'lsl', 0, 0, 24), # 0x0811f3ea
    ('shift', 'lsr', 0, 0, 24), # 0x0811f3ec
    ('imm', 'cmp', 0, 1), # 0x0811f3ee
    ('branch', 0, 135394302), # 0x0811f3f0
    ('call', 135006424), # 0x0811f3f2
    ('shift', 'lsl', 0, 0, 24), # 0x0811f3f6
    ('shift', 'lsr', 0, 0, 24), # 0x0811f3f8
    ('imm', 'cmp', 0, 1), # 0x0811f3fa
    ('branch', 1, 135394266), # 0x0811f3fc
    ('pop', 1, False), # 0x0811f3fe
    ('bx', 0), # 0x0811f400
])

put('scheduler', 0x0811f3a8, [
    ('push', 0, True), # 0x0811f3a8
    ('call', 134704400), # 0x0811f3aa
    ('call', 134244056), # 0x0811f3ae
    ('call', 134244132), # 0x0811f3b2
    ('call', 135231504), # 0x0811f3b6
    ('call', 134675572), # 0x0811f3ba
    ('pop', 1, False), # 0x0811f3be
    ('bx', 0), # 0x0811f3c0
])

put('vblank', 0x0811f3c4, [
    ('push', 0, True), # 0x0811f3c4
    ('call', 134246044), # 0x0811f3c6
    ('call', 134246796), # 0x0811f3ca
    ('call', 134675480), # 0x0811f3ce
    ('pop', 1, False), # 0x0811f3d2
    ('bx', 0), # 0x0811f3d4
])

put('abort_setup', 0x0811f640, [
    ('push', 0, True), # 0x0811f640
    ('spadd', -4), # 0x0811f642
    ('imm', 'mov', 0, 1), # 0x0811f644
    ('alu', 'neg', 0, 0), # 0x0811f646
    ('imm', 'mov', 1, 2), # 0x0811f648
    ('alu', 'neg', 1, 1), # 0x0811f64a
    ('imm', 'mov', 2, 0), # 0x0811f64c
    ('spmem', False, 2, 0), # 0x0811f64e
    ('imm', 'mov', 3, 16), # 0x0811f650
    ('call', 134675756), # 0x0811f652
    ('literal', 0, 135394928), # 0x0811f656
    ('imm', 'mov', 1, 0), # 0x0811f658
    ('call', 134704052), # 0x0811f65a
    ('literal', 0, 135394932), # 0x0811f65e
    ('call', 134219508), # 0x0811f660
    ('literal', 0, 135394936), # 0x0811f664
    ('call', 134219076), # 0x0811f666
    ('spadd', 4), # 0x0811f66a
    ('pop', 1, False), # 0x0811f66c
    ('bx', 0), # 0x0811f66e
])

put('abort_task', 0x0811f67c, [
    ('push', 16, True), # 0x0811f67c
    ('shift', 'lsl', 0, 0, 24), # 0x0811f67e
    ('shift', 'lsr', 4, 0, 24), # 0x0811f680
    ('literal', 0, 135394984), # 0x0811f682
    ('mem', True, 'byte', 1, 0, 7), # 0x0811f684
    ('imm', 'mov', 0, 128), # 0x0811f686
    ('alu', 'and', 0, 1), # 0x0811f688
    ('imm', 'cmp', 0, 0), # 0x0811f68a
    ('branch', 1, 135394976), # 0x0811f68c
    ('literal', 0, 135394988), # 0x0811f68e
    ('mem', True, 'word', 0, 0, 0), # 0x0811f690
    ('call', 134219076), # 0x0811f692
    ('call', 135395448), # 0x0811f696
    ('addi', 0, 4, 0), # 0x0811f69a
    ('call', 134704288), # 0x0811f69c
    ('pop', 16, False), # 0x0811f6a0
    ('pop', 1, False), # 0x0811f6a2
    ('bx', 0), # 0x0811f6a4
])

put('reset_pointers', 0x0811f6b0, [
    ('literal', 0, 135395012), # 0x0811f6b0
    ('imm', 'mov', 1, 0), # 0x0811f6b2
    ('mem', False, 'word', 1, 0, 0), # 0x0811f6b4
    ('literal', 0, 135395016), # 0x0811f6b6
    ('mem', False, 'word', 1, 0, 0), # 0x0811f6b8
    ('literal', 0, 135395020), # 0x0811f6ba
    ('mem', False, 'word', 1, 0, 0), # 0x0811f6bc
    ('literal', 0, 135395024), # 0x0811f6be
    ('mem', False, 'word', 1, 0, 0), # 0x0811f6c0
    ('bx', 14), # 0x0811f6c2
])

put('free_pointers', 0x0811f878, [
    ('push', 0, True), # 0x0811f878
    ('literal', 0, 135395508), # 0x0811f87a
    ('mem', True, 'word', 0, 0, 0), # 0x0811f87c
    ('imm', 'cmp', 0, 0), # 0x0811f87e
    ('branch', 0, 135395462), # 0x0811f880
    ('call', 134228932), # 0x0811f882
    ('literal', 0, 135395512), # 0x0811f886
    ('mem', True, 'word', 0, 0, 0), # 0x0811f888
    ('imm', 'cmp', 0, 0), # 0x0811f88a
    ('branch', 0, 135395474), # 0x0811f88c
    ('call', 134228932), # 0x0811f88e
    ('literal', 0, 135395516), # 0x0811f892
    ('mem', True, 'word', 0, 0, 0), # 0x0811f894
    ('imm', 'cmp', 0, 0), # 0x0811f896
    ('branch', 0, 135395486), # 0x0811f898
    ('call', 134228932), # 0x0811f89a
    ('literal', 0, 135395520), # 0x0811f89e
    ('mem', True, 'word', 0, 0, 0), # 0x0811f8a0
    ('imm', 'cmp', 0, 0), # 0x0811f8a2
    ('branch', 0, 135395498), # 0x0811f8a4
    ('call', 134228932), # 0x0811f8a6
    ('call', 134233752), # 0x0811f8aa
    ('pop', 1, False), # 0x0811f8ae
    ('bx', 0), # 0x0811f8b0
])

put('set_main_callback', 0x08000544, [
    ('literal', 1, 134219092), # 0x08000544
    ('mem', False, 'word', 0, 1, 4), # 0x08000546
    ('imm', 'mov', 0, 135), # 0x08000548
    ('shift', 'lsl', 0, 0, 3), # 0x0800054a
    ('add', 1, 1, 0), # 0x0800054c
    ('imm', 'mov', 0, 0), # 0x0800054e
    ('mem', False, 'byte', 0, 1, 0), # 0x08000550
    ('bx', 14), # 0x08000552
])

put('set_vblank', 0x080006f4, [
    ('literal', 1, 134219516), # 0x080006f4
    ('mem', False, 'word', 0, 1, 12), # 0x080006f6
    ('bx', 14), # 0x080006f8
])

put('set_hblank', 0x08000700, [
    ('literal', 1, 134219528), # 0x08000700
    ('mem', False, 'word', 0, 1, 16), # 0x08000702
    ('bx', 14), # 0x08000704
])

put('null_callbacks', 0x080c0938, [
    ('push', 0, True), # 0x080c0938
    ('imm', 'mov', 0, 0), # 0x080c093a
    ('call', 134219508), # 0x080c093c
    ('imm', 'mov', 0, 0), # 0x080c0940
    ('call', 134219520), # 0x080c0942
    ('pop', 1, False), # 0x080c0946
    ('bx', 0), # 0x080c0948
])

put('clear_bg_schedule', 0x080f77e8, [
    ('push', 0, True), # 0x080f77e8
    ('literal', 0, 135231480), # 0x080f77ea
    ('imm', 'mov', 1, 0), # 0x080f77ec
    ('imm', 'mov', 2, 4), # 0x080f77ee
    ('call', 136093176), # 0x080f77f0
    ('pop', 1, False), # 0x080f77f4
    ('bx', 0), # 0x080f77f6
])

put('memset', 0x081c9df8, [
    ('push', 48, True), # 0x081c9df8
    ('addi', 5, 0, 0), # 0x081c9dfa
    ('addi', 4, 1, 0), # 0x081c9dfc
    ('addi', 3, 5, 0), # 0x081c9dfe
    ('imm', 'cmp', 2, 3), # 0x081c9e00
    ('branch', 9, 136093246), # 0x081c9e02
    ('imm', 'mov', 0, 3), # 0x081c9e04
    ('alu', 'and', 0, 5), # 0x081c9e06
    ('imm', 'cmp', 0, 0), # 0x081c9e08
    ('branch', 1, 136093246), # 0x081c9e0a
    ('addi', 1, 5, 0), # 0x081c9e0c
    ('imm', 'mov', 0, 255), # 0x081c9e0e
    ('alu', 'and', 4, 0), # 0x081c9e10
    ('shift', 'lsl', 3, 4, 8), # 0x081c9e12
    ('alu', 'orr', 3, 4), # 0x081c9e14
    ('shift', 'lsl', 0, 3, 16), # 0x081c9e16
    ('alu', 'orr', 3, 0), # 0x081c9e18
    ('imm', 'cmp', 2, 15), # 0x081c9e1a
    ('branch', 9, 136093234), # 0x081c9e1c
    ('multiple', False, 1, 8), # 0x081c9e1e
    ('multiple', False, 1, 8), # 0x081c9e20
    ('multiple', False, 1, 8), # 0x081c9e22
    ('multiple', False, 1, 8), # 0x081c9e24
    ('imm', 'sub', 2, 16), # 0x081c9e26
    ('imm', 'cmp', 2, 15), # 0x081c9e28
    ('branch', 8, 136093214), # 0x081c9e2a
    ('jump', 136093234), # 0x081c9e2c
    ('multiple', False, 1, 8), # 0x081c9e2e
    ('imm', 'sub', 2, 4), # 0x081c9e30
    ('imm', 'cmp', 2, 3), # 0x081c9e32
    ('branch', 8, 136093230), # 0x081c9e34
    ('addi', 3, 1, 0), # 0x081c9e36
    ('jump', 136093246), # 0x081c9e38
    ('mem', False, 'byte', 4, 3, 0), # 0x081c9e3a
    ('imm', 'add', 3, 1), # 0x081c9e3c
    ('addi', 0, 2, 0), # 0x081c9e3e
    ('imm', 'sub', 2, 1), # 0x081c9e40
    ('imm', 'cmp', 0, 0), # 0x081c9e42
    ('branch', 1, 136093242), # 0x081c9e44
    ('addi', 0, 5, 0), # 0x081c9e46
    ('pop', 48, True), # 0x081c9e48
])

put('reset_tasks', 0x08076b54, [
    ('push', 240, True), # 0x08076b54
    ('imm', 'mov', 4, 0), # 0x08076b56
    ('literal', 6, 134704040), # 0x08076b58
    ('addi', 7, 6, 0), # 0x08076b5a
    ('imm', 'add', 7, 8), # 0x08076b5c
    ('shift', 'lsl', 0, 4, 2), # 0x08076b5e
    ('add', 0, 0, 4), # 0x08076b60
    ('shift', 'lsl', 0, 0, 3), # 0x08076b62
    ('add', 2, 0, 6), # 0x08076b64
    ('imm', 'mov', 1, 0), # 0x08076b66
    ('mem', False, 'byte', 1, 2, 4), # 0x08076b68
    ('literal', 1, 134704044), # 0x08076b6a
    ('mem', False, 'word', 1, 2, 0), # 0x08076b6c
    ('mem', False, 'byte', 4, 2, 5), # 0x08076b6e
    ('imm', 'add', 4, 1), # 0x08076b70
    ('mem', False, 'byte', 4, 2, 6), # 0x08076b72
    ('imm', 'mov', 1, 1), # 0x08076b74
    ('alu', 'neg', 1, 1), # 0x08076b76
    ('addi', 5, 1, 0), # 0x08076b78
    ('imm', 'mov', 1, 255), # 0x08076b7a
    ('mem', False, 'byte', 1, 2, 7), # 0x08076b7c
    ('add', 0, 0, 7), # 0x08076b7e
    ('imm', 'mov', 1, 0), # 0x08076b80
    ('imm', 'mov', 2, 32), # 0x08076b82
    ('call', 136093176), # 0x08076b84
    ('shift', 'lsl', 4, 4, 24), # 0x08076b88
    ('shift', 'lsr', 4, 4, 24), # 0x08076b8a
    ('imm', 'cmp', 4, 15), # 0x08076b8c
    ('branch', 9, 134703966), # 0x08076b8e
    ('literal', 0, 134704040), # 0x08076b90
    ('imm', 'mov', 1, 254), # 0x08076b92
    ('mem', False, 'byte', 1, 0, 5), # 0x08076b94
    ('literal', 1, 134704048), # 0x08076b96
    ('add', 0, 0, 1), # 0x08076b98
    ('mem', True, 'byte', 1, 0, 0), # 0x08076b9a
    ('alu', 'orr', 1, 5), # 0x08076b9c
    ('mem', False, 'byte', 1, 0, 0), # 0x08076b9e
    ('pop', 240, False), # 0x08076ba0
    ('pop', 1, False), # 0x08076ba2
    ('bx', 0), # 0x08076ba4
])

put('create_task_1', 0x08076bb4, [
    ('push', 240, True), # 0x08076bb4
    ('addi', 2, 0, 0), # 0x08076bb6
    ('shift', 'lsl', 1, 1, 24), # 0x08076bb8
    ('shift', 'lsr', 1, 1, 24), # 0x08076bba
    ('imm', 'mov', 6, 0), # 0x08076bbc
    ('literal', 7, 134704112), # 0x08076bbe
    ('shift', 'lsl', 0, 6, 2), # 0x08076bc0
    ('add', 0, 0, 6), # 0x08076bc2
    ('shift', 'lsl', 5, 0, 3), # 0x08076bc4
    ('add', 4, 5, 7), # 0x08076bc6
    ('mem', True, 'byte', 0, 4, 4), # 0x08076bc8
    ('imm', 'cmp', 0, 0), # 0x08076bca
    ('branch', 1, 134704116), # 0x08076bcc
    ('mem', False, 'word', 2, 4, 0), # 0x08076bce
    ('mem', False, 'byte', 1, 4, 7), # 0x08076bd0
    ('addi', 0, 6, 0), # 0x08076bd2
    ('call', 134704136), # 0x08076bd4
    ('addi', 0, 7, 0), # 0x08076bd8
    ('imm', 'add', 0, 8), # 0x08076bda
    ('add', 0, 5, 0), # 0x08076bdc
    ('imm', 'mov', 1, 0), # 0x08076bde
    ('imm', 'mov', 2, 32), # 0x08076be0
    ('call', 136093176), # 0x08076be2
    ('imm', 'mov', 0, 1), # 0x08076be6
    ('mem', False, 'byte', 0, 4, 4), # 0x08076be8
    ('addi', 0, 6, 0), # 0x08076bea
    ('jump', 134704128), # 0x08076bec
])

put('create_task_2', 0x08076bf4, [
    ('addi', 0, 6, 1), # 0x08076bf4
    ('shift', 'lsl', 0, 0, 24), # 0x08076bf6
    ('shift', 'lsr', 6, 0, 24), # 0x08076bf8
    ('imm', 'cmp', 6, 15), # 0x08076bfa
    ('branch', 9, 134704064), # 0x08076bfc
    ('imm', 'mov', 0, 0), # 0x08076bfe
    ('pop', 240, False), # 0x08076c00
    ('pop', 2, False), # 0x08076c02
    ('bx', 1), # 0x08076c04
])

put('insert_task_1', 0x08076c08, [
    ('push', 240, True), # 0x08076c08
    ('movhi', 7, 8), # 0x08076c0a
    ('push', 128, False), # 0x08076c0c
    ('shift', 'lsl', 0, 0, 24), # 0x08076c0e
    ('shift', 'lsr', 4, 0, 24), # 0x08076c10
    ('call', 134704448), # 0x08076c12
    ('shift', 'lsl', 0, 0, 24), # 0x08076c16
    ('shift', 'lsr', 1, 0, 24), # 0x08076c18
    ('imm', 'cmp', 1, 16), # 0x08076c1a
    ('branch', 1, 134704184), # 0x08076c1c
    ('literal', 1, 134704180), # 0x08076c1e
    ('shift', 'lsl', 0, 4, 2), # 0x08076c20
    ('add', 0, 0, 4), # 0x08076c22
    ('shift', 'lsl', 0, 0, 3), # 0x08076c24
    ('add', 0, 0, 1), # 0x08076c26
    ('imm', 'mov', 1, 254), # 0x08076c28
    ('mem', False, 'byte', 1, 0, 5), # 0x08076c2a
    ('imm', 'mov', 1, 255), # 0x08076c2c
    ('mem', False, 'byte', 1, 0, 6), # 0x08076c2e
    ('jump', 134704276), # 0x08076c30
])

put('insert_task_2', 0x08076c38, [
    ('literal', 6, 134704244), # 0x08076c38
    ('shift', 'lsl', 0, 4, 2), # 0x08076c3a
    ('movhi', 12, 0), # 0x08076c3c
    ('movhi', 8, 6), # 0x08076c3e
    ('add', 0, 0, 4), # 0x08076c40
    ('shift', 'lsl', 0, 0, 3), # 0x08076c42
    ('add', 2, 0, 6), # 0x08076c44
    ('shift', 'lsl', 0, 1, 2), # 0x08076c46
    ('add', 0, 0, 1), # 0x08076c48
    ('shift', 'lsl', 5, 0, 3), # 0x08076c4a
    ('movhi', 7, 8), # 0x08076c4c
    ('add', 3, 5, 7), # 0x08076c4e
    ('mem', True, 'byte', 0, 2, 7), # 0x08076c50
    ('mem', True, 'byte', 7, 3, 7), # 0x08076c52
    ('compare', 0, 7), # 0x08076c54
    ('branch', 2, 134704248), # 0x08076c56
    ('mem', True, 'byte', 0, 3, 5), # 0x08076c58
    ('mem', False, 'byte', 0, 2, 5), # 0x08076c5a
    ('mem', False, 'byte', 1, 2, 6), # 0x08076c5c
    ('mem', True, 'byte', 0, 3, 5), # 0x08076c5e
    ('imm', 'cmp', 0, 254), # 0x08076c60
    ('branch', 0, 134704240), # 0x08076c62
    ('addi', 1, 0, 0), # 0x08076c64
    ('shift', 'lsl', 0, 1, 2), # 0x08076c66
    ('add', 0, 0, 1), # 0x08076c68
    ('shift', 'lsl', 0, 0, 3), # 0x08076c6a
    ('addhi', 0, 8), # 0x08076c6c
    ('mem', False, 'byte', 4, 0, 6), # 0x08076c6e
    ('mem', False, 'byte', 4, 3, 5), # 0x08076c70
    ('jump', 134704276), # 0x08076c72
])

put('insert_task_3', 0x08076c78, [
    ('mem', True, 'byte', 0, 3, 6), # 0x08076c78
    ('imm', 'cmp', 0, 255), # 0x08076c7a
    ('branch', 0, 134704258), # 0x08076c7c
    ('addi', 1, 0, 0), # 0x08076c7e
    ('jump', 134704198), # 0x08076c80
    ('movhi', 2, 12), # 0x08076c82
    ('add', 0, 2, 4), # 0x08076c84
    ('shift', 'lsl', 0, 0, 3), # 0x08076c86
    ('add', 0, 0, 6), # 0x08076c88
    ('mem', False, 'byte', 1, 0, 5), # 0x08076c8a
    ('add', 2, 5, 6), # 0x08076c8c
    ('mem', True, 'byte', 1, 2, 6), # 0x08076c8e
    ('mem', False, 'byte', 1, 0, 6), # 0x08076c90
    ('mem', False, 'byte', 4, 2, 6), # 0x08076c92
    ('pop', 8, False), # 0x08076c94
    ('movhi', 8, 3), # 0x08076c96
    ('pop', 240, False), # 0x08076c98
    ('pop', 1, False), # 0x08076c9a
    ('bx', 0), # 0x08076c9c
])

put('find_first_task', 0x08076d40, [
    ('push', 0, True), # 0x08076d40
    ('imm', 'mov', 2, 0), # 0x08076d42
    ('literal', 0, 134704504), # 0x08076d44
    ('mem', True, 'byte', 1, 0, 4), # 0x08076d46
    ('addi', 3, 0, 0), # 0x08076d48
    ('imm', 'cmp', 1, 1), # 0x08076d4a
    ('branch', 1, 134704468), # 0x08076d4c
    ('mem', True, 'byte', 0, 3, 5), # 0x08076d4e
    ('imm', 'cmp', 0, 254), # 0x08076d50
    ('branch', 0, 134704498), # 0x08076d52
    ('addi', 0, 2, 1), # 0x08076d54
    ('shift', 'lsl', 0, 0, 24), # 0x08076d56
    ('shift', 'lsr', 2, 0, 24), # 0x08076d58
    ('imm', 'cmp', 2, 15), # 0x08076d5a
    ('branch', 8, 134704498), # 0x08076d5c
    ('shift', 'lsl', 0, 2, 2), # 0x08076d5e
    ('add', 0, 0, 2), # 0x08076d60
    ('shift', 'lsl', 0, 0, 3), # 0x08076d62
    ('add', 1, 0, 3), # 0x08076d64
    ('mem', True, 'byte', 0, 1, 4), # 0x08076d66
    ('imm', 'cmp', 0, 1), # 0x08076d68
    ('branch', 1, 134704468), # 0x08076d6a
    ('mem', True, 'byte', 0, 1, 5), # 0x08076d6c
    ('imm', 'cmp', 0, 254), # 0x08076d6e
    ('branch', 1, 134704468), # 0x08076d70
    ('addi', 0, 2, 0), # 0x08076d72
    ('pop', 2, False), # 0x08076d74
    ('bx', 1), # 0x08076d76
])

put('party_count_prefix', 0x08040330, [
    ('push', 16, True), # 0x08040330
    ('literal', 0, 134480700), # 0x08040332
    ('imm', 'mov', 1, 0), # 0x08040334
    ('mem', False, 'byte', 1, 0, 0), # 0x08040336
    ('jump', 134480712), # 0x08040338
])

put('party_count_loop', 0x08040340, [
    ('mem', True, 'byte', 0, 4, 0), # 0x08040340
    ('imm', 'add', 0, 1), # 0x08040342
    ('mem', False, 'byte', 0, 4, 0), # 0x08040344
    ('addi', 0, 4, 0), # 0x08040346
    ('addi', 4, 0, 0), # 0x08040348
    ('mem', True, 'byte', 0, 4, 0), # 0x0804034a
    ('imm', 'cmp', 0, 5), # 0x0804034c
    ('branch', 8, 134480742), # 0x0804034e
    ('addi', 1, 0, 0), # 0x08040350
    ('imm', 'mov', 0, 100), # 0x08040352
    ('alu', 'mul', 0, 1), # 0x08040354
    ('literal', 1, 134480752), # 0x08040356
    ('add', 0, 0, 1), # 0x08040358
    ('imm', 'mov', 1, 11), # 0x0804035a
    ('imm', 'mov', 2, 0), # 0x0804035c
    ('call', 134476628), # 0x0804035e
    ('imm', 'cmp', 0, 0), # 0x08040362
    ('branch', 1, 134480704), # 0x08040364
    ('mem', True, 'byte', 0, 4, 0), # 0x08040366
    ('pop', 16, False), # 0x08040368
    ('pop', 2, False), # 0x0804036a
    ('bx', 1), # 0x0804036c
])

put('getmon_species_gate', 0x0803f354, [
    ('push', 16, True), # 0x0803f354
    ('addi', 4, 0, 0), # 0x0803f356
    ('addi', 3, 1, 0), # 0x0803f358
    ('addi', 0, 3, 0), # 0x0803f35a
    ('imm', 'sub', 0, 55), # 0x0803f35c
    ('imm', 'cmp', 0, 33), # 0x0803f35e
    ('branch', 9, 134476644), # 0x0803f360
    ('jump', 134476962), # 0x0803f362
])

put('getbox_species_prefix', 0x0803f4a2, [
    ('addi', 0, 4, 0), # 0x0803f4a2
    ('addi', 1, 3, 0), # 0x0803f4a4
    ('call', 134476976), # 0x0803f4a6
    ('pop', 16, False), # 0x0803f4aa
    ('pop', 2, False), # 0x0803f4ac
    ('bx', 1), # 0x0803f4ae
    ('push', 240, True), # 0x0803f4b0
    ('movhi', 7, 10), # 0x0803f4b2
    ('movhi', 6, 9), # 0x0803f4b4
    ('movhi', 5, 8), # 0x0803f4b6
    ('push', 224, False), # 0x0803f4b8
    ('spadd', -4), # 0x0803f4ba
    ('movhi', 9, 0), # 0x0803f4bc
    ('spmem', False, 1, 0), # 0x0803f4be
    ('addi', 7, 2, 0), # 0x0803f4c0
    ('imm', 'mov', 4, 0), # 0x0803f4c2
    ('movhi', 8, 4), # 0x0803f4c4
    ('movhi', 10, 4), # 0x0803f4c6
    ('imm', 'mov', 6, 0), # 0x0803f4c8
    ('imm', 'mov', 5, 0), # 0x0803f4ca
    ('imm', 'cmp', 1, 10), # 0x0803f4cc
    ('branch', 13, 134477102), # 0x0803f4ce
    ('mem', True, 'word', 1, 0, 0), # 0x0803f4d0
    ('imm', 'mov', 2, 0), # 0x0803f4d2
    ('call', 134475948), # 0x0803f4d4
    ('movhi', 8, 0), # 0x0803f4d8
    ('movhi', 0, 9), # 0x0803f4da
    ('mem', True, 'word', 1, 0, 0), # 0x0803f4dc
    ('imm', 'mov', 2, 1), # 0x0803f4de
    ('call', 134475948), # 0x0803f4e0
    ('movhi', 10, 0), # 0x0803f4e4
    ('movhi', 2, 9), # 0x0803f4e6
    ('mem', True, 'word', 1, 2, 0), # 0x0803f4e8
    ('movhi', 0, 9), # 0x0803f4ea
    ('imm', 'mov', 2, 2), # 0x0803f4ec
    ('call', 134475948), # 0x0803f4ee
    ('addi', 6, 0, 0), # 0x0803f4f2
    ('movhi', 0, 9), # 0x0803f4f4
    ('mem', True, 'word', 1, 0, 0), # 0x0803f4f6
    ('imm', 'mov', 2, 3), # 0x0803f4f8
    ('call', 134475948), # 0x0803f4fa
    ('addi', 5, 0, 0), # 0x0803f4fe
    ('movhi', 8, 8), # 0x0803f500
    ('movhi', 8, 8), # 0x0803f502
    ('movhi', 8, 8), # 0x0803f504
    ('movhi', 8, 8), # 0x0803f506
    ('movhi', 8, 8), # 0x0803f508
    ('movhi', 8, 8), # 0x0803f50a
    ('movhi', 8, 8), # 0x0803f50c
    ('movhi', 8, 8), # 0x0803f50e
    ('movhi', 8, 8), # 0x0803f510
    ('movhi', 8, 8), # 0x0803f512
    ('jump', 134477102), # 0x0803f514
])

put('getbox_species_dispatch', 0x0803f52e, [
    ('spmem', True, 0, 0), # 0x0803f52e
    ('imm', 'cmp', 0, 83), # 0x0803f530
    ('branch', 9, 134477110), # 0x0803f532
    ('jump', 134478416), # 0x0803f534
    ('shift', 'lsl', 0, 0, 2), # 0x0803f536
    ('literal', 1, 134477120), # 0x0803f538
    ('add', 0, 0, 1), # 0x0803f53a
    ('mem', True, 'word', 0, 0, 0), # 0x0803f53c
    ('movhi', 15, 0), # 0x0803f53e
])

put('getbox_species_case', 0x0803f720, [
    ('movhi', 2, 9), # 0x0803f720
    ('mem', True, 'byte', 1, 2, 19), # 0x0803f722
    ('imm', 'mov', 0, 1), # 0x0803f724
    ('alu', 'and', 0, 1), # 0x0803f726
    ('imm', 'mov', 4, 206), # 0x0803f728
    ('shift', 'lsl', 4, 4, 1), # 0x0803f72a
    ('imm', 'cmp', 0, 0), # 0x0803f72c
    ('branch', 0, 134477618), # 0x0803f72e
    ('jump', 134478416), # 0x0803f730
    ('movhi', 7, 8), # 0x0803f732
    ('mem', True, 'half', 4, 7, 0), # 0x0803f734
    ('jump', 134478416), # 0x0803f736
])

put('getbox_species_exit', 0x0803fa50, [
    ('spmem', True, 7, 0), # 0x0803fa50
    ('imm', 'cmp', 7, 10), # 0x0803fa52
    ('branch', 13, 134478428), # 0x0803fa54
    ('movhi', 0, 9), # 0x0803fa56
    ('call', 134475876), # 0x0803fa58
    ('addi', 0, 4, 0), # 0x0803fa5c
    ('spadd', 4), # 0x0803fa5e
    ('pop', 56, False), # 0x0803fa60
    ('movhi', 8, 3), # 0x0803fa62
    ('movhi', 9, 4), # 0x0803fa64
    ('movhi', 10, 5), # 0x0803fa66
    ('pop', 240, False), # 0x0803fa68
    ('pop', 2, False), # 0x0803fa6a
    ('bx', 1), # 0x0803fa6c
])

put('getsubstruct_selector', 0x0803f0ac, [
    ('push', 112, True), # 0x0803f0ac
    ('addi', 5, 0, 0), # 0x0803f0ae
    ('addi', 0, 1, 0), # 0x0803f0b0
    ('shift', 'lsl', 2, 2, 24), # 0x0803f0b2
    ('shift', 'lsr', 4, 2, 24), # 0x0803f0b4
    ('imm', 'mov', 6, 0), # 0x0803f0b6
    ('imm', 'mov', 0, 0), # 0x0803f0b8
    ('movhi', 8, 8), # 0x0803f0ba
    ('movhi', 8, 8), # 0x0803f0bc
    ('imm', 'cmp', 0, 23), # 0x0803f0be
    ('branch', 9, 134475972), # 0x0803f0c0
    ('jump', 134476620), # 0x0803f0c2
    ('shift', 'lsl', 0, 0, 2), # 0x0803f0c4
    ('literal', 1, 134475984), # 0x0803f0c6
    ('add', 0, 0, 1), # 0x0803f0c8
    ('mem', True, 'word', 0, 0, 0), # 0x0803f0ca
    ('movhi', 15, 0), # 0x0803f0cc
])

put('getsubstruct_fixed_case', 0x0803f134, [
    ('addi', 0, 5, 0), # 0x0803f134
    ('imm', 'add', 0, 32), # 0x0803f136
    ('imm', 'cmp', 4, 1), # 0x0803f138
    ('branch', 1, 134476094), # 0x0803f13a
    ('jump', 134476612), # 0x0803f13c
    ('imm', 'cmp', 4, 1), # 0x0803f13e
    ('branch', 12, 134476106), # 0x0803f140
    ('imm', 'cmp', 4, 0), # 0x0803f142
    ('branch', 1, 134476104), # 0x0803f144
    ('jump', 134476618), # 0x0803f146
    ('jump', 134476620), # 0x0803f148
    ('imm', 'cmp', 4, 2), # 0x0803f14a
    ('branch', 1, 134476112), # 0x0803f14c
    ('jump', 134476606), # 0x0803f14e
    ('imm', 'cmp', 4, 3), # 0x0803f150
    ('branch', 0, 134476118), # 0x0803f152
    ('jump', 134476620), # 0x0803f154
    ('jump', 134476600), # 0x0803f156
])

put('getsubstruct_tails', 0x0803f338, [
    ('addi', 6, 5, 0), # 0x0803f338
    ('imm', 'add', 6, 68), # 0x0803f33a
    ('jump', 134476620), # 0x0803f33c
    ('addi', 6, 5, 0), # 0x0803f33e
    ('imm', 'add', 6, 56), # 0x0803f340
    ('jump', 134476620), # 0x0803f342
    ('addi', 6, 5, 0), # 0x0803f344
    ('imm', 'add', 6, 44), # 0x0803f346
    ('jump', 134476620), # 0x0803f348
    ('addi', 6, 0, 0), # 0x0803f34a
    ('addi', 0, 6, 0), # 0x0803f34c
    ('pop', 112, False), # 0x0803f34e
    ('pop', 2, False), # 0x0803f350
    ('bx', 1), # 0x0803f352
])

put('getbox_egg_case', 0x0803f7e8, [
    ('mem', True, 'byte', 0, 5, 7), # 0x0803f7e8
    ('jump', 134477894), # 0x0803f7ea
])

put('getbox_egg_bit', 0x0803f846, [
    ('shift', 'lsl', 0, 0, 25), # 0x0803f846
    ('shift', 'lsr', 4, 0, 31), # 0x0803f848
    ('jump', 134478416), # 0x0803f84a
])

put('species_encrypt_effect', 0x0803f064, [
    ('push', 16, True), # 0x0803f064
    ('addi', 3, 0, 0), # 0x0803f066
    ('imm', 'mov', 4, 0), # 0x0803f068
    ('addi', 2, 3, 0), # 0x0803f06a
    ('imm', 'add', 2, 32), # 0x0803f06c
    ('mem', True, 'word', 0, 2, 0), # 0x0803f06e
    ('mem', True, 'word', 1, 3, 0), # 0x0803f070
    ('movhi', 8, 8), # 0x0803f072
    ('mem', False, 'word', 0, 2, 0), # 0x0803f074
    ('mem', True, 'word', 1, 3, 4), # 0x0803f076
    ('movhi', 8, 8), # 0x0803f078
    ('multiple', False, 2, 1), # 0x0803f07a
    ('imm', 'add', 4, 1), # 0x0803f07c
    ('imm', 'cmp', 4, 11), # 0x0803f07e
    ('branch', 9, 134475886), # 0x0803f080
    ('pop', 16, False), # 0x0803f082
    ('pop', 1, False), # 0x0803f084
    ('bx', 0), # 0x0803f086
])

put('free_sprite_palettes', 0x0800846c, [
    ('push', 16, True), # 0x0800846c
    ('literal', 1, 134251672), # 0x0800846e
    ('imm', 'mov', 0, 0), # 0x08008470
    ('mem', False, 'byte', 0, 1, 0), # 0x08008472
    ('imm', 'mov', 2, 0), # 0x08008474
    ('literal', 4, 134251676), # 0x08008476
    ('literal', 0, 134251680), # 0x08008478
    ('addi', 3, 0, 0), # 0x0800847a
    ('shift', 'lsl', 0, 2, 1), # 0x0800847c
    ('add', 0, 0, 4), # 0x0800847e
    ('mem', True, 'half', 1, 0, 0), # 0x08008480
    ('alu', 'orr', 1, 3), # 0x08008482
    ('mem', False, 'half', 1, 0, 0), # 0x08008484
    ('addi', 0, 2, 1), # 0x08008486
    ('shift', 'lsl', 0, 0, 24), # 0x08008488
    ('shift', 'lsr', 2, 0, 24), # 0x0800848a
    ('imm', 'cmp', 2, 15), # 0x0800848c
    ('branch', 9, 134251644), # 0x0800848e
    ('pop', 16, False), # 0x08008490
    ('pop', 1, False), # 0x08008492
    ('bx', 0), # 0x08008494
])

put('set_help_context', 0x0812b9f4, [
    ('push', 0, True), # 0x0812b9f4
    ('shift', 'lsl', 0, 0, 24), # 0x0812b9f6
    ('shift', 'lsr', 1, 0, 24), # 0x0812b9f8
    ('literal', 0, 135445024), # 0x0812b9fa
    ('mem', True, 'half', 2, 0, 0), # 0x0812b9fc
    ('imm', 'cmp', 2, 26), # 0x0812b9fe
    ('branch', 12, 135445018), # 0x0812ba00
    ('imm', 'cmp', 2, 23), # 0x0812ba02
    ('branch', 11, 135445018), # 0x0812ba04
    ('imm', 'cmp', 1, 9), # 0x0812ba06
    ('branch', 0, 135445020), # 0x0812ba08
    ('imm', 'cmp', 1, 5), # 0x0812ba0a
    ('branch', 0, 135445020), # 0x0812ba0c
    ('imm', 'cmp', 1, 6), # 0x0812ba0e
    ('branch', 0, 135445020), # 0x0812ba10
    ('imm', 'cmp', 1, 7), # 0x0812ba12
    ('branch', 0, 135445020), # 0x0812ba14
    ('imm', 'cmp', 1, 8), # 0x0812ba16
    ('branch', 0, 135445020), # 0x0812ba18
    ('mem', False, 'half', 1, 0, 0), # 0x0812ba1a
    ('pop', 1, False), # 0x0812ba1c
    ('bx', 0), # 0x0812ba1e
])

put('minigame_selector', 0x081210d4, [
    ('push', 48, True), # 0x081210d4
    ('literal', 2, 135401764), # 0x081210d6
    ('mem', True, 'byte', 1, 2, 8), # 0x081210d8
    ('imm', 'mov', 0, 15), # 0x081210da
    ('alu', 'and', 0, 1), # 0x081210dc
    ('imm', 'cmp', 0, 11), # 0x081210de
    ('branch', 1, 135401822), # 0x081210e0
])

put('minigame_ordinary_return', 0x0812115e, [
    ('pop', 48, False), # 0x0812115e
    ('pop', 1, False), # 0x08121160
    ('bx', 0), # 0x08121162
])

LITERALS = {
    0x08000554: 0x03003130,
    0x080006fc: 0x03003130,
    0x08000708: 0x03003130,
    0x08008498: 0x03003e98,
    0x0800849c: 0x03000de8,
    0x080084a0: 0x0000ffff,
    0x0803f0d0: 0x0803f0d4,
    0x0803f540: 0x0803f544,
    0x0804033c: 0x02023f89,
    0x08040370: 0x020241e4,
    0x08076ba8: 0x030050d0,
    0x08076bac: 0x08076d7d,
    0x08076bb0: 0x0000025e,
    0x08076bf0: 0x030050d0,
    0x08076c34: 0x030050d0,
    0x08076c74: 0x030050d0,
    0x08076d78: 0x030050d0,
    0x080f77f8: 0x0203aad0,
    0x0811f294: 0x0203b010,
    0x0811f2e8: 0x0203b014,
    0x0811f398: 0x0203b010,
    0x0811f39c: 0x020241e4,
    0x0811f3a0: 0x03003e90,
    0x0811f3a4: 0x0811f3d9,
    0x0811f424: 0x03003130,
    0x0811f428: 0x0811f42c,
    0x0811f4ac: 0x020379ec,
    0x0811f4f8: 0x0203b010,
    0x0811f518: 0x0203b014,
    0x0811f538: 0x0203b014,
    0x0811f53c: 0x0203b010,
    0x0811f574: 0x0203b010,
    0x0811f594: 0x0203b010,
    0x0811f5b0: 0x0203b010,
    0x0811f5d4: 0x0203b010,
    0x0811f614: 0x020379ec,
    0x0811f618: 0x03003130,
    0x0811f62c: 0x0811f3c5,
    0x0811f630: 0x0811f3a9,
    0x0811f670: 0x0811f67d,
    0x0811f674: 0x0811f3c5,
    0x0811f678: 0x0811f3a9,
    0x0811f6a8: 0x020379ec,
    0x0811f6ac: 0x0203b014,
    0x0811f6c4: 0x0203b010,
    0x0811f6c8: 0x0203b030,
    0x0811f6cc: 0x0203b028,
    0x0811f6d0: 0x0203b02c,
    0x0811f8b4: 0x0203b010,
    0x0811f8b8: 0x0203b030,
    0x0811f8bc: 0x0203b02c,
    0x0811f8c0: 0x0203b028,
    0x08121124: 0x0203b014,
    0x0812ba20: 0x0203b060,
}

need,chunk,identity,d=inherited.need,inherited.chunk,inherited.identity,inherited.d
CANDIDATE=inherited.CANDIDATE
HEAP_CELL=inherited.HEAP_CELL
TASKS=inherited.TASKS
STATE=0x03003130+0x438
INS={i.address:i for rows in BLOCKS.values() for i in rows}
STATES=(0x0811F488,0x0811F496,0x0811F49C,0x0811F4B0,0x0811F4B6,0x0811F4BC,0x0811F4CE,0x0811F4D4,0x0811F4FC,0x0811F50A,0x0811F51C,0x0811F540,0x0811F546,0x0811F54C,0x0811F552,0x0811F558,0x0811F578,0x0811F598,0x0811F59E,0x0811F5B4,0x0811F5BC,0x0811F5D8,0x0811F5E6)
TABLE={0x0811F42C+4*i:a for i,a in enumerate(STATES)}
SELECTED_TABLE={0x0803F0D4:0x0803F134,0x0803F570:0x0803F720,0x0803F5F8:0x0803F7E8}
SELECTED_EDGES={(0x0803F360,0x0803F364):'GetMonData request in (11,45)'}
PADDING=(0x0811F2E6,0x0811F422,0x0811F4AA,0x0811F4F6,0x0811F572,0x0811F592,0x0811F5AE)
# 各範囲に命令、pool、table、非到達padding以外の未分類byteを許さない。
FULL_EXTENTS=((0x0811F24C,0x0811F3A8),(0x0811F404,0x0811F63E))
BLOCKERS=(
 'allocator_return_range_liveness_and_aliasing_not_bound',
 'retained_cursor_signed_slot_domain_not_bound_except_keepCursorPos_zero',
 'remaining_setup_helper_return_and_memory_effects_not_closed',
 'setup_task_slot_preservation_between_reset_and_state20_not_closed',
 'irq_link_wait_and_scheduler_memory_effects_not_closed',
 'outer_menu_and_post_setup_input_to_hit_lifetime_delegated_not_proven_here',
)
SAFE_ENTRIES={0x08040330,0x08000544,0x080006F4,0x08000700,0x080C0938,0x080F77E8,0x081C9DF8,0x08076B54,0x08076BB4,0x08076C08,0x08076D40,0x0800846C,0x0812B9F4}
# minigame entry は menuType=0 というconstructor束縛付き経路だけ閉じる。
CONDITIONAL_ENTRIES={0x081210D4:'(gPartyMenu.menuType & 15) == 0'}

def encoded(ins):
    k,x=ins.kind,ins.args
    if k=='multiple':
        load,rb,mask=x;need(rb<8 and 0<mask<256,'Thumb multiple fields')
        return (0xC000|(int(load)<<11)|(rb<<8)|mask).to_bytes(2,'little')
    if k=='addhi':
        rd,rs=x;return (0x4400|((rd&8)<<4)|(rs<<3)|(rd&7)).to_bytes(2,'little')
    return inherited.encoded(ins)

OLD_BLOCKS={('mail',k):v for k,v in inherited.BLOCKS.items()}
OLD_BLOCKS.update({('task',k):v for k,v in inherited_task.BLOCKS.items()})
OLD_WORDS={**inherited.LITERALS,**inherited_task.LITERALS}
OLD_BYTES={a for rows in OLD_BLOCKS.values() for i in rows for a in range(i.address,i.address+i.size)}
NEW_BYTES={a for i in INS.values() for a in range(i.address,i.address+i.size)}-OLD_BYTES

def runs(positions):
    out=[]
    for a in sorted(positions):
        if out and out[-1][0]+out[-1][1]==a:out[-1]=(out[-1][0],out[-1][1]+1)
        else:out.append((a,1))
    return tuple(out)
NEW_WINDOWS=runs(NEW_BYTES)
NEW_WORDS={a:v for a,v in LITERALS.items() if a not in OLD_WORDS}
OLD_REFS=[]
covered=set()
for (scope,name),rows in OLD_BLOCKS.items():
    extent=set(range(rows[0].address,rows[-1].address+rows[-1].size))
    needed=extent & ({a for i in INS.values() for a in range(i.address,i.address+i.size)}-NEW_BYTES)
    if needed-covered:OLD_REFS.append((scope,name));covered |= needed

def window(raw,address,size):return dict(address=address,**identity(chunk(raw,address,size)))
def obligations():
    result=[]
    for i in sorted(INS.values(),key=lambda i:i.address):
        if i.kind!='call':continue
        target=i.args[0];conditions=[]
        if target in (0x08076BB4,0x08076C08,0x08076D40):
            status='reset_then_uninterrupted_priority0_only'
            conditions=['ResetTasks completed before this trace','only zero-priority CreateTask calls intervene','no other task write or scheduler dispatch intervenes','valid disjoint caller stack','no asynchronous intervention']
        elif target==0x081C9DF8:
            status='memset_fixed_4_or_32_byte_context_only'
            conditions=['destination and size are the fixed clear-bg or task-array call contexts','size is 4 or 32','valid disjoint caller stack','no asynchronous intervention']
        elif target==0x0812B9F4:
            status='help_context_input5_only';conditions=['r0 input is 5','valid disjoint caller stack','no asynchronous intervention']
        elif target in SAFE_ENTRIES:
            status='bounded_callee_contract_requires_context';conditions=['only checked fixed call contexts and argument domains','valid disjoint caller stack','no asynchronous intervention']
        elif target in CONDITIONAL_ENTRIES:
            status='conditional_menu_type_zero';conditions=[CONDITIONAL_ENTRIES[target],'valid disjoint caller stack','no asynchronous intervention']
        else:status='locally_bound_but_transitive_effect_open' if target in INS else 'opaque_effect_open'
        result.append(dict(address=i.address,target=target,status=status,required_context=conditions,actual_setup_context_discharged=False))
    return result
def make_review(raw):
    return dict(schema_version=1,required_candidate=CANDIDATE,
        instruction_windows=[window(raw,a,n) for a,n in NEW_WINDOWS],
        literal_words={str(a):window(raw,a,4) for a in NEW_WORDS},
        state_dispatch_table=window(raw,0x0811F42C,92),
        selected_callee_dispatch_words={str(a):window(raw,a,4) for a in SELECTED_TABLE},
        padding=[window(raw,a,2) for a in PADDING],
        inherited_instruction_references=[list(x) for x in OLD_REFS],
        call_obligations=obligations(),unresolved_obligations=list(BLOCKERS),
        classifications_added=0,donor_eligible=False,root_to_hit_lifetime_proven=False)

def exact_window(raw,w,a,n):
    need(isinstance(w,dict) and set(w)=={'address','size','sha256'},'address/size/SHA only')
    need(type(w['address']) is int and type(w['size']) is int and (w['address'],w['size'])==(a,n),'fixed window geometry')
    d.signed(raw,w)

def cfg_proof():
    occupied={}
    for i in INS.values():
        for a in range(i.address,i.address+i.size):need(a not in occupied,'nonoverlapping semantic instructions');occupied[a]='instruction'
    for a in set(LITERALS)|set(TABLE)|set(SELECTED_TABLE):
        for x in range(a,a+4):need(x not in occupied,'pool/table not executable');occupied[x]='data'
    for a in PADDING:
        for x in range(a,a+2):need(x not in occupied,'padding disjoint');occupied[x]='padding'
    for lo,hi in FULL_EXTENTS:need(all(a in occupied for a in range(lo,hi)),'whole constructor/setup byte partition')
    targets=[]
    for i in INS.values():
        if i.kind=='branch':
            previous=INS.get(i.address-2)
            need(previous is not None and (previous.kind=='compare' or (previous.kind=='imm' and previous.args[0]=='cmp')),'every conditional branch immediately follows CMP')
        if i.kind in ('branch','jump'):
            t=i.args[-1];need(t in INS or (i.address,t) in SELECTED_EDGES,'every direct branch lands on an instruction or excluded conditional case');targets.append(t)
        elif i.kind=='movhi' and i.args[0]==15:
            need(i.address in (0x0811F420,0x0803F0CC,0x0803F53E),'only bound state/species dispatch')
    need(all(t in INS for t in STATES),'all 23 state targets are code')
    incoming={i.args[-1] for i in INS.values() if i.kind in ('branch','jump')}|set(STATES)|set(SELECTED_TABLE.values())|{i.args[0] for i in INS.values() if i.kind=='call'}
    need(not any(INS[t].kind=='branch' for t in incoming if t in INS),'no edge skips a conditional branch CMP producer')
    # 選択条件付きminigame部分以外のfallthroughは命令開始点に限定。
    for i in INS.values():
        if i.kind in ('jump','bx') or (i.kind=='pop' and i.args[1]) or (i.kind=='movhi' and i.args[0]==15):continue
        need(i.address+i.size in INS or i.address in (0x081210E0,), 'complete instruction fallthrough')
    return dict(whole_constructor_bytes=348,whole_setup_bytes=570,state_count=23,direct_branch_count=len(targets),instruction_count=len(INS))

# 値が不明なloadを具体値へ捏造せず、branchは両枝、未知address/write/callは失敗にする。
class Unknown:pass
U=Unknown()
def concrete(x):return type(x) is int
MASK=(1<<32)-1
class Machine:
    # Thumb全体の汎用emulatorではない。分岐根拠は直前CMPだけに限定し、
    # 他のflagwriterを挟む経路はcfg_proof/runtime gateで拒否する。
    def __init__(self,raw,entry,registers=None,memory=None):
        self.raw=raw;self.pc=entry;self.reg=[U]*16;self.reg[13]=0x03007000;self.reg[14]=0xFFFFFFF1
        if registers:
            for k,v in registers.items():self.reg[k]=v
        self.mem={} if memory is None else dict(memory);self.writes=[];self.calls=[];self.steps=0;self.flags=(U,U,U,U);self.flag_pc=None
    def read(self,a,n):
        need(concrete(a),'unknown memory address is not an effect proof')
        if 0x08000000<=a<0x0A000000:return int.from_bytes(chunk(self.raw,a,n),'little')
        b=[self.mem.get(a+j,U) for j in range(n)]
        return sum(v<<(8*j) for j,v in enumerate(b)) if all(concrete(v) for v in b) else U
    def write(self,a,n,value):
        need(concrete(a),'unknown write target is not an effect proof');self.writes.append((self.pc,a,n))
        for j in range(n):self.mem[a+j]=(value>>(j*8))&255 if concrete(value) else U
    def cmp(self,a,b):
        self.flag_pc=self.pc
        if not concrete(a) or not concrete(b):self.flags=(U,U,U,U);return
        val=(a-b)&MASK;self.flags=(val>>31,val==0,a>=b, bool(((a^b)&(a^val))>>31))
    def condition(self,c):
        need(self.flag_pc==self.pc-2,'branch flag provenance must be immediately preceding CMP')
        n,z,carry,v=self.flags
        need(all(concrete(x) or type(x) is bool for x in self.flags),'branch needs symbolic split')
        return {0:z,1:not z,2:carry,3:not carry,4:bool(n),5:not n,8:carry and not z,9:not carry or z,10:n==v,11:n!=v,12:not z and n==v,13:z or n!=v}[c]
    def step(self,branch_choice=None):
        need(self.pc in INS,'callee or control-flow effect outside closed model');i=INS[self.pc];k,x=i.kind,i.args;r=self.reg;nxt=self.pc+i.size
        def binary(op,a,b):return op(a,b)&MASK if concrete(a) and concrete(b) else U
        if k=='literal':r[x[0]]=self.read(x[1],4)
        elif k=='movhi':
            r[x[0]]=r[x[1]]
            if x[0]==15:need(concrete(r[15]),'bounded table dispatch');nxt=r[15]&~1
        elif k=='imm':
            op,rd,v=x
            if op=='cmp':self.cmp(r[rd],v)
            elif op=='mov':r[rd]=v
            else:r[rd]=binary((lambda a,b:a+b) if op=='add' else (lambda a,b:a-b),r[rd],v)
        elif k in ('add','addi','addhi'):
            rd=x[0];a=r[x[1]] if k!='addhi' else r[rd];b=x[2] if k=='addi' else r[x[2]] if k=='add' else r[x[1]];r[rd]=binary(lambda a,b:a+b,a,b)
        elif k=='compare':self.cmp(r[x[0]],r[x[1]])
        elif k=='shift':
            op,rd,rs,amt=x;v=r[rs]
            r[rd]=U if not concrete(v) else ((v<<amt)&MASK if op=='lsl' else v>>(amt or 32) if op=='lsr' else ((v if v<1<<31 else v-(1<<32))>>(amt or 32))&MASK)
        elif k=='alu':
            op,rd,rs=x
            r[rd]=binary({'and':lambda a,b:a&b,'orr':lambda a,b:a|b,'mul':lambda a,b:a*b,'neg':lambda a,b:-b}[op],r[rd] if op!='neg' else 0,r[rs])
        elif k=='mem':
            load,width,rd,rb,off=x;a=binary(lambda a,b:a+b,r[rb],off);size={'word':4,'half':2,'byte':1}[width]
            if load:r[rd]=self.read(a,size)
            else:self.write(a,size,r[rd])
        elif k=='multiple':
            load,rb,mask=x;need(not load,'store multiple only')
            for rd in range(8):
                if mask&(1<<rd):self.write(r[rb],4,r[rd]);r[rb]+=4
        elif k=='spadd':r[13]+=x[0]
        elif k=='spmem':
            load,rd,off=x
            if load:r[rd]=self.read(r[13]+off,4)
            else:self.write(r[13]+off,4,r[rd])
        elif k in ('push','pop'):
            mask,extra=x;registers=[j for j in range(8) if mask&(1<<j)]+([14 if k=='push' else 15] if extra else [])
            if k=='push':
                r[13]-=4*len(registers)
                for j,rd in enumerate(registers):self.write(r[13]+4*j,4,r[rd])
            else:
                for rd in registers:r[rd]=self.read(r[13],4);r[13]+=4
                if extra:nxt=r[15]&~1
        elif k=='call':self.calls.append((self.pc,x[0]));r[14]=nxt|1;nxt=x[0]
        elif k=='branch':
            need(self.flag_pc==self.pc-2,'branch flag provenance must be immediately preceding CMP')
            nxt=x[1] if (self.condition(x[0]) if branch_choice is None else branch_choice) else nxt
        elif k=='jump':nxt=x[0]
        elif k=='bx':need(concrete(r[x[0]]),'return/indirect unknown');nxt=r[x[0]]&~1
        else:raise ValueError('unsupported effect instruction '+k)
        self.pc=nxt;self.steps+=1;need(self.steps<30000,'finite local effect execution')
    def run(self):
        while self.pc!=0xFFFFFFF0:self.step()
        need(self.reg[13]==0x03007000,'balanced caller stack');return self
    def paths(self):
        pending=[self];finished=[]
        while pending:
            m=pending.pop()
            while m.pc!=0xFFFFFFF0:
                need(m.pc in INS,'selected effect path escaped bound code')
                if INS[m.pc].kind=='branch' and any(isinstance(x,Unknown) for x in m.flags):
                    other=copy.deepcopy(m);other.raw=m.raw;other.step(branch_choice=False);pending.append(other);m.step(branch_choice=True)
                else:m.step()
            need(m.reg[13]==0x03007000,'balanced caller stack on every symbolic path');finished.append(m)
            need(len(finished)+len(pending)<10000,'bounded symbolic path set')
        return finished
    def external_writes(self):return [(a,n) for _,a,n in self.writes if not 0x03006F00<=a<0x03007000]

def effects(raw):
    """未知値は未知のまま。完全閉鎖した固定calleeだけを実命令モデルで実行。"""
    reports=[]
    cases=[('set_main',0x08000544,{0:U},None,[(0x03003134,4),(STATE,1)]),
      ('set_vblank',0x080006F4,{0:U},None,[(0x0300313C,4)]),('set_hblank',0x08000700,{0:U},None,[(0x03003140,4)]),
      ('null_callbacks',0x080C0938,None,None,[(0x0300313C,4),(0x03003140,4)]),
      ('clear_bg_schedule',0x080F77E8,None,None,[(0x0203AAD0,4)]),
      ('reset_tasks',0x08076B54,None,None,[(TASKS,16*40)]),
      ('free_sprite_palettes',0x0800846C,None,None,[(LITERALS[0x08008498],1),(LITERALS[0x0800849C],32)]),
      ('ordinary_minigame_helper',0x081210D4,None,{0x0203B01C:0},[])]
    for label,entry,regs,mem,allowed in cases:
        m=Machine(raw,entry,regs,mem).run();wr=m.external_writes()
        need(all(any(lo<=a and a+n<=lo+size for lo,size in allowed) for a,n in wr),'closed effect outside declared memory')
        need(all(not(a<=HEAP_CELL<a+n) for a,n in wr),'heap pointer cell untouched')
        reports.append(dict(callee=entry,role=label,write_regions=[dict(address=a,size=n) for a,n in allowed],steps=m.steps))
    # previous値を未知のまま全branchを分岐。全値で書込先は同じ固定halfwordのみ。
    slot=LITERALS[0x0812BA20];paths=Machine(raw,0x0812B9F4,{0:5}).paths()
    for m in paths:need(all(a==slot and n==2 for a,n in m.external_writes()),'help context only fixed halfword for every symbolic branch')
    reports.append(dict(callee=0x0812B9F4,role='set_help_context_input5',write_regions=[dict(address=slot,size=2)],symbolic_paths=len(paths)))
    # CalculatePlayerPartyCountから種族getterの実改変を含む全有限経路。
    # species/egg flagは未知のまま全枝へ分岐。6体上限を実count loopが生成する。
    paths=Machine(raw,0x08040330).paths();count=LITERALS[0x0804033C];party=0x020241E4
    for m in paths:
        need(all((a==count and n==1) or (party<=a and a+n<=party+600) for a,n in m.external_writes()),'species getter touches only six party records and count')
        need(concrete(m.reg[0]) and 0<=m.reg[0]<=6,'actual count loop bounds every path')
    reports.append(dict(callee=0x08040330,role='calculate_party_count_species11',write_regions=[dict(address=count,size=1),dict(address=party,size=600)],symbolic_paths=len(paths),return_values=sorted({m.reg[0] for m in paths})))
    # ResetTasksはactive byte全16を0にする。無介入のCreateTask 16回が全slotを使用する。
    mem=Machine(raw,0x08076B54).run().mem
    need(all(mem[TASKS+40*i+4]==0 for i in range(16)),'producer empties all 16 task slots')
    task_trace=[]
    for slot_index in range(17):
        ptr=0x08120319+4*slot_index;m=Machine(raw,0x08076BB4,{0:ptr,1:0},mem).run();wr=m.external_writes()
        need(all(TASKS<=a and a+n<=TASKS+640 for a,n in wr),'task kernel only task array')
        if slot_index<16:
            need(m.reg[0]==slot_index and m.read(TASKS+slot_index*40,4)==ptr and m.read(TASKS+slot_index*40+4,1)==1,'concrete free-slot producer installs exact function')
        else:need(m.reg[0]==0 and not wr,'full task array returns ambiguous zero without registration')
        task_trace.append(dict(call_index=slot_index+1,result=m.reg[0],new_task_registered=slot_index<16));mem=m.mem
    return dict(status='PASS_BOUNDED_CALLEE_EFFECTS',closed_effects=reports,reset_then_uninterrupted_task_calls=task_trace,
      task_slot_guarantee_across_setup_helpers=False,allocation_range_precondition_proven=False,
      contract_ja='caller stackが対象allocationと非alias、SPが有効、同期実行中にIRQ等の介入なしという局所callee契約。未知loadは未知値を維持。task列は無介入の17回であり実setup経路の成功を主張しない。')

def pokemon_data_effects(raw):
    """通常party six slotsに限るfield11/45の合成用契約。全callee意味を自身で再確認。"""
    for i in INS.values():
        if 0x0803F064<=i.address<0x0804036E:need(chunk(raw,i.address,i.size)==encoded(i),'species/egg callee instruction semantics')
    for a,value in {**LITERALS,**SELECTED_TABLE}.items():
        if 0x0803F064<=a<0x08040374:need(d.u32(raw,a)==value,'species/egg fixed literal role')
    contracts=[]
    for field in (11,45):
        for slot in range(6):
            ptr=0x020241E4+slot*100;paths=Machine(raw,0x0803F354,{0:ptr,1:field,2:0}).paths()
            for m in paths:need(all(ptr+32<=a and a+n<=ptr+80 for a,n in m.external_writes()),'getter writes only same Pokemon encrypted fields')
            contracts.append(dict(field=field,party_slot=slot,argument_pointer=ptr,write_region=dict(address=ptr+32,size=48),symbolic_paths=len(paths)))
    return dict(status='PASS_SPECIES11_EGG45_BOUNDED_PARTY_CALLEES',contracts=contracts,
      heap_cell_written=False,task_array_written=False,allocation_nonalias_precondition_proven=False,
      preconditions_ja='pointerはgPlayerPartyの0..5slot。caller stackは有効でpointer/globalと非alias。同期callee内のIRQ等介入を対象外とする。任意heapポインタや任意fieldへ一般化しない。')

def check_local(raw,review,parent_review,sources):
    need(set(review)==set(make_review(raw)),'closed setup review schema')
    need(review['schema_version']==1 and review['required_candidate']==CANDIDATE,'fixed scope')
    need(review['classifications_added']==0 and review['donor_eligible'] is False and review['root_to_hit_lifetime_proven'] is False,'no promotion')
    need(review['unresolved_obligations']==list(BLOCKERS),'unclosed obligations retained')
    inherited.source_proof(parent_review,sources)
    need(review['inherited_instruction_references']==[list(x) for x in OLD_REFS],'fixed inherited evidence references')
    for scope,name in OLD_REFS:
        rows=OLD_BLOCKS[(scope,name)];src=parent_review if scope=='mail' else parent_review['task_evidence']
        exact_window(raw,src['instruction_windows'][name],rows[0].address,sum(i.size for i in rows))
    need(len(review['instruction_windows'])==len(NEW_WINDOWS),'all new gaps')
    for w,(a,n) in zip(review['instruction_windows'],NEW_WINDOWS):exact_window(raw,w,a,n)
    need(set(review['literal_words'])=={str(a) for a in NEW_WORDS},'new literal roles exact')
    for a,value in LITERALS.items():
        if a in NEW_WORDS:w=review['literal_words'][str(a)]
        elif a in inherited.LITERALS:w=parent_review['literal_words'][str(a)]
        else:w=parent_review['task_evidence']['literal_words'][str(a)]
        exact_window(raw,w,a,4);need(d.u32(raw,a)==value,'exact effect pointer role')
    exact_window(raw,review['state_dispatch_table'],0x0811F42C,92)
    for a,target in TABLE.items():need(d.u32(raw,a)==target,'complete state dispatch target')
    need(set(review['selected_callee_dispatch_words'])=={str(a) for a in SELECTED_TABLE},'closed selected getter table roles')
    for a,t in SELECTED_TABLE.items():exact_window(raw,review['selected_callee_dispatch_words'][str(a)],a,4);need(d.u32(raw,a)==t,'actual selected species table')
    need(len(review['padding'])==len(PADDING),'complete nonexecuted padding partition')
    for a,w in zip(PADDING,review['padding']):exact_window(raw,w,a,2);need(int.from_bytes(chunk(raw,a,2),'little')==0,'fixed unreachable padding')
    for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'semantic constraint '+str(i.address)+' '+i.kind)
    need(review['call_obligations']==obligations(),'every call remains closed or explicitly open')
    cfg=cfg_proof();effect=effects(raw);pokemon_effect=pokemon_data_effects(raw)
    return dict(status='PASS_COMPLETE_DIRECT_SETUP_CFG_LOCAL_CALLEE_EFFECTS_NOT_ACCEPTED',cfg=cfg,effects=effect,
        pokemon_data_effects=pokemon_effect,
        new_instruction_windows=len(NEW_WINDOWS),new_literal_words=len(NEW_WORDS),inherited_windows_reused=len(OLD_REFS),
        whole_input_identity=identity(raw),current_acceptance_claimed=False,newly_classified=0,
        root_to_hit_lifetime_proven=False,allocation_same_lifetime_proven=False,unresolved_obligations=list(BLOCKERS),call_obligations=obligations(),donor_eligible=False)

def regions(raw,review,parent_review,sources,*args,**kwargs):
    check_local(raw,review,parent_review,sources)
    raise ValueError('party setup same-allocation root-to-hit lifetime remains unproven; unknown retained')
