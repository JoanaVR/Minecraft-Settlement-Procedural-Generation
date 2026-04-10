import json
import os
import numpy as np
from datetime import datetime
from collections import Counter
import math


def aggregate_results():
    
    results_dir = "evaluation_results"
    
    if not os.path.exists(results_dir):
        print(f"ERROR: {results_dir} directory not found!")
        print("Run main.py multiple times in different locations to generate results first.")
        return
    
    # Load all results
    all_results = []
    files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json') and f != 'AGGREGATE_REPORT.json'])
    
    if not files:
        print(f"ERROR: No results found in {results_dir}")
        return
    
    print(f"Loading {len(files)} settlement evaluations...\n")
    
    for filename in files:
        filepath = os.path.join(results_dir, filename)
        try:
            with open(filepath, 'r') as f:
                result = json.load(f)
                all_results.append(result)
                print(f"  {filename}")
        except Exception as e:
            print(f"  ERROR reading {filename}: {e}")
    
    if not all_results:
        print("No valid results to aggregate.")
        return
    
    # Extract metrics
    reachabilities = [r["metrics"]["reachability_pct"] for r in all_results]
    heights = [r["metrics"]["avg_height_delta"] for r in all_results]
    entropies = [r["metrics"]["diversity_entropy"] for r in all_results]
    
    # Extract wood types only (ignore constant blocks like air, dirt_path, lantern, cobblestone)
    wood_types = [r.get("materials", {}).get("wood_type", "unknown") for r in all_results if "materials" in r]
    
    # Count unique wood block types used across all settlements
    unique_wood_blocks = set()
    for r in all_results:
        if "materials" in r and "wood_blocks" in r["materials"]:
            unique_wood_blocks.update(r["materials"]["wood_blocks"])
    
    # Calculate statistics
    print("\n" + "="*70)
    print("AGGREGATE STATISTICS")
    print("="*70 + "\n")
    
    print(f"Total Settlements Evaluated: {len(all_results)}\n")
    
    # Reachability
    print("REACHABILITY SCORE (% of buildings mutually connected):")
    print(f"  Average:    {np.mean(reachabilities):.1f}%")
    print(f"  Median:     {np.median(reachabilities):.1f}%")
    print(f"  Std Dev:    {np.std(reachabilities):.1f}%")
    print(f"  Min:        {np.min(reachabilities):.1f}%")
    print(f"  Max:        {np.max(reachabilities):.1f}%")
    
    reach_excellent = sum(1 for r in reachabilities if r >= 90)
    reach_good = sum(1 for r in reachabilities if 70 <= r < 90)
    reach_poor = sum(1 for r in reachabilities if r < 70)
    print(f"  Grade: {reach_excellent} EXCELLENT (≥90%), {reach_good} GOOD (70-90%), {reach_poor} POOR (<70%)")
    print()
    
    # Topographic Compliance
    print("TOPOGRAPHIC COMPLIANCE (Avg Height Delta in blocks):")
    print(f"  Average:    {np.mean(heights):.2f} blocks")
    print(f"  Median:     {np.median(heights):.2f} blocks")
    print(f"  Std Dev:    {np.std(heights):.2f} blocks")
    print(f"  Min:        {np.min(heights):.2f} blocks")
    print(f"  Max:        {np.max(heights):.2f} blocks")
    
    topo_excellent = sum(1 for h in heights if h < 1)
    topo_good = sum(1 for h in heights if 1 <= h < 3.0)
    topo_poor = sum(1 for h in heights if h >= 3.0)
    print(f"  Grade: {topo_excellent} EXCELLENT (<1), {topo_good} GOOD (1-3.0), {topo_poor} POOR (≥3.0)")
    print()
    
    # Structural Diversity
    print("STRUCTURAL DIVERSITY (Shannon Entropy in bits):")
    print(f"  Average:    {np.mean(entropies):.2f} bits")
    print(f"  Median:     {np.median(entropies):.2f} bits")
    print(f"  Std Dev:    {np.std(entropies):.2f} bits")
    print(f"  Min:        {np.min(entropies):.2f} bits")
    print(f"  Max:        {np.max(entropies):.2f} bits")
    
    div_excellent = sum(1 for e in entropies if e >= 4.0)
    div_good = sum(1 for e in entropies if 2.0 <= e < 4.0)
    div_poor = sum(1 for e in entropies if e < 2.0)
    print(f"  Grade: {div_excellent} EXCELLENT (≥4.0), {div_good} GOOD (2.0-4.0), {div_poor} POOR (<2.0)")
    print()    
    # Wood Type Diversity
    print("WOOD TYPE DIVERSITY (Across All Settlements):")
    wood_distribution = Counter(wood_types)
    wood_entropy = 0.0
    
    print(f"  Unique Wood Types: {len(wood_distribution)}")
    
    # Check if any wood type exceeds 40% threshold
    max_wood_percentage = 0
    max_wood_type = None
    for wood, count in wood_distribution.most_common():
        percentage = (count / len(wood_types) * 100) if wood_types else 0
        print(f"    {wood:15} : {count:2d} villages ({percentage:5.1f}%)", end="")
        
        if percentage > max_wood_percentage:
            max_wood_percentage = percentage
            max_wood_type = wood
        
        if percentage > 40:
            print(" EXCEEDS 40% THRESHOLD")
        else:
            print()
    
    # Calculate wood type entropy
    if wood_types:
        total_woods = len(wood_types)
        for count in wood_distribution.values():
            if count > 0:
                p = count / total_woods
                wood_entropy -= p * math.log2(p)
        print(f"\n  Wood Type Entropy: {wood_entropy:.2f} bits", end="")
        
        if wood_entropy >= 2.0:
            print(" HIGH - Good variety of wood types used")
        elif wood_entropy >= 1.0:
            print(" MEDIUM - Some wood type repetition")
        else:
            print(" LOW - Wood types not varying (possible mode collapse)")
        
        # Diversity constraint check
        print(f"\n  DIVERSITY CHECK (Max 40% per wood type):", end=" ")
        if max_wood_percentage <= 40:
            print(f"PASS - Largest: {max_wood_type} ({max_wood_percentage:.1f}%)")
        else:
            print(f"FAIL - {max_wood_type} used in {max_wood_percentage:.1f}% of villages (exceeds 40%)")
    print()
    
    # Block Type Diversity
    print("WOOD BLOCK TYPES USED (Across All Settlements):")
    print(f"  Unique Wood Block Types: {len(unique_wood_blocks)}")
    for block in sorted(unique_wood_blocks):
        print(f"    - {block}")
    print()    
    # Settlement details
    print("SETTLEMENT COMPOSITION:")
    total_houses = sum(r["settlement"]["num_houses"] for r in all_results)
    total_farms = sum(r["settlement"]["num_farms"] for r in all_results)
    total_roads = sum(r["settlement"]["num_roads"] for r in all_results)
    
    print(f"  Total Houses Planned: {total_houses} ({total_houses/len(all_results):.1f} per settlement)")
    print(f"  Total Farms:          {total_farms} ({total_farms/len(all_results):.1f} per settlement)")
    print(f"  Total Road Tiles:     {total_roads} ({total_roads/len(all_results):.1f} per settlement)")
    print()
    
    # Overall assessment
    print("OVERALL ASSESSMENT:")
    print("-" * 70)
    
    avg_reach = np.mean(reachabilities)
    avg_topo = np.mean(heights)
    avg_div = np.mean(entropies)
    
    print(f"Settlement Connectivity: ", end="")
    if avg_reach >= 85:
        print("EXCELLENT - Road network connects most buildings")
    elif avg_reach >= 70:
        print("GOOD - Most buildings reachable, some isolated clusters")
    else:
        print("NEEDS WORK - Poor connectivity, improve pathfinding")
    
    print(f"Terrain Adaptation:      ", end="")
    if avg_topo < 0.75:
        print("EXCELLENT - Buildings fit naturally on terrain")
    elif avg_topo < 3.0:
        print("GOOD - Acceptable terrain fit")
    else:
        print("NEEDS WORK - Buildings floating/sinking, improve slope tolerance")
    
    print(f"Wood Type Diversity:     ", end="")
    if max_wood_percentage <= 40 and len(wood_distribution) >= 3:
        print("EXCELLENT - Multiple biomes with balanced wood type distribution")
    elif max_wood_percentage <= 40 and len(wood_distribution) >= 2:
        print("GOOD - Different wood types per biome, passes 40% threshold")
    elif max_wood_percentage <= 50:
        print("ACCEPTABLE - Wood types used but some bias toward one type")
    else:
        print("NEEDS WORK - One wood type dominates (>50%)")
    
    print("\n" + "="*70)
    
    # Save aggregate report
    report = {
        "generated": datetime.now().isoformat(),
        "num_settlements": len(all_results),
        "reachability": {
            "mean": float(np.mean(reachabilities)),
            "median": float(np.median(reachabilities)),
            "std": float(np.std(reachabilities)),
            "min": float(np.min(reachabilities)),
            "max": float(np.max(reachabilities))
        },
        "topographic": {
            "mean": float(np.mean(heights)),
            "median": float(np.median(heights)),
            "std": float(np.std(heights)),
            "min": float(np.min(heights)),
            "max": float(np.max(heights))
        },
        "diversity": {
            "mean": float(np.mean(entropies)),
            "median": float(np.median(entropies)),
            "std": float(np.std(entropies)),
            "min": float(np.min(entropies)),
            "max": float(np.max(entropies))
        },
        "wood_types": dict(wood_distribution),
        "unique_wood_types": len(wood_distribution),
        "wood_type_entropy": float(wood_entropy) if wood_types else 0,
        "max_wood_percentage": float(max_wood_percentage) if wood_types else 0,
        "max_wood_type": max_wood_type if wood_types else "unknown",
        "diversity_40percent_pass": bool(max_wood_percentage <= 40) if wood_types else False,
        "unique_wood_block_types": len(unique_wood_blocks),
        "wood_block_types": list(sorted(unique_wood_blocks))
    }
    
    report_file = "evaluation_results/AGGREGATE_REPORT.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nAggregate report saved to: {report_file}")


if __name__ == "__main__":
    aggregate_results()
