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
    doorplacement(editor,x,y,z,depth,facing)
    
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

#Builds a farm for the villagers
def build_farm(editor, x, y, z, width, depth):
    for i in range(width):
        for j in range(depth):
            if i == 0 or i == width-1 or j == 0 or j == depth-1:
                editor.placeBlock((x+i, y, z+j), Block("stone"))
    for i in range(1, width-1):
        for j in range(1, depth-1):
            editor.placeBlock((x+i, y, z+j), Block("farmland"))
    water_z = z + depth // 2
    for i in range(1, width-1):
        editor.placeBlock((x+i, y, water_z), Block("water"))

  # plants the crops 
    crops = ["wheat[age=0]", "carrots[age=0]", "potatoes[age=0]", "beetroots[age=0]"]
    for i in range(1, width-1):
        for j in range(1, depth-1):
            if j != water_z - z: 
                crop = random.choice(crops)
                editor.placeBlock((x+i, y+1, z+j), Block(crop))
