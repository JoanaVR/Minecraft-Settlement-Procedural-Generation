import random
from math import copysign

def generate_village_layout(buildArea, heightmap, road_length=80):


    road_positions = []
    house_plots = []
    occupied = []

    # Start near center
    x = buildArea.offset.x + buildArea.size.x // 2
    z = buildArea.offset.z + buildArea.size.z // 2

    direction = (1, 0)  # start east
    ROAD_WIDTH = 3
    HOUSE_OFFSET = 8
    MIN_SPACING = 12

    last_house_step = 0

    for step in range(road_length):

        local_x = x - buildArea.offset.x
        local_z = z - buildArea.offset.z

        if not (0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z):
            break

        y = heightmap[local_x, local_z] - 1
        road_positions.append((x, y, z))

        # === Controlled slight turns (natural feel) ===
        if random.random() < 0.12:
            if direction[0] != 0:
                direction = (0, int(copysign(1, random.choice([-1, 1]))))
            else:
                direction = (int(copysign(1, random.choice([-1, 1]))), 0)

        # === House placement spacing control ===
        if step - last_house_step > MIN_SPACING:

            for side in [-1, 1]:  # left & right

                depth = random.randint(5, 8)
                width = 4
                height = random.randint(4, 6)

                # Perpendicular offset from road
                if direction[0] != 0:
                    hx = x
                    hz = z + side * HOUSE_OFFSET
                    facing = "north" if side > 0 else "south"
                else:
                    hx = x + side * HOUSE_OFFSET
                    hz = z
                    facing = "west" if side > 0 else "east"

                x1 = hx
                z1 = hz
                x2 = hx + width
                z2 = hz + depth

                # Overlap check
                overlap = False
                for ox1, oz1, ox2, oz2 in occupied:
                    if not (x2 < ox1 or x1 > ox2 or z2 < oz1 or z1 > oz2):
                        overlap = True
                        break

                if not overlap:
                    local_x = hx - buildArea.offset.x
                    local_z = hz - buildArea.offset.z

                    if 0 <= local_x < buildArea.size.x and 0 <= local_z < buildArea.size.z:
                        hy = heightmap[local_x, local_z] - 1

                        house_plots.append({
                            "x": hx,
                            "y": hy,
                            "z": hz,
                            "depth": depth,
                            "height": height,
                            "facing": facing
                        })

                        occupied.append((x1, z1, x2, z2))

                        last_house_step = step

        x += direction[0]
        z += direction[1]

    return road_positions, house_plots