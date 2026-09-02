"""最終world object集合の到達可能性と会話stanceを決定論的に扱う。

配置途中の空きマスではなく、全object確定後の占有を入力にする。NPC本体と
プレイヤーが会話に立つ隣接マスを一組で予約し、最後に入口から再BFSする。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


class WorldFinalStateError(ValueError):
    """最終配置または到達可能性の契約違反。"""


@dataclass(frozen=True)
class ConversationPlacement:
    """1体のobject tileと、通常会話に使う専用player tile。"""

    x: int
    y: int
    stance_x: int
    stance_y: int

    @property
    def object_tile(self) -> tuple[int, int]:
        return self.x, self.y

    @property
    def stance_tile(self) -> tuple[int, int]:
        return self.stance_x, self.stance_y


def neighbors(x: int, y: int) -> tuple[tuple[int, int], ...]:
    """同距離時の決定性を保つため、上・左・右・下の順で返す。"""
    return ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))


def walkable(
    blocks: Sequence[int], width: int, height: int,
    x: int, y: int, elevation: int = 3,
) -> bool:
    if not (0 <= x < width and 0 <= y < height):
        return False
    value = int(blocks[y * width + x])
    collision = (value >> 10) & 3
    tile_elevation = (value >> 12) & 0xF
    return collision == 0 and tile_elevation in {0, elevation}


def reachable_player_tiles(
    blocks: Sequence[int], width: int, height: int,
    seeds: Iterable[tuple[int, int]],
    occupied_objects: Iterable[tuple[int, int]] = (),
    *, elevation: int = 3,
) -> set[tuple[int, int]]:
    """入口から歩けるplayer tileを、最終表示objectを障害物として返す。

    入力seedはengineがplayerを配置したexact arrivalであり、door/ladder等では
    collision nibbleが非zeroでも到着そのものは成立する。到着tileだけを許容し、
    そこから先に追加するtileは通常のwalkable条件を必須にする。
    """
    blocked = set(occupied_objects)
    initial = {
        (x, y) for x, y in seeds
        if (x, y) not in blocked
        and 0 <= x < width and 0 <= y < height
    }
    reached = set(initial)
    pending = deque(sorted(initial, key=lambda point: (point[1], point[0])))
    while pending:
        x, y = pending.popleft()
        for point in neighbors(x, y):
            if (point in reached or point in blocked
                    or not walkable(blocks, width, height, *point, elevation)):
                continue
            reached.add(point)
            pending.append(point)
    return reached


def exact_reverse_entrance_seed_index(
    map_rows: Mapping[str, Mapping[str, object]],
    map_grids: Mapping[str, tuple[int, int, Sequence[int]]],
    *, elevation: int = 3,
) -> dict[str, dict[str, object]]:
    """全mapを逆引きし、局所exact incoming warp/connection seedを返す。

    単一mapのWarpEvent/MapConnectionはどちらも「そのmapから出る」行であり、
    自分自身の入口を証明しない。全catalogを入力に、foreign rowのtargetだけを
    destination側へ追加する。warpはdestination warp IDのexact座標だけ、
    connectionは方向・offset・両map寸法を使って変換できた境界tileだけである。
    ``RUNTIME_DYNAMIC_WARP`` 等はconcrete producerがないためseedにしない。

    このAPIはforeign rowの局所構造だけを証明する。new-game等のglobal rootから
    source map/triggerへ到達できることは証明せず、孤立したA↔B cycleも両側の
    local incomingとして列挙する。fresh-game global到達性を主張するcallerは、
    stateful transitionを含むrooted fixed-pointを別途通さなければならない。
    """

    keys = set(map_rows)
    if keys != set(map_grids):
        raise WorldFinalStateError(
            "map catalog/grid key sets differ"
        )
    result: dict[str, dict[str, object]] = {
        key: {
            "reachability_scope": "STRUCTURAL_EXACT_INCOMING_CANDIDATE_NOT_GLOBAL_ROOT",
            "globally_reachable_from_new_game": None,
            "seeds": set(),
            "incoming_warps": [],
            "incoming_connections": [],
            "dynamic_or_external_outgoing_warps": [],
        }
        for key in sorted(keys)
    }

    def grid(key: str) -> tuple[int, int, Sequence[int]]:
        width, height, blocks = map_grids[key]
        if width <= 0 or height <= 0 or len(blocks) != width * height:
            raise WorldFinalStateError(f"invalid map grid: {key}")
        return int(width), int(height), blocks

    warp_index: dict[str, dict[int, Mapping[str, object]]] = {}
    for key, row in map_rows.items():
        header = row.get("map_header")
        if not isinstance(header, Mapping) \
                or str(header.get("map_key")) != key:
            raise WorldFinalStateError(f"map key/header drift: {key}")
        indexed: dict[int, Mapping[str, object]] = {}
        for position, raw in enumerate(row.get("warps", ())):
            if not isinstance(raw, Mapping):
                raise WorldFinalStateError(f"invalid warp row: {key}/{position}")
            index = int(raw.get("source_warp_index", position))
            if index in indexed:
                raise WorldFinalStateError(f"duplicate warp index: {key}/{index}")
            indexed[index] = raw
        warp_index[key] = indexed

    # WarpEvent reverse edges.  The source row must at least be triggerable
    # from its tile or an adjacent walkable tile; destination collision is not
    # required because door/ladder arrivals may start on collision-bearing
    # metatiles and reachable_player_tiles handles that exact first tile.
    for source_key, row in sorted(map_rows.items()):
        source_width, source_height, source_blocks = grid(source_key)
        for position, raw in enumerate(row.get("warps", ())):
            if not isinstance(raw, Mapping):
                raise WorldFinalStateError(
                    f"invalid warp row: {source_key}/{position}"
                )
            destination_key = str(raw.get("dest_map"))
            destination_id_raw = raw.get("dest_warp_id")
            if destination_key not in keys:
                result[source_key][
                    "dynamic_or_external_outgoing_warps"
                ].append({
                    "source_warp_index": int(
                        raw.get("source_warp_index", position)
                    ),
                    "destination": destination_key,
                    "destination_warp_id": destination_id_raw,
                    "seeded": False,
                })
                continue
            try:
                destination_id = int(str(destination_id_raw), 0)
            except (TypeError, ValueError) as exc:
                raise WorldFinalStateError(
                    f"non-numeric concrete destination warp: "
                    f"{source_key}/{position}"
                ) from exc
            destination_warp = warp_index[destination_key].get(destination_id)
            if destination_warp is None:
                raise WorldFinalStateError(
                    f"destination warp missing: {source_key}/{position} -> "
                    f"{destination_key}/{destination_id}"
                )
            source_point = (int(raw["x"]), int(raw["y"]))
            source_in_bounds = (
                0 <= source_point[0] < source_width
                and 0 <= source_point[1] < source_height
            )
            source_predecessors = [
                point for point in neighbors(*source_point)
                if walkable(
                    source_blocks, source_width, source_height,
                    *point, elevation,
                )
            ]
            source_triggerable = source_in_bounds and (
                walkable(
                    source_blocks, source_width, source_height,
                    *source_point, elevation,
                ) or bool(source_predecessors)
            )
            destination_width, destination_height, _ = grid(destination_key)
            arrival = (
                int(destination_warp["x"]), int(destination_warp["y"]),
            )
            arrival_in_bounds = (
                0 <= arrival[0] < destination_width
                and 0 <= arrival[1] < destination_height
            )
            evidence = {
                "source_map": source_key,
                "source_warp_index": int(
                    raw.get("source_warp_index", position)
                ),
                "source_tile": list(source_point),
                "source_triggerable": source_triggerable,
                "source_predecessors": [list(point) for point in source_predecessors],
                "destination_map": destination_key,
                "destination_warp_id": destination_id,
                "arrival_tile": list(arrival),
                "arrival_in_bounds": arrival_in_bounds,
                "seeded": source_triggerable and arrival_in_bounds,
                "basis": "FOREIGN_WARP_ROW_EXACT_DESTINATION_WARP_ID",
            }
            result[destination_key]["incoming_warps"].append(evidence)
            if evidence["seeded"]:
                result[destination_key]["seeds"].add(arrival)

    direction_contract = {
        "down": ("HORIZONTAL", "BOTTOM", "TOP"),
        "up": ("HORIZONTAL", "TOP", "BOTTOM"),
        "left": ("VERTICAL", "LEFT", "RIGHT"),
        "right": ("VERTICAL", "RIGHT", "LEFT"),
    }
    for source_key, row in sorted(map_rows.items()):
        source_width, source_height, source_blocks = grid(source_key)
        for index, raw in enumerate(row.get("connections", ())):
            if not isinstance(raw, Mapping):
                raise WorldFinalStateError(
                    f"invalid connection row: {source_key}/{index}"
                )
            direction = str(raw.get("direction")).lower()
            if direction not in direction_contract:
                raise WorldFinalStateError(
                    f"invalid connection direction: {source_key}/{index}"
                )
            destination_key = str(raw.get("map"))
            if destination_key not in keys:
                raise WorldFinalStateError(
                    f"connection target outside catalog: "
                    f"{source_key}/{index}->{destination_key}"
                )
            offset = int(raw.get("offset", 0))
            destination_width, destination_height, destination_blocks = grid(
                destination_key
            )
            axis, source_side, destination_side = direction_contract[direction]
            candidates: list[dict[str, object]] = []
            if axis == "HORIZONTAL":
                source_y = 0 if source_side == "TOP" else source_height - 1
                destination_y = (
                    0 if destination_side == "TOP" else destination_height - 1
                )
                for source_x in range(source_width):
                    destination_x = source_x - offset
                    if not 0 <= destination_x < destination_width:
                        continue
                    source_point = (source_x, source_y)
                    arrival = (destination_x, destination_y)
                    candidates.append({
                        "source_boundary_tile": list(source_point),
                        "arrival_tile": list(arrival),
                        "source_walkable": walkable(
                            source_blocks, source_width, source_height,
                            *source_point, elevation,
                        ),
                        "arrival_walkable": walkable(
                            destination_blocks, destination_width,
                            destination_height, *arrival, elevation,
                        ),
                    })
            else:
                source_x = 0 if source_side == "LEFT" else source_width - 1
                destination_x = (
                    0 if destination_side == "LEFT" else destination_width - 1
                )
                for source_y in range(source_height):
                    destination_y = source_y - offset
                    if not 0 <= destination_y < destination_height:
                        continue
                    source_point = (source_x, source_y)
                    arrival = (destination_x, destination_y)
                    candidates.append({
                        "source_boundary_tile": list(source_point),
                        "arrival_tile": list(arrival),
                        "source_walkable": walkable(
                            source_blocks, source_width, source_height,
                            *source_point, elevation,
                        ),
                        "arrival_walkable": walkable(
                            destination_blocks, destination_width,
                            destination_height, *arrival, elevation,
                        ),
                    })
            usable = [
                item for item in candidates
                if item["source_walkable"] and item["arrival_walkable"]
            ]
            evidence = {
                "source_map": source_key,
                "connection_index": index,
                "direction": direction,
                "offset": offset,
                "destination_map": destination_key,
                "arrival_tiles": [item["arrival_tile"] for item in usable],
                "coordinate_evidence": candidates,
                "basis": (
                    "FOREIGN_CONNECTION_ROW_DIRECTION_OFFSET_AND_"
                    "BOTH_MAP_DIMENSIONS"
                ),
            }
            result[destination_key]["incoming_connections"].append(evidence)
            result[destination_key]["seeds"].update(
                tuple(map(int, item["arrival_tile"])) for item in usable
            )
    for row in result.values():
        row["incoming_warps"].sort(
            key=lambda item: (item["source_map"], item["source_warp_index"])
        )
        row["incoming_connections"].sort(
            key=lambda item: (item["source_map"], item["connection_index"])
        )
    return result


def entrance_seeds(
    map_row: Mapping[str, object], width: int, height: int,
    blocks: Sequence[int], *, elevation: int = 3,
) -> set[tuple[int, int]]:
    """歴史Stage35再生成専用のlegacy単一map seedを返す。

    このAPIはpublished Stage35のbyte再現互換だけに残す。outgoing rowしか
    入力されずproduct入口の証明にはならないため、Stage61以降の生成/gateは
    ``exact_reverse_entrance_seed_index`` またはROM exact producer解析を使う。
    """

    seeds: set[tuple[int, int]] = set()
    warps = map_row.get("warps", ())
    if isinstance(warps, Iterable):
        for raw in warps:
            if not isinstance(raw, Mapping):
                continue
            x, y = int(raw["x"]), int(raw["y"])
            if walkable(blocks, width, height, x, y, elevation):
                seeds.add((x, y))
            for point in neighbors(x, y):
                if walkable(blocks, width, height, *point, elevation):
                    seeds.add(point)
    connections = map_row.get("connections", ())
    if isinstance(connections, Sequence) and connections:
        for x in range(width):
            for y in (0, height - 1):
                if walkable(blocks, width, height, x, y, elevation):
                    seeds.add((x, y))
        for y in range(height):
            for x in (0, width - 1):
                if walkable(blocks, width, height, x, y, elevation):
                    seeds.add((x, y))
    return seeds


def allocate_objects_with_stances(
    blocks: Sequence[int], width: int, height: int,
    seeds: Iterable[tuple[int, int]],
    fixed_objects: Iterable[tuple[int, int]],
    origins: Sequence[tuple[int, int]],
    *, reserved_tiles: Iterable[tuple[int, int]] = (), elevation: int = 3,
) -> list[ConversationPlacement]:
    """全targetを同時条件で配置し、最終BFSで各stanceを証明する。

    候補はoriginからのManhattan距離、y、x、stance順で安定sortする。
    greedyで詰まった場合も全候補をbacktrackするため、中央十字のような後置
    objectによる囲い込みを合格させない。
    """
    if width <= 0 or height <= 0 or len(blocks) != width * height:
        raise WorldFinalStateError("blockdata dimensions differ")
    fixed = set(fixed_objects)
    reserved = set(reserved_tiles) | fixed
    seed_set = set(seeds)
    if not seed_set:
        raise WorldFinalStateError("map has no physical entrance seed")
    terrain_component = reachable_player_tiles(
        blocks, width, height, seed_set, fixed, elevation=elevation,
    )
    if not terrain_component:
        raise WorldFinalStateError("entrance component is empty")

    candidate_rows: list[list[ConversationPlacement]] = []
    for origin_x, origin_y in origins:
        rows: list[tuple[int, int, int, int, ConversationPlacement]] = []
        for y in range(height):
            for x in range(width):
                object_tile = (x, y)
                if object_tile in reserved or object_tile not in terrain_component:
                    continue
                for stance_order, (sx, sy) in enumerate(neighbors(x, y)):
                    stance = (sx, sy)
                    if stance in reserved or stance == object_tile \
                            or stance not in terrain_component:
                        continue
                    placement = ConversationPlacement(x, y, sx, sy)
                    rows.append((
                        abs(x - origin_x) + abs(y - origin_y), y, x,
                        stance_order, placement,
                    ))
        rows.sort(key=lambda row: row[:4])
        candidate_rows.append([row[4] for row in rows])
    if any(not rows for rows in candidate_rows):
        raise WorldFinalStateError("at least one target has no object/stance pair")

    assignments: list[ConversationPlacement] = []
    object_tiles = set(fixed)
    reserved_stances: set[tuple[int, int]] = set()

    def search(index: int) -> bool:
        if index == len(candidate_rows):
            reached = reachable_player_tiles(
                blocks, width, height, seed_set, object_tiles,
                elevation=elevation,
            )
            return all(item.stance_tile in reached for item in assignments)
        for candidate in candidate_rows[index]:
            object_tile = candidate.object_tile
            stance_tile = candidate.stance_tile
            if (object_tile in object_tiles or object_tile in reserved_stances
                    or stance_tile in object_tiles
                    or stance_tile in reserved_stances):
                continue
            object_tiles.add(object_tile)
            reserved_stances.add(stance_tile)
            assignments.append(candidate)
            # 早期枝刈り: 現在までのstanceが、現在までのobject集合で到達可能。
            reached = reachable_player_tiles(
                blocks, width, height, seed_set, object_tiles,
                elevation=elevation,
            )
            viable = all(item.stance_tile in reached for item in assignments)
            if viable and search(index + 1):
                return True
            assignments.pop()
            reserved_stances.remove(stance_tile)
            object_tiles.remove(object_tile)
        return False

    if not search(0):
        raise WorldFinalStateError(
            f"no final-state placement for {len(origins)} conversation objects"
        )
    return list(assignments)


def audit_conversation_placements(
    blocks: Sequence[int], width: int, height: int,
    seeds: Iterable[tuple[int, int]], fixed_objects: Iterable[tuple[int, int]],
    placements: Sequence[ConversationPlacement], *,
    reserved_tiles: Iterable[tuple[int, int]] = (), elevation: int = 3,
) -> dict[str, object]:
    """生成後gate。重複、隣接、最終到達を同じ入力から再計算する。"""
    fixed = set(fixed_objects)
    reserved = set(reserved_tiles) | fixed
    objects = fixed | {item.object_tile for item in placements}
    stances = [item.stance_tile for item in placements]
    reached = reachable_player_tiles(
        blocks, width, height, seeds, objects, elevation=elevation,
    )
    duplicate_objects = len(objects) != len(fixed) + len(placements)
    duplicate_stances = len(stances) != len(set(stances))
    reserved_conflicts = [
        index for index, item in enumerate(placements)
        if item.object_tile in reserved or item.stance_tile in reserved
    ]
    bad_adjacency = [
        index for index, item in enumerate(placements)
        if item.stance_tile not in neighbors(*item.object_tile)
    ]
    unreachable = [
        index for index, item in enumerate(placements)
        if item.stance_tile not in reached
    ]
    status = not duplicate_objects and not duplicate_stances \
        and not reserved_conflicts \
        and not bad_adjacency and not unreachable
    return {
        "status": "PASS" if status else "FAIL",
        "object_count": len(placements),
        "reachable_player_tile_count": len(reached),
        "duplicate_object": duplicate_objects,
        "duplicate_stance": duplicate_stances,
        "reserved_conflict_indices": reserved_conflicts,
        "bad_adjacency_indices": bad_adjacency,
        "unreachable_indices": unreachable,
        "placements": [
            {
                "object": list(item.object_tile),
                "stance": list(item.stance_tile),
            }
            for item in placements
        ],
    }
