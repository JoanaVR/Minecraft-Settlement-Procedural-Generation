block_palettes={
    "Plains":{
        "walls": ["Oak_Planks", "oak_logs", "cobblestone"],
        "floor": ["grass"],
        "roof": ["cobblestone", "oak_wood"]},

    "Woodlands":{
        "walls": ["dark_oak_planks","dark_oak_logs", "cobblestone"],
        "floor": ["Birch_wood_planks"],
        "roof": ["dark_oak_planks", "dark_oak_stairs", "cobblestone_stairs"]},

    "Caves":{
        "walls": ["stone", "deepslate", "gravel"],
        "floor": ["stone", "deepslate", "moss_blocks"],
        "roof": ["sculk_blocks", "deepslate", "stone", "moss_blocks", "cave_vines"]},

    "Mountains":{
        "walls" : ["stone", "deepslate", "spruce_logs", "granite", "snow_blocks"],
        "floor": ["stone", "gravel", "snow", "calcite"],
        "roof": ["snow", "dark_oakwood_slabs", "spruce_wood_stairs"]},

    "Swamps":{
        "walls": ["mud_bricks", "magrove_planks"],
        "floor": ["mud", "muddy_mangrove_roots", "moss_carpet", "grass_blocks", "clay", "water"],
        "roof": ["mangrove_planks", "mangrove_stairs", "mud_bricks", "dark_oak_planks"]},

    "Sandy Areas":{
        "walls": ["sandstone", "terracotta", "Concrete"],
        "floor": ["sand", "red_sand", "sandstone", "soul_sand"],
        "roof": ["sandstoneTerracottaMud_Bricks", "sandstone_stairs", "terracotta", "mud_brick_stairs"]},

    "Water Areas":{
        "walls": ["sand", "gravel", "dirt", "stone_bricks", "prismarine", "dark_prismarine"],
        "floor": ["gravelsandclay", "dirt"],
        "roof": ["prismarine", "stone_bricks", "sandstone"]},

    "The Nether Biomes":{
        "walls": ["netherrack", "basalt", "blackstone", "nether_bricks"],
        "floor": ["nether_wastes", "crimson_forest", "warped_forest"],
        "roof": ["bedrock", "nether_ceiling"]},

    "The End Biomes":{
        "walls": ["purpur_blocks", "purpur_pillars", "end_stone_bricks"],
        "floor": ["end_stone", "obsidian"],
        "roof":["end_stone_bricks", "obsidian", "purpur_stairs"]}
}

##add windows, doors
import random
def biome_palette(biome):
    if biome in block_palettes:
        palette = block_palettes[biome]
    else:
        palette= block_palettes["Plains"]

    palette_selection={
        "walls": random.choice(palette["walls"]),
        "floor": random.choice(palette["floor"]),
        "roof": random.choice(palette["roof"])
    }
    return palette_selection
    
print(biome_palette("Plains"))
print(biome_palette("Caves"))
print(biome_palette("Mountains"))
print(biome_palette("Unknown"))