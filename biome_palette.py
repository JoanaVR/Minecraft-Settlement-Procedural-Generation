import random

def tree_scanner(worldslice, heightmap, origin):
    ox, oz = origin
    sx, sz = heightmap.shape

    tree_counter = {}

    
    for lx in range(0, sx, 2):
        for lz in range(0, sz, 2):
            global_x = ox + lx
            global_z = oz + lz
            
            y = int(heightmap[lx, lz])

            # Check down a few blocks of the tree log
            for dy in range(0, -5, -1):
                try:
                    block = worldslice.getBlock((lx,y + dy, lz))
                    
                    
                    full_id = block.id if hasattr(block, "id") else block
                    block_id = full_id.split(":")[-1]

                    if "log" in block_id or "stem" in block_id:
                        tree_counter[block_id] = tree_counter.get(block_id, 0) + 1
                        break 
                        
                except Exception as e:
                    print(f"ERROR reading block at {global_x}, {global_z}: {e}")

    if not tree_counter:
        # If trees are not detected:
        return "oak_log"
        
    
    return max(tree_counter, key=tree_counter.get)

def get_palette(worldslice, heightmap,origin):
    print("CODE RUNNING")
    tree = tree_scanner(worldslice, heightmap, origin)
    print("Detected tree type:", tree)
 
    wood = tree.replace("_log","").replace("_stem","")
    pillar_type = "stem" if "stem" in tree else "log"
    return{
        "floor":random.choice(["cobblestone", f"{wood}_planks"]),
        "pillars": f"{wood}_{pillar_type}",
        "walls": f"{wood}_{pillar_type}",
        "roof":f"{wood}_stairs"
    }
        

   

