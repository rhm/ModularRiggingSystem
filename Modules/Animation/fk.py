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
        containedNodes = []

        (fkControl, _, translationControl) = self.initFKControl(joint, spaceSwitchable=False)

        orientGrp = cmds.group(n=fkControl+"_orientGrp", empty=True, parent=parent)
        containedNodes.append(orientGrp)

        orientGrp_parentConstraint = cmds.parentConstraint(joint, orientGrp, maintainOffset=False)[0]
        cmds.delete(orientGrp_parentConstraint)

        jointParnet = cmds.listRelatives(joint, parent=True)[0]

        orientGrp_parentConstraint = cmds.parentConstraint(jointParnet, orientGrp, maintainOffset=True,
                                                           skipTranslate=["x","y","z"], n=orientGrp+"_parentConstraint")[0]
        pointConstraint_parent = joint
        if translationControl:
            pointConstraint_parent = jointParnet

        orientGrp_pointConstraint = cmds.pointConstraint(pointConstraint_parent, orientGrp, maintainOffset=False,
                                                         n=orientGrp+"_pointConstraint")[0]

        orientGrp_scaleConstraint = cmds.scaleConstraint(jointParnet, orientGrp, maintainOffset=True, n=orientGrp+"_scaleConstraint")[0]
        containedNodes.extend([orientGrp_parentConstraint, orientGrp_pointConstraint, orientGrp_scaleConstraint])

        cmds.parent(fkControl, orientGrp, relative=True)

        # RHM NOTE - This orient constraint causes Maya 2014 to crash when duplicating the animation module container
        orientConstraint = cmds.orientConstraint(fkControl, joint, maintainOffset=False, n=joint+"_orientConstraint")[0]
        containedNodes.append(orientConstraint)

        if translationControl:
            cmds.xform(fkControl, worldSpace=True, absolute=True, translation=cmds.xform(joint, q=True, translation=True))
            pointConstraint = cmds.pointConstraint(fkControl, joint, maintainOffset=False, n=joint+"_pointConstraint")[0]
            containedNodes.append(pointConstraint)

        utils.addNodeToContainer(moduleContainer, containedNodes)

        return fkControl


    def initFKControl(self, joint, spaceSwitchable=False):
        translationControl = False
        jointName = utils.stripAllNamespaces(joint)[1]

        blueprintJoint = self.blueprintNamespace + ":blueprint_"+jointName
        if cmds.objExists(blueprintJoint+"_addTranslate"):
            translationControl = True

        name = jointName + "_fkControl"

        controlObjectInstance = controlObject.ControlObject()

        (fkControl, fkParent) = controlObjectInstance.create(name, "sphere.ma", self, lod=1, translation=translationControl, rotation=True,
                                                      globalScale=False, spaceSwitching=spaceSwitchable)
        cmds.connectAttr(joint+".rotateOrder", fkControl+".rotateOrder")

        return (fkControl, fkParent, translationControl)


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


    def match(self, *args):
        jointsGrp = self.blueprintNamespace + ":blueprint_joints_grp"
        joints = utils.findJointChain(jointsGrp)
        joints.pop(0)

        moduleJointsGrp = self.blueprintNamespace + ":" + self.moduleNamespace + ":joints_grp"
        moduleJoints = utils.findJointChain(moduleJointsGrp)
        moduleJoints.pop(0)

        if len(moduleJoints) > 1:
            moduleJoints.pop()

        index = 0
        fkControls = []
        for joint in moduleJoints:
            fkControl = joint + "_fkControl"
            fkControls.append(fkControl)

            if not cmds.getAttr(fkControl+".translateX", l=True):
                cmds.xform(fkControl, worldSpace=True, absolute=True, translation=cmds.xform(joints[index], q=True, worldSpace=True, translation=True))

            cmds.xform(fkControl, worldSpace=True, absolute=True, rotation=cmds.xform(joints[index], q=True, worldSpace=True, rotation=True))
            index += 1

        return (joints, fkControls)
