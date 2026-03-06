import random

block_palettes = {
    "Plains": {
        "walls": ["oak_planks", "birch_planks"],
        "pillars": ["oak_log"],
        "floor": ["cobblestone", "oak_planks"],
        "roof": ["oak_stairs", "cobblestone_stairs"]
    },
    "Woodlands": {
        "walls": ["dark_oak_planks", "spruce_planks"],
        "pillars": ["dark_oak_log", "spruce_log"],
        "floor": ["birch_planks", "cobblestone"],
        "roof": ["dark_oak_stairs", "spruce_stairs"]
    },
    "Caves": {
        "walls": ["stone", "deepslate", "cobblestone"],
        "pillars": ["polished_deepslate", "stone_bricks"],
        "floor": ["moss_block", "gravel"],
        "roof": ["deepslate_brick_stairs", "stone_brick_stairs"]
    },
    "Mountains": {
        "walls": ["spruce_planks", "stone"],
        "pillars": ["spruce_log", "stone_bricks"],
        "floor": ["calcite", "gravel"],
        "roof": ["spruce_stairs", "dark_oak_stairs"]
    },
    "Sandy Areas": {
        "walls": ["smooth_sandstone", "terracotta"],
        "pillars": ["cut_sandstone", "chiseled_sandstone"],
        "floor": ["sandstone", "birch_planks"],
        "roof": ["sandstone_stairs", "smooth_sandstone_stairs"]
    }
}

def get_biome_palette(biome="Plains"):
    if biome in block_palettes:
        palette = block_palettes[biome]
    else:
        palette = block_palettes["Plains"]

    palette_selection = {
        "walls": random.choice(palette["walls"]),
        "pillars": random.choice(palette["pillars"]),
        "floor": random.choice(palette["floor"]),
        "roof": random.choice(palette["roof"])
    }
    return palette_selection

if __name__ == "__main__":
    print(get_biome_palette("Plains"))
    print(get_biome_palette("Mountains"))
