import random
import heapq
import numpy as np
from gdpc import Block
from biome_palette import get_biome_palette
import build_houses

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
    ox, oz = origin
    lx, lz = x - ox, z - oz
    sx, sz = worldslice.heightmaps["MOTION_BLOCKING_NO_LEAVES"].shape
    if not (0 <= lx < sx and 0 <= lz < sz): return False
    
    y = int(worldslice.heightmaps["MOTION_BLOCKING_NO_LEAVES"][lx, lz])
    for dy in range(0, 3):
        try:
            block = worldslice.getBlock((lx, y - dy, lz))
            if "water" in block.id or "kelp" in block.id or "seagrass" in block.id:
                return True
        except Exception:
            pass
    return False

def slope_in_area(heightmap, origin, x, z, width=5, depth=5):
    heights = []
    for dx in range(width):
        for dz in range(depth):
            h = get_height(heightmap, x + dx, z + dz, origin)
            if h is not None: heights.append(h)
    if not heights: return 999
    return max(heights) - min(heights)

def is_valid_house_site(worldslice, heightmap, origin, x, z, width=5, depth=5, max_slope=2):
    if slope_in_area(heightmap, origin, x, z, width, depth) > max_slope: return False
    for dx in range(0, width, 2):
        for dz in range(0, depth, 2):
            if is_water_ws(worldslice, x + dx, z + dz, origin): return False
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
            if not valid(nxt) or nxt in closed: continue

            h1 = height(current.pos)
            h2 = height(nxt)
            slope_cost = abs(h1 - h2) * 4
            water_cost = water_penalty if (worldslice and is_water_ws(worldslice, nxt[0], nxt[1], origin)) else 0

            cost = 1 + slope_cost + water_cost
            heapq.heappush(open_list, Node(nxt, current.g + cost, heuristic(nxt, goal), current))
    return []

# ─────────────────────────────────────────────
#  Layout & Tracking
# ─────────────────────────────────────────────

def footprint(hx, hz, width=5, depth=5, padding=2):
    cells = set()
    for dx in range(-padding, width + padding):
        for dz in range(-padding, depth + padding):
            cells.add((hx + dx, hz + dz))
    return cells

def overlaps_any(hx, hz, placed_footprints, width=5, depth=5, padding=2):
    fp = footprint(hx, hz, width, depth, padding)
    for existing in placed_footprints:
        if fp & existing: return True
    return False

def facing_toward(hx, hz, cx, cz):
    dx, dz = cx - hx, cz - hz
    if abs(dx) >= abs(dz): return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"

def place_houses_radial(worldslice, heightmap, origin, center, num_houses=10, min_radius=10, max_radius=30, max_attempts=200):
    cx, cz = center
    placed_footprints = []
    houses = []
    attempts = 0

    while len(houses) < num_houses and attempts < max_attempts:
        attempts += 1
        angle = random.uniform(0, 2 * 3.14159)
        radius = random.uniform(min_radius, max_radius)
        hx = int(cx + radius * np.cos(angle))
        hz = int(cz + radius * np.sin(angle))
        

        depth = random.choice([4, 6])

        if not in_bounds(hx, hz, heightmap, origin) or not in_bounds(hx + 4, hz + depth, heightmap, origin): continue
        if not is_valid_house_site(worldslice, heightmap, origin, hx, hz, depth=depth): continue
        if overlaps_any(hx, hz, placed_footprints, depth=depth): continue

        hy = get_height(heightmap, hx, hz, origin)
        facing = facing_toward(hx, hz, cx, cz)
        
        houses.append((hx, hy, hz, depth, facing))
        placed_footprints.append(footprint(hx, hz, depth=depth))

    return houses, placed_footprints

def find_farm_site(worldslice, heightmap, origin, center, placed_footprints, farm_w=9, farm_d=9, max_attempts=300, max_slope=2, min_r=0, max_r=None):
    ox, oz = origin
    sx, sz = heightmap.shape
    if max_r is None: max_r = sx - farm_w

    for _ in range(max_attempts):
        fx = ox + random.randint(min_r, max_r)
        fz = oz + random.randint(min_r, sz - farm_d - 1)
        
        if not in_bounds(fx + farm_w, fz + farm_d, heightmap, origin): continue
        if not is_valid_house_site(worldslice, heightmap, origin, fx, fz, width=farm_w, depth=farm_d, max_slope=max_slope): continue
        if overlaps_any(fx, fz, placed_footprints, width=farm_w, depth=farm_d, padding=2): continue
        
        fy = get_height(heightmap, fx, fz, origin)
        if fy is not None: return fx, int(fy), fz
    return None

def build_path_network(center, houses, farms, heightmap, origin, worldslice):
    road_tiles = set()
    cx, cz = center
    
    # Path to house DOORS rather than house corners
    for hx, hy, hz, depth, facing in houses:
        door_x, door_z = build_houses.get_door_outside_pos(hx, hz, depth, facing)
        path = astar((door_x, door_z), (cx, cz), heightmap, origin, worldslice)
        for tile in path: road_tiles.add(tile)
        
    for fx, fy, fz in farms:
        path = astar((fx, fz), center, heightmap, origin, worldslice)
        for tile in path: road_tiles.add(tile)
        
    return road_tiles

def place_road(editor, heightmap, origin, road_tiles):
    for (x, z) in road_tiles:
        y = get_height(heightmap, x, z, origin)
        if y is None: continue
        

        editor.placeBlock((x, y-1, z), Block("dirt_path"))
        editor.placeBlock((x, y, z), Block("air"))
        editor.placeBlock((x, y+1, z), Block("air"))

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
    if center is None: center = (ox + sx // 2, oz + sz // 2)

    # 2. Houses
    houses, placed_footprints = place_houses_radial(worldslice, heightmap, origin, center, num_houses=num_houses)

    # 3. Farms
    farms = []
    for _ in range(num_farms):
        site = find_farm_site(worldslice, heightmap, origin, center, placed_footprints)
        if site is None:
            site = find_farm_site(worldslice, heightmap, origin, center, placed_footprints, min_r=3, max_r=40, max_slope=3, max_attempts=300)
        if site:
            farms.append(site)
            fx, fy, fz = site
            placed_footprints.append(footprint(fx, fz, width=9, depth=9))

    # 4. Paths
    road_tiles = build_path_network(center, houses, farms, heightmap, origin, worldslice)
    place_road(editor, heightmap, origin, road_tiles)

    # 5. Build Structures
    palette = get_biome_palette("Plains") # Could detect biome dynamically
    
    for hx, hy, hz, depth, facing in houses:
        if random.random() < 0.4:
            build_houses.build_2fhouse(editor, hx, hy, hz, depth, palette, facing)
        else:
            build_houses.build_1fhouse(editor, hx, hy, hz, depth, 4, palette, facing)
            
    for fx, fy, fz in farms:
        build_houses.build_farm(editor, fx, fy, fz, width=9, depth=9)
        
    print(f"Village generation complete. {len(houses)} houses, {len(farms)} farms.")
