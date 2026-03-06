import numpy as np
from gdpc import Editor, WorldSlice
import path_finding

def main():
    print("Connecting to Minecraft... (Ensure GDPC mod/server is running)")
    editor = Editor(buffering=True)
    build_area = editor.getBuildArea()
    
    print(f"Build area bounded by: {build_area.toRect()}")
    ws = WorldSlice(build_area.toRect())
    heightmap = np.array(ws.heightmaps["MOTION_BLOCKING_NO_LEAVES"])

    path_finding.generate_village(
        editor, 
        build_area, 
        heightmap, 
        worldslice=ws, 
        num_houses=12, 
        num_farms=2
    )
    
    print("Flushing buffer to place blocks...")
    editor.flushBuffer()
    print("Done!")

if __name__ == "__main__":
    main()
