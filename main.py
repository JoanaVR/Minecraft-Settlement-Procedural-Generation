import numpy as np
from gdpc import Editor, WorldSlice

import build_houses 
import path_finding


def main():

    editor = Editor(buffering=True)
    build_area = editor.getBuildArea()
    ws = WorldSlice(build_area.toRect())
    heightmap = np.array(ws.heightmaps["MOTION_BLOCKING_NO_LEAVES"])

    path_finding.generate_village(editor, build_area, heightmap, worldslice=ws, num_houses=10, num_farms=2)
    editor.flushBuffer()

if __name__ == "__main__":
    main()