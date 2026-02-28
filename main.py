from gdpc import Editor, Block

import build_houses 
from path_finding import *

def get_height(heightmap, origin, x, z):
    ox, oz = origin
    return heightmap[x-ox, z-oz]

def main():
    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()

    editor.loadWorldSlice(cache=True)
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    origin_x = buildArea.begin[0]
    origin_z = buildArea.begin[2]

    start = (
        buildArea.begin[0] + 5,
        buildArea.begin[2] + 5
    )

    goal = (
        buildArea.end[0] - 5,
        buildArea.end[2] - 5
    )

    path, houses = generate_village_layout(
        start=start,
        goal=goal,
        heightmap=heightmap,
        origin=(buildArea.begin[0], buildArea.begin[2])
    )

    for x,z in path:
        lx = x - origin_x
        lz = z - origin_z

        y = get_height(heightmap,(origin_x, origin_z),x, z)
        editor.placeBlock((x,y,z), Block("dirt_path"))

    for x,y,z,facing in houses:
        build_houses.build_robust_house(
        editor,
        x,y,z,
        depth=6,
        height=4,
        wall=Block("oak_planks"),
        floor=Block("cobblestone"),
        facing=facing
    )


    # # Build road
    # for x, y, z in road_positions:
    #     editor.placeBlock((x, y, z), Block("dirt_path"))

    # # Build houses
    # for house in house_plots:
    #     flat_settlement.build_robust_house(
    #         editor,
    #         house["x"],
    #         house["y"],
    #         house["z"],
    #         house["depth"],
    #         house["height"],
    #         Block("oak_planks"),
    #         Block("stone_bricks"),
    #         house["facing"]
    # )

    # editor.flushBuffer()
    # editor = Editor(buffering=True)

    # house_plots is the list returned from your village generator
    # each house dict has keys 'x', 'y', 'z', 'depth', etc.


    editor.flushBuffer()
    print("Village generated.")

if __name__ == "__main__":
    main()