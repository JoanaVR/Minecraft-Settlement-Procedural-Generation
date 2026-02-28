import random
import heapq
import numpy as np
from gdpc import Editor, Block
from gdpc.geometry import placeCuboid
import build_houses
import math


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def get_height(heightmap, x, z, origin):
    ox, oz = origin
    lx, lz = x - ox, z - oz
    if 0 <= lx < heightmap.shape[0] and 0 <= lz < heightmap.shape[1]:
        return int(heightmap[lx, lz])
    return None


def in_bounds(x, z, heightmap, origin):
    ox, oz = origin
    lx, lz = x - ox, z - oz
    return 0 <= lx < heightmap.shape[0] and 0 <= lz < heightmap.shape[1]


def is_water_ws(worldslice, x, z, origin):
    """Check surface block for water using local WorldSlice data (no HTTP)."""
    ox, oz = origin
    lx, lz = x - ox, z - oz
    sx, sz = worldslice.heightmaps["MOTION_BLOCKING_NO_LEAVES"].shape
    if not (0 <= lx < sx and 0 <= lz < sz):
        return False
    y = int(worldslice.heightmaps["MOTION_BLOCKING_NO_LEAVES"][lx, lz])
    # Check the block at and just below the surface
    for dy in range(0, 3):
        try:
            block = worldslice.getBlock((lx, y - dy, lz))
            if block.id in ("minecraft:water", "minecraft:flowing_water",
                            "minecraft:seagrass", "minecraft:tall_seagrass",
                            "minecraft:kelp", "minecraft:kelp_plant"):
                return True
        except Exception:
            pass
    return False


def slope_in_area(heightmap, origin, x, z, width=5, depth=5):
    """Return max height difference within a rectangular footprint."""
    heights = []
    for dx in range(width):
        for dz in range(depth):
            h = get_height(heightmap, x + dx, z + dz, origin)
            if h is not None:
                heights.append(h)
    if not heights:
        return 999
    return max(heights) - min(heights)


def is_valid_house_site(worldslice, heightmap, origin, x, z,
                         width=5, depth=5, max_slope=2):
    if slope_in_area(heightmap, origin, x, z, width, depth) > max_slope:
        return False
    for dx in range(0, width, 2):
        for dz in range(0, depth, 2):
            if is_water_ws(worldslice, x + dx, z + dz, origin):
                return False
    return True


# ─────────────────────────────────────────────
#  A* path-finder
# ─────────────────────────────────────────────

class Node:
    def __init__(self, pos, g=0, h=0, parent=None):
        self.pos = pos
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(start, goal, heightmap, origin, worldslice=None, water_penalty=50):
    ox, oz = origin
    sx, sz = heightmap.shape
    open_list = []
    closed = set()
    heapq.heappush(open_list, Node(start, 0, heuristic(start, goal)))
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def valid(pos):
        lx, lz = pos[0] - ox, pos[1] - oz
        return 0 <= lx < sx and 0 <= lz < sz

    def height(pos):
        lx, lz = pos[0] - ox, pos[1] - oz
        return int(heightmap[lx, lz])

    while open_list:
        current = heapq.heappop(open_list)
        if current.pos == goal:
            path = []
            while current:
                path.append(current.pos)
                current = current.parent
            return path[::-1]

        closed.add(current.pos)
        for dx, dz in directions:
            nxt = (current.pos[0] + dx, current.pos[1] + dz)
            if not valid(nxt) or nxt in closed:
                continue

            h1 = height(current.pos)
            h2 = height(nxt)
            slope_cost = abs(h1 - h2) * 4

            water_cost = 0
            if worldslice is not None and is_water_ws(worldslice, nxt[0], nxt[1], origin):
                water_cost = water_penalty

            cost = 1 + slope_cost + water_cost
            heapq.heappush(open_list, Node(nxt, current.g + cost,
                                           heuristic(nxt, goal), current))
    return []


# ─────────────────────────────────────────────
#  Footprint / collision tracking
# ─────────────────────────────────────────────

def footprint(hx, hz, width=5, depth=5, padding=2):
    """Return all (x,z) cells occupied by a house + padding."""
    cells = set()
    for dx in range(-padding, width + padding):
        for dz in range(-padding, depth + padding):
            cells.add((hx + dx, hz + dz))
    return cells


def overlaps_any(hx, hz, placed_footprints, width=5, depth=5, padding=2):
    fp = footprint(hx, hz, width, depth, padding)
    for existing in placed_footprints:
        if fp & existing:
            return True
    return False


# ─────────────────────────────────────────────
#  House placement – radial scatter
# ─────────────────────────────────────────────

def facing_toward(hx, hz, cx, cz):
    """Return the facing that points the door toward the village centre."""
    dx, dz = cx - hx, cz - hz
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def place_houses_radial(worldslice, heightmap, origin, center, num_houses=10,
                         min_radius=10, max_radius=30, max_attempts=200):
    cx, cz = center
    placed_footprints = []
    houses = []
    attempts = 0

    while len(houses) < num_houses and attempts < max_attempts:
        attempts += 1
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(min_radius, max_radius)
        hx = int(cx + radius * math.cos(angle))
        hz = int(cz + radius * math.sin(angle))

        if not in_bounds(hx, hz, heightmap, origin):
            continue
        if not in_bounds(hx + 4, hz + 4, heightmap, origin):
            continue
        if not is_valid_house_site(worldslice, heightmap, origin, hx, hz):
            continue
        if overlaps_any(hx, hz, placed_footprints):
            continue

        hy = get_height(heightmap, hx, hz, origin)
        facing = facing_toward(hx, hz, cx, cz)
        houses.append((hx, hy, hz, facing))
        placed_footprints.append(footprint(hx, hz))

    return houses


# ─────────────────────────────────────────────
#  Farm placement
# ─────────────────────────────────────────────

def find_farm_site(worldslice, heightmap, origin, center, placed_footprints,
                   farm_w=9, farm_d=9, max_attempts=300, max_slope=2):
    import math
    ox, oz = origin
    sx, sz = heightmap.shape
    
    for _ in range(max_attempts):
        # Pick anywhere in the build area randomly
        fx = ox + random.randint(0, sx - farm_w - 1)
        fz = oz + random.randint(0, sz - farm_d - 1)
        
        if not in_bounds(fx + farm_w, fz + farm_d, heightmap, origin):
            continue
        if not is_valid_house_site(worldslice, heightmap, origin, fx, fz,
                                   width=farm_w, depth=farm_d, max_slope=max_slope):
            continue
        if overlaps_any(fx, fz, placed_footprints, width=farm_w, depth=farm_d, padding=2):
            continue
        
        fy = get_height(heightmap, fx, fz, origin)
        if fy is None:
            continue
        return fx, int(fy), fz
    
    print("WARNING: Could not place farm")
    return None

# ─────────────────────────────────────────────
#  Path network
# ─────────────────────────────────────────────

def build_path_network(center, houses, heightmap, origin, worldslice):
    road_tiles = set()
    cx, cz = center
    for hx, hy, hz, facing in houses:
        path = astar((hx, hz), (cx, cz), heightmap, origin, worldslice)
        for tile in path:
            road_tiles.add(tile)
    return road_tiles


# ─────────────────────────────────────────────
#  Road surface placement
# ─────────────────────────────────────────────

def place_road(editor, heightmap, origin, road_tiles):
    """Replace surface blocks on road tiles with gravel/stone path."""
    for (x, z) in road_tiles:
        y = get_height(heightmap, x, z, origin)
        if y is None:
            continue
        editor.placeBlock((x, y-1, z), Block("dirt_path"))
        # editor.placeBlock((x, y, z), Block("gravel"))
        # editor.placeBlock((x, y - 1, z), Block("stone"))


# ─────────────────────────────────────────────
#  Master generate function
# ─────────────────────────────────────────────

def generate_village(editor, buildArea, heightmap, worldslice, num_houses=10, num_farms=1):
    origin = (buildArea.offset.x, buildArea.offset.z)
    ox, oz = origin
    sx, sz = heightmap.shape
    # 1. Village centre
    center = None
    for _ in range(100):
        cx = ox + random.randint(sx // 4, 3 * sx // 4)
        cz = oz + random.randint(sz // 4, 3 * sz // 4)
        if is_valid_house_site(worldslice, heightmap, origin, cx, cz, max_slope=2):
            center = (cx, cz)
            break
    if center is None:
        center = (ox + sx // 2, oz + sz // 2)
    print(f"Village centre: {center}")
    # 2. Houses
    houses = place_houses_radial(worldslice, heightmap, origin, center,
                                  num_houses=num_houses)
    print(f"Placed {len(houses)} houses")

    # 3. Build footprints list from placed houses          ← ADD THIS
    placed_footprints = [footprint(hx, hz) for hx, hy, hz, facing in houses]


    # 4. Farms - guarantee at least one
    farms = []
    for _ in range(num_farms):
        # First try with strict settings
        site = find_farm_site(worldslice, heightmap, origin, center, placed_footprints)
        
        # If that fails, retry with very relaxed settings
        if site is None:
            print("Farm placement failed with strict settings, retrying relaxed...")
            site = find_farm_site(worldslice, heightmap, origin, center, 
                                placed_footprints, min_r=3, max_r=40, 
                                max_slope=3, max_attempts=300)
    
    if site:
        farms.append(site)
        fx, fy, fz = site
        placed_footprints.append(footprint(fx, fz, width=9, depth=9))
    else:
        print("WARNING: Could not place farm after retrying")

    # 5. Paths
    road_tiles = build_path_network(center, houses, heightmap, origin, worldslice)
    for fx, fy, fz in farms:
        path = astar((fx, fz), center, heightmap, origin, worldslice)
        for tile in path:
            road_tiles.add(tile)
    # 6. Build
    place_road(editor, heightmap, origin, road_tiles)
    for hx, hy, hz, facing in houses:
        wall = Block("oak_planks")
        floor = Block("oak_planks")
        depth = random.choice([4, 5, 6])
        if random.random() < 0.4:
            build_houses.build_2fhouse(editor, hx, hy, hz, depth, 4, wall, floor, facing)
        else:
            build_houses.build_1fhouse(editor, hx, hy, hz, depth, 4, wall, floor, facing)
    for fx, fy, fz in farms:
        build_houses.build_farm(editor, fx, fy, fz, width=9, depth=9)
    print("Village generation complete.")
