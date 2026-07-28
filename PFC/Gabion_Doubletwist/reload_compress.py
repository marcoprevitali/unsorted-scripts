import itasca as it

cmd = it.command


# -----------------------------------------------------------------------------
# User parameters
# -----------------------------------------------------------------------------
RESTORE_MODEL_NAME = "gabion_final_no_scale.sav"
COMPRESSED_MODEL_NAME = "gabion_compressed.sav"
HISTORY_ASCII_FILE = "gabion_compression_force_displacement.txt"

PLATEN_VELOCITY_Z = -0.2       # m/s; negative moves the platen downward
TARGET_AXIAL_STRAIN = 0.20      # stop after 20% of the initial specimen height
MAX_COMPRESSION_CYCLES = 5000000
HISTORY_INTERVAL = 100
PLATEN_INITIAL_GAP = 1.0e-4     # m above the highest ball/rblock point
PLATEN_EDGE_MARGIN = 0.0        # m beyond the permanent support footprint

CONTACT_EMOD = 300.0e6
CONTACT_KRATIO = 4.0
PLATEN_FRICTION = 0.0

# Mesh-ball/rblock interface.
BALL_RBLOCK_EMOD = 300.0e6
BALL_RBLOCK_KRATIO = 4.0
BALL_RBLOCK_FRICTION = 0.25
CONTACT_DP_NRATIO = 0.50
CONTACT_DP_SRATIO = 0.20
CONTACT_DP_MODE = 3             # no-tension normal; slip-cut shear dashpot
MESH_BALL_LOCAL_DAMP = 0.50
RBLOCK_LOCAL_DAMP = 0.70
PRECOMPRESSION_SETTLE_CYCLES = 20000
PRECOMPRESSION_SETTLE_CALM = 500

# Parallel-bond stiffness, different wire types have different stiffnesses
map_mesh_tensile_stiffness = {
    "sw": 1.0e8,
    "dt": 5.0e7,
    "se": 2.0e8,
}
MESH_COMPRESSIVE_STIFFNESS_RATIO = 0.70 # set the compressive to tensile stiffness to this ratio


# loop for each ball-ball contact and change the model parameter to the target. this allows us to do any mesh parameter without regenerating contacts, or change model, etc..
def assign_mesh_contact_stiffness(map_stiffness, compressive_ratio):
    map_updated_counts = {contact_type: 0 for contact_type in map_stiffness}

    for contact in it.contact.list(type=it.BallBallContact, all=True):
        if contact.model().lower() != "linearpbond":
            continue

        contact_type = None
        for group_name in map_stiffness:
            if contact.in_group(group_name):
                contact_type = group_name
                break
        if contact_type is None:
            continue

        tensile_stiffness = float(map_stiffness[contact_type])
        compressive_stiffness = compressive_ratio * tensile_stiffness

        contact.set_prop("pb_kn", tensile_stiffness)
        contact.set_prop("pb_ks", tensile_stiffness)
        contact.set_prop("kn", compressive_stiffness)
        contact.set_prop("ks", compressive_stiffness)
        map_updated_counts[contact_type] += 1

    cmd("model clean all")
    return map_updated_counts



cmd("python-reset-state false")
cmd("model restore '"+str(RESTORE_MODEL_NAME)+"'")

# Do not inherit the wall-limit callback when this script is executed in the
# same PFC Python session as the generation script.
try:
    it.remove_callback("enforce_lateral_wall_limits", -11.0)
except Exception:
    pass

cmd("model mechanical active on")
cmd("model large-strain on")
cmd("wall attribute velocity-x 0 velocity-y 0 velocity-z 0")

if not list(it.ball.list()):
    raise RuntimeError("The restored model contains no mesh balls")
if not list(it.rblock.list()):
    raise RuntimeError("The restored model contains no rblocks")

map_updated_mesh_contacts = assign_mesh_contact_stiffness(
    map_mesh_tensile_stiffness,
    MESH_COMPRESSIVE_STIFFNESS_RATIO,
)
missing_mesh_contact_types = [
    contact_type for contact_type, count in map_updated_mesh_contacts.items()
    if count == 0
]
if missing_mesh_contact_types:
    raise RuntimeError(
        "The restored model has no linearpbond contacts in groups: "+
        ", ".join(missing_mesh_contact_types)
    )
print("Assigned mesh contact stiffness:")
for contact_type, tensile_stiffness in map_mesh_tensile_stiffness.items():
    compressive_stiffness = MESH_COMPRESSIVE_STIFFNESS_RATIO * tensile_stiffness
    print("  "+str(contact_type)+": contacts="+
          str(map_updated_mesh_contacts[contact_type])+
          ", pb_kn=pb_ks="+str(tensile_stiffness)+
          ", kn=ks="+str(compressive_stiffness))


# Find the permanent bottom support
support_walls = []
for wall in it.wall.list():
    if wall.in_group("supportwall"):
        support_walls.append(wall)

if len(support_walls) != 1:
    raise RuntimeError(
        "Expected one wall in group 'supportwall', found "+
        str(len(support_walls))
    )
support_wall = support_walls[0]
support_vertices = list(support_wall.vertices())
if len(support_vertices) < 3:
    raise RuntimeError("The support wall does not contain a valid polygon")

platen_x_min = min(float(vertex.pos()[0]) for vertex in support_vertices)
platen_x_max = max(float(vertex.pos()[0]) for vertex in support_vertices)
platen_y_min = min(float(vertex.pos()[1]) for vertex in support_vertices)
platen_y_max = max(float(vertex.pos()[1]) for vertex in support_vertices)
support_z = sum(float(vertex.pos()[2]) for vertex in support_vertices) / len(support_vertices)

platen_x_min -= PLATEN_EDGE_MARGIN
platen_x_max += PLATEN_EDGE_MARGIN
platen_y_min -= PLATEN_EDGE_MARGIN
platen_y_max += PLATEN_EDGE_MARGIN


# Measure the true upper extent of both mesh balls and rblocks.
ball_top = support_z
for ball in it.ball.list():
    ball_top = max(ball_top, float(ball.pos()[2]) + float(ball.radius()))

cmd("""
fish define measure_reload_rblock_top
    global reload_rblock_top = -1.0e30
    loop foreach local block rblock.list
        loop foreach local vertex rblock.vertex.list(block)
            reload_rblock_top = math.max(reload_rblock_top,vertex->z)
        endloop
    endloop
end
[measure_reload_rblock_top]
""")
rblock_top = float(it.fish.get("reload_rblock_top"))
specimen_top = max(ball_top, rblock_top)
initial_specimen_height = specimen_top - support_z
if initial_specimen_height <= 0.0:
    raise RuntimeError(
        "Invalid restored specimen height: "+str(initial_specimen_height)
    )


platen_z = specimen_top + PLATEN_INITIAL_GAP
target_displacement = TARGET_AXIAL_STRAIN * initial_specimen_height


# just create a 4 platen vertices polygon as a wall (instead of 2 triangles)
wall_ids_before = {int(wall.id()) for wall in it.wall.list()}
platen_vertices = " ".join((
    "("+str(platen_x_min)+","+str(platen_y_max)+","+str(platen_z)+")",
    "("+str(platen_x_max)+","+str(platen_y_max)+","+str(platen_z)+")",
    "("+str(platen_x_max)+","+str(platen_y_min)+","+str(platen_z)+")",
    "("+str(platen_x_min)+","+str(platen_y_min)+","+str(platen_z)+")",
))

cmd("wall generate name 'compression_platen' group 'compression_platen' "+
    "polygon "+str(platen_vertices))
new_walls = [
    wall for wall in it.wall.list()
    if int(wall.id()) not in wall_ids_before
]
if len(new_walls) != 1:
    raise RuntimeError("Expected one compression platen, found "+str(len(new_walls)))
platen = new_walls[0]
platen_id = int(platen.id())


# Keep the mesh/rblock interface linear elastic, but add contact dashpots. This
# is important because each mesh ball is only 4.3 g whereas one rblock is orders
# of magnitude heavier. The CMAT entry handles contacts created later during
# compression; contact property updates the ball-rblock contacts already in the
# restored save without resetting their elastic force state.
it.fish.set("reload_ball_rblock_friction", BALL_RBLOCK_FRICTION)
cmd("contact cmat default type ball-rblock model linear method deformability ...\n"+
    "    emod "+str(BALL_RBLOCK_EMOD)+" kratio "+str(BALL_RBLOCK_KRATIO)+
    " property fric @reload_ball_rblock_friction ...\n"+
    "    dp_nratio "+str(CONTACT_DP_NRATIO)+" dp_sratio "+str(CONTACT_DP_SRATIO)+
    " dp_mode "+str(CONTACT_DP_MODE)+"\n"+
    "contact property fric @reload_ball_rblock_friction ...\n"+
    "    dp_nratio "+str(CONTACT_DP_NRATIO)+" dp_sratio "+str(CONTACT_DP_SRATIO)+
    " dp_mode "+str(CONTACT_DP_MODE)+" ...\n"+
    "    range contact type 'ball-rblock'\n"+
    "model clean all")


# The platen and support contacts are also linear elastic and damped. Existing
# ball-ball mesh bonds and rblock-rblock contacts are deliberately untouched.
it.fish.set("reload_platen_friction", PLATEN_FRICTION)
cmd("contact cmat default type ball-facet model linear method deformability ...\n"+
    "    emod "+str(CONTACT_EMOD)+" kratio "+str(CONTACT_KRATIO)+
    " property fric @reload_platen_friction ...\n"+
    "    dp_nratio "+str(CONTACT_DP_NRATIO)+" dp_sratio "+str(CONTACT_DP_SRATIO)+
    " dp_mode "+str(CONTACT_DP_MODE)+"\n"+
    "contact cmat default type rblock-facet model linear method deformability ...\n"+
    "    emod "+str(CONTACT_EMOD)+" kratio "+str(CONTACT_KRATIO)+
    " property fric @reload_platen_friction ...\n"+
    "    dp_nratio "+str(CONTACT_DP_NRATIO)+" dp_sratio "+str(CONTACT_DP_SRATIO)+
    " dp_mode "+str(CONTACT_DP_MODE)+"\n"+
    "contact cmat apply range contact type 'ball-facet'\n"+
    "contact cmat apply range contact type 'rblock-facet'\n"+
    "model clean all")

cmd("ball attribute damp "+str(MESH_BALL_LOCAL_DAMP))
cmd("rblock attribute damp "+str(RBLOCK_LOCAL_DAMP))

# Dissipate residual motion and any transient caused by creating the platen or
# changing interface damping. The platen remains fixed during this stage.
cmd("model cycle "+str(PRECOMPRESSION_SETTLE_CYCLES)+
    " calm "+str(PRECOMPRESSION_SETTLE_CALM))
cmd("model calm")
cmd("model clean all")


# FISH histories make downward displacement and compressive force positive.
it.fish.set("reload_platen_id", platen_id)
it.fish.set("reload_platen_initial_z", platen_z)
it.fish.set("reload_initial_height", initial_specimen_height)
it.fish.set("reload_target_displacement", target_displacement)
cmd("""
fish define platen_compression_displacement
    local platen_pointer = wall.find(reload_platen_id)
    platen_compression_displacement = reload_platen_initial_z - wall.pos.z(platen_pointer)
end

fish define platen_reaction_force
    local platen_pointer = wall.find(reload_platen_id)
    platen_reaction_force = math.abs(wall.force.contact.z(platen_pointer))
end

fish define platen_axial_strain
    platen_axial_strain = platen_compression_displacement / reload_initial_height
end

fish define stop_platen_compression
    stop_platen_compression = 0
    if platen_compression_displacement >= reload_target_displacement
        stop_platen_compression = 1
    endif
end

history purge
history interval """+str(HISTORY_INTERVAL)+"""
fish history name 'platen_displacement' platen_compression_displacement
fish history name 'platen_reaction_force' platen_reaction_force
fish history name 'platen_axial_strain' platen_axial_strain
""")


# Prescribed wall velocity remains constant throughout the loading stage.
cmd("wall attribute velocity-z "+str(PLATEN_VELOCITY_Z)+
    " range id "+str(platen_id))
cmd("model solve fish-halt @stop_platen_compression cycles "+
    str(MAX_COMPRESSION_CYCLES))
cmd("wall attribute velocity-z 0 range id "+str(platen_id))


# Export force versus displacement as formatted ASCII and preserve the end state.
cmd("history export 'platen_reaction_force' vs 'platen_displacement' "+
    "file '"+str(HISTORY_ASCII_FILE)+"' truncate")
cmd("model save '"+str(COMPRESSED_MODEL_NAME)+"'")

final_displacement = platen_z - float(platen.pos()[2])
final_reaction = abs(float(platen.force_contact()[2]))
