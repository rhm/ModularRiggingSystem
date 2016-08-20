from math import atan2, degrees

import maya.cmds as cmds

import System.utils as utils
#reload(utils)

import Animation.circleControlStretchyIK as circleIK
import System.controlObject as controlObject


CLASS_NAME="LegIK_ReverseFoot"
TITLE="Leg IK with Reverse Foot"
DESCRIPTION="This module provides an IK leg with reverse foot controls"


class LegIK_ReverseFoot(circleIK.CircleControlStretchyIK):
    def __init__(self, moduleNamespace):
        circleIK.CircleControlStretchyIK.__init__(self, moduleNamespace)


    def compatibleBlueprintModules(self):
        return ["LegFoot"]


    def install_custom(self, joints, moduleGrp, moduleContainer):
        ankleJoint = joints[3]
        ballJoint = joints[4]
        toeJoint = joints[5]

        # get position of ball, ankle and toe joints in module-space

        tempLocator = cmds.spaceLocator()[0]
        cmds.parent(tempLocator, ballJoint, relative=True)
        cmds.parent(tempLocator, moduleGrp, absolute=True)

        ballJoint_modulePos = [ cmds.getAttr(tempLocator+".translateX"),
                                cmds.getAttr(tempLocator+".translateY"),
                                cmds.getAttr(tempLocator+".translateZ") ]

        cmds.parent(tempLocator, ankleJoint)
        for attr in [".translateX",".translateY",".translateZ"]:
            cmds.setAttr(tempLocator+attr, 0.0)
        cmds.parent(tempLocator, moduleGrp, absolute=True)

        ankleJoint_modulePos = [ cmds.getAttr(tempLocator+".translateX"),
                                 cmds.getAttr(tempLocator+".translateY"),
                                 cmds.getAttr(tempLocator+".translateZ") ]

        cmds.parent(tempLocator, toeJoint)
        for attr in [".translateX",".translateY",".translateZ"]:
            cmds.setAttr(tempLocator+attr, 0.0)
        cmds.parent(tempLocator, moduleGrp, absolute=True)

        toeJoint_modulePos = [ cmds.getAttr(tempLocator+".translateX"),
                               cmds.getAttr(tempLocator+".translateY"),
                               cmds.getAttr(tempLocator+".translateZ") ]

        cmds.delete(tempLocator)

        # Set up leg IK

        containedNodes = []

        ikNodes = circleIK.CircleControlStretchyIK.install_custom(self, joints, moduleGrp, moduleContainer,
                                                                  createHandleControl=False, poleVectorAtRoot=False)
        ikEndPosLocator = ikNodes["endLocator"]
        ikPoleVectorLocator = ikNodes["poleVectorObject"]
        stretchinessAttribute = ikNodes["stretchinessAttribute"]

        name = "footControl"
        controlObjectInstance = controlObject.ControlObject()
        (footControl, footControlRootParent) = controlObjectInstance.create(name, "footControl.ma", self, lod=1,
                                                                            translation=True, rotation=True,
                                                                            globalScale=False, spaceSwitching=True)
        cmds.parent(footControlRootParent, moduleGrp, relative=True)

        footControlPos = [ankleJoint_modulePos[0], ballJoint_modulePos[1], ankleJoint_modulePos[2]]
        cmds.xform(footControl, objectSpace=True, absolute=True, translation=footControlPos)

        cmds.setAttr(footControl+".rotateOrder", 3) # xzy

        orientationVector = [toeJoint_modulePos[0] - ankleJoint_modulePos[0], toeJoint_modulePos[2] - ankleJoint_modulePos[2]]
        footControlRotation = atan2(orientationVector[1], orientationVector[0])
        cmds.setAttr(footControl+".rotateY", -degrees(footControlRotation))

        # expose stretchiness attribute

        cmds.select(footControl)
        cmds.addAttr(at="float", minValue=0.0, maxValue=1.0, defaultValue=1.0, keyable=True, longName="stretchiness")
        self.publishNameToModuleContainer(footControl+".stretchiness", "stretchiness", publishToOuterContainers=True)

        cmds.connectAttr(footControl+".stretchiness", stretchinessAttribute, force=True)

        # ball and toe controls

        ballToeControls = []
        ballToeControl_orientGrps = []

        for joint in [ballJoint, toeJoint]:
            controlObjectInstance = controlObject.ControlObject()
            jointName = utils.stripAllNamespaces(joint)[1]
            name = jointName + "_ryControl"

            ryControlInfo = controlObjectInstance.create(name, "yAxisCircle.ma", self, lod=2, translation=False,
                                                         rotation=[False, True, False], globalScale=False,
                                                         spaceSwitching=False)
            ryControl = ryControlInfo[0]
            ballToeControls.append(ryControl)

            orientGrp = cmds.group(empty=True, n=ryControl+"_orientGrp")
            containedNodes.append(orientGrp)
            ballToeControl_orientGrps.append(orientGrp)

            cmds.delete(cmds.parentConstraint(joint, orientGrp, maintainOffset=False))
            cmds.parent(ryControl, orientGrp, relative=True)

        for grp in ballToeControl_orientGrps:
            cmds.parent(grp, moduleGrp, absolute=True)

        containedNodes.append(cmds.parentConstraint(footControl, ballToeControl_orientGrps[1], maintainOffset=True,
                                                    n=ballToeControl_orientGrps[1]+"_parentConstraint")[0])
        containedNodes.append(cmds.parentConstraint(ballToeControls[1], ballToeControl_orientGrps[0], maintainOffset=True,
                                                    n=ballToeControl_orientGrps[0]+"_parentConstraint")[0])

        cmds.parent(ikEndPosLocator, ballToeControls[0], absolute=True)
        cmds.parent(ikPoleVectorLocator, ballToeControls[0], absolute=True)

        ankleIKNodes = cmds.ikHandle(sj=ankleJoint, ee=ballJoint, solver="ikSCsolver", n=ankleJoint+"_ikHandle")
        ankleIKNodes[1] = cmds.rename(ankleIKNodes[1], ankleIKNodes[1]+"_ikEffector")
        containedNodes.extend(ankleIKNodes)

        cmds.parent(ankleIKNodes[0], ballToeControls[0])
        cmds.setAttr(ankleIKNodes[0]+".visibility", 0)

        ballIKNodes = cmds.ikHandle(sj=ballJoint, ee=toeJoint, solver="ikSCsolver", n=ballJoint+"_ikHandle")
        ballIKNodes[1] = cmds.rename(ballIKNodes[1], ballIKNodes[1]+"_ikEffector")
        containedNodes.extend(ballIKNodes)

        cmds.parent(ballIKNodes[0], ballToeControls[1])
        cmds.setAttr(ballIKNodes[0]+".visibility", 0)

        # finish up

        utils.addNodeToContainer(moduleContainer, containedNodes, ihb=True)


    def UI(self, parentLayout):
        footControl = self.blueprintNamespace+":"+self.moduleNamespace+":footControl"

        controlObjectInstance = controlObject.ControlObject(footControl)
        controlObjectInstance.UI(parentLayout)

        cmds.attrControlGrp(attribute=footControl+".stretchiness", label="Stretchiness")

        circleIK.CircleControlStretchyIK.UI(self, parentLayout)

        jointsGrp = self.blueprintNamespace+":"+self.moduleNamespace+":joints_grp"
        joints = utils.findJointChain(jointsGrp)

        ballJoint = joints[4]
        toeJoint = joints[5]

        for joint in [ballJoint, toeJoint]:
            jointControl = joint+"_ryControl"
            controlObjectInstance = controlObject.ControlObject(jointControl)
            controlObjectInstance.UI(parentLayout)


    def match(self, *args):
        characterContainer = self.characterNamespaceOnly+":character_container"
        blueprintContainter = self.blueprintNamespace+":module_container"
        moduleContainer = self.blueprintNamespace+":"+self.moduleNamespace+":module_container"

        containers = [characterContainer, blueprintContainter, moduleContainer]
        for c in containers:
            cmds.lockNode(c, lock=False, lockUnpublished=False)

        ikJoints = utils.findJointChain(self.blueprintNamespace+":"+self.moduleNamespace+":joints_grp")
        blueprintJoints = utils.findJointChain(self.blueprintNamespace+":blueprint_joints_grp")

        footControl = self.blueprintNamespace+":"+self.moduleNamespace+":footControl"

        # foot control orientation

        tempChildTransform = cmds.group(empty=True)
        cmds.parent(tempChildTransform, footControl, relative=True)
        cmds.setAttr(tempChildTransform+".translateZ", 5.0)

        ikToePos = cmds.xform(ikJoints[5], q=True, worldSpace=True, translation=True)
        footControlPos = cmds.xform(footControl, q=True, worldSpace=True, translation=True)
        worldSpacePositionOffset = utils.vec_sub_vec(ikToePos, footControlPos)
        cmds.xform(tempChildTransform, worldSpace=True, relative=True, translation=worldSpacePositionOffset)

        cmds.parent(tempChildTransform, ikJoints[5], absolute=True)
        cmds.setAttr(tempChildTransform+".translateX", 0)
        cmds.setAttr(tempChildTransform+".translateZ", 0)

        cmds.parent(tempChildTransform, blueprintJoints[5], relative=True)

        cmds.xform(footControl, worldSpace=True, absolute=True, translation=cmds.xform(blueprintJoints[4], q=True, worldSpace=True, translation=True))

        aimConstraint = cmds.aimConstraint(blueprintJoints[5], footControl, maintainOffset=False, aimVector=[1.0, 0.0, 0.0],
                                           upVector=[0.0, 0.0, 1.0], worldUpType="object", worldUpObject=tempChildTransform)
        cmds.delete(aimConstraint)
        cmds.delete(tempChildTransform)

        # Toe position

        blueprint_toeJointPos = cmds.xform(blueprintJoints[5], q=True, worldSpace=True, translation=True)
        ikToePos = cmds.xform(ikJoints[5], q=True, worldSpace=True, translation=True)
        worldSpacePositionOffset = utils.vec_sub_vec(blueprint_toeJointPos, ikToePos)
        cmds.xform(footControl, worldSpace=True, relative=True, translation=worldSpacePositionOffset)

        # rotate toe and ball controls to match

        self.matchRotationControl(ikJoints[5]+"_ryControl", ikJoints[4], blueprintJoints[4])
        self.matchRotationControl(ikJoints[4]+"_ryControl", ikJoints[3], blueprintJoints[3])

        # match the leg twist
        circleIK.CircleControlStretchyIK.match(self, args)

        # re-lock containers
        for c in containers:
            cmds.lockNode(c, lock=True, lockUnpublished=True)


    def matchRotationControl(self, rotationControl, drivenJoint, targetJoint):
        controlPos = cmds.xform(rotationControl, q=True, worldSpace=True, translation=True)
        drivenJointPos = cmds.xform(drivenJoint, q=True, worldSpace=True, translation=True)
        targetJointPos = cmds.xform(targetJoint, q=True, worldSpace=True, translation=True)

        currentVector = utils.normaliseVector(utils.vec_sub_vec(drivenJointPos, controlPos))
        targetVector = utils.normaliseVector(utils.vec_sub_vec(targetJointPos, controlPos))

        offsetAngle = utils.angleBetweenVectors(targetVector, currentVector)
        cmds.setAttr(rotationControl+".rotateY", cmds.getAttr(rotationControl+".rotateY") + offsetAngle)

        drivenJointPos = cmds.xform(drivenJoint, q=True, worldSpace=True, translation=True)
        currentVector = utils.normaliseVector(utils.vec_sub_vec(drivenJointPos, controlPos))

        offsetAngle = utils.angleBetweenVectors(targetVector, currentVector)
        if offsetAngle > 0.1:
            offsetAngle *= -2.0
            cmds.setAttr(rotationControl+".rotateY", cmds.getAttr(rotationControl+".rotateY") + offsetAngle)
