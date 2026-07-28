import math as ma, os, numpy as np, itasca as it


# parameters for generating / controlling the box size. using all caps for parameters, because i keep overwriting my box_x variables
INITIAL_BOX_SIZE_X = 1.0            
INITIAL_BOX_SIZE_Y = 1.0
INITIAL_FILL_HEIGHT = 1.0
LATERAL_WALL_HEIGHT = 1.25     # how tall the side walls should be (eg 1.25 wall height, 1 box size = 0.25 m space left to dilate)
WALL_CORNER_OVERLAP = 0.25     # same
SUPPORT_WALL_MARGIN = 0.25      # same but for the bottom, non moving wall
INITIAL_XY_OFFSET = 0.25 # from the axes origin

TARGET_PRESSURE = 50.0 # low lateral pressure to have a square geometry that doesnt expllode
SERVO_GAIN_FACTOR = 0.5
SERVO_VELOCITY_MAX = 0.01

PRESSURE_CONTROL_CYCLES = 20000

FIXED_SETTLE_CYCLES = 5000
FIXED_SETTLE_CALM = 500

# calculating the box dimension after compression
FREE_SURFACE_RADIUS_FACTOR = 3.0
FREE_SURFACE_CLEARANCE = 0.5 * 0.070
MESH_INSERTION_CLEARANCE = 1.0e-3


# generate rblocks
RANDOM_SEED = 123
VERTEX_DIR = "gravel"
NUM_RBLOCK_TEMPLATES = 7
NUM_RBLOCKS = 500
TARGET_POROSITY = 0.3 # after dilation (doesnt matter but it's just a way to control how quickly to dilate)
INITIAL_SCALE = 0.30 # keep it low if you want to generate the actual target number of rblocks
NUM_DILATION_STEPS = 30 # keep it high-ish to avoid overpressures (rblocks can get stuck if you have large dilation steps)
RBLOCK_FRICTION_FINAL = ma.tan(ma.radians(27.0))
WALL_FRICTION = 0.0

RBLOCK_DENSITY = 2700.0
RBLOCK_DAMP = 0.7
RBLOCK_FRIC = 0.3
RBLOCK_EMOD = 300.0e6
RBLOCK_WALL_EMOD = 300.0e7
RBLOCK_KRATIO = 4.0
RBLOCK_ROUNDING = 0.5 # how much the rblock boundaries are rounded. just keep it as it is or check the manual

DILATION_CYCLES = 500 # number of cycles between each rblock dilation
FINAL_SETTLE_CYCLES = 5000
FINAL_SETTLE_CALM = 100
RBLOCK_MESH_FRICTION = 0.5 * RBLOCK_FRICTION_FINAL
SUPPORT_WALL_FRICTION = 0.0 # increase if the rblocks are just sliding off
SUPPORT_WALL_EMOD = 300.0e6

# mesh props
NET_BALL_RADIUS = 0.0108 / 2.0
NET_BALL_MASS = 4.3e-3
NET_BALL_DENSITY = NET_BALL_MASS / (4.0 / 3.0 * ma.pi * NET_BALL_RADIUS**3)
MOS = 0.070
DT = 0.035
SW = 0.049
SW_DIST = 0.0602

# meta parameters to get the mesh to join together a bunch of nodes, dont worry about it
EDGE_SPACING = MOS / 2.0 # how far apart are the particles on the boundary edges
EDGE_SNAP_TOL = 0.55 * DT
ROUND_DIGITS = 10
CONTACT_GAP_TOL = 1.0e-4

SAVE_MODEL_NAME = "gabion_final"



it.command("python-reset-state false")
it.command("model new")
it.command("model random "+str(RANDOM_SEED))
it.command("model large-strain on")
it.command("model mechanical active on")
it.command("model domain extent -100 100")


# -----------------------------------------------------------------------------
# Create the permanent support and four overlapping open-top lateral walls.
# -----------------------------------------------------------------------------
x_min = INITIAL_XY_OFFSET
x_max = x_min + INITIAL_BOX_SIZE_X
y_min = INITIAL_XY_OFFSET
y_max = y_min + INITIAL_BOX_SIZE_Y
z_min = 0.0
fill_z_max = INITIAL_FILL_HEIGHT
wall_z_max = max(LATERAL_WALL_HEIGHT, fill_z_max + FREE_SURFACE_CLEARANCE)
overlap = WALL_CORNER_OVERLAP
support_margin = max(SUPPORT_WALL_MARGIN, overlap)

# generate the 6 walls (1 fixed bottom, 4 moving sides, 1 moving top)
wall_specs = (
    (
        "bottom_support", "supportwall",
        ((x_min - support_margin, y_min - support_margin, 0.0),
         (x_max + support_margin, y_min - support_margin, 0.0),
         (x_max + support_margin, y_max + support_margin, 0.0),
         (x_min - support_margin, y_max + support_margin, 0.0)),
    ),
    (
        "x_min_wall", "lateralwall",
        ((x_min, y_min - overlap, 0.0), (x_min, y_max + overlap, 0.0),
         (x_min, y_max + overlap, wall_z_max),
         (x_min, y_min - overlap, wall_z_max)),
    ),
    (
        "x_max_wall", "lateralwall",
        ((x_max, y_max + overlap, 0.0), (x_max, y_min - overlap, 0.0),
         (x_max, y_min - overlap, wall_z_max),
         (x_max, y_max + overlap, wall_z_max)),
    ),
    (
        "y_min_wall", "lateralwall",
        ((x_max + overlap, y_min, 0.0), (x_min - overlap, y_min, 0.0),
         (x_min - overlap, y_min, wall_z_max),
         (x_max + overlap, y_min, wall_z_max)),
    ),
    (
        "y_max_wall", "lateralwall",
        ((x_min - overlap, y_max, 0.0), (x_max + overlap, y_max, 0.0),
         (x_max + overlap, y_max, wall_z_max),
         (x_min - overlap, y_max, wall_z_max)),
    ),
)

created_wall_ids = []
for wall_name, wall_group, points in wall_specs:
    ids_before = {int(wall.id()) for wall in it.wall.list()}
    vertices = " ".join(
        "("+str(px)+","+str(py)+","+str(pz)+")"
        for px, py, pz in points
    )
    it.command("wall generate name '"+str(wall_name)+"' group '"+
               str(wall_group)+"' polygon "+str(vertices))
    new_walls = [wall for wall in it.wall.list() if int(wall.id()) not in ids_before]
    if len(new_walls) != 1:
        raise RuntimeError("Expected one wall for "+str(wall_name)+
                           ", found "+str(len(new_walls)))
    created_wall_ids.append(int(new_walls[0].id()))

support_id, x_min_id, x_max_id, y_min_id, y_max_id = created_wall_ids
support_wall = next(w for w in it.wall.list() if int(w.id()) == support_id)
x_min_wall = next(w for w in it.wall.list() if int(w.id()) == x_min_id)
x_max_wall = next(w for w in it.wall.list() if int(w.id()) == x_max_id)
y_min_wall = next(w for w in it.wall.list() if int(w.id()) == y_min_id)
y_max_wall = next(w for w in it.wall.list() if int(w.id()) == y_max_id)
print("Created four overlapping lateral walls of height "+str(wall_z_max)+" m.")
print("Support center = ("+str(float(support_wall.pos()[0]))+", "+
      str(float(support_wall.pos()[1]))+", "+
      str(float(support_wall.pos()[2]))+").")


# -----------------------------------------------------------------------------
# Generate reduced rblocks in the positive-coordinate box.
# -----------------------------------------------------------------------------
total_vol = INITIAL_BOX_SIZE_X * INITIAL_BOX_SIZE_Y * INITIAL_FILL_HEIGHT
target_solid_vol = total_vol * (1.0 - TARGET_POROSITY)
final_vol_per_rblock = target_solid_vol / float(NUM_RBLOCKS)
initial_vol_per_rblock = final_vol_per_rblock * INITIAL_SCALE
initial_equiv_diameter = (6.0 * initial_vol_per_rblock / ma.pi) ** (1.0 / 3.0)
box_text = (str(x_min)+" "+str(x_max)+" "+str(y_min)+" "+str(y_max)+
            " 0 "+str(fill_z_max))
template_pairs = " ".join(
    "'"+str(i)+"' 1" for i in range(1, NUM_RBLOCK_TEMPLATES + 1)
)

print("Generating "+str(NUM_RBLOCKS)+" rblocks; initial diameter="+
      str(initial_equiv_diameter)+" m")
for i in range(1, NUM_RBLOCK_TEMPLATES + 1):
    filename = os.path.join(VERTEX_DIR, "vertices_"+str(i)+".txt")
    if not os.path.isfile(filename):
        raise RuntimeError("Missing rblock vertex file: " + filename)
    vertices = np.loadtxt(filename, delimiter=",")
    flat_vertices = " ".join(str(value) for value in vertices.reshape(-1))
    it.command("rblock template create '"+str(i)+"' vertices "+
               str(flat_vertices)+" rounding "+str(RBLOCK_ROUNDING))

it.command("rblock generate diameter size "+str(initial_equiv_diameter)+
           " box "+str(box_text)+" number "+str(NUM_RBLOCKS)+
           " tries 5000000 group 'fill_rblocks' templates "+
           str(NUM_RBLOCK_TEMPLATES)+" "+str(template_pairs))
if not list(it.rblock.list()):
    raise RuntimeError("No rblocks were generated")

it.fish.set('fric',RBLOCK_FRIC)
it.command("contact cmat default type rblock-facet model linear method deformability ...\n"+
           "    emod "+str(RBLOCK_WALL_EMOD)+" kratio "+str(RBLOCK_KRATIO)+"\n"+
           "contact cmat default type rblock-rblock model linear method deformability ...\n"+
           "    emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric\n"+
           "contact cmat default model linear method deformability ...\n"+
           "    emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric\n"+
           "rblock attribute density "+str(RBLOCK_DENSITY)+" damp "+str(RBLOCK_DAMP)+" range group 'fill_rblocks'\n"+
           "contact cmat apply\nmodel mechanical active on\nmodel clean all")
it.command("rblock attribute velocity 0 0 0 spin 0 0 0 range group 'fill_rblocks'")
it.command("model clean all")
it.command("model gravity 9.81")



# -----------------------------------------------------------------------------
# Add the top wall and start common pressure control before dilation.
# -----------------------------------------------------------------------------
free_surface_z = 0.0
for rb in it.rblock.list():
    equivalent_radius = (3.0 * rb.vol() / (4.0 * ma.pi)) ** (1.0 / 3.0)
    free_surface_z = max(
        free_surface_z,
        rb.pos()[2] + FREE_SURFACE_RADIUS_FACTOR * equivalent_radius,
    )
initial_top_z = max(INITIAL_FILL_HEIGHT, free_surface_z + FREE_SURFACE_CLEARANCE)

current_x_min = (x_min_wall.pos()[0])
current_x_max = (x_max_wall.pos()[0])
current_y_min = (y_min_wall.pos()[1])
current_y_max = (y_max_wall.pos()[1])
top_points = (
    (current_x_min - overlap, current_y_max + overlap, initial_top_z),
    (current_x_max + overlap, current_y_max + overlap, initial_top_z),
    (current_x_max + overlap, current_y_min - overlap, initial_top_z),
    (current_x_min - overlap, current_y_min - overlap, initial_top_z),
)
ids_before = {int(wall.id()) for wall in it.wall.list()}
top_vertices = " ".join(
    "("+str(px)+","+str(py)+","+str(pz)+")"
    for px, py, pz in top_points
)
it.command("wall generate name 'top_control_wall' group 'topwall' polygon " + top_vertices)
new_walls = [wall for wall in it.wall.list() if int(wall.id()) not in ids_before]
top_wall = new_walls[0]
top_id = int(top_wall.id())

support_vertices = list(support_wall.vertices())
support_limits = (
    min(float(vertex.pos()[0]) for vertex in support_vertices),
    max(float(vertex.pos()[0]) for vertex in support_vertices),
    min(float(vertex.pos()[1]) for vertex in support_vertices),
    max(float(vertex.pos()[1]) for vertex in support_vertices),
)
limited_walls = (x_min_wall, x_max_wall, y_min_wall, y_max_wall)

def enforce_lateral_wall_limits(*args):
    support_x_min, support_x_max, support_y_min, support_y_max = support_limits
    checks = (
        (limited_walls[0], 0, support_x_min, -1),
        (limited_walls[1], 0, support_x_max, 1),
        (limited_walls[2], 1, support_y_min, -1),
        (limited_walls[3], 1, support_y_max, 1),
    )
    for wall, axis, limit, outward_sign in checks:
        pos = [float(value) for value in wall.pos()]
        outside = pos[axis] < limit if outward_sign < 0 else pos[axis] > limit
        if not outside:
            continue
        pos[axis] = limit
        wall.set_pos(tuple(pos))
        velocity = [float(value) for value in wall.vel()]
        if velocity[axis] * outward_sign > 0.0:
            velocity[axis] = 0.0
            wall.set_vel(tuple(velocity))


it.set_callback("enforce_lateral_wall_limits", -11.0)


# Refresh the force target directly here and after every dilation increment.
current_height = max(float(top_wall.pos()[2]), 1.0e-6)
force_x = TARGET_PRESSURE * max(current_y_max - current_y_min, 1.0e-6) * current_height
force_y = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * current_height
force_z = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * max(current_y_max - current_y_min, 1.0e-6)
servo_text = ("activate on gain-factor "+str(SERVO_GAIN_FACTOR)+
              " velocity-max "+str(SERVO_VELOCITY_MAX))
it.command("wall servo force-x  "+str(force_x)+" "+servo_text+" range id "+str(x_min_id))
it.command("wall servo force-x -"+str(force_x)+" "+servo_text+" range id "+str(x_max_id))
it.command("wall servo force-y  "+str(force_y)+" "+servo_text+" range id "+str(y_min_id))
it.command("wall servo force-y -"+str(force_y)+" "+servo_text+" range id "+str(y_max_id))
it.command("wall servo force-z -"+str(force_z)+" "+servo_text+" range id "+str(top_id))

print("Dilating rblocks to target porosity")
for dilation_step in range(1, NUM_DILATION_STEPS + 1):
    solid_vol = sum(rb.vol() for rb in it.rblock.list())
    porosity = 1.0 - solid_vol / total_vol

    remaining_multiplier = target_solid_vol / max(solid_vol, 1.0e-30)
    steps_left = NUM_DILATION_STEPS - dilation_step + 1
    relative_expansion = remaining_multiplier ** (1.0 / (3.0 * steps_left)) - 1.0

    it.command("rblock dilate expand "+str(relative_expansion)+
               " relative range group 'fill_rblocks'")
    it.command("model clean all")

    current_x_min = float(x_min_wall.pos()[0])
    current_x_max = float(x_max_wall.pos()[0])
    current_y_min = float(y_min_wall.pos()[1])
    current_y_max = float(y_max_wall.pos()[1])
    current_height = max(float(top_wall.pos()[2]), 1.0e-6)
    force_x = TARGET_PRESSURE * max(current_y_max - current_y_min, 1.0e-6) * current_height
    force_y = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * current_height
    force_z = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * max(current_y_max - current_y_min, 1.0e-6)
    it.command("wall servo force-x  "+str(force_x)+" "+servo_text+" range id "+str(x_min_id))
    it.command("wall servo force-x -"+str(force_x)+" "+servo_text+" range id "+str(x_max_id))
    it.command("wall servo force-y  "+str(force_y)+" "+servo_text+" range id "+str(y_min_id))
    it.command("wall servo force-y -"+str(force_y)+" "+servo_text+" range id "+str(y_max_id))
    it.command("wall servo force-z -"+str(force_z)+" "+servo_text+" range id "+str(top_id))
    it.command("model cycle "+str(DILATION_CYCLES)+" calm "+str(DILATION_CYCLES))
    it.command("model clean all")

it.command("model clean all")
it.fish.set("fric", RBLOCK_FRICTION_FINAL)
it.fish.set("fric_wall", WALL_FRICTION)

it.command("contact cmat default type rblock-facet model linear method deformability emod "+str(RBLOCK_WALL_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric_wall")
it.command("contact cmat default type rblock-rblock model linear method deformability emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric")
it.command("contact cmat default model linear method deformability emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric")
it.command("contact cmat apply")
it.command("contact property fric @fric range contact type 'rblock-rblock'")
it.command("contact property fric @fric_wall range contact type 'rblock-facet'")
it.command("model clean all")
it.command("model cycle "+str(FINAL_SETTLE_CYCLES)+" calm "+str(FINAL_SETTLE_CALM))
solid_vol = sum(rb.vol() for rb in it.rblock.list())
print("rblock generation complete; porosity:"+str(1.0 - solid_vol / total_vol))
it.command("model save 'rblocks_generated_v2.sav'")


# Apply one final pressure-control stage using the post-dilation box dimensions.
current_x_min = float(x_min_wall.pos()[0])
current_x_max = float(x_max_wall.pos()[0])
current_y_min = float(y_min_wall.pos()[1])
current_y_max = float(y_max_wall.pos()[1])
current_height = max(float(top_wall.pos()[2]), 1.0e-6)
force_x = TARGET_PRESSURE * max(current_y_max - current_y_min, 1.0e-6) * current_height
force_y = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * current_height
force_z = TARGET_PRESSURE * max(current_x_max - current_x_min, 1.0e-6) * max(current_y_max - current_y_min, 1.0e-6)
it.command("wall servo force-x  "+str(force_x)+" "+servo_text+" range id "+str(x_min_id))
it.command("wall servo force-x -"+str(force_x)+" "+servo_text+" range id "+str(x_max_id))
it.command("wall servo force-y  "+str(force_y)+" "+servo_text+" range id "+str(y_min_id))
it.command("wall servo force-y -"+str(force_y)+" "+servo_text+" range id "+str(y_max_id))
it.command("wall servo force-z -"+str(force_z)+" "+servo_text+" range id "+str(top_id))
it.command("model cycle "+str(PRESSURE_CONTROL_CYCLES)+" calm "+str(FIXED_SETTLE_CALM))


it.command("wall servo activate off")
it.command("wall attribute velocity-x 0 velocity-y 0 velocity-z 0")
it.remove_callback("enforce_lateral_wall_limits", -11.0)
it.command("model cycle "+str(FIXED_SETTLE_CYCLES)+" calm "+str(FIXED_SETTLE_CALM))
it.command("model clean all")
it.command("model save 'rblocks_low_pressure_settled_v2.sav'")


# Measure exact rblock vertices, remove the top, and open a bottom-mesh slot.
settled_top_wall_z = (top_wall.pos()[2])
it.command("""
fish define measure_rblock_vertex_bounds_v2
global rb_vxmin = 1.0e30
global rb_vxmax = -1.0e30
global rb_vymin = 1.0e30
global rb_vymax = -1.0e30
global rb_vzmin = 1.0e30
global rb_vzmax = -1.0e30
loop foreach local block rblock.list
    loop foreach local vertex rblock.vertex.list(block)
        rb_vxmin = math.min(rb_vxmin,vertex->x)
        rb_vxmax = math.max(rb_vxmax,vertex->x)
        rb_vymin = math.min(rb_vymin,vertex->y)
        rb_vymax = math.max(rb_vymax,vertex->y)
        rb_vzmin = math.min(rb_vzmin,vertex->z)
        rb_vzmax = math.max(rb_vzmax,vertex->z)
    endloop
endloop
end
[measure_rblock_vertex_bounds_v2]
""")

vertex_bounds = (
    float(it.fish.get("rb_vxmin")),
    float(it.fish.get("rb_vxmax")),
    float(it.fish.get("rb_vymin")),
    float(it.fish.get("rb_vymax")),
    float(it.fish.get("rb_vzmin")),
    float(it.fish.get("rb_vzmax")),
)

top_facet_count = len(list(top_wall.facets()))
top_wall.delete()
it.command("model clean all")

insertion_lift = 2.0 * NET_BALL_RADIUS + MESH_INSERTION_CLEARANCE
for rb in it.rblock.list():
    vec_position = rb.pos()
    rb.set_pos((float(vec_position[0]), float(vec_position[1]), float(vec_position[2]) + insertion_lift))
it.command("rblock attribute velocity 0 0 0 spin 0 0 0 range group 'fill_rblocks'")
it.command("model clean all")

current_x_min = (x_min_wall.pos()[0])
current_x_max = (x_max_wall.pos()[0])
current_y_min = (y_min_wall.pos()[1])
current_y_max = (y_max_wall.pos()[1])
mx0 = current_x_min - NET_BALL_RADIUS - MESH_INSERTION_CLEARANCE
mx1 = current_x_max + NET_BALL_RADIUS + MESH_INSERTION_CLEARANCE
my0 = current_y_min - NET_BALL_RADIUS - MESH_INSERTION_CLEARANCE
my1 = current_y_max + NET_BALL_RADIUS + MESH_INSERTION_CLEARANCE
mz0 = NET_BALL_RADIUS
mz1 = vertex_bounds[5] + insertion_lift + NET_BALL_RADIUS + MESH_INSERTION_CLEARANCE

# Build the six-face mesh graph. Shared box edges use shared balls.
mcx = 0.5 * (mx0 + mx1)
mcy = 0.5 * (my0 + my1)
mcz = 0.5 * (mz0 + mz1)
mhx = 0.5 * (mx1 - mx0)
mhy = 0.5 * (my1 - my0)
mhz = 0.5 * (mz1 - mz0)

# name, center, u-axis, v-axis, half-u, half-v
faces = (
    ("+Z", (mcx, mcy, mz1), (1, 0, 0), (0, 1, 0), mhx, mhy),
    ("-Z", (mcx, mcy, mz0), (1, 0, 0), (0, 1, 0), mhx, mhy),
    ("+Y", (mcx, my1, mcz), (1, 0, 0), (0, 0, 1), mhx, mhz),
    ("-Y", (mcx, my0, mcz), (1, 0, 0), (0, 0, 1), mhx, mhz),
    ("+X", (mx1, mcy, mcz), (0, 1, 0), (0, 0, 1), mhy, mhz),
    ("-X", (mx0, mcy, mcz), (0, 1, 0), (0, 0, 1), mhy, mhz),
)

map_position_group = {}
map_edge_endpoints = {}
map_edge_positions = {}
dt_position_pairs = set()
sw_position_pairs = set()
selvedge_position_pairs = set()
joint_position_pairs = set()

for face_name, vec_center, vec_u_axis, vec_v_axis, half_u, half_v in faces:
    corners = []
    for sign_u, sign_v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        vec_point = tuple(round(
            vec_center[k] + sign_u * half_u * vec_u_axis[k] + sign_v * half_v * vec_v_axis[k],
            ROUND_DIGITS
        ) for k in range(3))
        corners.append(vec_point)
    for vec_edge_start, vec_edge_end in zip(corners, corners[1:] + corners[:1]):
        edge_key = tuple(sorted((vec_edge_start, vec_edge_end)))
        map_edge_endpoints[edge_key] = (vec_edge_start, vec_edge_end)

for edge_key, endpoints in map_edge_endpoints.items():
    vec_p1, vec_p2 = endpoints
    dx, dy, dz = vec_p2[0] - vec_p1[0], vec_p2[1] - vec_p1[1], vec_p2[2] - vec_p1[2]
    edge_length = ma.sqrt(dx * dx + dy * dy + dz * dz)
    segment_count = max(1, int(ma.ceil(edge_length / EDGE_SPACING)))
    positions = []
    for index in range(segment_count + 1):
        fraction = index / float(segment_count)
        vec_position = tuple(round(
            vec_p1[k] + fraction * (vec_p2[k] - vec_p1[k]), ROUND_DIGITS
        ) for k in range(3))
        positions.append(vec_position)
        map_position_group[vec_position] = "dt2"
    map_edge_positions[edge_key] = positions
    for vec_pair_start, vec_pair_end in zip(positions[:-1], positions[1:]):
        selvedge_position_pairs.add(tuple(sorted((vec_pair_start, vec_pair_end))))

for face_name, vec_center, vec_u_axis, vec_v_axis, half_u, half_v in faces:
    target_width = 2.0 * half_u
    target_height = 2.0 * half_v
    nx_guess = max(1, int(round(target_width / MOS)))
    ny_guess = max(1, int(round(target_height / (DT + SW))))
    best_choice = None
    for trial_ny in range(max(1, ny_guess - 4), ny_guess + 5):
        for trial_nx in range(max(1, nx_guess - 4), nx_guess + 5):
            trial_points = []
            x_start = 0.0
            row_count = trial_nx
            for row_index in range(trial_ny + 1):
                v0 = row_index * (DT + SW)
                for column in range(1, row_count + 1):
                    trial_points.append((x_start + column * MOS, v0))
                    trial_points.append((x_start + column * MOS, v0 + DT))
                x_start -= 0.5 * MOS * ((-1) ** (row_index + 1))
                row_count += ((-1) ** (row_index + 1))
            trial_width = max(p[0] for p in trial_points) - min(p[0] for p in trial_points)
            trial_height = max(p[1] for p in trial_points) - min(p[1] for p in trial_points)
            score = (trial_width - target_width) ** 2 + (trial_height - target_height) ** 2
            score += 1.0e-6 * (abs(trial_nx - nx_guess) + abs(trial_ny - ny_guess))
            candidate = (score, trial_nx, trial_ny)
            if best_choice is None or candidate < best_choice:
                best_choice = candidate
    nx = best_choice[1]
    ny = best_choice[2]

    # Local DT panel nodes and their exact DT/SW graph.
    map_local_nodes = {}
    panel_rows = []
    local_dt_pairs = set()
    x_start = 0.0
    row_group = 0
    row_count = nx
    for row_index in range(ny + 1):
        v0 = row_index * (DT + SW)
        row_keys = []
        for column in range(1, row_count + 1):
            lower_key = (row_index, column, 0)
            upper_key = (row_index, column, 1)
            u_value = x_start + column * MOS
            map_local_nodes[lower_key] = (u_value, v0, row_group)
            map_local_nodes[upper_key] = (u_value, v0 + DT, row_group)
            row_keys.append((lower_key, upper_key))
            local_dt_pairs.add(tuple(sorted((lower_key, upper_key))))
        panel_rows.append(row_keys)
        x_start -= 0.5 * MOS * ((-1) ** (row_index + 1))
        row_group = 1 - row_group
        row_count += ((-1) ** (row_index + 1))

    local_sw_pairs = set()
    for row_index in range(len(panel_rows) - 1):
        upper_keys = [pair[1] for pair in panel_rows[row_index]]
        lower_keys = [pair[0] for pair in panel_rows[row_index + 1]]
        for upper_key in upper_keys:
            u1, v1, unused_group = map_local_nodes[upper_key]
            for lower_key in lower_keys:
                u2, v2, unused_group = map_local_nodes[lower_key]
                if abs(ma.hypot(u2 - u1, v2 - v1) - SW_DIST) <= CONTACT_GAP_TOL:
                    local_sw_pairs.add(tuple(sorted((upper_key, lower_key))))

    local_u_center = 0.5 * (
        min(value[0] for value in map_local_nodes.values())
        + max(value[0] for value in map_local_nodes.values())
    )
    local_v_center = 0.5 * (
        min(value[1] for value in map_local_nodes.values())
        + max(value[1] for value in map_local_nodes.values())
    )
    face_edge_points = []
    face_corners = []
    for sign_u, sign_v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        face_corners.append(tuple(round(
            vec_center[k] + sign_u * half_u * vec_u_axis[k] + sign_v * half_v * vec_v_axis[k],
            ROUND_DIGITS
        ) for k in range(3)))
    for vec_edge_start, vec_edge_end in zip(face_corners, face_corners[1:] + face_corners[:1]):
        face_edge_points.extend(map_edge_positions[tuple(sorted((vec_edge_start, vec_edge_end)))])
    face_edge_points = sorted(set(face_edge_points))

    map_local_to_global = {}
    for node_key, local_value in map_local_nodes.items():
        local_u = local_value[0] - local_u_center
        local_v = local_value[1] - local_v_center
        group_index = local_value[2]
        if abs(local_u - half_u) <= EDGE_SNAP_TOL:
            local_u = half_u
        elif abs(local_u + half_u) <= EDGE_SNAP_TOL:
            local_u = -half_u
        if abs(local_v - half_v) <= EDGE_SNAP_TOL:
            local_v = half_v
        elif abs(local_v + half_v) <= EDGE_SNAP_TOL:
            local_v = -half_v
        vec_exact_position = tuple(
            vec_center[k] + local_u * vec_u_axis[k] + local_v * vec_v_axis[k]
            for k in range(3)
        )
        vec_position = tuple(round(value, ROUND_DIGITS) for value in vec_exact_position)
        on_edge = (
            abs(abs(local_u) - half_u) <= 10.0 ** (-ROUND_DIGITS)
            or abs(abs(local_v) - half_v) <= 10.0 ** (-ROUND_DIGITS)
        )
        if on_edge:
            vec_position = min(face_edge_points, key=lambda vec_edge_point: (
                sum((vec_edge_point[k] - vec_exact_position[k]) ** 2 for k in range(3)),
                vec_edge_point,
            ))
        elif vec_position not in map_position_group:
            map_position_group[vec_position] = "dt"+str(group_index)
        map_local_to_global[node_key] = vec_position

    for local_pair in local_dt_pairs:
        vec_p1 = map_local_to_global[local_pair[0]]
        vec_p2 = map_local_to_global[local_pair[1]]
        if vec_p1 != vec_p2:
            dt_position_pairs.add(tuple(sorted((vec_p1, vec_p2))))
    for local_pair in local_sw_pairs:
        vec_p1 = map_local_to_global[local_pair[0]]
        vec_p2 = map_local_to_global[local_pair[1]]
        if vec_p1 != vec_p2:
            sw_position_pairs.add(tuple(sorted((vec_p1, vec_p2))))

dt_position_pairs.difference_update(selvedge_position_pairs)
sw_position_pairs.difference_update(selvedge_position_pairs)
sw_position_pairs.difference_update(dt_position_pairs)


# create net balls and convert position topology to explicit ball-ID pairs.
for (px, py, pz), group in map_position_group.items():
    it.command("ball create radius "+str(NET_BALL_RADIUS)+" group '"+
               str(group)+"' position "+str(px)+" "+str(py)+" "+str(pz))
it.command("ball attribute density "+str(NET_BALL_DENSITY)+" damp 0.3")
it.command("model clean all")

map_position_id = {}
for ball in it.ball.list():
    vec_position = tuple(round(float(value), ROUND_DIGITS) for value in ball.pos())
    if vec_position in map_position_group:
        map_position_id[vec_position] = int(ball.id())

dt_id_pairs = {tuple(sorted((map_position_id[vec_p1], map_position_id[vec_p2]))) for vec_p1, vec_p2 in dt_position_pairs}
sw_id_pairs = {tuple(sorted((map_position_id[vec_p1], map_position_id[vec_p2]))) for vec_p1, vec_p2 in sw_position_pairs}
selvedge_id_pairs = {
    tuple(sorted((map_position_id[vec_p1], map_position_id[vec_p2])))
    for vec_p1, vec_p2 in selvedge_position_pairs
}
joint_id_pairs = set()
all_id_pairs = set()
for contact_type, pairs in (
    ("dt", dt_id_pairs), ("sw", sw_id_pairs),
    ("se", selvedge_id_pairs), ("joint", joint_id_pairs),
):
    all_id_pairs.update(pairs)


# Instantiate all required bonds by proximity, then keep only explicit pairs.
max_center_distance = 0.0
for position_pairs in (dt_position_pairs, sw_position_pairs, selvedge_position_pairs, joint_position_pairs,):
    for vec_p1, vec_p2 in position_pairs:
        distance = ma.sqrt(sum((vec_p2[k] - vec_p1[k]) ** 2 for k in range(3)))
        max_center_distance = max(max_center_distance, distance)
proximity = max(0.0, max_center_distance - 2.0 * NET_BALL_RADIUS) + CONTACT_GAP_TOL
it.command("contact cmat default model linearpbond property pb_ten 1e99 pb_coh 1e99")
it.command("contact cmat proximity "+str(proximity))
it.command("contact cmat apply")
it.command("model clean")
it.command("contact property lin_mode 1")
it.command("contact method bond gap 4")
it.command("model energy mechanical on")
it.command("model large-strain on")
it.command("model orientation-tracking on")

map_pair_type = {}
for contact_type, pairs in (("dt", dt_id_pairs), ("sw", sw_id_pairs), ("se", selvedge_id_pairs), ("joint", joint_id_pairs),):
    for pair in pairs:
        map_pair_type[pair] = contact_type
count_dt = count_sw = count_se = count_joint = count_delete = count_skipped = 0
for contact in it.contact.list():
    try:
        endpoint1 = contact.end1()
        endpoint2 = contact.end2()
        group1 = "" if endpoint1.group() is None else str(endpoint1.group()).lower()
        group2 = "" if endpoint2.group() is None else str(endpoint2.group()).lower()
    except Exception:
        continue
    if group1 not in ("dt0", "dt1", "dt2") or group2 not in ("dt0", "dt1", "dt2"):
        count_skipped += 1
        continue
    contact.set_prop("rgap", contact.gap())
    pair = tuple(sorted((int(endpoint1.id()), int(endpoint2.id()))))
    contact_type = map_pair_type.get(pair)
    if contact_type is None:
        contact.set_group("delete")
        count_delete += 1
    else:
        contact.set_group(contact_type)
        if contact_type == "dt":
            count_dt += 1
        elif contact_type == "sw":
            count_sw += 1
        elif contact_type == "se":
            count_se += 1
        else:
            count_joint += 1
it.command("contact delete range group 'delete' contact type 'ball-ball'")

# final fill/net/support models.
it.fish.set("fric_fill", RBLOCK_FRICTION_FINAL)
it.fish.set("fric_mesh", RBLOCK_MESH_FRICTION)
it.fish.set("fric_support", SUPPORT_WALL_FRICTION)
it.command("contact cmat default type rblock-rblock model linear method deformability emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric_fill")
it.command("contact cmat default type ball-rblock model linear method deformability emod "+str(RBLOCK_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric_mesh")
it.command("contact cmat apply range contact type 'rblock-rblock'")
it.command("contact cmat apply range contact type 'ball-rblock'")

it.command("contact property fric @fric_fill range contact type 'rblock-rblock'")
it.command("contact property fric @fric_mesh range contact type 'ball-rblock'")
it.command("contact cmat default type ball-facet model linear method deformability emod "+str(SUPPORT_WALL_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric_support")
it.command("contact cmat default type rblock-facet model linear method deformability emod "+str(SUPPORT_WALL_EMOD)+" kratio "+str(RBLOCK_KRATIO)+" property fric @fric_support")
it.command("contact cmat apply range contact type 'ball-facet'")
it.command("contact cmat apply range contact type 'rblock-facet'")
it.command("model clean all")
it.command("rblock attribute damp "+str(RBLOCK_DAMP)+" range group 'fill_rblocks'")
it.command("rblock free velocity spin range group 'fill_rblocks'")


# delete walls
lateral_ids = {x_min_id, x_max_id, y_min_id, y_max_id}
lateral_walls = [wall for wall in list(it.wall.list()) if int(wall.id()) in lateral_ids]
for wall in lateral_walls:
    wall.delete()
it.command("model clean all")
it.command("model cycle "+str(FIXED_SETTLE_CYCLES)+" calm "+str(FIXED_SETTLE_CALM))
it.command("model save '"+str(SAVE_MODEL_NAME)+"'")
