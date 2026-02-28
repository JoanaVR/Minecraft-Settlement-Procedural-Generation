from gdpc import Editor, Block
import random
from gdpc.geometry import placeCuboid,placeCuboidHollow

def build_robust_house(editor, x, y, z, depth, height, wall, floor, facing):
    """
    Builds a house with a foundation and proper floor alignment.
    y: the height of the ground block.
    """

    placeCuboidHollow(editor, (x,y,z), (x+4, y+height, z+depth), wall)
    placeCuboid(editor, (x,y,z), (x+4,y-5,z+depth), floor)
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height-1, z+3), Block("air"))
        
    # Build roof: loop through distance from the middle
    for dx in range(1, 4):
        yy = y + height + 2 - dx

        # Build row of stairs blocks
        leftBlock  = Block("oak_stairs", {"facing": "east"})
        rightBlock = Block("oak_stairs", {"facing": "west"})
        placeCuboid(editor, (x+2-dx, yy, z-1), (x+2-dx, yy, z+depth+1), leftBlock)
        placeCuboid(editor, (x+2+dx, yy, z-1), (x+2+dx, yy, z+depth+1), rightBlock)

        # Add upside-down accent blocks
        leftBlock  = Block("oak_stairs", {"facing": "west", "half": "top"})
        rightBlock = Block("oak_stairs", {"facing": "east", "half": "top"})
        for zz in [z-1, z+depth+1]:
            editor.placeBlock((x+2-dx+1, yy, zz), leftBlock)
            editor.placeBlock((x+2+dx-1, yy, zz), rightBlock)

    yy = y+height+1
    placeCuboid(editor, (x+2, yy, z-1), (x+2, yy, z+depth+1), floor)
    
    # 5. Door placement 
    #place door and windows on the front wall (facing the road)
    if facing == "north":
        door_pos = (x+2, y+1, z)
        window1 = (x+1, y+2, z+depth)
        window2 = (x+3, y+2, z+depth)

    elif facing == "south":
        door_pos = (x+2, y+1, z+depth)
        window1 = (x+1, y+2, z)
        window2 = (x+3, y+2, z)

    elif facing == "east":
        door_pos = (x+4, y+1, z+depth//2)
        window1 = (x, y+2, z+1)
        window2 = (x, y+2, z+depth-1)

    elif facing == "west":
        door_pos = (x, y+1, z+depth//2)
        window1 = (x+4, y+2, z+1)
        window2 = (x+4, y+2, z+depth-1)

    editor.placeBlock(door_pos, Block("oak_door", {"facing": facing}))
    
    # Clear space in front of door
    dx, dz = 0, 0
    if facing == "north": dz = -1
    if facing == "south": dz = 1
    if facing == "east": dx = 1
    if facing == "west": dx = -1

    editor.placeBlock((door_pos[0]+dx, door_pos[1], door_pos[2]+dz), Block("air"))
    
    # 6. Windows
    editor.placeBlock(window1, Block("glass_pane"))
    editor.placeBlock(window2, Block("glass_pane"))


def generate_road(editor, buildArea, length=100):
    x = buildArea.offset.x + buildArea.size.x // 2
    z = buildArea.offset.z + buildArea.size.z // 2
    
    direction = (1, 0)
    road_positions = []

    for i in range(length):
        road_positions.append((x, z))
        
        # Occasionally change direction slighly to have a more natural, winding road
        if random.random() < 0.2:
            direction = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        
        x += direction[0]
        z += direction[1]

    return road_positions
