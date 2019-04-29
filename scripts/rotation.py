# OpenMaya API 2.0
import maya.api.OpenMaya as OpenMaya

selectionList = OpenMaya.MSelectionList()
selectionList.add('pCube1')
nodeDagPath = selectionList.getDagPath(0)

mFnTransform = OpenMaya.MFnTransform(nodeDagPath)
xform_matrix = mFnTransform.transformation().asMatrix()

# Rotation of -53.130 degrees (chosen as has nice values for sin(theta) and cos(theta))
transformation = OpenMaya.MMatrix([[0.6, -0.8, 0.0, 0.0], [0.8, 0.6, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])

new_mat = xform_matrix * transformation     # In maya matrices are post-multiplied
new_trans = OpenMaya.MTransformationMatrix(new_mat)
mFnTransform.setTransformation(new_trans)

# # Euler angle rotation
# space = OpenMaya.MSpace.kWorld
# eul = OpenMaya.MEulerRotation(0.0, 0.0, -0.89)
# mFnTransform.rotateBy(eul, space)
