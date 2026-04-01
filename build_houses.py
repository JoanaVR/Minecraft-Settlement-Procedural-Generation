import random
from gdpc import Block
from gdpc.geometry import placeCuboid, placeCuboidHollow

#  House Placement Logic

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

    # Adjusting door block to match the new lowered floor heights
    if facing == "north":
        door_pos = (x+2, y+1, z)
    elif facing == "south":
        door_pos = (x+2, y+1, z+depth)
    elif facing == "east":
        door_pos = (x+4, y+1, z+depth//2)
    elif facing == "west":
        door_pos = (x, y+1, z+depth//2)

    wood_type = palette["walls"].replace("_planks","").replace("_log", "").replace("_stem", "")
    
    editor.placeBlock(door_pos, Block(f"{wood_type}_door", {"facing": facing, "half": "lower"}))
    
    editor.placeBlock((door_pos[0], door_pos[1]+1, door_pos[2]), Block(f"{wood_type}_door", {"facing": facing, "half": "upper"}))
    stair_type =palette["roof"]
    editor.placeBlock((door_pos[0], door_pos[1]+2, door_pos[2]), Block(stair_type, {"facing": facing, "half": "top"}))
    editor.placeBlock((door_pos[0], y, door_pos[2]), Block(palette["floor"]))

    ox, oz = outside_pos
    
    for dy in range(1, 4):
        editor.placeBlock((ox, y+dy, oz), Block("air"))
    
    editor.placeBlock((ox, y, oz), Block("dirt_path"))

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
        editor.placeBlock((wx, wy, wz), Block("glass"))

def place_stairs(editor, x, y, z, depth, middle_y, floor_block, facing, palette):
    """Places stairs on the wall opposite the door, sealing any wall holes."""
    stair_block = palette["roof"]
    wall_block  = Block(palette["walls"])
    stair_height = middle_y - y
 
    if facing == "north":
        stair_x = x + 1
        steps = min(depth - 2, stair_height)
        for i in range(steps):
            sz = z + depth - 1 - i
            editor.placeBlock((stair_x, y + i,     sz), floor_block)
            editor.placeBlock((stair_x, y + i + 1, sz), Block(stair_block, {"facing": "north"}))
            for dy in range(3):
                editor.placeBlock((stair_x, middle_y + dy, sz), Block("air"))
        for dy in range(3):
            editor.placeBlock((stair_x, middle_y + dy, z + depth), wall_block)
 
    elif facing == "south":
        stair_x = x + 1
        steps = min(depth - 2, stair_height)
        for i in range(steps):
            sz = z + 1 + i
            editor.placeBlock((stair_x, y + i,     sz), floor_block)
            editor.placeBlock((stair_x, y + i + 1, sz), Block(stair_block, {"facing": "south"}))
            for dy in range(3):
                editor.placeBlock((stair_x, middle_y + dy, sz), Block("air"))
        for dy in range(3):
            editor.placeBlock((stair_x, middle_y + dy, z), wall_block)
 
    elif facing == "east":
        stair_z = z + 1
        steps = min(3, stair_height)
        for i in range(steps):
            sx = x + 1 + i
            editor.placeBlock((sx, y + i,     stair_z), floor_block)
            editor.placeBlock((sx, y + i + 1, stair_z), Block(stair_block, {"facing": "east"}))
            for dy in range(3):
                editor.placeBlock((sx, middle_y + dy, stair_z), Block("air"))
        for dy in range(3):
            editor.placeBlock((x, middle_y + dy, stair_z), wall_block)
 
    elif facing == "west":
        stair_z = z + 1
        steps = min(3, stair_height)
        for i in range(steps):
            sx = x + 3 - i
            editor.placeBlock((sx, y + i,     stair_z), floor_block)
            editor.placeBlock((sx, y + i + 1, stair_z), Block(stair_block, {"facing": "west"}))
            for dy in range(3):
                editor.placeBlock((sx, middle_y + dy, stair_z), Block("air"))
        for dy in range(3):
            editor.placeBlock((x + 4, middle_y + dy, stair_z), wall_block)
 
def roof_placement(editor, x, y, z, height, depth, palette, facing):
    """Symmetrical pitched roof with upside-down stair accents on the eaves."""
    roof_stair_block = palette["roof"]
    wall_block = palette["walls"]
 
    if facing in ["north", "south"]:
        for dx in range(1, 4):
            yy = y + height + 2 - dx
 
            # Main roof slope
            leftBlock  = Block(roof_stair_block, {"facing": "east"})
            rightBlock = Block(roof_stair_block, {"facing": "west"})
            placeCuboid(editor, (x+2-dx, yy, z-1), (x+2-dx, yy, z+depth+1), leftBlock)
            placeCuboid(editor, (x+2+dx, yy, z-1), (x+2+dx, yy, z+depth+1), rightBlock)
 
            # Upside-down accent stairs on gable ends
            accentLeft  = Block(roof_stair_block, {"facing": "west", "half": "top"})
            accentRight = Block(roof_stair_block, {"facing": "east", "half": "top"})
            for zz in [z-1, z+depth+1]:
                editor.placeBlock((x+2-dx+1, yy, zz), accentLeft)
                editor.placeBlock((x+2+dx-1, yy, zz), accentRight)
 
            # Filled gable walls
            if dx <= 2:
                placeCuboid(editor, (x+2-dx, y+height+1, z),       (x+2-dx, yy-1, z),       Block(wall_block))
                placeCuboid(editor, (x+2+dx, y+height+1, z),       (x+2+dx, yy-1, z),       Block(wall_block))
                placeCuboid(editor, (x+2-dx, y+height+1, z+depth), (x+2-dx, yy-1, z+depth), Block(wall_block))
                placeCuboid(editor, (x+2+dx, y+height+1, z+depth), (x+2+dx, yy-1, z+depth), Block(wall_block))
 
    else:
        for dz in range(-1, (depth//2) + 2):
            yy = y + height + 1 + dz
            if z + dz > z + depth - dz:
                break
 
            frontBlock = Block(roof_stair_block, {"facing": "south"})
            backBlock  = Block(roof_stair_block, {"facing": "north"})
            placeCuboid(editor, (x-1, yy, z+dz),       (x+5, yy, z+dz),       frontBlock)
            placeCuboid(editor, (x-1, yy, z+depth-dz), (x+5, yy, z+depth-dz), backBlock)
 
            # Upside-down accent stairs on side eaves
            if dz >= 0 and (z + dz <= z + depth - dz):
                accentFront = Block(roof_stair_block, {"facing": "north", "half": "top"})
                accentBack  = Block(roof_stair_block, {"facing": "south", "half": "top"})
                for xx in [x-1, x+5]:
                    editor.placeBlock((xx, yy, z+dz+1),       accentFront)
                    editor.placeBlock((xx, yy, z+depth-dz-1), accentBack)
 
                # Filled gable walls
                placeCuboid(editor, (x,   y+height+1, z+dz),       (x,   yy-1, z+dz),       Block(wall_block))
                placeCuboid(editor, (x,   y+height+1, z+depth-dz), (x,   yy-1, z+depth-dz), Block(wall_block))
                placeCuboid(editor, (x+4, y+height+1, z+dz),       (x+4, yy-1, z+dz),       Block(wall_block))
                placeCuboid(editor, (x+4, y+height+1, z+depth-dz), (x+4, yy-1, z+depth-dz), Block(wall_block))

def add_pillars(editor, x, y, z, depth, height, pillar_block):
    """Adds solid pillars to the 4 corners for better aesthetics."""
    for cx in (x, x+4):
        for cz in (z, z+depth):
            placeCuboid(editor, (cx, y, cz), (cx, y+height, cz), Block(pillar_block))

#  Main Builders

def build_1fhouse(editor, x, y, z, depth, height, palette, facing):
    wall = Block(palette["walls"])
    floor = Block(palette["floor"])
    pillar = palette["pillars"]

    # Clear space above the house so it's carved out of steep hillsides
    placeCuboid(editor, (x, y, z), (x+4, y+height+6, z+depth), Block("air"))

    # Sink the entire structure by 1 block so the internal floor exactly matches the path outside
    y -= 1 

    # Deep Foundation (15 blocks) to anchor perfectly onto any slope
    placeCuboid(editor, (x, y-15, z), (x+4, y-1, z+depth), Block("cobblestone"))

    # Hollow wall shell
    placeCuboidHollow(editor, (x, y, z), (x+4, y+height, z+depth), wall)
    
    # Fill in just the inner floor layer explicitly
    placeCuboid(editor, (x+1, y, z+1), (x+3, y, z+depth-1), floor) 
    
    # Ensure interior is open
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height-1, z+depth-1), Block("air")) 

    add_pillars(editor, x, y, z, depth, height, pillar)
    roof_placement(editor, x, y, z, height, depth, palette, facing)
    doorplacement(editor, x, y, z, depth, facing, palette)
    place_windows(editor, x, y, z, depth, facing)

def build_2fhouse(editor, x, y, z, depth, palette, facing):
    height = 8 # 2 floors
    
    placeCuboid(editor, (x, y, z), (x+4, y+height+6, z+depth), Block("air"))
    
    y -= 1

    wall = Block(palette["walls"])
    floor = Block(palette["floor"])
    pillar = palette["pillars"]

    # Deep cobblestone foundation for steep drops
    placeCuboid(editor, (x, y-15, z), (x+4, y-1, z+depth), Block("cobblestone"))

    # Main structure shell
    placeCuboidHollow(editor, (x, y, z), (x+4, y+height, z+depth), wall)
    
    # Interior floor
    placeCuboid(editor, (x+1, y, z+1), (x+3, y, z+depth-1), floor) 
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height-1, z+depth-1), Block("air")) 

    # 2nd Floor
    middle_y = y + 4
    placeCuboid(editor, (x+1, middle_y, z+1), (x+3, middle_y, z+depth-1), floor)
    
    add_pillars(editor, x, y, z, depth, height, pillar)
    place_stairs(editor, x, y, z, depth, middle_y, floor, facing, palette)
    roof_placement(editor, x, y, z, height, depth, palette, facing)
    doorplacement(editor, x, y, z, depth, facing, palette)
    
    place_windows(editor, x, y, z, depth, facing)
    place_windows(editor, x, middle_y, z, depth, facing)

def classify_house(depth, slope, near_road, near_water):
    """
    Decides house type based on terrain and site context.
    Adapted to allow generating on any terrain without rigid aborts.
    """
    if near_water: return "1f" 
    if depth < 5: return "1f"
    if near_road and depth >= 5: return "2f"
    
    return "1f"

def build_house(editor, x, y, z, depth, palette, facing,
                slope=0, near_road=False, near_water=False):
    """
    Rule-based dispatcher. Classifies the site and calls the appropriate builder.
    """
    house_type = classify_house(depth, slope, near_road, near_water)

    if house_type == "2f":
        build_2fhouse(editor, x, y, z, depth, palette, facing)
    else:
        build_1fhouse(editor, x, y, z, depth, 4, palette, facing)


def build_farm(editor, x, y, z, width, depth, palette):
    placeCuboid(editor, (x, y, z), (x+width-1, y+6, z+depth-1), Block("air"))
    
    y -= 1
    
    placeCuboid(editor, (x, y-15, z), (x+width-1, y-1, z+depth-1), Block("dirt"))

    log_block = palette["pillars"]
    for i in range(width):
        for j in range(depth):
            if i == 0 or i == width-1 or j == 0 or j == depth-1:
                editor.placeBlock((x+i, y, z+j), Block(log_block))
                
    for i in range(1, width-1):
        for j in range(1, depth-1):
            editor.placeBlock((x+i, y, z+j), Block("farmland"))
            
    water_z = z + depth // 2
    for i in range(1, width-1):
        editor.placeBlock((x+i, y, water_z), Block("water"))
        editor.placeBlock((x+i, y+1, water_z), Block("air")) 

    crops = ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]"]
    for i in range(1, width-1):
        for j in range(1, depth-1):
            if j != water_z - z: 
                crop = random.choice(crops)
                editor.placeBlock((x+i, y+1, z+j), Block(crop))
