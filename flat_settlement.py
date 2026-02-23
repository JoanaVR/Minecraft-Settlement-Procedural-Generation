from gdpc import Editor, Block
import random
from gdpc.geometry import placeCuboid,placeCuboidHollow

def build_robust_house(editor, x, y, z, depth, height, wall, floor):
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
    # Placed at house_base_y so it sits on the floor
    editor.placeBlock((x+2, y+1, z), Block("oak_door", {"facing":"north", "hinge":"left"}))
    placeCuboid(editor, (x+1, y+1, z-1), (x+3, y+3, z-1), Block("air"))
    
    # 6. Windows
    editor.placeBlock((x + 1, y + 2, z), Block("glass_pane"))
    editor.placeBlock((x - 2, y + 2, z), Block("glass_pane"))

def main():
    editor = Editor(buffering=True)
    
    buildArea = editor.getBuildArea()

    #Load world slice
    editor.loadWorldSlice(cache=True)
    #Get heightmap
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    start_x = buildArea.offset.x
    start_z = buildArea.offset.z
    local_x = curr_x - buildArea.offset.x
    local_z = start_z - buildArea.offset.z
    ground_y = heightmap[local_x, local_z] - 1
    
    num_buildings = random.randint(8, 12)
    spacing = 12

    #floor palette
    floorpalette = [
        Block("stone_bricks"),
        Block("cracked_stone_bricks"),
        Block("cobblestone")
    ]

    #wall palette
    wallpalette = [
        Block("oak_planks"),
        Block("stripped_oak_wood"),
        Block("stripped_birch_wood"),
        Block("birch_planks")
    ]

    print(f"Generating robust settlement at Y: {ground_y}")

    curr_x = start_x

    for i in range(num_buildings):
        
        # Randomize dimensions
        h = random.randint(3,7)
        d = random.randint(3,10)
        wall = random.choice(wallpalette)
        floor = random.choice(floorpalette)
        
        # Build!
        build_robust_house(editor, curr_x, ground_y, start_z, d, h, wall, floor)

        curr_x += spacing
   
    editor.flushBuffer()
    print("Done! The doors should now be flush with the ground.")

if __name__ == "__main__":
    main()