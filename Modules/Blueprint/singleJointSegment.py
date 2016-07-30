import os

import maya.cmds as cmds

import System.blueprint as bpmod
reload(bpmod)

CLASS_NAME = 'SingleJointSegment'

TITLE = "Single Joint Segment"
DESCRIPTION = "Creates 2 joints, with control for 1st joint's orientation and rotation order. Ideal use: clavicle bones/shoulder"
ICON = os.environ["RIGGING_TOOL_ROOT"] + "/Icons/_singleJointSeg.xpm"


class SingleJointSegment(bpmod.Blueprint):
    def __init__(self, userSpecifiedName, hookObj):
        jointInfo = [ ["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]]  ]

        bpmod.Blueprint.__init__(self, CLASS_NAME, userSpecifiedName, jointInfo, hookObj)


    def install_custom(self, joints):
        self.createOrientationControl(joints[0], joints[1])


    def lock_phase1(self):
        # Gather and return all required information from this module's control objects

        # jointPositions = list of joint positions, from root down the hierarchy
        # jointOrientations = a list of orientations, or a list of axis information (orientJoint and secondaryAxisOrient) for each joint
        #                   # These are passed in the following tuple: (orientations, None) or (None, axisInfo)
        # jointRotationOrders = a list of joint rotations orders (integer values gathered with getAttr)
        # jointPreferredAngles = a list of joint preferred angles, optional (can pass None)
        # hookObject = self.findHookObjectForLock()
        # rootTransform = a bool, True == R, T & S on root joint, False == R only
        #
        # moduleInfo = (jointPositions, jointOrientations, jointRotationOrders, jointPreferredAngles, hookObject, rootTransform)
        # return moduleInfo

        jointPositions = []
        jointOrientationValues = []
        jointRotationOrders = []

        joints = self.getJoints()

        for joint in joints:
            jointPositions.append(cmds.xform(joint, q=True, worldSpace=True, translation=True))

        cleanParent = self.moduleNamespace+":joints_grp"
        orientationInfo = self.orientationControlledJoint_getOrientation(joints[0], cleanParent)
        cmds.delete(orientationInfo[1])
        jointOrientationValues.append(orientationInfo[0])
        #jointOrientationValues.append(["xyz","zup"])

        jointOrientations = (jointOrientationValues, None)
        #jointOrientations = (None, jointOrientationValues)

        jointRotationOrders.append(cmds.getAttr(joints[0]+".rotateOrder"))

        jointPreferredAngles = None
        hookObject = self.findHookObjectForLock()
        rootTransform = True

        moduleInfo = (jointPositions, jointOrientations, jointRotationOrders, jointPreferredAngles, hookObject, rootTransform)
        return moduleInfo


    def UI_custom(self):
        joints = self.getJoints()
        self.createRotationOrderUIControl(joints[0])



