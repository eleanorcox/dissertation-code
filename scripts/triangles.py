import maya.api.OpenMaya as OpenMaya
import math

def getHeights(l_pos, c_pos, r_pos):
    xz_point = [0.25, 0.2]       # Test point

    selectionList = OpenMaya.MSelectionList()
    selectionList.add('pPlane1')
    nodeDagPath = selectionList.getDagPath(0)
    mFnMesh = OpenMaya.MFnMesh(nodeDagPath)

    vtx_pos = getGroundVertexPositions(mFnMesh)
    tri_vtx_indx = getGroundTriangleIndices(mFnMesh)

    closest_vtx_index = getClosestVertexIndex(xz_point, vtx_pos)
    closest_vtx_pos = vtx_pos[closest_vtx_index]
    on_vertex = xz_point[0] == closest_vtx_pos[0] and xz_point[1] == closest_vtx_pos[2]

    if not on_vertex:
        poss_tri = getPossibleTriangles(closest_vtx_index, tri_vtx_indx)
        height = interpolateHeight(xz_point, poss_tri, vtx_pos)
    else:
        height = closest_vtx_pos[1]

    return height

def getGroundVertexPositions(mFnMesh):
    space = OpenMaya.MSpace.kWorld
    vtx = mFnMesh.getPoints(space)

    vtx_pos = []
    for x in range(len(vtx)):
        vtx_pos.append([vtx[x].x, vtx[x].y, vtx[x].z])
    return vtx_pos

def getGroundTriangleIndices(mFnMesh):
    triangle_count, triangle_indices = mFnMesh.getTriangles()
    
    tri_vtx_indx = [triangle_indices[i:i + 3] for i in xrange(0, len(triangle_indices), 3)]
    return tri_vtx_indx

def getClosestVertexIndex(xz_point, vertices):
    closest = -1
    shortest_dist = float('inf')
    for i in range(len(vertices)):
        xdist = (xz_point[0] - vertices[i][0]) ** 2
        zdist = (xz_point[1] - vertices[i][2]) ** 2
        euc_dist = math.sqrt(xdist + zdist)
        if euc_dist <= shortest_dist:
            closest = i
            shortest_dist = euc_dist
    return closest

def getPossibleTriangles(closest_vtx_index, tri_vtx_indx):
    possTriangles = []
    for i in range(len(tri_vtx_indx)):
        if closest_vtx_index in tri_vtx_indx[i]:
            possTriangles.append(tri_vtx_indx[i])
    return possTriangles

def interpolateHeight(xz_point, poss_tri, vtx_pos):
    # Takes list of possible triangles point lies within and creates list of the world space coordinates of the vertices defining the triangles
    possible_triangles = []
    for tri in poss_tri:
        a_index = tri[0]
        b_index = tri[1]
        c_index = tri[2]
        possible_triangles.append([vtx_pos[a_index], vtx_pos[b_index], vtx_pos[c_index]])

    # Using barycetric coordinates, find which triangle the point lies in and interpolate to find the height of the point
    in_triangle = False
    for triangle in possible_triangles:
        A = triangle[0]
        B = triangle[1]
        C = triangle[2]
        P = xz_point

        # TODO: make vectorsub function
        v0 = [C[0] - A[0], C[2] - A[2]]    # v0 = C-A
        v1 = [B[0] - A[0], B[2] - A[2]]    # v1 = B-A
        v2 = [P[0] - A[0], P[1] - A[2]]    # v2 = P-A

        # Dot product is commutative (for real numbers)
        dot00 = dotProduct2D(v0, v0)
        dot01 = dotProduct2D(v0, v1)
        dot02 = dotProduct2D(v0, v2)
        dot11 = dotProduct2D(v1, v1)
        dot12 = dotProduct2D(v1, v2)

        # Compute barycentric coordinates
        inv_denominator = 1 / float(dot00 * dot11 - dot01 * dot01)
        u = (dot11 * dot02 - dot01 * dot12) * inv_denominator
        v = (dot00 * dot12 - dot01 * dot02) * inv_denominator

        # Check if point is in triangle
        in_triangle = (u >= 0) and (v >= 0) and (u + v <= 1)
        if in_triangle:
            # Interpolate to find height
            height = A[1] + u*(C[1] - A[1]) + v*(B[1] - A[1])
            break

    return height

def dotProduct2D(a, b):
    dot = a[0]*b[0] + a[1]*b[1]
    return dot
