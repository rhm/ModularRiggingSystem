import os
import maya.cmds as cmds

import System.blueprint as bpmod
#reload(bpmod)

import System.utils as utils
reload(utils)



CLASS_NAME = 'HingeJoint'

TITLE = "Hinge Joint"
DESCRIPTION = "Creates 3 joints, (the middle joint acting as a hinge joint). Ideal use: arm/leg"
ICON = os.environ["RIGGING_TOOL_ROOT"] + "/Icons/_hinge.xpm"


class HingeJoint(bpmod.Blueprint):
    def __init__(self, userSpecifiedName, hookObject):
        jointInfo = [
            ["root_joint",      [0.0, 0.0, 0.0]],
            ["hinge_joint",     [4.0, 0.0, -1.0]],
            ["end_joint",       [8.0, 0.0, 0.0]]
        ]

        bpmod.Blueprint.__init__(self, CLASS_NAME, userSpecifiedName, jointInfo, hookObject)


    def install_custom(self, joints):
        cmds.select(clear=True)
        ikJoints = []

        if not self.mirrored:
            index = 0
            for joint in self.jointInfo:
                ikJoints.append(cmds.joint(n=self.moduleNamespace+":IK_"+joint[0], p=joint[1], absolute=True, rotationOrder="xyz"))
                cmds.setAttr(ikJoints[index]+".visibility", 0)

                if index != 0:
                    cmds.joint(ikJoints[index-1], edit=True, oj="xyz", sao="yup")

                index += 1
        else:
            rootJointName = self.jointInfo[0][0]
            tempDuplicateNodes = cmds.duplicate(self.originalModule+":IK_"+rootJointName, renameChildren=True)

            cmds.delete(tempDuplicateNodes.pop())

            mirrorXY = False
            mirrorYZ = False
            mirrorXZ = False
            if self.mirrorPlane == "XY":
                mirrorXY = True
            elif self.mirrorPlane == "YZ":
                mirrorYZ = True
            if self.mirrorPlane == "XZ":
                mirrorXZ = True

            mirrorBehavior = False
            if self.rotationFunction == "behaviour":
                mirrorBehavior = True

            mirrorJoints = cmds.mirrorJoint(tempDuplicateNodes[0], mirrorXY=mirrorXY, mirrorYZ=mirrorYZ, mirrorXZ=mirrorXZ, mirrorBehavior=mirrorBehavior)
            cmds.delete(tempDuplicateNodes)
            cmds.xform(mirrorJoints[0], worldSpace=True, absolute=True, translation=cmds.xform(self.moduleNamespace+":"+rootJointName, q=True, worldSpace=True, translation=True))


            for i in range(3):
                jointName = self.jointInfo[i][0]
                newName = cmds.rename(mirrorJoints[i], self.moduleNamespace+":IK_"+jointName)
                ikJoints.append(newName)


        utils.addNodeToContainer(self.containerName, ikJoints)

        for joint in ikJoints:
            jointName = utils.stripAllNamespaces(joint)[1]
            cmds.container(self.containerName, edit=True, publishAndBind=[joint+".rotate", jointName+"_R"])

        cmds.setAttr(ikJoints[0]+".preferredAngleY", -50.0)
        cmds.setAttr(ikJoints[1]+".preferredAngleY", 50.0)

        ikNodes = utils.RP_2segment_stretchy_IK(ikJoints[0], ikJoints[1], ikJoints[2], self.containerName)
        locators = (ikNodes[0], ikNodes[1], ikNodes[2])
        distanceNodes = ikNodes[3]

        constraints = []
        for i in range(3):
            constraints.append(cmds.pointConstraint(self.getTranslationControl(joints[i]), locators[i], maintainOffset=False)[0])
            cmds.parent(locators[i], self.moduleNamespace+":module_grp", absolute=True)
            cmds.setAttr(locators[i]+".visibility", 0)

        utils.addNodeToContainer(self.containerName, constraints)

        scaleTarget = self.getTranslationControl(joints[1])
        paRep = self.createPreferredAngleRepresentation(ikJoints[1], scaleTarget)

        cmds.setAttr(paRep+".axis", lock=True)


    def UI_custom(self):
        joints = self.getJoints()
        self.createRotationOrderUIControl(joints[0])
        self.createRotationOrderUIControl(joints[1])


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
        jointPreferredAngles = []

        cmds.lockNode(self.containerName, lock=False, lockUnpublished=False)
        ikHandle = self.moduleNamespace+":IK_"+self.jointInfo[0][0]+"_ikHandle"
        cmds.delete(ikHandle)

        for i in range(3):
            jointName = self.jointInfo[i][0]
            ikJointName = self.moduleNamespace+":IK_"+jointName
            cmds.makeIdentity(ikJointName, rotate=True, translate=False, scale=False, apply=True)

            jointPositions.append(cmds.xform(ikJointName, q=True, worldSpace=True, translation=True))
            jointRotationOrders.append(cmds.getAttr(self.moduleNamespace+":"+jointName+".rotateOrder"))

            if i < 2:
                jointOrientX = cmds.getAttr(ikJointName+".jointOrientX")
                jointOrientY = cmds.getAttr(ikJointName+".jointOrientY")
                jointOrientZ = cmds.getAttr(ikJointName+".jointOrientZ")

                jointOrientationValues.append( (jointOrientX, jointOrientY, jointOrientZ) )

                joint_paX = cmds.getAttr(ikJointName+".preferredAngleX")
                joint_paY = cmds.getAttr(ikJointName+".preferredAngleY")
                joint_paZ = cmds.getAttr(ikJointName+".preferredAngleZ")

                jointPreferredAngles.append( (joint_paX, joint_paY, joint_paZ) )

        jointOrientations = (jointOrientationValues, None)
        hookObject = self.findHookObjectForLock()
        rootTransform = False

        moduleInfo = (jointPositions, jointOrientations, jointRotationOrders, jointPreferredAngles, hookObject, rootTransform)
        return moduleInfo
