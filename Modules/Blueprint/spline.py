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


    def install_custom(self, joints):
        self.setup_interpolation()


    def setup_interpolation(self, unlockContainer=False, *args):
        previousSelect = cmds.ls(selection=True)

        if unlockContainer:
            cmds.lockNode(self.containerName, lock=False, lockUnpublished=False)

        joints = self.getJoints()
        numberOfJoints = len(joints)

        startControl = self.getTranslationControl(joints[0])
        endControl = self.getTranslationControl(joints[-1])

        pointConstraints = []

        for i in range(1, numberOfJoints-1):
            material = joints[i]+"_m_translation_control"
            cmds.setAttr(material+".colorR", 0.815)
            cmds.setAttr(material+".colorG", 0.629)
            cmds.setAttr(material+".colorB", 0.498)

            translationControl = self.getTranslationControl(joints[i])

            endWeight = 0.0 + (float(i) / (numberOfJoints-1))
            startWeight = 1.0 - endWeight

            pointConstraints.append(cmds.pointConstraint(startControl, translationControl, maintainOffset=False, weight=startWeight)[0])
            pointConstraints.append(cmds.pointConstraint(endControl, translationControl, maintainOffset=False, weight=endWeight)[0])

            for attr in [".translateX", ".translateY", ".translateZ"]:
                cmds.setAttr(translationControl+attr, lock=True)

        interpolationContainer = cmds.container(n=self.moduleNamespace+":interpolation_container")
        utils.addNodeToContainer(interpolationContainer, pointConstraints)
        utils.addNodeToContainer(self.containerName, interpolationContainer)

        if unlockContainer:
            cmds.lockNode(self.containerName, lock=True, lockUnpublished=True)

        if previousSelect:
            cmds.select(previousSelect, replace=True)
        else:
            cmds.select(clear=True)