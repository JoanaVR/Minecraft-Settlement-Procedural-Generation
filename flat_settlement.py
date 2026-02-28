from gdpc import Editor, Block
import random
from gdpc.geometry import *

#Places the door according to the direction of the house
def doorplacement(editor,x,y,z,depth, facing):
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
    
    dx, dz = 0, 0
    if facing == "north": dz = -1
    if facing == "south": dz = 1
    if facing == "east": dx = 1
    if facing == "west": dx = -1

    
    editor.placeBlock((door_pos[0]+dx, door_pos[1], door_pos[2]+dz), Block("air"))
    
    #Window placement - to be changed to also include second floor houses
    editor.placeBlock(window1, Block("glass_pane"))
    editor.placeBlock(window2, Block("glass_pane"))

#Places stairs in houses that have multiple floors depending on the direction the house is facing
# as to not be placed infront of doors
def place_stairs(editor, x, y, z, depth, middle_y, floor, facing):
    x_start_in = x + 1       
    x_end_in = x + 3         

    z_start_in = z + 1
    z_end_in = z + depth - 1

    if facing in ["north", "south"]:
        stair_z = z_start_in if facing == "south" else z_end_in  
        stair_facing = "east"

        stair_length = x_end_in - x_start_in + 1
        stair_height = middle_y - y
        steps = min(stair_length, stair_height)

        for i in range(steps):
            editor.placeBlock((x_start_in + i, y + i, stair_z), floor)  
            editor.placeBlock((x_start_in + i, y + i + 1, stair_z), Block("oak_stairs", {"facing": stair_facing}))
            editor.placeBlock((x_start_in + i, y + i + 2, stair_z), Block("air"))
            editor.placeBlock((x_start_in + i, y + i + 3, stair_z), Block("air"))

    else:
        stair_x = x_start_in if facing == "east" else x_end_in  
        stair_facing = "north" if facing == "east" else "south"

        stair_length = depth - 2  
        stair_height = middle_y - y
        steps = min(stair_length, stair_height)

        for i in range(steps):
            editor.placeBlock((stair_x, y + i, z_start_in + i), floor)  
            editor.placeBlock((stair_x, y + i + 1, z_start_in + i), Block("oak_stairs", {"facing": stair_facing}))
            editor.placeBlock((stair_x, y + i + 2, z_start_in + i), Block("air"))
            editor.placeBlock((stair_x, y + i + 3, z_start_in + i), Block("air"))

#Places the roof
def roof_placement(editor,x,y,z,height, depth,floor):
    for dx in range(1, 4):
        yy = y + height + 2 - dx

        leftBlock  = Block("oak_stairs", {"facing": "east"})
        rightBlock = Block("oak_stairs", {"facing": "west"})
        placeCuboid(editor, (x+2-dx, yy, z-1), (x+2-dx, yy, z+depth+1), leftBlock)
        placeCuboid(editor, (x+2+dx, yy, z-1), (x+2+dx, yy, z+depth+1), rightBlock)

        leftBlock  = Block("oak_stairs", {"facing": "west", "half": "top"})
        rightBlock = Block("oak_stairs", {"facing": "east", "half": "top"})
        for zz in [z-1, z+depth+1]:
            editor.placeBlock((x+2-dx+1, yy, zz), leftBlock)
            editor.placeBlock((x+2+dx-1, yy, zz), rightBlock)

    yy = y+height+1
    placeCuboid(editor, (x+2, yy, z-1), (x+2, yy, z+depth+1), floor)

#Builds a 1 floor standard house
def build_1fhouse(editor, x, y, z, depth, height, wall, floor, facing):

    placeCuboidHollow(editor, (x,y,z), (x+4, y+height, z+depth), wall)
    placeCuboid(editor, (x,y,z), (x+4,y-5,z+depth), floor)
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height-1, z+3), Block("air"))

    roof_placement(editor,x,y,z,height,depth,floor)
    doorplacement(x,y,z,depth,facing)
    
#Builds a 2 floor house
def build_2fhouse(editor, x,y,z,depth,height,wall,floor,facing):
    height = height + (0.5*height)
    placeCuboidHollow(editor, (x,y,z), (x+4, y+height, z+depth), wall)
    placeCuboid(editor, (x,y,z), (x+4,y-5,z+depth), floor)
    placeCuboid(editor, (x+1, y+1, z+1), (x+3, y+height-1, z+3), Block("air"))
    middle_y = int(y + height / 2 +1)
    placeCuboid(editor, (x+1, middle_y, z+1), (x+3, middle_y, z+depth-1), floor)
    place_stairs(editor, x, y, z, depth, middle_y, floor, facing)
    roof_placement(editor,x,y,z,height,depth,floor)
    doorplacement(editor, x,y,z,depth,facing)


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

# def main():
#     editor = Editor(buffering=True)
    
#     buildArea = editor.getBuildArea()

#     #Load world slice
#     editor.loadWorldSlice(cache=True)
#     #Get heightmap
#     heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

#     x = buildArea.offset.x + buildArea.size.x // 2
#     z = buildArea.offset.z + buildArea.size.z // 2

#     road_positions = []

#     direction = (1, 0)

#     # Generate road
#     for i in range(80):

#         # Convert world coords to heightmap local coords
#         local_x = x - buildArea.offset.x
#         local_z = z - buildArea.offset.z

#         # Stay inside build area
#         if not (0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z):
#             break

#         y = heightmap[local_x, local_z] - 1

#         road_positions.append((x, y, z))

#         # Place road block
#         editor.placeBlock((x, y, z), Block("dirt_path"))

#         # Occasionally turn
#         if random.random() < 0.15:
#             direction = random.choice([(1,0), (-1,0), (0,1), (0,-1)])

#         x += direction[0]
#         z += direction[1]

#     # Place houses along road
#     spacing = 12
#     for i in range(0, len(road_positions), spacing):

#         rx, ry, rz = road_positions[i]
#         facing = None

#         # Alternate left/right
#         if i % 2 == 0:
#             hx = rx + 6
#             hz = rz
#             facing = "east"
#         else:
#             hx = rx - 6
#             hz = rz
#             facing = "west"
           
#         # Recalculate ground height for house
#         local_x = hx - buildArea.offset.x
#         local_z = hz - buildArea.offset.z

#         if 0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z:
#             hy = heightmap[local_x, local_z] - 1

#             build_robust_house(
#                 editor,
#                 hx,
#                 hy,
#                 hz,
#                 depth=random.randint(4,8),
#                 height=random.randint(4,6),
#                 wall=Block("oak_planks"),
#                 floor=Block("stone_bricks"),
#                 facing=facing
#             )

#     editor.flushBuffer()
#     print("Village generated.")
