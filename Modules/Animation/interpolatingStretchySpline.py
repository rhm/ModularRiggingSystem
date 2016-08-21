import maya.cmds as cmds

import System.utils as utils
reload(utils)

import System.controlModule as controlModule
#reload(controlModule)
import System.controlObject as controlObject
#reload(controlObject)


CLASS_NAME="InterpolatingStretchySpline"
TITLE="Interpolation-based Stretchy Spline"
DESCRIPTION="This module provides root and end controls for translation and rotation (root control is optional), with " \
            "fine-tuning interpolation controls for specific spline shapes."


class InterpolatingStretchySpline(controlModule.ControlModule):
    def __init__(self, moduleNamespace):
        controlModule.ControlModule.__init__(self, moduleNamespace)


    def compatibleBlueprintModules(self):
        return ["Spline"]


    def install_requirements(self):
        blueprintJointsGrp = self.blueprintNamespace + ":blueprint_joints_grp"
        blueprintJoints = utils.findJointChain(blueprintJointsGrp)

        if len(blueprintJoints) >= 6:
            return True
        else:
            cmds.confirmDialog(title=TITLE, button=["Accept"], defaultButton="Accept",
                               message="This control module can only be installed on spline blueprints with 5 joints or more.")
            return False


    def install_custom(self, joints, moduleGrp, moduleContainer):
        result = cmds.confirmDialog(title=TITLE, message="Please specify the root control type:",
                                    button=["Translation & Rotation", "Rotation", "None"],
                                    defaultButton="Translation & Rotation", cancelButton="None",
                                    dismissString="None")
        rootControlTranslation = (result == "Translation & Rotation")
        createRootControl = result != "None"

        containedNodes = []

        creationPoseJoints = []
        for joint in joints:
            jointName = utils.stripAllNamespaces(joint)[1]
            creationPoseJoint = self.blueprintNamespace+":creationPose_"+jointName
            creationPoseJoints.append(creationPoseJoint)

        # start and end control objects

        rootControlObject = moduleGrp
        if createRootControl:
            (rootControlObject, rootControlParent) = self.createRootEndControl("rootControl", creationPoseJoints[1], creationPoseJoints[1],
                                                                               rootControlTranslation, containedNodes, moduleGrp)
            if not rootControlTranslation:
                containedNodes.append(cmds.pointConstraint(moduleGrp, rootControlParent, maintainOffset=True)[0])

        (endControlObject, _) = self.createRootEndControl("endControl", creationPoseJoints[-2], creationPoseJoints[-1], True, containedNodes, moduleGrp)

        # Spline IK setup

        stretchyIKJoints = list(joints)

        rootJoint = stretchyIKJoints[1]
        endJoint = stretchyIKJoints[-1]

        ikNodes = cmds.ikHandle(sj=rootJoint, ee=endJoint, n=rootJoint+"_splineIKHandle", sol="ikSplineSolver", rootOnCurve=False, createCurve=True)
        ikNodes[1] = cmds.rename(ikNodes[1], rootJoint+"_splineIKEffector")
        ikNodes[2] = cmds.rename(ikNodes[2], rootJoint+"_splineIKCurve")
        containedNodes.extend(ikNodes)

        splineIKHandle = ikNodes[0]
        splineIKCurve = ikNodes[2]

        cmds.parent(splineIKHandle, moduleGrp, absolute=True)
        cmds.setAttr(splineIKHandle+".visibility", 0)
        cmds.setAttr(splineIKCurve+".visibility", 0)

        # avoid double-transformations on the curve
        cmds.parent(splineIKCurve, world=True, absolute=True)
        cmds.setAttr(splineIKCurve+".inheritsTransform", 0)
        cmds.parent(splineIKCurve, moduleGrp, relative=True)


        cmds.select(splineIKCurve+".cv[0:1]", replace=True)
        clusterNodes = cmds.cluster(n=splineIKCurve+"_rootCluster")
        cmds.container(moduleContainer, edit=True, addNode=clusterNodes, ihb=True, includeNetwork=True)
        rootClusterHandle = clusterNodes[1]

        cmds.select(splineIKCurve+".cv[2:3]", replace=True)
        clusterNodes = cmds.cluster(n=splineIKCurve+"_rootCluster")
        cmds.container(moduleContainer, edit=True, addNode=clusterNodes, ihb=True, includeNetwork=True)
        endClusterHandle = clusterNodes[1]

        for handle in [rootClusterHandle, endClusterHandle]:
            cmds.setAttr(handle+".visibility", 0)

        cmds.parent(rootClusterHandle, rootControlObject, absolute=True)
        cmds.parent(endClusterHandle, endControlObject, absolute=True)

        containedNodes.append(cmds.parentConstraint(rootControlObject, rootJoint, maintainOffset=True)[0])


        # finish up
        utils.addNodeToContainer(moduleContainer, containedNodes, ihb=True)



    def createRootEndControl(self, name, orientJoint, posJoint, translation, containedNodes, moduleGrp):
        controlObjectInstance = controlObject.ControlObject()
        (controlObj, controlParent) = controlObjectInstance.create(name, "flattenedCube.ma", self, lod=1, translation=translation,
                                                                   rotation=True, globalScale=False, spaceSwitching=True)

        preTransform = cmds.group(empty=True, n=controlObj+"_preTransform")
        containedNodes.append(preTransform)

        cmds.parent(controlObj, preTransform, relative=True)
        cmds.parent(preTransform, controlParent, relative=True)

        tempOrientLoc = cmds.spaceLocator()[0]
        tempOrientConstraint = cmds.orientConstraint(orientJoint, tempOrientLoc, maintainOffset=False)[0]

        targetOrientation = cmds.xform(tempOrientLoc, q=True, worldSpace=True, rotation=True)
        cmds.delete(tempOrientConstraint)
        cmds.delete(tempOrientLoc)

        cmds.xform(preTransform, worldSpace=True, absolute=True, rotation=targetOrientation)

        cmds.parent(controlParent, moduleGrp, relative=True)
        cmds.setAttr(controlObj+".rotateOrder", cmds.getAttr(orientJoint+".rotateOrder"))

        cmds.xform(controlObj, worldSpace=True, absolute=True,
                   translation=cmds.xform(posJoint, q=True, worldSpace=True, translation=True))

        return (controlObj, controlParent)
