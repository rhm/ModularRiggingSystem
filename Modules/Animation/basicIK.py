import maya.cmds as cmds

import System.utils as utils
reload(utils)

import System.controlModule as controlModule
#reload(controlModule)
import System.controlObject as controlObject
#reload(controlObject)


CLASS_NAME="BasicStretchyIK"
TITLE="Basic Stretchy IK"
DESCRIPTION="This module provides stretchy IK on the joint chain with the ability to lock the stretchiness with a " \
            "0->1 slider value. Note: the ik handle is not space-switchable and for that reason has frozen " \
            "transformations at its creation position."


class BasicStretchyIK(controlModule.ControlModule):
    def __init__(self, moduleNamespace):
        controlModule.ControlModule.__init__(self, moduleNamespace)


    def compatibleBlueprintModules(self):
        return ["Finger", "HingeJoint", "SingleJointSegment"]


    def install_custom(self, joints, moduleGrp, moduleContainer):
        containedNodes = []
        rootJoint = joints[1]
        endJoint = joints[-1]

        ikNodes = utils.basic_stretchy_IK(rootJoint, endJoint, container=moduleContainer,
                                          scaleCorrectionAttribute=self.blueprintNamespace+":module_grp.hierarchicalScale")
        ikHandle = ikNodes["ikHandle"]
        rootLocator = ikNodes["rootLocator"]
        endLocator = ikNodes["endLocator"]
        poleVectorLocator = ikNodes["poleVectorObject"]
        stretchinessAttribute = ikNodes["stretchinessAttribute"]

        for node in [rootLocator, ikHandle, poleVectorLocator]:
            cmds.parent(node, moduleGrp, absolute=True)

        name = "ikHandleControl"

        controlObjectInstance = controlObject.ControlObject()
        handleControlInfo = controlObjectInstance.create(name, "cubeLocator.ma", self, lod=1, translation=True, rotation=False,
                                                         globalScale=False, spaceSwitching=False)
        handleControl = handleControlInfo[0]
        handleRootParent = handleControlInfo[1]

        cmds.parent(handleRootParent, moduleGrp, relative=True)

        cmds.xform(handleControl, worldSpace=True, absolute=True, translation=cmds.xform(endLocator, q=True, worldSpace=True, translation=True))
        cmds.parent(endLocator, handleControl, absolute=True)

        handleControlParent = cmds.listRelatives(handleControl, parent=True)[0]
        preTransform = cmds.group(empty=True, n=handleControl+"_preTransform")
        containedNodes.append(preTransform)

        cmds.parent(preTransform, handleControl, relative=True)
        cmds.parent(preTransform, handleControlParent, absolute=True)
        cmds.parent(handleControl, preTransform, absolute=True)

        cmds.select(handleControl)
        cmds.addAttr(at="float", minValue=0.0, maxValue=1.0, defaultValue=1.0, keyable=True, longName="stretchiness")
        cmds.addAttr(at="float", softMinValue=-360.0, softMaxValue=360.0, defaultValue=0.0, keyable=True, longName="twist")

        cmds.connectAttr(handleControl+".twist", ikHandle+".twist")
        cmds.connectAttr(handleControl+".stretchiness", stretchinessAttribute)

        self.publishNameToModuleContainer(handleControl+".twist", "twist", publishToOuterContainers=True)
        self.publishNameToModuleContainer(handleControl+".stretchiness", "stretchiness", publishToOuterContainers=True)

        utils.addNodeToContainer(moduleContainer, containedNodes)


    def UI(self, parentLayout):
        ikHandleControl = self.blueprintNamespace+":"+self.moduleNamespace+":ikHandleControl"
        controlObjectInstance = controlObject.ControlObject(ikHandleControl)
        controlObjectInstance.UI(parentLayout)

        cmds.attrControlGrp(attribute=ikHandleControl+".twist", label="twist")
        cmds.attrControlGrp(attribute=ikHandleControl+".stretchiness", label="Stretchiness")