"""新しいbinary変換と1始まりWiki slot補正の境界試験。"""
import unittest
from tools import pr16_learnset_payloads as p


def row(mid=33, family='level_up', lev=1, ordinals=None):
    result={'move_id':mid,'move_key':'MOVE_'+str(mid),'consumer':family,
            'provenance':{'source_route':{'target_learning_level':lev}}}
    if ordinals is not None:
        result['runtime_binding']={'candidate_slots_zero_based':ordinals,
             'status':'CANDIDATE_SLOT_REBIND_REQUIRED' if ordinals else 'ARCHIVE_ADAPTER_REQUIRED',
             'compatibility_granted':False,'physical_supply_verified':False}
    return result


class PayloadTests(unittest.TestCase):
    def test_level_exact_bytes_and_terminator(self):
        raw=p.pack_levels([row(),row(535,lev=9)])
        self.assertEqual(raw.hex(),'2100011702090000ff')
        self.assertEqual(p.unpack_levels(raw),[(33,1),(535,9)])

    def test_level_order_and_duplicates_preserved(self):
        self.assertEqual(p.unpack_levels(p.pack_levels([row(33,lev=100),row(),row()])),[(33,100),(33,1),(33,1)])

    def test_evolution_not_level_zero(self):
        with self.assertRaises(ValueError):p.pack_levels([row(family='evolution',lev=0)])

    def test_zero_and_out_of_range_level_rejected(self):
        for lev in (0,-1,101,None,True):
            with self.assertRaises(ValueError):p.pack_levels([row(lev=lev)])

    def test_terminator_required(self):
        with self.assertRaises(ValueError):p.unpack_levels(bytes.fromhex('210001'))

    def test_early_terminator_rejected(self):
        with self.assertRaises(ValueError):p.unpack_levels(bytes.fromhex('0000ff0000ff'))

    def test_empty_selected_owner_has_explicit_terminator(self):
        self.assertEqual(p.pack_levels([]),b'\0\0\xff')

    def test_side_change_not_serializable(self):
        for value in (0,1063,65535,True):
            with self.assertRaises(ValueError):p.pack_moves([value])

    def test_u16_round_trip(self):
        self.assertEqual(p.unpack_moves(p.pack_moves([1,1062,1])),[1,1062,1])

    def test_u16_odd_length_rejected(self):
        with self.assertRaises(ValueError):p.unpack_moves(b'\1')

    def test_machine_endpoints(self):
        self.assertEqual(p.wiki_ordinal_to_bit(1,'machine'),0)
        self.assertEqual(p.wiki_ordinal_to_bit(128,'machine'),127)

    def test_tutor_endpoints(self):
        self.assertEqual(p.wiki_ordinal_to_bit(1,'tutor'),0)
        self.assertEqual(p.wiki_ordinal_to_bit(64,'tutor'),63)

    def test_zero_based_input_never_guessed(self):
        for value in (0,129,True,'1'):
            with self.assertRaises(ValueError):p.wiki_ordinal_to_bit(value,'machine')

    def test_tutor_high_bit_never_used(self):
        with self.assertRaises(ValueError):p.wiki_ordinal_to_bit(65,'tutor')
        with self.assertRaises(ValueError):p.compatibility([row(family='tutor')],'tutor',{33:[64]})

    def test_catalog_corrects_misnamed_input(self):
        blocks=[{'routes':[row(family='machine',ordinals=[1,128])]}]
        catalog,bits=p.catalog(blocks,'machine')
        self.assertEqual(catalog,{33:[0,127]});self.assertEqual(set(bits),{0,127})

    def test_catalog_slot_collision_rejected(self):
        blocks=[{'routes':[row(family='machine',ordinals=[1]),row(44,'machine',ordinals=[1])]}]
        with self.assertRaises(ValueError):p.catalog(blocks,'machine')

    def test_catalog_duplicate_slots_rejected(self):
        with self.assertRaises(ValueError):p.catalog([{'routes':[row(family='machine',ordinals=[1,1])]}],'machine')

    def test_catalog_does_not_claim_supply(self):
        value=row(family='machine',ordinals=[1]);value['runtime_binding']['physical_supply_verified']=True
        with self.assertRaises(ValueError):p.catalog([{'routes':[value]}],'machine')

    def test_compatibility_and_archive_are_separate(self):
        raw,archive,positions=p.compatibility([row(family='machine'),row(44,'machine')],'machine',{33:[0,127]})
        self.assertEqual(raw.hex(),'01000000000000000000000000000080')
        self.assertEqual(p.bits_set(raw,'machine'),[0,127]);self.assertEqual(archive,[44]);self.assertEqual(positions,[[0,127],[]])

    def test_archive_dedup_keeps_route_provenance_count(self):
        _,archive,positions=p.compatibility([row(family='machine'),row(family='machine')],'machine',{})
        self.assertEqual(archive,[33]);self.assertEqual(len(positions),2)

    def test_no_cross_consumer_compatibility(self):
        with self.assertRaises(ValueError):p.compatibility([row(family='tutor')],'machine',{})

    def test_tutor_upper_bytes_rejected(self):
        with self.assertRaises(ValueError):p.bits_set(b'\0'*8+b'\1'+b'\0'*7,'tutor')

    def test_payload_not_install_permission(self):
        with self.assertRaises(ValueError):p.require_install_ready({'install_ready':False,'blocking':[]})

    def test_blocker_not_ignored(self):
        with self.assertRaises(ValueError):p.require_install_ready({'install_ready':True,'blocking':[1029],
            'conditional_form_runtime_connection':True,'physical_supply_verified':True})


if __name__=='__main__':unittest.main()
