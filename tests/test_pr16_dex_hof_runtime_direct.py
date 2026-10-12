"""New QuestLog direct-root tests only. The caller injects private bytes in memory."""
import copy
import hashlib
import unittest

import pr16_dex_hof_runtime_direct as v

FIXTURE = None


def reseal(obj, raw):
    if isinstance(obj, dict):
        if {'address', 'size', 'sha256'} <= obj.keys():
            a = obj['address'] - 0x08000000
            obj['sha256'] = hashlib.sha256(raw[a:a + obj['size']]).hexdigest()
        for x in obj.values():
            reseal(x, raw)
    elif isinstance(obj, list):
        for x in obj:
            reseal(x, raw)


class DirectQuestLogTests(unittest.TestCase):
    def setUp(self):
        if FIXTURE is None:
            raise RuntimeError('explicit fixture injection required')
        self.raw, self.inherited, self.review, self.sources = FIXTURE

    def check(self, raw=None, inherited=None, review=None, sources=None):
        return v._regions(self.raw if raw is None else raw,
                          self.inherited if inherited is None else inherited,
                          self.review if review is None else review,
                          self.sources if sources is None else sources)

    def reject(self, edit):
        r = copy.deepcopy(self.review)
        edit(r)
        with self.assertRaises((ValueError, KeyError, StopIteration)):
            self.check(review=r)

    def mutate(self, a, size, value):
        raw = bytearray(self.raw)
        pos = a - 0x08000000
        encoded = value.to_bytes(size, 'little')
        self.assertNotEqual(raw[pos:pos + size], encoded)
        raw[pos:pos + size] = encoded
        raw = bytes(raw)
        review, inherited = copy.deepcopy(self.review), copy.deepcopy(self.inherited)
        reseal(review, raw)
        reseal(inherited, raw)
        with self.assertRaises((ValueError, KeyError, StopIteration)):
            self.check(raw=raw, inherited=inherited, review=review)

    def test_01_only_new_six_byte_instruction_window(self):
        before = copy.deepcopy(self.inherited)
        rows, proof = self.check()
        self.assertEqual([(r.start, r.end, r.kind) for r in rows], [(0x081161EA, 0x081161F0, v.KIND)])
        self.assertEqual(proof['count'], 1)
        self.assertEqual(self.inherited, before)
        self.assertEqual(proof['protected_windows'], 13)
        self.assertEqual(proof['protected_bytes'], 133)

    def test_02_chain_geometry_compatibility(self):
        import pr16_dex_hof_runtime_chain as chain
        region = self.check()[0][0]
        self.assertEqual(chain.witness_geometry({'kind':region.kind,'evidence':region.evidence}), (region.start, 6))

    def test_03_whole_current_identity_mandatory(self):
        if v.identity(self.raw) == v.CANDIDATE:
            self.assertEqual(v.regions(self.raw, self.inherited, self.review, self.sources)[1]['count'], 1)
        else:
            with self.assertRaises(ValueError):
                v.regions(self.raw, self.inherited, self.review, self.sources)

    def test_04_inherited_current_target(self):
        i = copy.deepcopy(self.inherited);i['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_05_original_unknown_required(self):
        i = copy.deepcopy(self.inherited)
        next(h for h in i['hits'] if h['address'] == v.HIT)['accepted'] = True
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_06_owner_external_required(self):
        i = copy.deepcopy(self.inherited);r = copy.deepcopy(self.review)
        next(h for h in i['hits'] if h['address'] == v.HIT)['owner_candidates'] = ['invented']
        r['hit']['owner_candidates'] = ['invented']
        with self.assertRaises(ValueError):self.check(inherited=i,review=r)

    def test_07_duplicate_original_rejected(self):
        i = copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
        with self.assertRaises(ValueError):self.check(inherited=i)

    def test_08_wrong_hit(self):self.reject(lambda r:r['hit'].update(target=0x09FED000))
    def test_09_symbol_is_not_root(self):self.reject(lambda r:r['root'].update(kind='symbol_only'))
    def test_10_wrong_event_selector(self):self.reject(lambda r:r['root'].update(event_id=39))
    def test_11_wrong_table_slot(self):self.reject(lambda r:r['root'].update(slot=v.TABLE+4*39))
    def test_12_wrong_indirect_consumer(self):self.reject(lambda r:r['root'].update(synchronous_indirect_consumer=0x081C7AC8))
    def test_13_root_entry_without_thumb_table_proof(self):self.reject(lambda r:r['root'].update(entry=v.ENTRY+2))
    def test_14_missing_window(self):self.reject(lambda r:r['windows'].pop())
    def test_15_duplicate_window(self):self.reject(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
    def test_16_reorder_window(self):self.reject(lambda r:r['windows'].reverse())
    def test_17_expand_exclusion_to_whole_function(self):self.reject(lambda r:next(w for w in r['windows']if w['label']=='hit_instruction_window').update(size=56))
    def test_18_half_bl_window(self):self.reject(lambda r:next(w for w in r['windows']if w['label']=='hit_instruction_window').update(size=4))
    def test_19_no_literal_pool_classification(self):self.reject(lambda r:r['claims'].update(literal_pool_included=True))
    def test_20_no_universal_runtime_claim(self):self.reject(lambda r:r['claims'].update(all_entry_states_safe_claimed=True))
    def test_21_no_actual_execution_claim(self):self.reject(lambda r:r['claims'].update(runtime_execution_observed=True))
    def test_22_no_callee_return_claim(self):self.reject(lambda r:r['claims'].update(get_map_name_return_proven=True))
    def test_23_no_donor_claim(self):self.reject(lambda r:r['claims'].update(donor_eligible=True))
    def test_24_no_extra_review_fields(self):self.reject(lambda r:r.update(unsafe_override=True))

    def test_25_all_window_dependency_mutations_resealed(self):
        count = 0
        for a, n in v.WINDOWS.values():
            for offset in range(0, n, 2):
                size = min(2, n-offset);address=a+offset
                value=int.from_bytes(v.chunk(self.raw,address,size),'little')
                with self.subTest(address=address,size=size):self.mutate(address,size,value^1)
                count += 1
        self.assertEqual(count, 67)

    def test_26_wrong_table_thumb_bit_resealed(self):self.mutate(v.TABLE+4*v.EVENT_ID,4,v.ENTRY)
    def test_27_wrong_dispatch_stride_resealed(self):self.mutate(0x08114630,2,0x00C0)
    def test_28_wrong_mask_resealed(self):self.mutate(0x08114660,4,0x0FF)
    def test_29_wrong_guard_signedness_resealed(self):
        old=int.from_bytes(v.chunk(self.raw,0x0811461C,2),'little')
        self.mutate(0x0811461C,2,(old&255)|0xDD00)
    def test_30_wrong_reader_size_resealed(self):self.mutate(v.SIZE_TABLE+v.EVENT_ID,1,10)
    def test_31_wrong_reader_register_resealed(self):
        old=int.from_bytes(v.chunk(self.raw,0x081149B2,2),'little');self.mutate(0x081149B2,2,old^1)
    def test_32_wrong_mapname_target_resealed(self):
        old=int.from_bytes(v.chunk(self.raw,0x081161EC,2),'little');self.mutate(0x081161EC,2,old^2)
    def test_33_source_content_changed(self):
        s=dict(self.sources);s['pret-quest_log_events.c']+=b'\n'
        with self.assertRaises(ValueError):self.check(sources=s)
    def test_34_resealed_source_manifest_rejected(self):self.reject(lambda r:r['source_bindings']['pret-quest_log.h'].update(sha256='0'*64))
    def test_35_missing_source_role(self):
        s=dict(self.sources);s.pop('pret-quest_log.h')
        with self.assertRaises(ValueError):self.check(sources=s)

    def test_36_all_header_count_bits_keep_event40(self):
        for count in range(16):
            with self.subTest(count=count):
                p=v.selected_event_contract(40|(count<<12),7,7,count,8+4*count)
                self.assertEqual(p['slot'],v.TABLE+160)
                self.assertEqual(p['map_section_byte_offset'],6+4*count)
    def test_37_wrong_event_id_rejected(self):
        for h in (0,39,41,4095,65535,-1,65536,True):
            with self.subTest(header=h),self.assertRaises(ValueError):v.selected_event_contract(h,0,0,0,8)
    def test_38_future_action_rejected(self):
        with self.assertRaises(ValueError):v.selected_event_contract(40,1,0,0,8)
    def test_39_payload_extent_not_origin_word_width(self):
        for n in (0,4,7):
            with self.subTest(available=n),self.assertRaises(ValueError):v.selected_event_contract(40,0,0,0,n)
    def test_40_counter_requires_corresponding_extent(self):
        with self.assertRaises(ValueError):v.selected_event_contract(40,0,0,4,8)
        p=v.selected_event_contract(40,0,0,65535,8+4*65535)
        self.assertEqual(p['payload_offset'],4+4*65535)
    def test_41_negative_or_noninteger_fields_rejected(self):
        for x in (-1,65536,True,1.0):
            with self.subTest(counter=x),self.assertRaises(ValueError):v.selected_event_contract(40,0,0,x,1000000)
    def test_42_source_window_bytes_are_not_published(self):
        def check(obj):
            if isinstance(obj,dict):
                self.assertFalse(set(obj)&{'raw','rawhex','bytes','data','private_path','member_path'})
                for child in obj.values():check(child)
            elif isinstance(obj,list):
                for child in obj:check(child)
        check(self.review)
