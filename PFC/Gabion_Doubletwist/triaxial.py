import math as ma, os, numpy as np, itasca as it


# parameters for generating / controlling the box size. using all caps for parameters, because i keep overwriting my box_x variables
INITIAL_BOX_SIZE_X = 1.0            
INITIAL_BOX_SIZE_Y = 1.0
INITIAL_FILL_HEIGHT = 1.0
LATERAL_WALL_HEIGHT = 1.25     # how tall the side walls should be (eg 1.25 wall height, 1 box size = 0.25 m space left to dilate)
WALL_CORNER_OVERLAP = 0.25     # same
SUPPORT_WALL_MARGIN = 0.25      # same but for the bottom, non moving wall
INITIAL_XY_OFFSET = 0.25 # from the axes origin

TARGET_PRESSURE = 10000.0 # Pa, the constant lateral stress
SERVO_GAIN_FACTOR = 0.5
SERVO_VELOCITY_MAX = 0.01

PRESSURE_CONTROL_CYCLES = 20000
FIXED_SETTLE_CALM = 500

# Triaxial loading control and output.
TARGET_AXIAL_STRAIN = 0.20
HISTORY_INTERVAL = 100
HISTORY_ASCII_FILE = "triaxial_history.txt"
TRIAXIAL_SAVE_MODEL_NAME = "triaxial_compressed.sav"

# I = |epsilon_dot_axial| d / sqrt(p / rho).  The top-wall velocity is
# updated so this inertial number remains below the requested limit.
TARGET_INERTIA_NUMBER_LIMIT = 1.0e-3

# Calculating the box dimension after compression.
FREE_SURFACE_RADIUS_FACTOR = 3.0
FREE_SURFACE_CLEARANCE = 0.5 * 0.070


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
 

it.command("python-reset-state false")
it.command("model new")
it.command("model random "+str(RANDOM_SEED))
it.command("model large-strain on")
it.command("model mechanical active on")
it.command("model gravity 0 0 0")
it.command("model domain extent -100 100")


# -----------------------------------------------------------------------------
# Create the permanent support and four overlapping open-top lateral walls.
# -----------------------------------------------------------------------------
x_min = INITIAL_XY_OFFSET
x_max = x_min + INITIAL_BOX_SIZE_X
y_min = INITIAL_XY_OFFSET
y_max = y_min + INITIAL_BOX_SIZE_Y
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


# compress to target pressure
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

##########################################################################################################################
# Displacement-controlled triaxial compression
##########################################################################################################################

def triaxial_dimensions():
    width = float(x_max_wall.pos()[0]) - float(x_min_wall.pos()[0])
    depth = float(y_max_wall.pos()[1]) - float(y_min_wall.pos()[1])
    height = float(top_wall.pos()[2]) - float(support_wall.pos()[2])
    return max(width, 1.0e-12), max(depth, 1.0e-12), max(height, 1.0e-12)


def set_lateral_stress_servo_targets():
    width, depth, height = triaxial_dimensions()
    force_x = TARGET_PRESSURE * depth * height
    force_y = TARGET_PRESSURE * width * height
    it.command("wall servo force-x  "+str(force_x)+" "+servo_text+
               " range id "+str(x_min_id))
    it.command("wall servo force-x -"+str(force_x)+" "+servo_text+
               " range id "+str(x_max_id))
    it.command("wall servo force-y  "+str(force_y)+" "+servo_text+
               " range id "+str(y_min_id))
    it.command("wall servo force-y -"+str(force_y)+" "+servo_text+
               " range id "+str(y_max_id))


initial_width, initial_depth, initial_height = triaxial_dimensions()
mean_rblock_diameter = sum(2.0 * (3.0 * float(rb.vol()) / (4.0 * ma.pi)) ** (1.0 / 3.0)for rb in it.rblock.list()) / float(len(list(it.rblock.list())))

it.fish.set("triaxial_x_min_id", x_min_id)
it.fish.set("triaxial_x_max_id", x_max_id)
it.fish.set("triaxial_y_min_id", y_min_id)
it.fish.set("triaxial_y_max_id", y_max_id)
it.fish.set("triaxial_top_id", top_id)
it.fish.set("triaxial_support_id", support_id)
it.fish.set("triaxial_initial_width", initial_width)
it.fish.set("triaxial_initial_depth", initial_depth)
it.fish.set("triaxial_initial_height", initial_height)
it.fish.set("triaxial_initial_volume", initial_width * initial_depth * initial_height)
it.fish.set("triaxial_density", RBLOCK_DENSITY)
it.fish.set("triaxial_particle_diameter", mean_rblock_diameter)
it.fish.set("triaxial_lateral_stress", TARGET_PRESSURE)
it.fish.set("triaxial_inertia_limit", TARGET_INERTIA_NUMBER_LIMIT)
it.fish.set("triaxial_target_axial_strain", TARGET_AXIAL_STRAIN)
it.fish.set("triaxial_compression_velocity", 0.0)

# It is perhaps more useful to run the measurement/servo control in fish, so it stays in the save file. Compression is positive for stress and strain.
it.command("""
fish define triaxial_measure
    global triaxial_x_min_id
    global triaxial_x_max_id
    global triaxial_y_min_id
    global triaxial_y_max_id
    global triaxial_top_id
    global triaxial_support_id
    global triaxial_initial_width
    global triaxial_initial_depth
    global triaxial_initial_height
    global triaxial_initial_volume
    global triaxial_density
    global triaxial_particle_diameter
    global triaxial_lateral_stress
    global triaxial_inertia_limit
    global triaxial_width
    global triaxial_depth
    global triaxial_height
    global triaxial_sigma_x
    global triaxial_sigma_y
    global triaxial_sigma_z
    global triaxial_mean_stress
    global triaxial_j2
    global triaxial_j3
    global triaxial_q
    global triaxial_axial_strain
    global triaxial_lateral_strain_x
    global triaxial_lateral_strain_y
    global triaxial_volumetric_strain
    global triaxial_strain_j2
    global triaxial_strain_q
    global triaxial_compression_velocity
    global triaxial_axial_strain_rate
    global triaxial_inertia_number

    local wp_xminus = wall.find(triaxial_x_min_id)
    local wp_xplus = wall.find(triaxial_x_max_id)
    local wp_yminus = wall.find(triaxial_y_min_id)
    local wp_yplus = wall.find(triaxial_y_max_id)
    local wp_top = wall.find(triaxial_top_id)
    local wp_bottom = wall.find(triaxial_support_id)

    triaxial_width = wall.pos.x(wp_xplus) - wall.pos.x(wp_xminus)
    triaxial_depth = wall.pos.y(wp_yplus) - wall.pos.y(wp_yminus)
    triaxial_height = wall.pos.z(wp_top) - wall.pos.z(wp_bottom)

    local area_x = math.max(triaxial_depth * triaxial_height,1.0e-30)
    local area_y = math.max(triaxial_width * triaxial_height,1.0e-30)
    local area_z = math.max(triaxial_width * triaxial_depth,1.0e-30)
    triaxial_sigma_x = 0.5 * (math.abs(wall.force.contact.x(wp_xminus)) + ...
        math.abs(wall.force.contact.x(wp_xplus))) / area_x
    triaxial_sigma_y = 0.5 * (math.abs(wall.force.contact.y(wp_yminus)) + ...
        math.abs(wall.force.contact.y(wp_yplus))) / area_y
    triaxial_sigma_z = math.abs(wall.force.contact.z(wp_top)) / area_z

    triaxial_mean_stress = (triaxial_sigma_x + triaxial_sigma_y + ...
        triaxial_sigma_z) / 3.0
    local dev_x = triaxial_sigma_x - triaxial_mean_stress
    local dev_y = triaxial_sigma_y - triaxial_mean_stress
    local dev_z = triaxial_sigma_z - triaxial_mean_stress
    triaxial_j2 = 0.5 * (dev_x * dev_x + dev_y * dev_y + dev_z * dev_z)
    triaxial_j3 = dev_x * dev_y * dev_z
    triaxial_q = math.sqrt(math.max(3.0 * triaxial_j2,0.0))

    triaxial_axial_strain = (triaxial_initial_height - triaxial_height) / ...
        triaxial_initial_height
    triaxial_lateral_strain_x = (triaxial_initial_width - triaxial_width) / ...
        triaxial_initial_width
    triaxial_lateral_strain_y = (triaxial_initial_depth - triaxial_depth) / ...
        triaxial_initial_depth
    triaxial_volumetric_strain = 1.0 - ...
        triaxial_width * triaxial_depth * triaxial_height / ...
        triaxial_initial_volume

    local strain_mean = (triaxial_axial_strain + ...
        triaxial_lateral_strain_x + triaxial_lateral_strain_y) / 3.0
    local strain_dev_x = triaxial_lateral_strain_x - strain_mean
    local strain_dev_y = triaxial_lateral_strain_y - strain_mean
    local strain_dev_z = triaxial_axial_strain - strain_mean
    triaxial_strain_j2 = 0.5 * (strain_dev_x * strain_dev_x + ...
        strain_dev_y * strain_dev_y + strain_dev_z * strain_dev_z)
    triaxial_strain_q = math.sqrt(math.max(3.0 * triaxial_strain_j2,0.0))

    local pressure_for_rate = math.max(triaxial_mean_stress,1.0e-30)
    triaxial_compression_velocity = triaxial_inertia_limit * ...
        triaxial_height * math.sqrt(pressure_for_rate / triaxial_density) / ...
        triaxial_particle_diameter
    wall.vel.z(wp_top) = -triaxial_compression_velocity

    triaxial_axial_strain_rate = triaxial_compression_velocity / ...
        math.max(triaxial_height,1.0e-30)
    triaxial_inertia_number = triaxial_axial_strain_rate * ...
        triaxial_particle_diameter / ...
        math.sqrt(pressure_for_rate / triaxial_density)

    wall.servo.force.x(wp_xminus) = triaxial_lateral_stress * area_x
    wall.servo.force.x(wp_xplus) = -triaxial_lateral_stress * area_x
    wall.servo.force.y(wp_yminus) = triaxial_lateral_stress * area_y
    wall.servo.force.y(wp_yplus) = -triaxial_lateral_stress * area_y
end

fish define triaxial_stop
    global triaxial_axial_strain
    global triaxial_target_axial_strain
    triaxial_stop = 0
    if triaxial_axial_strain >= triaxial_target_axial_strain
        triaxial_stop = 1
    endif
end
""")
it.command("fish callback add @triaxial_measure 9.0")

it.command("history purge")
it.command("history interval "+str(HISTORY_INTERVAL))
it.command("fish history name 'sigma_x' triaxial_sigma_x")
it.command("fish history name 'sigma_y' triaxial_sigma_y")
it.command("fish history name 'sigma_z' triaxial_sigma_z")
it.command("fish history name 'mean_stress' triaxial_mean_stress")
it.command("fish history name 'j2' triaxial_j2")
it.command("fish history name 'j3' triaxial_j3")
it.command("fish history name 'q' triaxial_q")
it.command("fish history name 'axial_strain' triaxial_axial_strain")
it.command("fish history name 'lateral_strain_x' triaxial_lateral_strain_x")
it.command("fish history name 'lateral_strain_y' triaxial_lateral_strain_y")
it.command("fish history name 'volumetric_strain' triaxial_volumetric_strain")
it.command("fish history name 'strain_j2' triaxial_strain_j2")
it.command("fish history name 'strain_q' triaxial_strain_q")
it.command("fish history name 'axial_strain_rate' triaxial_axial_strain_rate")
it.command("fish history name 'inertia_number' triaxial_inertia_number")

# Remove the top-wall force servo and re-enable only the four lateral servos.
it.command("wall servo activate off")
it.command("wall attribute velocity-x 0 velocity-y 0 velocity-z 0")
set_lateral_stress_servo_targets()
it.command("[triaxial_measure]")

# The FISH callback updates the lateral force targets and the top-wall velocity every cycle.  The solve terminates as soon as the target strain is reached.
loading_start_cycle = int(it.cycle())
it.command("model solve fish-halt @triaxial_stop")
loading_cycles = int(it.cycle()) - loading_start_cycle
final_inertia_number = float(it.fish.get("triaxial_inertia_number"))

it.command("fish callback remove @triaxial_measure 9.0")
top_wall.set_vel((0.0, 0.0, 0.0))
it.command("wall servo activate off")
it.command("wall attribute velocity-x 0 velocity-y 0 velocity-z 0")
it.fish.set("triaxial_compression_velocity", 0.0)
it.fish.set("triaxial_axial_strain_rate", 0.0)
it.fish.set("triaxial_inertia_number", 0.0)

# doing it this way is better to concatenate the strings without + + + + + + + + +
history_export = (
    "history export 'sigma_x' 'sigma_y' 'sigma_z' 'mean_stress' 'j2' 'j3' 'q' "
    "'axial_strain' 'lateral_strain_x' "
    "'lateral_strain_y' 'volumetric_strain' 'strain_j2' 'strain_q' "
    "'axial_strain_rate' 'inertia_number' file '"+
    HISTORY_ASCII_FILE+"' truncate"
)
it.command(history_export)
it.command("model save '"+TRIAXIAL_SAVE_MODEL_NAME+"'")
print("Triaxial compression complete: cycles="+str(loading_cycles)+
      ", axial strain="+str(float(it.fish.get("triaxial_axial_strain")))+
      ", loading inertia number="+str(final_inertia_number))
