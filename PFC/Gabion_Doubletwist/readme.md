The code builds a box of rblocks, compresses them to a low target pressure and then instantiates a double-twist hexagons mesh.

This is done to prevent the model from exploding due to excessive pressures during rblock generation. Additionally, rblocks work very well to obtain a cube-like structure (instead of spheres or clumps).

Most of the code is self explainatory (generate at scaled size -> dilate -> compress for an arbitrary amount of steps).

#######################################################

The main change is in the logic used to define the double-twist box: instead of placing the particles and then defining the contact based on their relative positions,
the code first generates a particle graph based on the desired topology, and then places the particles, so that it is straightforward to define contacts based on their ids.

This mapping code was written by GML-5.2

Balls are graph nodes and bonded contacts are graph edges.
The six face panels are generated independently, but their boundary nodes are snapped onto shared selvedge nodes, preventing duplicate particles or weird ambiguities at the connection between two panels.

The construction has four coordinate levels:
1. The gabion has six global mesh bounds (its faces).
2. Each box face is represented by a tuple defining a local coordinate frame.
3. A double-twist pattern is generated in local (u, v) coordinates.
4. Local panel nodes are mapped to rounded global (x, y,z) positions, with boundary nodes redirected to shared edge positions.

The resulting position graph is converted to PFC ball IDs only after all six faces have been assembled.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

The enclosing box is represented by the tuple

mesh_bounds = (mx0, mx1, my0, my1, mz0, mz1)

where each pair is the minimum and maximum bead-center coordinate along one
global axis. The lateral limits are derived from the settled walls with a bead radius and insertion clearance. The lower mesh is one bead radius above the
support. The upper mesh is placed above the highest rblock vertex after the rblocks are lifted for bottom-mesh insertion.

Each of the six faces is described by one tuple: (face_name, vec_center, vec_u_axis, vec_v_axis, half_u, half_v)

vec_center locates the face in global coordinates. vec_u_axis and vec_v_axis are global unit vectors defining its local in-plane axes.
half_u and half_v are its local half-widths.

for each node, the position in global coordinates is given as:
global_position = vec_center + u * vec_u_axis + v * vec_v_axis

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Box-edge maps

Every face contributes four edges, giving 24 face-edge occurrences. Since the box only has 12 edges, duplicates much collapse to shared edges.

For an edge with rounded endpoint vectors A and B, its key is

edge_key = tuple(sorted((A, B)))

The tuple is sorted to make it independent from the direction of traversal (i.e. A->B = B->A).

Each (selv)edge is divided into equally spaced segments:

segment_count = ceil(edge_length / EDGE_SPACING)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Local double-twist panel tuples

For each face, the code searches near the estimated (nx, ny) values and selects the pattern dimensions whose width and height best match the face. By best match it means that it gives it a score, i.e. the squared size error.

Each local panel node has a topology key

(row_index, column_index, endpoint_index)


where endpoint_index is 0 for the lower particle and 1 for the upper particle of a double-twist segment, which is then mapped to (u,v,group) coordinates, where group is dt0 and dt1

The following topology is adopted:
local_dt_pairs =  joins the lower and upper keys of every double-twist segment.
local_sw_pairs =  joins the spheres in adjacent rows when their local center distance is approx SW_DIST (within CONTACT_GAP_TOL).


#######################################################

Snapping local nodes to shared edges

The local panel pattern is centered about the face. A node is first shifted to
centered local coordinates (local_u, local_v).

If a local coordinate lies within EDGE_SNAP_TOL of a face boundary, it is placed exactly on that boundary:

if abs(local_u - half_u) <= EDGE_SNAP_TOL: local_u = half_u
if abs(local_u + half_u) <= EDGE_SNAP_TOL: local_u = -half_u
if abs(local_v - half_v) <= EDGE_SNAP_TOL: local_v = half_v
if abs(local_v + half_v) <= EDGE_SNAP_TOL: local_v = -half_v

And then it is snapped to a pre-existing edge if it exists.

