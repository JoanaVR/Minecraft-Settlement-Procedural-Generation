import random
import heapq
from math import copysign

# def get_height(heightmap, x, z):
#     return heightmap[(x, z)]

class Node:
    def __init__(self, pos, g=0, h=0, parent=None):
        self.pos = pos
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def terrain_cost(heightmap, a, b):

    h1 = heightmap[a]
    h2 = heightmap[b]

    height_diff = abs(h1 - h2)

    # punish steep slopes
    return 1 + height_diff * 3

def astar(start, goal, heightmap, origin):

    ox, oz = origin

    size_x, size_z = heightmap.shape

    open_list = []
    closed = set()

    heapq.heappush(
        open_list,
        Node(start, 0, heuristic(start, goal))
    )

    directions = [(1,0),(-1,0),(0,1),(0,-1)]

    def valid(pos):
        lx = pos[0] - ox
        lz = pos[1] - oz

        return (
            0 <= lx < size_x and
            0 <= lz < size_z
        )

    def height(pos):
        lx = pos[0] - ox
        lz = pos[1] - oz
        return heightmap[lx, lz]

    while open_list:

        current = heapq.heappop(open_list)

        if current.pos == goal:
            path = []
            while current:
                path.append(current.pos)
                current = current.parent
            return path[::-1]

        closed.add(current.pos)

        for dx, dz in directions:

            nxt = (
                current.pos[0] + dx,
                current.pos[1] + dz
            )

            if not valid(nxt):
                continue

            if nxt in closed:
                continue

            h1 = height(current.pos)
            h2 = height(nxt)

            cost = 1 + abs(h1 - h2) * 3

            node = Node(
                nxt,
                current.g + cost,
                heuristic(nxt, goal),
                current
            )

            heapq.heappush(open_list, node)

    return []


def far_enough(pos, houses, min_dist=7):
    for hx, _, hz, _ in houses:
        if abs(pos[0]-hx) + abs(pos[1]-hz) < min_dist:
            return False
    return True

def facing_from_offset(dx, dz):

    if dx == 1:
        return "west"
    elif dx == -1:
        return "east"
    elif dz == 1:
        return "north"
    elif dz == -1:
        return "south"

    return "north"   # safe fallback


def place_houses_along_path(path, heightmap, origin):

    ox, oz = origin
    sx, sz = heightmap.shape

    def valid(x,z):
        lx = x - ox
        lz = z - oz
        return 0 <= lx < sx and 0 <= lz < sz

    def height(x,z):
        return heightmap[x-ox, z-oz]

    houses = []

    offsets = [
        (2,0), (-2,0),
        (0,2), (0,-2)
    ]

    for i in range(5, len(path), 6):

        px, pz = path[i]

        random.shuffle(offsets)

        for dx, dz in offsets:

            hx = px + dx
            hz = pz + dz

            if not valid(hx, hz):
                continue

            if not far_enough((hx, hz), houses):
                continue

            facing = facing_from_offset(dx, dz)
            hy = height(hx, hz)

            houses.append((hx, hy, hz, facing))
            break

    return houses

def generate_village_layout(start, goal, heightmap, origin):

    path = astar(start, goal, heightmap, origin)

    houses = place_houses_along_path(
        path,
        heightmap,
        origin
    )

    return path, houses

# def generate_village_layout(buildArea, heightmap, road_length=80):


#     road_positions = []
#     house_plots = []
#     occupied = []

#     # Start near center
#     x = buildArea.offset.x + buildArea.size.x // 2
#     z = buildArea.offset.z + buildArea.size.z // 2

#     direction = (1, 0)  # start east
#     ROAD_WIDTH = 3
#     HOUSE_OFFSET = 8
#     MIN_SPACING = 12

#     last_house_step = 0

#     for step in range(road_length):

#         local_x = x - buildArea.offset.x
#         local_z = z - buildArea.offset.z

#         if not (0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z):
#             break

#         y = heightmap[local_x, local_z] - 1
#         road_positions.append((x, y, z))

#         # === Controlled slight turns (natural feel) ===
#         if random.random() < 0.12:
#             if direction[0] != 0:
#                 direction = (0, int(copysign(1, random.choice([-1, 1]))))
#             else:
#                 direction = (int(copysign(1, random.choice([-1, 1]))), 0)

#         # === House placement spacing control ===
#         if step - last_house_step > MIN_SPACING:

#             for side in [-1, 1]:  # left & right

#                 depth = random.randint(5, 8)
#                 width = 4
#                 height = random.randint(4, 6)

#                 # Perpendicular offset from road
#                 if direction[0] != 0:
#                     hx = x
#                     hz = z + side * HOUSE_OFFSET
#                     facing = "north" if side > 0 else "south"
#                 else:
#                     hx = x + side * HOUSE_OFFSET
#                     hz = z
#                     facing = "west" if side > 0 else "east"

#                 x1 = hx
#                 z1 = hz
#                 x2 = hx + width
#                 z2 = hz + depth

#                 # Overlap check
#                 overlap = False
#                 for ox1, oz1, ox2, oz2 in occupied:
#                     if not (x2 < ox1 or x1 > ox2 or z2 < oz1 or z1 > oz2):
#                         overlap = True
#                         break

#                 if not overlap:
#                     local_x = hx - buildArea.offset.x
#                     local_z = hz - buildArea.offset.z

#                     if 0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z:
#                         hy = heightmap[local_x, local_z] - 1

#                         house_plots.append({
#                             "x": hx,
#                             "y": hy,
#                             "z": hz,
#                             "depth": depth,
#                             "height": height,
#                             "facing": facing
#                         })

#                         occupied.append((x1, z1, x2, z2))

#                         last_house_step = step

#         x += direction[0]
#         z += direction[1]

#     return road_positions, house_plots


# import heapq

# def astar_path(buildArea, heightmap, start, goal):
#     """Terrain-aware A* returning list of (x, y, z)"""
#     def heuristic(a, b):
#         return abs(a[0]-b[0]) + abs(a[1]-b[1])

#     def neighbors(pos):
#         x, z = pos
#         for dx, dz in [(-1,0),(1,0),(0,-1),(0,1)]:
#             nx, nz = x+dx, z+dz
#             if 0 <= nx - buildArea.offset.x < buildArea.size.x and 0 <= nz - buildArea.offset.z < buildArea.size.z:
#                 yield (nx, nz)

#     start_node = start
#     goal_node = goal
#     open_set = []
#     heapq.heappush(open_set, (0, start_node))
#     came_from = {}
#     g_score = {start_node: 0}

#     while open_set:
#         current_f, current = heapq.heappop(open_set)
#         if current == goal_node:
#             # reconstruct path
#             path = []
#             node = current
#             while node in came_from:
#                 x, z = node
#                 y = heightmap[x - buildArea.offset.x, z - buildArea.offset.z]
#                 path.append((x, y, z))
#                 node = came_from[node]
#             x, z = start_node
#             path.append((x, heightmap[x - buildArea.offset.x, z - buildArea.offset.z], z))
#             return path[::-1]
        
#         for neighbor in neighbors(current):
#             nx, nz = neighbor
#             x_cur, z_cur = current
#             y_cur = heightmap[x_cur - buildArea.offset.x, z_cur - buildArea.offset.z]
#             y_next = heightmap[nx - buildArea.offset.x, nz - buildArea.offset.z]
#             cost = 1 + abs(y_next - y_cur)
#             tentative_g = g_score[current] + cost
#             if neighbor not in g_score or tentative_g < g_score[neighbor]:
#                 came_from[neighbor] = current
#                 g_score[neighbor] = tentative_g
#                 f_score = tentative_g + heuristic(neighbor, goal_node)
#                 heapq.heappush(open_set, (f_score, neighbor))
#     return []

# def connect_all_houses(buildArea, heightmap, house_plots):
#     """
#     Connects all houses with A* roads.
#     house_plots: list of dicts with 'x', 'z' (and 'y' optional)
#     Returns: list of all (x, y, z) road positions
#     """
#     road_positions = []
#     if not house_plots:
#         return road_positions

#     # Choose first house as hub
#     hub = house_plots[0]
#     hub_pos = (hub['x'], hub['z'])

#     connected = {0}
#     to_connect = set(range(1, len(house_plots)))

#     while to_connect:
#         best_pair = None
#         best_dist = float('inf')
#         # Find closest unconnected house
#         for idx in to_connect:
#             house = house_plots[idx]
#             house_pos = (house['x'], house['z'])
#             dist = abs(hub_pos[0] - house_pos[0]) + abs(hub_pos[1] - house_pos[1])
#             if dist < best_dist:
#                 best_dist = dist
#                 best_pair = (hub_pos, house_pos, idx)
#         # Generate A* path
#         start, goal, idx = best_pair
#         path = astar_path(buildArea, heightmap, start, goal)
#         road_positions.extend(path)
#         # Mark as connected
#         connected.add(idx)
#         to_connect.remove(idx)
#         # Optionally: next hub can be this house for branching
#         hub_pos = goal

#     return road_positions