import numpy as np
from gdpc import Editor, WorldSlice
import path_finding
from evaluation import SettlementEvaluator
from collections import Counter
import json
import os
from datetime import datetime


def main():
    print("Connecting to Minecraft... (Ensure GDPC mod/server is running)")
    editor = Editor(buffering=True)
    build_area = editor.getBuildArea()
    
    print(f"Build area bounded by: {build_area.toRect()}")
    ws = WorldSlice(build_area.toRect())
    heightmap = np.array(ws.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
    origin = (build_area.offset.x, build_area.offset.z)

    # Generate the layout first (to evaluate it)
    print("\nGenerating settlement layout...")
    buildings, farms, road_tiles, center, exact_building_tiles = path_finding.generate_layout(
        ws, heightmap, origin, num_houses=12, num_farms=2
    )
    
    if not buildings and not farms:
        print("ERROR: No valid layout generated. Aborting.")
        return
    
    # Evaluate the generated layout
    print("Evaluating settlement...")
    evaluator = SettlementEvaluator()
    palette = path_finding.get_palette(ws, heightmap, origin)
    
    all_buildings = buildings.copy()
    for fx, fy, fz in farms:
        all_buildings.append((fx, fy, fz, 9, "north"))
    
    print(f"  Computing reachability ({len(all_buildings)} buildings)...", end="", flush=True)
    reachability = evaluator.reachability_score(all_buildings, road_tiles, heightmap, origin, ws)
    print(" ✓")
    
    print(f"  Computing topographic compliance...", end="", flush=True)
    mean_delta, max_delta, min_delta, _ = evaluator.topographic_compliance(all_buildings, heightmap, origin)
    print(" ✓")
    
    block_dist = Counter()
    for _ in exact_building_tiles:
        block_dist[palette.get("walls", "oak_log")] += 1
    for _ in road_tiles:
        block_dist["dirt_path"] += 1
    
    diversity_mean, diversity_max, diversity_min, _ = evaluator.structural_diversity([block_dist])
    
    # Save evaluation results
    results = {
        "timestamp": datetime.now().isoformat(),
        "location": {"x": origin[0], "z": origin[1]},
        "settlement": {
            "num_houses": len(buildings),
            "num_farms": len(farms),
            "num_roads": len(road_tiles),
            "center": center
        },
        "metrics": {
            "reachability_pct": float(reachability),
            "avg_height_delta": float(mean_delta),
            "max_height_delta": float(max_delta),
            "diversity_entropy": float(diversity_mean)
        }
    }
    
    # Create results directory if it doesn't exist
    os.makedirs("evaluation_results", exist_ok=True)
    
    # Save to timestamped file
    filename = f"evaluation_results/settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {filename}")
    print(f"  Reachability: {reachability:.1f}%")
    print(f"  Avg Height Delta: {mean_delta:.2f} blocks")
    print(f"  Diversity Entropy: {diversity_mean:.2f} bits")
    
    # Now build the village in Minecraft
    print("\nBuilding settlement in Minecraft...")
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
