import numpy as np
from collections import Counter
import math
import heapq
from path_finding import astar_to_network, get_height, is_water_ws, heuristic


class SettlementEvaluator:
    
    def reachability_score(self, buildings, road_tiles, heightmap, origin, worldslice=None):

        if not buildings or len(buildings) < 2:
            return 100.0
        
        # Extract building center positions (using door position as representative point)
        building_positions = []
        for x, y, z, depth, facing in buildings:
            # Center of building footprint
            center_x = x + 2
            center_z = z + depth // 2
            building_positions.append((center_x, center_z))
        
        # Fast check: how many buildings are within 20 blocks of a road?
        reachable_buildings = 0
        for bx, bz in building_positions:
            # Check if this building is close to any road tile
            for rx, rz in road_tiles:
                if abs(bx - rx) <= 20 and abs(bz - rz) <= 20:
                    reachable_buildings += 1
                    break
        
        return (reachable_buildings / len(buildings) * 100) if buildings else 100.0
    
    
    def topographic_compliance(self, buildings, heightmap, origin):

        if not buildings:
            return 0, 0, 0, 0
        
        all_deltas = []
        
        for x, y, z, depth, facing in buildings:
            # Sample the building footprint at regular intervals
            for dx in range(0, 5):
                for dz in range(max(0, 0), depth):
                    natural_height = get_height(heightmap, x + dx, z + dz, origin)
                    if natural_height is not None:
                        delta = abs(y - natural_height)
                        all_deltas.append(delta)
        
        if not all_deltas:
            return 0, 0, 0, 0
        
        mean_delta = np.mean(all_deltas)
        max_delta = np.max(all_deltas)
        min_delta = np.min(all_deltas)
        
        return mean_delta, max_delta, min_delta, len(buildings)
    
    
    def analyze_block_distribution(self, palette):
        """
        Analyze blocks used in a single village based on palette.
        Focuses ONLY on wood types (which vary by biome).
        Ignores: air, dirt_path, lantern, cobblestone (constant across biomes).
        
        Args:
            palette: Dict with keys 'walls', 'floor', 'pillars', 'roof'
        
        Returns:
            dict with:
                - wood_type: Extracted wood type name
                - wood_blocks: List of all wood-based block types
                - distribution: Counter of wood blocks only
        """
        wood_blocks = Counter()
        
        # Extract wood type from palette
        wood_type = "unknown"
        if "pillars" in palette:
            pillar = palette["pillars"]
            wood_type = pillar.replace("_log", "").replace("_stem", "").replace("_planks", "")
        
        # Only track wood-based blocks (what changes with biome)
        wood_materials = {
            "walls": palette.get("walls", "oak_log"),
            "floor": palette.get("floor", "oak_planks"),
            "pillars": palette.get("pillars", "oak_log"),
            "roof": palette.get("roof", "oak_stairs"),
        }
        
        # Weight: walls and pillars are heavy (many blocks)
        for block_type, count in [("walls", 40), ("pillars", 30), ("floor", 20), ("roof", 10)]:
            if block_type in wood_materials:
                wood_blocks[wood_materials[block_type]] += count
        
        return {
            "wood_type": wood_type,
            "wood_blocks": list(wood_blocks.keys()),
            "distribution": wood_blocks
        }
    
    
    def structural_diversity(self, block_distributions):
        """
        Calculate Shannon Entropy of block type distributions across settlements.
        
        Args:
            block_distributions: List of Counter dicts
        
        Returns:
            tuple: (mean_entropy, max_entropy, min_entropy, num_settlements)
        """

        if not block_distributions or len(block_distributions) == 0:
            return 0, 0, 0, 0
        
        entropies = []
        
        for distribution in block_distributions:
            if not distribution or sum(distribution.values()) == 0:
                entropies.append(0)
                continue
            
            total = sum(distribution.values())
            entropy = 0.0
            
            for count in distribution.values():
                if count > 0:
                    p = count / total
                    entropy -= p * math.log2(p)
            
            entropies.append(entropy)
        
        if not entropies:
            return 0, 0, 0, 0
        
        mean_entropy = np.mean(entropies)
        max_entropy = np.max(entropies)
        min_entropy = np.min(entropies)
        
        return mean_entropy, max_entropy, min_entropy, len(block_distributions)
    
    
    def format_report(self, reachability_pct, topo_compliance, diversity_results):

        report = "\n" + "="*70 + "\n"
        report += "SETTLEMENT GENERATION EVALUATION REPORT\n"
        report += "="*70 + "\n\n"
        
        # Reachability Score
        report += "1. REACHABILITY SCORE\n"
        report += "-" * 70 + "\n"
        report += f"   Buildings Mutually Reachable: {reachability_pct:.1f}%\n"
        report += "   EXCELLENT (>90%): Settlers can traverse the whole village\n"
        report += "   GOOD (70-90%): Most buildings connected, some isolated clusters\n"
        report += "   POOR (<70%): Significant pathfinding issues\n\n"
        
        # Topographic Compliance
        report += "2. TOPOGRAPHIC COMPLIANCE (Delta-Height in blocks)\n"
        report += "-" * 70 + "\n"
        mean_delta, max_delta, min_delta, num_buildings = topo_compliance
        report += f"   Average Height Difference: {mean_delta:.2f} blocks\n"
        report += f"   Maximum Height Difference: {max_delta:.2f} blocks\n"
        report += f"   Minimum Height Difference: {min_delta:.2f} blocks\n"
        report += f"   Buildings Analyzed: {num_buildings}\n"
        report += "   EXCELLENT (<0.75): Perfect terrain adaptation\n"
        report += "   GOOD (0.75-3.0): Buildings sit naturally on terrain\n"
        report += "   POOR (≥3.0): Buildings floating/sinking into terrain\n\n"
        
        # Structural Diversity
        report += "3. STRUCTURAL DIVERSITY (Shannon Entropy)\n"
        report += "-" * 70 + "\n"
        mean_entropy, max_entropy, min_entropy, num_settlements = diversity_results
        report += f"   Average Entropy: {mean_entropy:.2f} bits\n"
        report += f"   Max Entropy: {max_entropy:.2f} bits\n"
        report += f"   Min Entropy: {min_entropy:.2f} bits\n"
        report += f"   Settlements Analyzed: {num_settlements}\n"
        report += "   HIGH (>4.0): Excellent material diversity\n"
        report += "   MEDIUM (2.0-4.0): Good variety, some patterns repeat\n"
        report += "   LOW (<2.0): Mode collapse - same designs generated\n\n"
        
        report += "="*70 + "\n"
        
        return report


def evaluate_single_settlement(buildings, farms, road_tiles, center, exact_building_tiles, 
                               heightmap, worldslice, origin, palette):

    evaluator = SettlementEvaluator()
    
    # Reachability: all buildings (houses + farms)
    all_buildings = buildings + [(x, y, z) for x, y, z in farms]
    if len(buildings) > 0:  # Convert farms to needed format
        all_buildings_full = buildings + [(fx, get_height(heightmap, fx, fz, origin), fz, 9, "north") 
                                          for fx, fy, fz in farms]
    else:
        all_buildings_full = buildings
    
    reachability = evaluator.reachability_score(all_buildings_full, road_tiles, heightmap, origin, worldslice)
    
    # Topographic compliance
    topo = evaluator.topographic_compliance(all_buildings_full, heightmap, origin)
    
    # Block distribution based on palette
    block_analysis = evaluator.analyze_block_distribution(palette)
    
    return reachability, topo, block_analysis
