"""実原本の陽性を先に確認し、その新区間だけへ負例を適用する。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pr16_research_story_route as m


class RouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev = ROOT/m.DEV
        cls.raw = (cls.dev/'progress.stdout.txt').read_bytes()
        cls.cold_raw = (cls.dev/'continue.stdout.txt').read_bytes()
        cls.parent = m.load((ROOT/m.PARENT).read_bytes())
        cls.first, cls.second = m.read_trace(cls.raw), m.read_trace(cls.cold_raw)
        # Every negative case depends on a working positive baseline, not a broken oracle.
        cls.positive = m.verify(cls.raw, cls.cold_raw, cls.parent, m.OUTPUT_SAVE)
        assert cls.positive['status'] == 'PASS_NATURAL_STORY_POTION_SAVE_SCOPED'

    def test_original_scoped_success(self):
        self.assertEqual(self.positive['trainer_losses'], 2)
        self.assertEqual(self.positive['trainer_victories'], 0)
        self.assertFalse(self.positive['natural_research_arrival_accepted'])
        self.assertFalse(self.positive['release_ready'])
        self.assertEqual(self.positive['screen_count'], 53)
        self.assertEqual(self.positive['transition_only_screens'], [16])

    def test_actual_commands(self):
        m.commands((self.dev/'commands.txt').read_text())
        m.commands((self.dev/'continue-commands.txt').read_text(), True)

    def test_healing_transition_not_content(self):
        raw = b'P6\n240 160\n255\n' + bytes(240*160*3)
        m.screen_bytes(raw, self.first['screens'][16], self.first['observations'][16], 'progress')
        with self.assertRaises(ValueError):
            m.screen_bytes(raw, self.first['screens'][16], self.first['observations'][16], 'continue')

    def test_nonblank_screen_format_positive(self):
        raw = b'P6\n240 160\n255\n' + b'\xff\x00\x00' + bytes(240*160*3-3)
        screen = {'screen': 0, 'frame': 0, 'sha256': m.identity(raw)['sha256']}
        m.screen_bytes(raw, screen, self.first['observations'][0], 'continue')

    def test_unknown_blank_is_rejected(self):
        raw = b'P6\n240 160\n255\n' + bytes(240*160*3)
        screen = dict(self.first['screens'][16], screen=15)
        with self.assertRaises(ValueError):
            m.screen_bytes(raw, screen, self.first['observations'][16], 'progress')

    def test_fake_transition_state_is_rejected(self):
        raw = b'P6\n240 160\n255\n' + bytes(240*160*3)
        obs = dict(self.first['observations'][16], field=True, lock=0)
        with self.assertRaises(ValueError):
            m.screen_bytes(raw, self.first['screens'][16], obs, 'progress')

    def test_bad_dimensions_are_rejected(self):
        raw = b'P6\n160 240\n255\n' + b'\xff\x00\x00' + bytes(240*160*3-3)
        with self.assertRaises(ValueError):
            m.screen_bytes(raw, dict(screen=0, sha256=m.identity(raw)['sha256']), {}, 'continue')

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaises(ValueError):
            m.read_trace(self.raw.replace(b'"host_write_barriers":7', b'"host_write_barriers":7,"host_write_barriers":7', 1))

    def test_missing_terminal_is_rejected(self):
        with self.assertRaises(ValueError):
            m.read_trace(b'\n'.join(self.raw.splitlines()[:-1])+b'\n')

    def test_injected_unknown_row_is_rejected(self):
        raw = self.raw.splitlines();raw.insert(1, b'{"write32":123}')
        with self.assertRaises(ValueError):
            m.read_trace(b'\n'.join(raw)+b'\n')

    def test_missing_screen_directory_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as name, self.assertRaises(ValueError):
            m.screens(self.first, Path(name), 'progress')

    def test_cold_command_extra_save_rejected(self):
        raw = (self.dev/'continue-commands.txt').read_text().replace('quit\n','save\nquit\n')
        with self.assertRaises(ValueError):m.commands(raw, True)

    def test_progress_missing_save_rejected(self):
        raw = (self.dev/'commands.txt').read_text().replace('save\n','')
        with self.assertRaises(ValueError):m.commands(raw)

    def test_unknown_command_rejected(self):
        raw = (self.dev/'commands.txt').read_text().replace('quit\n','warp 96 0\nquit\n')
        with self.assertRaises(ValueError):m.commands(raw)

    def test_zero_observation_reissue_rejected(self):
        raw = (self.dev/'commands.txt').read_text().replace('observe 1\n','observe 0\n')
        with self.assertRaises(ValueError):m.commands(raw)

    def test_multikey_injection_rejected(self):
        # Find a guaranteed actual key rather than depending on an exploratory movement.
        raw = 'key 3 2\n'+(self.dev/'commands.txt').read_text()
        with self.assertRaises(ValueError):m.commands(raw)


def path_set(value, path, new):
    for key in path[:-1]:value=value[key]
    value[path[-1]]=new


# The mutation field itself is the assertion target; full-record hash equality is not used.
MUTATIONS = [
    ('parent_status', 'parent', ('status',), 'UNCONFIRMED'),
    ('parent_terminal', 'parent', ('actions_completion_confirmed',), False),
    ('parent_run', 'parent', ('run_id',), 36325475402),
    ('parent_source', 'parent', ('source_head',), '0'*40),
    ('parent_artifact', 'parent', ('retained_artifact_id',), 10933499470),
    ('parent_candidate', 'parent', ('checkpoint','candidate','sha256'), '0'*64),
    ('parent_save', 'parent', ('checkpoint','save','sha256'), '0'*64),
    ('parent_runner', 'parent', ('checkpoint','executable','sha256'), '0'*64),
    ('parent_runtime', 'parent', ('checkpoint','runtime_artifact'), 1),
    ('parent_data', 'parent', ('checkpoint','data_artifact'), 1),
    ('parent_scope', 'parent', ('natural_research_arrival_accepted',), True),
    ('parent_release', 'parent', ('release_ready',), True),
    ('parent_baseline', 'parent', ('active_baseline_changed',), True),
    ('input_save', 'first', ('start','initial_save_sha256'), '0'*64),
    ('cold_save', 'second', ('start','initial_save_sha256'), '0'*64),
    ('output_rtc', 'saved', ('sha256',), '0'*64),
    ('output_size', 'saved', ('size',), 131072),
    ('progress_count', 'first', ('end','inputs'), 300),
    ('progress_frames', 'first', ('end','frames'), 31903),
    ('cold_count', 'second', ('end','inputs'), 23),
    ('cold_frames', 'second', ('end','frames'), 1941),
    ('save_receipt', 'first', ('saves',0,'after'), 4),
    ('extra_party', 'first', ('observations',42,'party_count'), 2),
    ('extra_rp', 'first', ('observations',43,'rp'), 6),
    ('extra_save', 'first', ('observations',43,'save_counter'), 3),
    ('parent_xy', 'first', ('observations',0,'xy'), [2,14]),
    ('facility_warp', 'first', ('observations',42,'map'), [96,0]),
    ('first_loss_as_win', 'first', ('observations',14,'battle_outcome'), 1),
    ('second_loss_as_win', 'first', ('observations',32,'battle_outcome'), 1),
    ('home_warp', 'first', ('observations',15,'xy'), [7,5]),
    ('mother_recovery', 'first', ('observations',17,'party_sha256'), '0'*64),
    ('second_recovery', 'first', ('observations',35,'party_sha256'), '0'*64),
    ('trainer_flags', 'first', ('observations',30,'battle_flags'), 0),
    ('detour_position', 'first', ('observations',42,'xy'), [27,8]),
    ('item_facing', 'first', ('observations',43,'facing'), 2),
    ('item_not_scripted', 'first', ('observations',43,'lock'), 0),
    ('progress_bag_image', 'first', ('screens',45,'sha256'), '0'*64),
    ('cold_bag_image', 'second', ('screens',2,'sha256'), '0'*64),
    ('bag_callback', 'second', ('observations',2,'callback2'), 0),
    ('healing_image', 'first', ('screens',16,'sha256'), '0'*64),
    ('healing_frame', 'first', ('screens',16,'frame'), 10081),
    ('final_lock', 'first', ('observations',48,'lock'), 1),
    ('final_xy', 'first', ('observations',48,'xy'), [1,14]),
    ('cold_party_bytes', 'second', ('observations',0,'party_sha256'), '0'*64),
    ('cold_flash_bytes', 'second', ('observations',0,'flash_sha256'), '0'*64),
    ('cold_ledger_bytes', 'second', ('observations',0,'ledger_sha256'), '0'*64),
    ('cold_save_counter', 'second', ('observations',0,'save_counter'), 2),
    ('cold_rp', 'second', ('observations',0,'rp'), 1),
    ('cold_xy', 'second', ('observations',0,'xy'), [1,14]),
    ('cold_transient_flags', 'second', ('observations',0,'battle_flags'), 12),
    ('cold_transient_outcome', 'second', ('observations',0,'battle_outcome'), 2),
    ('cold_exit_lock', 'second', ('observations',3,'lock'), 1),
]


def mutation_test(which, path, value):
    def test(self):
        args = dict(first=copy.deepcopy(self.first),second=copy.deepcopy(self.second),
                    parent=copy.deepcopy(self.parent),saved=copy.deepcopy(m.OUTPUT_SAVE))
        path_set(args[which],path,value)
        with self.assertRaises(ValueError):m.retained(**args)
    return test


for name, which, path, value in MUTATIONS:
    setattr(RouteTests, 'test_reject_'+name, mutation_test(which, path, value))


def terminal_test(key, value):
    def test(self):
        rows=m.load_rows(self.raw);rows[-1][key]=value
        with self.assertRaises(ValueError):
            m.read_trace(('\n'.join(json.dumps(x) for x in rows)+'\n').encode())
    return test


for key,value in [('warnings_errors',1),('host_write_barriers',6),('guarded_host_writes',1),
                  ('fixture_calls',1),('natural_research_arrival_accepted',True),('warnings_errors',False)]:
    setattr(RouteTests,'test_terminal_'+key+'_'+str(value),terminal_test(key,value))

if __name__ == '__main__':unittest.main()
