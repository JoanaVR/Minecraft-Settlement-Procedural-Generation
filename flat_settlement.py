from gdpc import Editor, Block, geometry
import random

def build_robust_house(editor, x, y, z, width, depth, height, wall_type, roof_type):
    """
    Builds a house with a foundation and proper floor alignment.
    y: the height of the ground block.
    """

    foundation_y = y 
    geometry.placeCuboid(editor, (x, foundation_y, z), (x + width - 1, foundation_y, z + depth - 1), Block("cobblestone"))

    # 2. Walls (Starting at y + 1 so the floor is ABOVE the grass)
    house_base_y = y + 1
    geometry.placeCuboid(editor, (x, house_base_y, z), (x + width - 1, house_base_y + height - 1, z + depth - 1), Block(wall_type))
    
    # 3. Hollow out the inside
    geometry.placeCuboid(editor, (x + 1, house_base_y, z + 1), (x + width - 2, house_base_y + height - 1, z + depth - 2), Block("air"))
    
    # 4. Roof
    roof_y = house_base_y + height
    geometry.placeCuboid(editor, (x, roof_y, z), (x + width - 1, roof_y, z + depth - 1), Block(roof_type))
    
    # 5. Door placement 
    # Placed at house_base_y so it sits on the floor
    editor.placeBlock((x + width // 2, house_base_y, z), Block("oak_door", {"half": "lower", "facing": "north"}))
    editor.placeBlock((x + width // 2, house_base_y + 1, z), Block("oak_door", {"half": "upper", "facing": "north"}))
    
    # 6. Windows
    editor.placeBlock((x + 1, house_base_y + 2, z), Block("glass_pane"))
    editor.placeBlock((x + width - 2, house_base_y + 2, z), Block("glass_pane"))

def main():
    editor = Editor(buffering=True)
    
    # Coordinates for a flat world
    start_x, start_z = -50, 20
    ground_y = -61  # The Y-level of the grass/dirt
    
    num_buildings = random.randint(8, 12)
    spacing = 12

    palettes = [
        ("oak_planks", "stone_slab"),
        ("stone_bricks", "spruce_planks"),
        ("spruce_planks", "cobblestone_stairs"),
        ("bricks", "oak_slab")
    ]

    print(f"Generating robust settlement at Y: {ground_y}")

    for i in range(num_buildings):
        curr_x = start_x + (i * spacing)
        
        # Randomize dimensions
        w, d, h = random.randint(5, 8), random.randint(5, 8), random.randint(4, 5)
        wall, roof = random.choice(palettes)
        
        # Build!
        build_robust_house(editor, curr_x, ground_y, start_z, w, d, h, wall, roof)

    editor.flushBuffer()
    print("Done! The doors should now be flush with the ground.")

if __name__ == "__main__":
    main()