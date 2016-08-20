import maya.cmds as cmds

import System.utils as utils
reload(utils)

import System.controlModule as controlModule
#reload(controlModule)
import System.controlObject as controlObject
#reload(controlObject)


CLASS_NAME="CircleControlStretchyIK"
TITLE="Circle-controlled Stretchy IK"
DESCRIPTION="This module provides stretchy IK on the joint chain, with the ability to lock the stretchiness with a " \
            "0->1 slider. IK twist is controlled by an adjustable circle rotation control."


class CircleControlStretchyIK(controlModule.ControlModule):
    def __init__(self, moduleNamespace):
        controlModule.ControlModule.__init__(self, moduleNamespace)


    def compatibleBlueprintModules(self):
        return ["HingeJoint"]


    def install_custom(self, joints, moduleGrp, moduleContainer, createHandleControl=True, poleVectorAtRoot=True):
        rootJoint = joints[1]
        hingeJoint = joints[2]
        endJoint = joints[3]

        containedNodes = []

        twistRotationAimer = cmds.group(empty=True, n=rootJoint+"_twistRotationAimer")
        containedNodes.append(twistRotationAimer)

        containedNodes.append(cmds.pointConstraint(rootJoint, twistRotationAimer, maintainOffset=False,
                                                   n=twistRotationAimer+"_pointConstraint")[0])
        cmds.pointConstraint(endJoint, twistRotationAimer, maintainOffset=False)

        upVectorTarget = cmds.group(empty=True, n=rootJoint+"_twistRotationAimer_upVectorTarget")
        containedNodes.append(upVectorTarget)

        cmds.parent(upVectorTarget, hingeJoint, relative=True)
        cmds.setAttr(upVectorTarget+".translateZ", cmds.getAttr(hingeJoint+".translateX"))

        containedNodes.append(cmds.aimConstraint(endJoint, twistRotationAimer, maintainOffset=False,
                                                 n=twistRotationAimer+"_aimConstraint", aimVector=[0.0, 0.0, 1.0],
                                                 upVector=[1.0, 0.0, 0.0], worldUpType="object",
                                                 worldUpObject=upVectorTarget)[0])

        tempLocator = cmds.spaceLocator()[0]
        cmds.parent(tempLocator, twistRotationAimer, relative=True)
        cmds.setAttr(tempLocator+".translateY", 10)

        twistRotationAimerPos = cmds.xform(twistRotationAimer, q=True, worldSpace=True, translation=True)
        tempLocatorPos = cmds.xform(tempLocator, q=True, worldSpace=True, translation=True)
        offsetVector = utils.vec_sub_vec(tempLocatorPos, twistRotationAimerPos)
        cmds.delete(tempLocator)

        ikNodes = utils.basic_stretchy_IK(rootJoint, endJoint, container=moduleContainer,
                                          scaleCorrectionAttribute=self.blueprintNamespace+":module_grp.hierarchicalScale")
        ikHandle = ikNodes["ikHandle"]
        rootPosLocator = ikNodes["rootLocator"]
        endPosLocator = ikNodes["endLocator"]
        poleVectorLocator = ikNodes["poleVectorObject"]
        stretchinessAttribute = ikNodes["stretchinessAttribute"]

        for node in [ikHandle, rootPosLocator, endPosLocator, poleVectorLocator]:
            cmds.parent(node, moduleGrp, absolute=True)

        if poleVectorAtRoot:
            poleVectorPos = cmds.xform(rootJoint, q=True, worldSpace=True, translation=True)
        else:
            poleVectorPos = cmds.xform(endJoint, q=True, worldSpace=True, translation=True)

        poleVectorPos = utils.vec_add_vec(poleVectorPos, offsetVector)
        cmds.xform(poleVectorLocator, worldSpace=True, absolute=True, translation=poleVectorPos)

        if createHandleControl:
            name = "ikHandleControl"
            controlObjectInstance = controlObject.ControlObject()
            (handleControl, handleRootParent) = controlObjectInstance.create(name, "cubeLocator.ma", self, lod=1, translation=True,
                                                                             rotation=False, globalScale=False, spaceSwitching=True)
            cmds.parent(handleRootParent, moduleGrp, relative=True)
            cmds.xform(handleControl, worldSpace=True, absolute=True,
                       translation=cmds.xform(endPosLocator, q=True, worldSpace=True, translation=True))

            pointConstraint = cmds.pointConstraint(handleControl, endPosLocator, maintainOffset=False,
                                                   n=endPosLocator+"_pointConstraint")[0]
            containedNodes.append(pointConstraint)

            cmds.select(handleControl)
            cmds.addAttr(at="float", minValue=0.0, maxValue=1.0, defaultValue=1.0, keyable=True, longName="stretchiness")
            cmds.connectAttr(handleControl+".stretchiness", stretchinessAttribute)

            self.publishNameToModuleContainer(handleControl+".stretchiness", "stretchiness", publishToOuterContainers=True)

        rotationCancellation = cmds.group(empty=True, n=self.blueprintNamespace+":"+self.moduleNamespace+":twistRotationCancellation")
        containedNodes.append(rotationCancellation)
        cmds.parent(rotationCancellation, twistRotationAimer, relative=True)

        twistControlOffset = cmds.group(empty=True, n=self.blueprintNamespace+":"+self.moduleNamespace+":twistControlOffset")
        containedNodes.append(twistControlOffset)
        cmds.parent(twistControlOffset, rotationCancellation, relative=True)

        twistControlObjectInstance = controlObject.ControlObject()
        (twistControl, _) = twistControlObjectInstance.create("twistControl", "zAxisCircle.ma", self, lod=2, translation=False,
                                                              rotation=[False,False,True], globalScale=False, spaceSwitching=False)
        cmds.parent(twistControl, twistControlOffset, relative=True)
        cmds.connectAttr(twistControl+".rotateZ", ikHandle+".twist")

        pivotMultNode = cmds.shadingNode("multiplyDivide", asUtility=True, n=twistControl+"_invertOffset")
        containedNodes.append(pivotMultNode)

        cmds.connectAttr(twistControlOffset+".translateX", pivotMultNode+".input1X")
        cmds.setAttr(pivotMultNode+".input2X", -1)
        cmds.connectAttr(pivotMultNode+".output", twistControl+".rotatePivot")

        multNode = cmds.shadingNode("multiplyDivide", asUtility=True, n=rotationCancellation+"_invertRotateZ")
        containedNodes.append(multNode)

        cmds.connectAttr(twistControl+".rotateZ", multNode+".input1X")
        cmds.setAttr(multNode+".input2X", -1)
        cmds.connectAttr(multNode+".outputX", rotationCancellation+".rotateZ")

        cmds.parent(twistRotationAimer, moduleGrp, absolute=True)

        # Match creation pose pole vector orientation
        ikJoints = joints[1:4]
        jointName = utils.stripAllNamespaces(joints[1])[1]
        creationPoseRoot = self.blueprintNamespace+":creationPose_"+jointName
        creationPoseJoints = utils.findJointChain(creationPoseRoot)

        targetJoints = creationPoseJoints[0:3]
        utils.matchTwistAngle(twistControl+".rotateZ", ikJoints, targetJoints)

        offsetNode = cmds.shadingNode("plusMinusAverage", asUtility=True, n=twistControl+"_twistOffset")
        containedNodes.append(offsetNode)

        cmds.setAttr(offsetNode+".input1D[0]", cmds.getAttr(twistControl+".rotateZ"))
        cmds.connectAttr(twistControl+".rotateZ", offsetNode+".input1D[1]")
        cmds.connectAttr(offsetNode+".output1D", ikHandle+".twist", force=True)

        utils.forceSceneUpdate()
        cmds.setAttr(twistControl+".rotateZ", 0)

        # Finish up

        utils.addNodeToContainer(moduleContainer, containedNodes)
        self.publishNameToModuleContainer(twistControlOffset+".translateX", "twistControlOffset", publishToOuterContainers=True)

        cmds.setAttr(moduleGrp+".lod", 2)

        return ikNodes


    def UI(self, parentLayout):
        ikHandleControl = self.blueprintNamespace+":"+self.moduleNamespace+":ikHandleControl"

        if cmds.objExists(ikHandleControl):
            controlObjectInstance = controlObject.ControlObject(ikHandleControl)
            controlObjectInstance.UI(parentLayout)

            cmds.attrControlGrp(attribute=ikHandleControl+".stretchiness", label="Stretchiness")

        twistControl = self.blueprintNamespace+":"+self.moduleNamespace+":twistControl"
        controlObjectInstance = controlObject.ControlObject(twistControl)
        controlObjectInstance.UI(parentLayout)


    def UI_preferences(self, parentLayout):
        twistOffset = self.blueprintNamespace+":"+self.moduleNamespace+":twistControlOffset"
        cmds.attrControlGrp(attribute=twistOffset+".translateX", label="Twist Offset")


    def match(self, *args):
        characterContainer = self.characterNamespaceOnly+":character_container"
        blueprintContainer = self.blueprintNamespace+":module_container"
        moduleContainer = self.blueprintNamespace+":"+self.moduleNamespace+":module_container"

        containers = [characterContainer, blueprintContainer, moduleContainer]
        for c in containers:
            cmds.lockNode(c, lock=False, lockUnpublished=False)

        ikJointsAll = utils.findJointChain(self.blueprintNamespace+":"+self.moduleNamespace+":joints_grp")
        blueprintJointsAll = utils.findJointChain(self.blueprintNamespace+":blueprint_joints_grp")

        ikJoints = ikJointsAll[1:4]
        blueprintJoints = blueprintJointsAll[1:4]

        ikHandleControl = self.blueprintNamespace+":"+self.moduleNamespace+":ikHandleControl"
        if cmds.objExists(ikHandleControl):
            cmds.setAttr(ikHandleControl+".stretchiness", 1)

            endPos = cmds.xform(blueprintJoints[2], q=True, worldSpace=True, translation=True)
            cmds.xform(ikHandleControl, worldSpace=True, absolute=True, translation=endPos)

        twistControl = self.blueprintNamespace+":"+self.moduleNamespace+":twistControl"
        utils.matchTwistAngle(twistControl+".rotateZ", ikJoints, blueprintJoints)

        for c in containers:
            cmds.lockNode(c, lock=True, lockUnpublished=True)