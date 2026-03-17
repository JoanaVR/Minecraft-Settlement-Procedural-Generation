import random

# block_palettes = {
#     "Plains": {
#         "walls": ["oak_planks", "birch_planks"],
#         "pillars": ["oak_log"],
#         "floor": ["cobblestone", "oak_planks"],
#         "roof": ["oak_stairs", "cobblestone_stairs"]
#     },
#     "Woodlands": {
#         "walls": ["dark_oak_planks", "spruce_planks"],
#         "pillars": ["dark_oak_log", "spruce_log"],
#         "floor": ["birch_planks", "cobblestone"],
#         "roof": ["dark_oak_stairs", "spruce_stairs"]
#     },
#     "Caves": {
#         "walls": ["stone", "deepslate", "cobblestone"],
#         "pillars": ["polished_deepslate", "stone_bricks"],
#         "floor": ["moss_block", "gravel"],
#         "roof": ["deepslate_brick_stairs", "stone_brick_stairs"]
#     },
#     "Mountains": {
#         "walls": ["spruce_planks", "stone"],
#         "pillars": ["spruce_log", "stone_bricks"],
#         "floor": ["calcite", "gravel"],
#         "roof": ["spruce_stairs", "dark_oak_stairs"]
#     },
#     "Sandy Areas": {
#         "walls": ["smooth_sandstone", "terracotta"],
#         "pillars": ["cut_sandstone", "chiseled_sandstone"],
#         "floor": ["sandstone", "birch_planks"],
#         "roof": ["sandstone_stairs", "smooth_sandstone_stairs"]
#     }
# }

# def get_biome_palette(biome="Plains"):
#     if biome in block_palettes:
#         palette = block_palettes[biome]
#     else:
#         palette = block_palettes["Plains"]

#     palette_selection = {
#         "walls": random.choice(palette["walls"]),
#         "pillars": random.choice(palette["pillars"]),
#         "floor": random.choice(palette["floor"]),
#         "roof": random.choice(palette["roof"])
#     }
#     return palette_selection

# if __name__ == "__main__":
#     print(get_biome_palette("Plains"))
#     print(get_biome_palette("Mountains"))

def tree_scanner(worldslice, heightmap, origin):
    ox, oz = origin
    sx, sz = heightmap.shape

    tree_counter = {}

    # Scan a grid across the whole slice instead of random sampling. 
    # A step of 2 is fast and guarantees we catch standard tree trunks.
    for lx in range(0, sx, 2):
        for lz in range(0, sz, 2):
            global_x = ox + lx
            global_z = oz + lz
            
            y = int(heightmap[lx, lz])

            # Check down a few blocks (heightmaps often return Y+1)
            for dy in range(0, -5, -1):
                try:
                    block = worldslice.getBlock((lx,y + dy, lz))
                    
                    # Compatible with both GDPC 1.x (Block objects) and older versions (strings)
                    raw_id = block.id if hasattr(block, "id") else block
                    block_id = raw_id.split(":")[-1]

                    if "log" in block_id or "stem" in block_id:
                        tree_counter[block_id] = tree_counter.get(block_id, 0) + 1
                        break # Found the trunk, break the Y loop and move to the next X/Z
                        
                except Exception as e:
                    print(f"ERROR reading block at {global_x}, {global_z}: {e}")

    if not tree_counter:
        # Fallback if literally zero trees exist in the entire biome (e.g., plain desert/plains)
        return "oak_log"
        
    # Return the most frequent tree type found
    return max(tree_counter, key=tree_counter.get)

def get_palette(worldslice, heightmap,origin):
    print("CODE RUNNING")
    tree = tree_scanner(worldslice, heightmap, origin)
    print("Detected tree type:", tree)
    #tree_map ={
        # "oak_log" : "oak",
        # "spruce_log" : "spruce",
        # "birch_log" : "birch",
        # "jungle_log" : "jungle",
        # "acacia_log" : "acacia",
        # "dark_oak_log" : "dark_oak",
        # "mangrove_log" : "mangrove",
        # "cherry_log" :"cherry",
        # "pale_oak_log" : "pale_oak",
        # "crimson_stem" : "crimson",
        # "warped_stem" : "warped"
    #}
    wood = tree.replace("_log","").replace("_stem","")
    pillar_type = "stem" if "stem" in tree else "log"
    return{
        "floor":random.choice(["cobblestone", f"{wood}_planks"]),
        "pillars": f"{wood}_{pillar_type}",
        "walls": f"{wood}_planks",
        "roof":random.choice([f"{wood}_stairs", "cobblestone_stairs"])
    }
        

   

