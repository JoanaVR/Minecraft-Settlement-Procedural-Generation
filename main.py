from gdpc import Editor, Block

import flat_settlement
from path_finding import generate_village_layout



def main():
    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()

    editor.loadWorldSlice(cache=True)
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    road_positions, house_plots = generate_village_layout(buildArea, heightmap)

    # Build road
    for x, y, z in road_positions:
        editor.placeBlock((x, y, z), Block("dirt_path"))

    # Build houses
    for house in house_plots:
        flat_settlement.build_robust_house(
            editor,
            house["x"],
            house["y"],
            house["z"],
            house["depth"],
            house["height"],
            Block("oak_planks"),
            Block("stone_bricks"),
            house["facing"]
    )

    editor.flushBuffer()
    print("Village generated.")

if __name__ == "__main__":
    main()