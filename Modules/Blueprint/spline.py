import os
import maya.cmds as cmds

import System.blueprint as bpmod
#reload(bpmod)

import System.utils as utils
reload(utils)



CLASS_NAME = 'Spline'

TITLE = "Spline"
DESCRIPTION = "Creates an optionally interpolating, joint-count adjustable spline. Ideal use: spine, neck/head, tails, tentacles, etc."
ICON = os.environ["RIGGING_TOOL_ROOT"] + "/Icons/_spline.xpm"


class Spline(bpmod.Blueprint):
    def __init__(self, userSpecifiedName, hookObject, numberOfJoints=None, startJointPos=None, endJointPos=None):
        if numberOfJoints == None:
            jointsGrp = CLASS_NAME + "__" + userSpecifiedName + ":joints_grp"
            if not cmds.objExists(jointsGrp):
                numberOfJoints = 5 #default
            else:
                joints = utils.findJointChain(jointsGrp)
                joints.pop()
                numberOfJoints = len(joints)

        jointInfo = []

        if not startJointPos:
            startJointPos = [0.0,0.0,0.0]
        if not endJointPos:
            endJointPos = [0.0, 15.0, 0.0]

        jointIncrement = list(endJointPos)
        jointIncrement[0] -= startJointPos[0]
        jointIncrement[1] -= startJointPos[1]
        jointIncrement[2] -= startJointPos[2]

        jointIncrement[0] /= (numberOfJoints-1)
        jointIncrement[1] /= (numberOfJoints-1)
        jointIncrement[2] /= (numberOfJoints-1)

        jointPos = startJointPos
        for i in range(numberOfJoints):
            jointName = "spline_"+str(i)+"_joint"
            jointInfo.append([jointName, list(jointPos)])
            jointPos[0] += jointIncrement[0]
            jointPos[1] += jointIncrement[1]
            jointPos[2] += jointIncrement[2]

        bpmod.Blueprint.__init__(self, CLASS_NAME, userSpecifiedName, jointInfo, hookObject)

        self.canBeMirrored = False
