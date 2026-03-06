import random
from gdpc import Block
from gdpc.geometry import placeCuboid, placeCuboidHollow

# ─────────────────────────────────────────────
#  House Placement Logic
# ─────────────────────────────────────────────

def get_door_outside_pos(x, z, depth, facing):
    """Returns the (x, z) coordinate immediately outside the door for pathfinding."""
    if facing == "north": return (x+2, z-1)
    elif facing == "south": return (x+2, z+depth+1)
    elif facing == "east": return (x+5, z+depth//2)
    elif facing == "west": return (x-1, z+depth//2)
    return (x+2, z-1)

def opposite_facing(facing):
    """Returns the opposite direction, useful for placing stairs facing outwards."""
    return {"north":"south", "south":"north", "east":"west", "west":"east"}.get(facing, "north")

def doorplacement(editor, x, y, z, depth, facing, palette):
    """Places the door and ensures a clear, level step outside."""
    outside_pos = get_door_outside_pos(x, z, depth, facing)
    dx, dz = 0, 0

    if facing == "north":
        door_pos = (x+2, y+1, z)
        dz = -1
    elif facing == "south":
        door_pos = (x+2, y+1, z+depth)
        dz = 1
    elif facing == "east":
        door_pos = (x+4, y+1, z+depth//2)
        dx = 1
    elif facing == "west":
        door_pos = (x, y+1, z+depth//2)
        dx = -1


    editor.placeBlock(door_pos, Block("oak_door", {"facing": facing, "half": "lower"}))
    editor.placeBlock((door_pos[0], door_pos[1]+1, door_pos[2]), Block("oak_door", {"facing": facing, "half": "upper"}))
    
    ox, oz = outside_pos
    step_block = palette["roof"]
    

    if "stairs" in step_block:
        editor.placeBlock((ox, y, oz), Block(step_block, {"facing": opposite_facing(facing)}))
    else:
        editor.placeBlock((ox, y, oz), Block("cobblestone_slab"))


    for dy in range(1, 5):
        editor.placeBlock((ox, y+dy, oz), Block("air"))

def place_windows(editor, x, y, z, depth, facing):
    """Places symmetrical windows based on house direction."""
    window_blocks = [
        (x+1, y+2, z), (x+3, y+2, z),                   # North wall
        (x+1, y+2, z+depth), (x+3, y+2, z+depth),       # South wall
        (x, y+2, z+1), (x, y+2, z+depth-1),             # West wall
        (x+4, y+2, z+1), (x+4, y+2, z+depth-1)          # East wall
    ]
    

    for wx, wy, wz in window_blocks:
        if facing == "north" and wz == z: continue
        if facing == "south" and wz == z+depth: continue
        if facing == "east" and wx == x+4: continue
        if facing == "west" and wx == x: continue
        editor.placeBlock((wx, wy, wz), Block("glass_pane"))

def place_stairs(editor, x, y, z, depth, middle_y, floor_block, facing):
    """Places stairs for a 2-story house with guaranteed head clearance."""
    stair_x = x + 1 
    stair_z = z + 1
    stair_facing = "south"
    
    stair_height = middle_y - y
    steps = min(depth - 2, stair_height)

    for i in range(steps):

        editor.placeBlock((stair_x, y + i, stair_z + i), floor_block)  
        editor.placeBlock((stair_x, y + i + 1, stair_z + i), Block("oak_stairs", {"facing": stair_facing}))
        

        editor.placeBlock((stair_x, middle_y, stair_z + i), Block("air"))
        editor.placeBlock((stair_x, middle_y + 1, stair_z + i), Block("air"))
        editor.placeBlock((stair_x, middle_y + 2, stair_z + i), Block("air"))

def roof_placement(editor, x, y, z, height, depth, palette, facing):
    """Symmetrical roof depending on facing direction, with filled gables."""
    roof_stair_block = palette["roof"]
    wall_block = palette["walls"]

    if facing in ["north", "south"]:

        for dx in range(-1, 4):
            yy = y + height + 1 + dx
            if dx > 2: 
                break
                
            leftBlock  = Block(roof_stair_block, {"facing": "east"})
            rightBlock = Block(roof_stair_block, {"facing": "west"})
            placeCuboid(editor, (x+dx, yy, z-1), (x+dx, yy, z+depth+1), leftBlock)
            placeCuboid(editor, (x+4-dx, yy, z-1), (x+4-dx, yy, z+depth+1), rightBlock)
            

            if 0 <= dx <= 2:
                placeCuboid(editor, (x+dx, y+height+1, z), (x+dx, yy-1, z), Block(wall_block))
                placeCuboid(editor, (x+4-dx, y+height+1, z), (x+4-dx, yy-1, z), Block(wall_block))
                placeCuboid(editor, (x+dx, y+height+1, z+depth), (x+dx, yy-1, z+depth), Block(wall_block))
                placeCuboid(editor, (x+4-dx, y+height+1, z+depth), (x+4-dx, yy-1, z+depth), Block(wall_block))
    else:

        for dz in range(-1, (depth//2) + 2):
            yy = y + height + 1 + dz
            if z + dz > z + depth - dz: 
                break
                
            frontBlock  = Block(roof_stair_block, {"facing": "south"})
            backBlock = Block(roof_stair_block, {"facing": "north"})
            placeCuboid(editor, (x-1, yy, z+dz), (x+5, yy, z+dz), frontBlock)
            placeCuboid(editor, (x-1, yy, z+depth-dz), (x+5, yy, z+depth-dz), backBlock)
            

            if dz >= 0 and (z + dz <= z + depth - dz):
                placeCuboid(editor, (x, y+height+1, z+dz), (x, yy-1, z+dz), Block(wall_block))
                placeCuboid(editor, (x, y+height+1, z+depth-dz), (x, yy-1, z+depth-dz), Block(wall_block))
                placeCuboid(editor, (x+4, y+height+1, z+dz), (x+4, yy-1, z+dz), Block(wall_block))
                placeCuboid(editor, (x+4, y+height+1, z+depth-dz), (x+4, yy-1, z+depth-dz), Block(wall_block))

def add_pillars(editor, x, y, z, depth, height, pillar_block):
    """Adds solid pillars to the 4 corners for better aesthetics."""
    for cx in (x, x+4):
        for cz in (z, z+depth):
            placeCuboid(editor, (cx, y, cz), (cx, y+height, cz), Block(pillar_block))

# ─────────────────────────────────────────────
#  Main Builders
# ─────────────────────────────────────────────

def build_1fhouse(editor, x, y, z, depth, height, palette, facing):
    wall = Block(palette["walls"])
    floor = Block(palette["floor"])
    pillar = palette["pillars"]
    roof = palette["roof"]

    # Main structure
    placeCuboidHollow(editor, (x, y, z), (x+4, y+height, z+depth), wall)
    placeCuboid(editor, (x, y-5, z), (x+4, y, z+depth), floor) # Foundation
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height, z+depth-1), Block("air")) # Interior clear

    add_pillars(editor, x, y, z, depth, height, pillar)
    roof_placement(editor, x, y, z, height, depth, palette, facing)
    doorplacement(editor, x, y, z, depth, facing, palette)
    place_windows(editor, x, y, z, depth, facing)

def build_2fhouse(editor, x, y, z, depth, palette, facing):
    height = 8 # 2 floors
    wall = Block(palette["walls"])
    floor = Block(palette["floor"])
    pillar = palette["pillars"]
    roof = palette["roof"]

    # Main structure
    placeCuboidHollow(editor, (x, y, z), (x+4, y+height, z+depth), wall)
    placeCuboid(editor, (x, y-5, z), (x+4, y, z+depth), floor) # Foundation
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height, z+depth-1), Block("air")) # Interior clear

    # 2nd Floor
    middle_y = y + 4
    placeCuboid(editor, (x+1, middle_y, z+1), (x+3, middle_y, z+depth-1), floor)
    
    add_pillars(editor, x, y, z, depth, height, pillar)
    place_stairs(editor, x, y, z, depth, middle_y, floor, facing)
    roof_placement(editor, x, y, z, height, depth, palette, facing)
    doorplacement(editor, x, y, z, depth, facing, palette)
    place_windows(editor, x, y, z, depth, facing)
    # 2nd floor windows
    place_windows(editor, x, y+4, z, depth, facing)

def build_farm(editor, x, y, z, width, depth):
    for i in range(width):
        for j in range(depth):
            if i == 0 or i == width-1 or j == 0 or j == depth-1:
                editor.placeBlock((x+i, y, z+j), Block("oak_log"))
    for i in range(1, width-1):
        for j in range(1, depth-1):
            editor.placeBlock((x+i, y, z+j), Block("farmland"))
            
    water_z = z + depth // 2
    for i in range(1, width-1):
        editor.placeBlock((x+i, y, water_z), Block("water"))

    crops = ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]"]
    for i in range(1, width-1):
        for j in range(1, depth-1):
            if j != water_z - z: 
                crop = random.choice(crops)
                editor.placeBlock((x+i, y+1, z+j), Block(crop))
