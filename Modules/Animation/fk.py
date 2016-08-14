import maya.cmds as cmds

import System.utils as utils
reload(utils)

import System.controlModule as controlModule
#reload(controlModule)
import System.controlObject as controlObject
#reload(controlObject)


CLASS_NAME="FK"
TITLE="Forward Kinematics"
DESCRIPTION="This module provides FK rotational controls for every joint in the blueprint it is installed on"


class FK(controlModule.ControlModule):
    def __init__(self, moduleNamespace):
        controlModule.ControlModule.__init__(self, moduleNamespace)


    def compatibleBlueprintModules(self):
        return ["Finger", "HingeJoint", "LegFoot", "SingleJointSegment", "SingleOrientableJoint", "Spline", "Thumb"]


    def install_custom(self, joints, moduleGrp, moduleContainer):
        controlsGrp = cmds.group(empty=True, name=self.blueprintNamespace+":"+self.moduleNamespace+":controls_grp")
        cmds.parent(controlsGrp, moduleGrp, absolute=True)
        utils.addNodeToContainer(moduleContainer, controlsGrp)

        numJoint = len(joints)-1

        for i in range(1, len(joints)):
            if i < numJoint or numJoint == 1:
                self.createFKControl(joints[i], controlsGrp, moduleContainer)


    def createFKControl(self, joint, parent, moduleContainer):
        jointName = utils.stripAllNamespaces(joint)[1]
        containedNodes = []
        name = jointName + "_fkControl"

        controlObjectInstance = controlObject.ControlObject()

        (fkControl, _) = controlObjectInstance.create(name, "sphere.ma", self, lod=1, translation=False, rotation=True, globalScale=False, spaceSwitching=False)
        cmds.connectAttr(joint+".rotateOrder", fkControl+".rotateOrder")

        orientGrp = cmds.group(n=fkControl+"_orientGrp", empty=True, parent=parent)
        containedNodes.append(orientGrp)

        orientGrp_parentConstraint = cmds.parentConstraint(joint, orientGrp, maintainOffset=False)[0]
        cmds.delete(orientGrp_parentConstraint)

        jointParnet = cmds.listRelatives(joint, parent=True)[0]

        orientGrp_parentConstraint = cmds.parentConstraint(jointParnet, orientGrp, maintainOffset=True, n=orientGrp+"_parentConstraint")[0]
        orientGrp_scaleConstraint = cmds.scaleConstraint(jointParnet, orientGrp, maintainOffset=True, n=orientGrp+"_scaleConstraint")[0]
        containedNodes.extend([orientGrp_parentConstraint, orientGrp_scaleConstraint])

        cmds.parent(fkControl, orientGrp, relative=True)

        orientConstraint = cmds.orientConstraint(fkControl, joint, maintainOffset=False, n=joint+"_orientConstraint")[0]
        containedNodes.append(orientConstraint)

        utils.addNodeToContainer(moduleContainer, containedNodes)

        return fkControl


    def UI(self, parentLayout):
        jointsGrp = self.blueprintNamespace+":"+self.moduleNamespace+":joints_grp"

        joints = utils.findJointChain(jointsGrp)
        joints.pop(0)

        numJoints = len(joints)
        if numJoints > 1:
            numJoints -= 1

        for i in range(numJoints):
            fkControl = joints[i] + "_fkControl"
            controlObjectInstance = controlObject.ControlObject(fkControl)
            controlObjectInstance.UI(parentLayout)
