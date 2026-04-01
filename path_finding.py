import random
import heapq
import math
import numpy as np
from gdpc import Block
from biome_palette import get_palette
import build_houses

#  Helpers & Terrain Evaluation

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

# Increased max_slope to allow adaptable hill generation
def is_valid_site(worldslice, heightmap, origin, x, z, width=5, depth=5, max_slope=15):
    if not in_bounds(x, z, heightmap, origin) or not in_bounds(x + width, z + depth, heightmap, origin):
        return False
    if slope_in_area(heightmap, origin, x, z, width, depth) > max_slope: 
        return False
    for dx in range(0, width, 2):
        for dz in range(0, depth, 2):
            if is_water_ws(worldslice, x + dx, z + dz, origin): return False
    return True

def is_build_area_wholly_water(worldslice, heightmap, origin, sample_step=10):
    """Check if the entire build area is water by sampling points."""
    ox, oz = origin
    sx, sz = heightmap.shape
    for lx in range(0, sx, sample_step):
        for lz in range(0, sz, sample_step):
            x, z = ox + lx, oz + lz
            if not is_water_ws(worldslice, x, z, origin):
                return False
    return True

#  Footprint Management

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

#  Algorithm 1: A* Path-finder (8-Way Adaptive)

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
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def astar_to_network(start, existing_network, heightmap, origin, worldslice=None, water_penalty=50, strict_buildings=None):
    if not existing_network: return []
    if start in existing_network: return [start]
    if strict_buildings is None: strict_buildings = set()

    ox, oz = origin
    sx, sz = heightmap.shape
    closest_goal = min(existing_network, key=lambda p: heuristic(start, p))

    open_list = []
    closed = set()
    heapq.heappush(open_list, Node(start, 0, heuristic(start, closest_goal)))
    
    directions = [
        (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
    ]

    def valid(pos):
        lx, lz = pos[0] - ox, pos[1] - oz
        return 0 <= lx < sx and 0 <= lz < sz

    while open_list:
        current = heapq.heappop(open_list)
        if current.pos in existing_network:
            path = []
            while current:
                path.append(current.pos)
                current = current.parent
            return path[::-1]

        closed.add(current.pos)
        for dx, dz, move_cost in directions:
            nxt = (current.pos[0] + dx, current.pos[1] + dz)
            
            if not valid(nxt) or nxt in closed or nxt in strict_buildings: continue

            if worldslice and is_water_ws(worldslice, nxt[0], nxt[1], origin):
                continue  
            
            h1 = get_height(heightmap, current.pos[0], current.pos[1], origin)
            h2 = get_height(heightmap, nxt[0], nxt[1], origin)

            slope_cost = abs(h1 - h2) * 2
            water_cost = water_penalty if (worldslice and is_water_ws(worldslice, nxt[0], nxt[1], origin)) else 0

            cost = move_cost + slope_cost + water_cost
            heapq.heappush(open_list, Node(nxt, current.g + cost, heuristic(nxt, closest_goal), current))
            
    return []

#  Algorithm 2: Minecraft Jigsaw Layout Generator

def generate_layout(worldslice, heightmap, origin, num_houses, num_farms):
    ox, oz = origin
    sx, sz = heightmap.shape
    
    center = None
    for _ in range(100):
        cx = ox + random.randint(sx // 4, 3 * sx // 4)
        cz = oz + random.randint(sz // 4, 3 * sz // 4)
        if is_valid_site(worldslice, heightmap, origin, cx-3, cz-3, 7, 7, max_slope=15):
            center = (cx, cz)
            break
            
    if center is None:
        print("No valid center found for village, aborting layout generation.")
        return [], [], set(), None, set()  

    road_tiles = set()
    houses = []
    farms = []
    placed_footprints = []
    exact_building_tiles = set() 
    

    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if math.hypot(dx, dz) <= 3:
                tx, tz = cx + dx, cz + dz
                if not is_water_ws(worldslice, tx, tz, origin):
                    road_tiles.add((tx, tz))
                
    well_fp = footprint(cx-2, cz-2, 5, 5, padding=1)
    placed_footprints.append(well_fp)
    exact_building_tiles.update(footprint(cx-2, cz-2, 5, 5, padding=0))
    
    queue = [
        (cx, cz - 3, 0, -1, random.randint(15, 30)), # North
        (cx, cz + 3, 0, 1, random.randint(15, 30)),  # South
        (cx + 3, cz, 1, 0, random.randint(15, 30)),  # East
        (cx - 3, cz, -1, 0, random.randint(15, 30))  # West
    ]
    
    target_buildings = num_houses + num_farms
    buildings_placed = 0
    branches = 0
    max_branches = 20 
    
    while queue and buildings_placed < target_buildings:
        rx, rz, dx, dz, length = queue.pop(0)
        
        for step in range(length):
            if step > 2 and random.random() < 0.15:
                shift_dx, shift_dz = -dz, dx 
                if random.random() < 0.5: shift_dx, shift_dz = -shift_dx, -shift_dz
                rx += shift_dx
                rz += shift_dz
            else:
                rx += dx
                rz += dz
            
            if not in_bounds(rx, rz, heightmap, origin): break
            if is_water_ws(worldslice, rx, rz, origin): break   
            road_tiles.add((rx, rz))

            if step % 6 == 0 and step > 3:
                is_farm = (len(farms) < num_farms) and (random.random() < 0.3 or len(houses) >= num_houses)
                width = 9 if is_farm else 5
                depth = 9 if is_farm else random.choice([4, 6])
                
                sides = []
                if dx == 0:
                    sides = [
                        (rx + 2, rz - depth//2, "west"),        
                        (rx - width - 1, rz - depth//2, "east")   
                    ]
                else:      
                    sides = [
                        (rx - width//2, rz + 2, "north"),         
                        (rx - width//2, rz - depth - 1, "south")  
                    ]
                    
                random.shuffle(sides)
                for hx, hz, facing in sides:
                    if not in_bounds(hx, hz, heightmap, origin) or not in_bounds(hx+width, hz+depth, heightmap, origin):
                        continue
                        

                    if is_valid_site(worldslice, heightmap, origin, hx, hz, width, depth, max_slope=15):
                        if not overlaps_any(hx, hz, placed_footprints, width, depth, padding=2):
                            

                            if is_farm:
                                hy = get_height(heightmap, hx + width//2, hz + depth//2, origin)
                                farms.append((hx, hy, hz))
                            else:
                                door_x, door_z = build_houses.get_door_outside_pos(hx, hz, depth, facing)
                                door_y = get_height(heightmap, door_x, door_z, origin)
                                hy = door_y if door_y is not None else get_height(heightmap, hx, hz, origin)
                                houses.append((hx, hy, hz, depth, facing))
                                
                            placed_footprints.append(footprint(hx, hz, width, depth, padding=2))
                            exact_building_tiles.update(footprint(hx, hz, width, depth, padding=0))
                            buildings_placed += 1
                            
                            if not is_farm:
                                door_x, door_z = build_houses.get_door_outside_pos(hx, hz, depth, facing)
                                path = astar_to_network((door_x, door_z), road_tiles, heightmap, origin, worldslice, strict_buildings=exact_building_tiles)
                                road_tiles.update(path)
                            else:
                                path = astar_to_network((hx + 4, hz - 1), road_tiles, heightmap, origin, worldslice, strict_buildings=exact_building_tiles)
                                road_tiles.update(path)
                            break
                            
        if buildings_placed < target_buildings and branches < max_branches:
            branches += 2
            if dx == 0: 
                queue.append((rx, rz, 1, 0, random.randint(10, 20)))
                queue.append((rx, rz, -1, 0, random.randint(10, 20)))
            else:       
                queue.append((rx, rz, 0, 1, random.randint(10, 20)))
                queue.append((rx, rz, 0, -1, random.randint(10, 20)))
                
    return houses, farms, road_tiles, center, exact_building_tiles

def thicken_path_network(road_tiles, worldslice, heightmap, origin, exact_building_tiles):
    """Expands paths organically, respecting terrain slopes and building walls."""
    thick_roads = set()

    for rx, rz in road_tiles:
        if is_water_ws(worldslice, rx, rz, origin):
            continue
        thick_roads.add((rx, rz))
        is_center_water = is_water_ws(worldslice, rx, rz, origin)
        center_h = get_height(heightmap, rx, rz, origin)

        for dx, dz in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]:
            nx, nz = rx + dx, rz + dz
            
            if (nx, nz) in exact_building_tiles: continue
            if is_water_ws(worldslice, nx, nz, origin): continue
            if not is_center_water and is_water_ws(worldslice, nx, nz, origin): continue
            
            neighbor_h = get_height(heightmap, nx, nz, origin)
            if center_h is not None and neighbor_h is not None:
                if abs(center_h - neighbor_h) > 3: continue 
            
            is_diag = (abs(dx) + abs(dz) == 2)
            if is_diag and random.random() > 0.6: continue
                
            thick_roads.add((nx, nz))

    fringe = set()
    for rx, rz in list(thick_roads):
        if is_water_ws(worldslice, rx, rz, origin):
            continue
        for dx, dz in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, nz = rx + dx, rz + dz
            if (nx, nz) not in thick_roads and (nx, nz) not in exact_building_tiles:
                if not is_center_water and is_water_ws(worldslice, nx, nz, origin): continue
                if random.random() < 0.25: 
                    fringe.add((nx, nz))

    return thick_roads.union(fringe)

def build_well(editor, x, y, z, palette=None):
    stone_mix = ["cobblestone", "mossy_cobblestone", "stone_bricks", "andesite"]
    
    wood_type = "oak"
    if palette and "pillars" in palette:
        wood_type = palette["pillars"].replace("_log", "").replace("_stem", "")
        
    roof_mat = "stone_brick"
    if palette and "roof" in palette:
        roof_mat = palette["roof"].replace("_stairs", "")

    for dy in range(1, 6):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                editor.placeBlock((x+dx, y+dy, z+dz), Block("air"))

    for dy in range(-4, 0):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    editor.placeBlock((x, y+dy, z), Block("water"))
                else:
                    editor.placeBlock((x+dx, y+dy, z+dz), Block(random.choice(stone_mix)))
                    
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx == 0 and dz == 0:
                editor.placeBlock((x, y, z), Block("air"))
            elif abs(dx) + abs(dz) == 2: 
                editor.placeBlock((x+dx, y, z+dz), Block(random.choice(stone_mix)))
            else:
                facing = "south" if dz == -1 else "north" if dz == 1 else "east" if dx == -1 else "west"
                stair_block = random.choice(["cobblestone_stairs", "stone_brick_stairs"])
                editor.placeBlock((x+dx, y, z+dz), Block(stair_block, {"facing": facing}))

    for dx, dz in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        editor.placeBlock((x+dx, y+1, z+dz), Block(f"{wood_type}_fence"))
        editor.placeBlock((x+dx, y+2, z+dz), Block(f"{wood_type}_fence"))
    
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx == 0 and dz == 0:
                editor.placeBlock((x, y+3, z), Block(f"{roof_mat}_slab", {"type": "bottom"}))
                editor.placeBlock((x, y+2, z), Block("iron_chain", {"axis": "y"}))
                editor.placeBlock((x, y+1, z), Block("lantern", {"hanging": "true"}))
            elif abs(dx) + abs(dz) == 2:
                editor.placeBlock((x+dx, y+3, z+dz), Block(f"{roof_mat}_slab", {"type": "bottom"}))
            else: 
                facing = "south" if dz == -1 else "north" if dz == 1 else "east" if dx == -1 else "west"
                editor.placeBlock((x+dx, y+3, z+dz), Block(f"{roof_mat}_stairs", {"facing": facing}))

def place_road(editor, heightmap, origin, road_tiles, worldslice, palette):
    bridge_block = palette["walls"]
    if "planks" in palette["floor"]:
        bridge_block = palette["floor"]

    for (x, z) in road_tiles:
        y = get_height(heightmap, x, z, origin)
        if y is None: continue

        editor.placeBlock((x, y, z), Block("air"))
        editor.placeBlock((x, y+1, z), Block("air"))
        editor.placeBlock((x, y+2, z), Block("air"))


        if is_water_ws(worldslice, x, z, origin):
            editor.placeBlock((x, y-1, z), Block(bridge_block))
        else:
            editor.placeBlock((x, y-1, z), Block("dirt_path"))

def add_street_lights(editor, road_tiles, heightmap, origin, worldslice, palette):
    """Adds rustic street lighting posts randomly alongside roads."""
    wood_type = palette["pillars"].replace("_log", "").replace("_stem", "")
    fence_block = f"{wood_type}_fence"
    
    placed_lights = []
    road_list = list(road_tiles)
    random.shuffle(road_list) # randomize iteration
    
    for (rx, rz) in road_list:
        if is_water_ws(worldslice, rx, rz, origin): continue
        
        too_close = False
        for lx, lz in placed_lights:
            if abs(lx - rx) + abs(lz - rz) < 12: # Check distance between lamps
                too_close = True
                break
        
        # 15% chance per eligible chunk of road to place a light
        if not too_close and random.random() < 0.15:
            y = get_height(heightmap, rx, rz, origin)
            if y is None: continue
            
            # Check for space directly next to the path
            sides = [(rx+1, rz), (rx-1, rz), (rx, rz+1), (rx, rz-1)]
            random.shuffle(sides)
            
            for sx, sz in sides:
                if (sx, sz) not in road_tiles and not is_water_ws(worldslice, sx, sz, origin):
                    sy = get_height(heightmap, sx, sz, origin)
                    # Needs reasonably flat ground to connect cleanly
                    if sy is not None and abs(sy - y) <= 1:
                        editor.placeBlock((sx, sy, sz), Block("mossy_cobblestone_wall"))
                        editor.placeBlock((sx, sy+1, sz), Block(fence_block))
                        editor.placeBlock((sx, sy+2, sz), Block(fence_block))
                        editor.placeBlock((sx, sy+3, sz), Block("lantern"))
                        placed_lights.append((sx, sz))
                        break

def generate_village(editor, buildArea, heightmap, worldslice, num_houses=10, num_farms=1):
    origin = (buildArea.offset.x, buildArea.offset.z)
    
    if is_build_area_wholly_water(worldslice, heightmap, origin):
        print("Build area is wholly water; skipping village generation.")
        return

    palette = get_palette(worldslice, heightmap, origin)

    print("Tracing adaptable jigsaw layouts...")
    houses, farms, road_tiles, center, exact_building_tiles = generate_layout(worldslice, heightmap, origin, num_houses, num_farms)
    if center is None or (not houses and not farms and not road_tiles):
        print("No viable land layout found; skipping village generation.")
        return

    print("Thickening roads and handling hills...")
    road_tiles = thicken_path_network(road_tiles, worldslice, heightmap, origin, exact_building_tiles)

    road_tiles = { (x, z) for (x, z) in road_tiles if not is_water_ws(worldslice, x, z, origin) }
    if not road_tiles:
        print("All roads are over water after thickening; aborting.")
        return

    print("Weaving road network and bridges...")
    place_road(editor, heightmap, origin, road_tiles, worldslice, palette)

    print("Adding street lights...")
    add_street_lights(editor, road_tiles, heightmap, origin, worldslice, palette)

    print("Building central well...")
    cx, cz = center
    cy = get_height(heightmap, cx, cz, origin)
    if cy is not None: build_well(editor, cx, cy, cz, palette)

    print("Constructing buildings with adaptive foundations...")
    for hx, hy, hz, depth, facing in houses:
        slope = slope_in_area(heightmap, origin, hx, hz, 5, depth)
        near_road = len(road_tiles) > 0 
        build_houses.build_house(editor, hx, hy, hz, depth, palette, facing, slope=slope, near_road=near_road)
            
    for fx, fy, fz in farms:
        build_houses.build_farm(editor, fx, fy, fz, width=9, depth=9, palette=palette)
        
    print(f"Village generation complete. Placed {len(houses)} houses and {len(farms)} farms.")
