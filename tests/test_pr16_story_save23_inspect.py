"""新しい静的経路選択だけ。ROM/native/既受入fixtureを再実行しない。"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_story_save23_inspect as m


def view(rows):
    return dict(width=len(rows[0]), height=len(rows), collision_grid=rows)


class CavePathTests(unittest.TestCase):
    def test_shortest_ordinary_path(self):
        self.assertEqual(m.static_path(view(['W..', '##.', '..W']), [0,0], [2,2]),
                         [[0,0],[1,0],[2,0],[2,1],[2,2]])
    def test_no_intermediate_warp(self):
        self.assertIsNone(m.static_path(view(['WWW']), [0,0], [2,0]))
    def test_no_object_crossing(self):
        self.assertIsNone(m.static_path(view(['.O.']), [0,0], [2,0]))
    def test_no_wall_crossing(self):
        self.assertIsNone(m.static_path(view(['.#.']), [0,0], [2,0]))
    def test_same_start_end(self):
        self.assertEqual(m.static_path(view(['W']), [0,0], [0,0]), [[0,0]])
    def test_bounded_grid(self):
        with self.assertRaises(ValueError):m.checked_grid(dict(width=True,height=1,collision_grid=['.']))
    def test_wrong_row_count(self):
        with self.assertRaises(ValueError):m.checked_grid(dict(width=1,height=2,collision_grid=['.']))
    def test_unknown_collision(self):
        with self.assertRaises(ValueError):m.static_path(view(['.?']), [0,0], [1,0])
    def test_short_row(self):
        with self.assertRaises(ValueError):m.checked_grid(view(['..','.']))
    def test_outside_endpoint(self):
        with self.assertRaises(ValueError):m.static_path(view(['.']), [0,0], [1,0])
    def test_boolean_coordinate(self):
        with self.assertRaises(ValueError):m.static_path(view(['..']), [False,0], [1,0])
    def test_blocked_endpoint(self):
        with self.assertRaises(ValueError):m.static_path(view(['.#']), [0,0], [1,0])
    def test_wrong_map_rejected(self):
        with self.assertRaises(ValueError):m.route_options(dict(map=[3,21]))
    def test_entrance_not_replayed(self):
        v=view(['.....']*6+['....W']);v.update(map=[1,36],warps=[dict(id=1,xy=[4,6],target_map=[3,21])])
        self.assertEqual(m.route_options(v), [])


if __name__ == '__main__':unittest.main()
