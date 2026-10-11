"""新規のSpecies binding境界だけを検証。既受入試験/原本生成は呼ばない。"""
import copy
import unittest
from tools import pr16_learnset_species_binding as b


def route(sid=1, family='level_up', move=33):
    return {'species_id':sid,'species_key':'KEY_'+str(sid),'consumer':family,
            'move_id':move,'move_key':'MOVE_'+str(move),'source_id':'route:1',
            'form_key':'','provenance':{'source_route':{'level':7}},'conditional_egg':False}


def block(sid=1, selected=True, family='level_up'):
    return {'species_id':sid,'species_key':'KEY_'+str(sid),'runtime_applied':False,
            'selection':'OFFICIAL_SOURCE_SELECTED' if selected else 'SOURCE_NOT_SELECTED',
            'routes':[route(sid,family)] if selected else []}


def binding(sid=2, policy='INTERNAL_IDENTITY_ONLY'):
    return {'species_id':sid,'species_key':'KEY_'+str(sid),'original_selection':'SOURCE_NOT_SELECTED',
            'automatic_fallback':False,'runtime_applied':False,'rewrite_existing_moves':False,
            'direct_grant_on_transform':False,'policy':policy,'evidence':[{'contract':'fixture'}]}


def fixture():
    # 正本schemaの最小例。全数/実値照合はActionsの独立実データ監査で行う。
    rows=[{'species_id':1,'species_key':'KEY_1','selection':'OFFICIAL_SOURCE_SELECTED',
           'active_routes':1,'automatic_fallback':False,'source_target':None},
          {'species_id':2,'species_key':'KEY_2','selection':'RUNTIME_EXTENSION_NOT_SELECTED',
           'active_routes':0,'automatic_fallback':False,'source_target':None},
          {'species_id':3,'species_key':'KEY_3','selection':'RUNTIME_EXTENSION_NOT_SELECTED',
           'active_routes':0,'automatic_fallback':False,'source_target':None}]
    own={'identity':{'species_id':2,'species_key':'KEY_2','classification':'INTERNAL_CONDITIONAL_FORM',
                      'normal_species_id':1,'reference_id':'fixture:2'},
         'p03':{'source_route_clone':{'policy':'EXACT_LEARNSET_CLONE_WITH_DISTINCT_INTERNAL_SPECIES_OWNER',
                                    'source_reference_id':'fixture:1','route_count':1},
                'owner_clone':{'donor_species':1}}}
    spec={'id':3,'species_key':'KEY_3','classification':'BATTLE_ONLY_MEGA','source_species_id':1,
          'source_species_key':'KEY_1','clone_policy':{'source_rows':['level_up_pointer','tmhm','tutor']}}
    link={'target_species_id':3,'target_species_key':'KEY_3','source_species_id':1,'source_species_key':'KEY_1'}
    contracts={'identity':{'target_normalization':{'records':[]}},'p04_species':{'records':[spec]},
               'p04_mega':{'mappings':[link]},'own_tempo':own,'p02':{'current_table':{'rows':[]}}}
    return rows, {}, contracts


class QueryTests(unittest.TestCase):
    def test_selected_route_is_lossless_copy(self):
        original=block(); result=b.query_routes(original,'level_up')
        self.assertEqual(result,original['routes']); result[0]['move_id']=10
        self.assertEqual(original['routes'][0]['move_id'],33)

    def test_vega_selection_supported(self):
        row=block(); row['selection']='VEGA_SOURCE_SELECTED'
        self.assertEqual(len(b.query_routes(row,'level_up')),1)

    def test_unknown_selection_is_not_empty(self):
        row=block(2,False); row['selection']='BASELINE_SELECTED'
        with self.assertRaises(ValueError): b.query_routes(row,'level_up',binding())

    def test_missing_binding_is_not_empty(self):
        with self.assertRaises(b.BindingRequired): b.query_routes(block(2,False),'level_up')

    def test_nonlearning_is_typed_not_list(self):
        for policy in b.NONPERMANENT:
            result=b.query_routes(block(2,False),'level_up',binding(policy=policy))
            self.assertIsInstance(result,b.NonLearningIdentity)
            self.assertTrue(result.preserve_current_moves)
            self.assertFalse(result.automatic_fallback)

    def test_no_selected_binding_override(self):
        with self.assertRaises(ValueError): b.query_routes(block(),'level_up',binding(1))

    def test_binding_key_mismatch(self):
        value=binding(); value['species_key']='WRONG'
        with self.assertRaises(ValueError): b.query_routes(block(2,False),'level_up',value)

    def test_runtime_block_rejected(self):
        row=block(); row['runtime_applied']=True
        with self.assertRaises(ValueError): b.query_routes(row,'level_up')

    def test_gift_permission_does_not_adopt_baseline(self):
        with self.assertRaises(b.BindingRequired):
            b.query_routes(block(2,False),'level_up',binding(policy='GIFT_LEARNSET_ADOPTION_REQUIRED'))

    def test_unknown_policy_fails(self):
        with self.assertRaises(b.BindingRequired): b.query_routes(block(2,False),'level_up',binding(policy='AUTO_ALIAS'))

    def test_no_transform_grant(self):
        value=binding(); value['direct_grant_on_transform']=True
        with self.assertRaises(ValueError): b.query_routes(block(2,False),'level_up',value)

    def test_no_current_move_rewrite(self):
        value=binding(); value['rewrite_existing_moves']=True
        with self.assertRaises(ValueError): b.query_routes(block(2,False),'level_up',value)

    def test_consumer_cross_contamination_fails(self):
        with self.assertRaises(ValueError): b.query_routes(block(),'egg')

    def test_side_change_fails(self):
        row=block(); row['routes'][0]['move_id']=1063
        with self.assertRaises(ValueError): b.query_routes(row,'level_up')

    def test_bool_move_fails(self):
        row=block(); row['routes'][0]['move_id']=True
        with self.assertRaises(ValueError): b.query_routes(row,'level_up')

    def test_owner_clone_keeps_original_conditions(self):
        value=binding(policy='STAGE75_DISTINCT_OWNER_CLONE')
        value.update(source_species_id=1,source_species_key='KEY_1')
        src=block(); before=copy.deepcopy(src)
        result=b.query_routes(block(2,False),'level_up',value,donor_block=src)
        self.assertEqual(src,before)
        self.assertEqual(result[0]['species_id'],2)
        self.assertEqual(result[0]['provenance'],src['routes'][0]['provenance'])
        self.assertEqual(result[0]['binding_origin']['species_id'],1)
        self.assertEqual(result[0]['source_id'],'binding:own-tempo:route:1')

    def test_clone_donor_not_selected_fails(self):
        value=binding(policy='STAGE75_DISTINCT_OWNER_CLONE')
        value.update(source_species_id=1,source_species_key='KEY_1')
        with self.assertRaises(ValueError): b.query_routes(block(2,False),'level_up',value,donor_block=block(1,False))

    def test_caterpie_routes_not_union(self):
        value=binding(policy='EXPLICIT_CATERPIE_IDENTITY_REPAIR')
        value['routes']=[{'route_id':'level','consumer':'level_up','project_move_id':33,'move_key':'MOVE_33','learning_level':1},
                         {'route_id':'tm','consumer':'machine','project_move_id':489,'move_key':'MOVE_489'}]
        result=b.query_routes(block(2,False),'level_up',value)
        self.assertEqual([r['move_id'] for r in result],[33])
        self.assertEqual(result[0]['layer'],'explicit_identity_repair')

    def test_none_and_egg_not_playable_empty_arrays(self):
        result=b.query_routes(block(0,False),'egg',binding(0))
        self.assertIsInstance(result,b.NonLearningIdentity)


class ContractTests(unittest.TestCase):
    def test_minimal_binding_and_input_purity(self):
        args=fixture(); before=copy.deepcopy(args)
        result=b.build_bindings(*args)
        self.assertEqual(args,before)
        self.assertEqual([r['policy'] for r in result],['STAGE75_DISTINCT_OWNER_CLONE','P04_MEGA_CARRY_ONLY'])

    def test_duplicate_species_id_fails(self):
        args=fixture(); args[0].append(copy.deepcopy(args[0][0]))
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_duplicate_species_key_fails(self):
        args=fixture(); args[0][1]['species_key']='KEY_1'
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_unknown_extension_fails(self):
        args=fixture(); args[0].append(dict(args[0][2],species_id=4,species_key='KEY_4'))
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_mega_reverse_identity_disagreement_fails(self):
        args=fixture(); args[2]['p04_mega']['mappings'][0]['source_species_key']='WRONG'
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_mega_cloning_without_move_contract_fails(self):
        args=fixture(); args[2]['p04_species']['records'][0]['clone_policy']['source_rows']=[]
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_normal_owner_not_selected_fails(self):
        args=fixture(); args[0][0]['selection']='SOURCE_NOT_SELECTED'
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_extension_manifest_collision_fails(self):
        args=fixture(); args[1][3]={'species_key':'KEY_3'}
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_bool_species_id_fails(self):
        args=fixture(); args[0][0]['species_id']=True
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_reverse_forms_do_not_collapse(self):
        args=fixture()
        # 複数の解除先は原本conditionを保持できる。片方を黙って上書きしない。
        reverse=[]
        for dst in (1,2):
            reverse.append({'source':{'canonical_id':3,'species_key':'KEY_3'},
                            'target':{'canonical_id':dst,'species_key':'KEY_'+str(dst)},
                            'method':{'family':'BATTLE_TRANSFORM'},'condition':{'parameter':{'value':0}},'slot':dst})
        args[2]['p02']['current_table']['rows']=reverse
        self.assertEqual(len(b.build_bindings(*args)),2)
        args[2]['p02']['current_table']['rows'].append(copy.deepcopy(reverse[0]))
        with self.assertRaises(ValueError): b.build_bindings(*args)

    def test_summary_retains_blockers(self):
        result=b.summarize([dict(binding(),blocking=True)])
        self.assertEqual(len(result['blocking']),1)
        for key in ('runtime_applied','issue19_complete','release_ready','automatic_fallback','blanket_deletion'):
            self.assertFalse(result[key])


if __name__=='__main__': unittest.main()
