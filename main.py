import numpy as np
from gdpc import Editor, WorldSlice

import build_houses 
import path_finding

# def get_height(heightmap, origin, x, z):
#     ox, oz = origin
#     return heightmap[x-ox, z-oz]

def main():

    editor = Editor(buffering=True)
    build_area = editor.getBuildArea()
    ws = WorldSlice(build_area.toRect())
    heightmap = np.array(ws.heightmaps["MOTION_BLOCKING_NO_LEAVES"])

    path_finding.generate_village(editor, build_area, heightmap, worldslice=ws, num_houses=10, num_farms=2)
    editor.flushBuffer()
    # editor = Editor(buffering=True)
    # buildArea = editor.getBuildArea()

    # editor.loadWorldSlice(cache=True)
    # heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    # origin_x = buildArea.begin[0]
    # origin_z = buildArea.begin[2]

    # start = (
    #     buildArea.begin[0] + 5,
    #     buildArea.begin[2] + 5
    # )

    # goal = (
    #     buildArea.end[0] - 5,
    #     buildArea.end[2] - 5
    # )

    # path, houses = generate_village_layout(
    #     start=start,
    #     goal=goal,
    #     heightmap=heightmap,
    #     origin=(buildArea.begin[0], buildArea.begin[2])
    # )

    # for x,z in path:
    #     lx = x - origin_x
    #     lz = z - origin_z

    #     y = get_height(heightmap,(origin_x, origin_z),x, z)
    #     editor.placeBlock((x,y,z), Block("dirt_path"))

    # for x,y,z,facing in houses:
    #     build_houses.build_robust_house(
    #     editor,
    #     x,y,z,
    #     depth=6,
    #     height=4,
    #     wall=Block("oak_planks"),
    #     floor=Block("cobblestone"),
    #     facing=facing
    # )

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

if __name__ == "__main__":
    main()