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

        stretchyIKJoints = cmds.duplicate(joints, renameChildren=True)
        index = 0
        for joint in stretchyIKJoints:
            stretchyIKJoints[index] = cmds.rename(joint, joints[index]+"_stretchyIKJoint")
            index += 1

        containedNodes.extend(stretchyIKJoints)


        rootJoint = stretchyIKJoints[1]
        endJoint = stretchyIKJoints[-1]
        secondJoint = stretchyIKJoints[2]
        secondToLastJoint = stretchyIKJoints[-2]

        # store an original length for each joint

        rootPos = cmds.xform(rootJoint, q=True, worldSpace=True, translation=True)
        endPos = cmds.xform(endJoint, q=True, worldSpace=True, translation=True)

        rootLocator = cmds.spaceLocator(n=stretchyIKJoints[0]+"_systemStretch_rootLocator")[0]
        cmds.xform(rootLocator, worldSpace=True, absolute=True, translation=rootPos)
        containedNodes.append(rootLocator)

        endLocator = cmds.spaceLocator(n=stretchyIKJoints[0]+"_systemStretch_endLocator")[0]
        cmds.xform(endLocator, worldSpace=True, absolute=True, translation=endPos)
        containedNodes.append(endLocator)

        for loc in [rootLocator, endLocator]:
            cmds.setAttr(loc+".visibility", 0)

        cmds.parent(rootLocator, rootControlObject, absolute=True)
        cmds.parent(endLocator, endControlObject, absolute=True)

        index = 0
        for joint in stretchyIKJoints:
            if index > 2 and index < len(stretchyIKJoints)-1:
                cmds.select(stretchyIKJoints[index], replace=True)
                cmds.addAttr(at="float", longName="originalLength")
                originalLength = cmds.getAttr(stretchyIKJoints[index]+".translateX")
                cmds.setAttr(stretchyIKJoints[index]+".originalLength", originalLength)
            index += 1

        scaleFactorAttr = self.createDistanceCalculations(rootLocator, endLocator, containedNodes)

        # cluster scaling

        rootScaler = self.createScaler(rootLocator, scaleFactorAttr, containedNodes)
        endScaler = self.createScaler(endLocator, scaleFactorAttr, containedNodes)

        # setup basic stretchy IK on the outer two joints

        (rootIK_rootLocator, rootIK_endLocator) = self.setupBasicStretchyIK(rootJoint, secondJoint, creationPoseJoints[1],
                                                                            rootControlObject, moduleContainer, moduleGrp)
        cmds.parent(rootIK_endLocator, rootScaler, absolute=True)

        (endIK_rootLocator, endIK_endLocator) = self.setupBasicStretchyIK(secondToLastJoint, endJoint, creationPoseJoints[-2],
                                                                          endControlObject, moduleContainer, moduleGrp)
        cmds.parent(endIK_endLocator, endControlObject, absolute=True)

        # implement the spline IK for the joint chain

        ikNodes = cmds.ikHandle(sj=secondJoint, ee=secondToLastJoint, n=secondJoint+"_splineIKHandle", sol="ikSplineSolver", rootOnCurve=False, createCurve=True)
        ikNodes[1] = cmds.rename(ikNodes[1], secondJoint+"_splineIKEffector")
        ikNodes[2] = cmds.rename(ikNodes[2], secondJoint+"_splineIKCurve")
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

        cmds.parent(rootClusterHandle, rootScaler, absolute=True)
        cmds.parent(endClusterHandle, endScaler, absolute=True)

        containedNodes.append(cmds.parentConstraint(rootControlObject, rootJoint, maintainOffset=True)[0])

        # Make each joint (excluding first and last) scale proportionately

        targetLocatorNodes = cmds.duplicate(endIK_rootLocator, name=endIK_rootLocator+"_duplicateTarget")
        targetLocator = targetLocatorNodes[0]
        cmds.delete(targetLocatorNodes[1])
        cmds.parent(targetLocator, endScaler, absolute=True)

        splineScaleFactorAttr = self.createDistanceCalculations(rootIK_endLocator, targetLocator, containedNodes)

        index = 0
        for joint in stretchyIKJoints:
            if index > 2 and index < len(stretchyIKJoints)-1:
                multNode = cmds.shadingNode("multiplyDivide", asUtility=True, n=joint+"_jointScale")
                containedNodes.append(multNode)
                cmds.connectAttr(splineScaleFactorAttr, multNode+".input1X")
                cmds.setAttr(multNode+".input2X", cmds.getAttr(joint+".originalLength"))
                cmds.connectAttr(multNode+".outputX", joint+".translateX")
            index += 1

        # twist correction for the central section

        cmds.setAttr(splineIKHandle+".dTwistControlEnable", 1)
        cmds.setAttr(splineIKHandle+".dWorldUpType", 4)
        cmds.setAttr(splineIKHandle+".dWorldUpAxis", 5) # Z axis

        cmds.setAttr(splineIKHandle+".dWorldUpVector", 0.0, 0.0, 1.0, type="double3")
        cmds.setAttr(splineIKHandle+".dWorldUpVectorEnd", 0.0, 0.0, 1.0, type="double3")

        if createRootControl:
            cmds.connectAttr(rootControlObject+".worldMatrix[0]", splineIKHandle+".dWorldUpMatrix")
        else:
            dummyNode = cmds.duplicate(rootJoint, parentOnly=True, n=rootJoint+"_dummyDuplicate")[0]
            containedNodes.append(dummyNode)
            cmds.parent(dummyNode, moduleGrp, absolute=True)
            cmds.connectAttr(dummyNode+".worldMatrix[0]", splineIKHandle+".dWorldUpMatrix")

        cmds.connectAttr(endControlObject+".worldMatrix[0]", splineIKHandle+".dWorldUpMatrixEnd")

        # set up spline interpolators

        cmds.select(moduleGrp)
        cmds.addAttr(at="float", defaultValue=0.0, softMinValue=-10.0, softMaxValue=10.0, keyable=True, longName="offsetY")
        cmds.addAttr(at="float", defaultValue=0.0, softMinValue=-10.0, softMaxValue=10.0, keyable=True, longName="offsetZ")

        self.publishNameToModuleContainer(moduleGrp+".offsetY", "interpolator_offsetY", publishToOuterContainers=True)
        self.publishNameToModuleContainer(moduleGrp+".offsetZ", "interpolator_offsetZ", publishToOuterContainers=True)

        inverseNode = cmds.shadingNode("multiplyDivide", asUtility=True, n=moduleGrp+"_offsetInverse")
        containedNodes.append(inverseNode)

        cmds.connectAttr(moduleGrp+".offsetY", inverseNode+".input1Y")
        cmds.connectAttr(moduleGrp+".offsetZ", inverseNode+".input1Z")
        cmds.setAttr(inverseNode+".input2Y", -1)
        cmds.setAttr(inverseNode+".input2Z", -1)

        numStretchyIKJoints = len(stretchyIKJoints) - 1

        interpolators_ikParents = []
        aimChildren = []

        for i in range(1, numStretchyIKJoints):
            if i > 1:
                jointFollower = cmds.group(empty=True, n=stretchyIKJoints[i]+"_follower")
                containedNodes.append(jointFollower)
                cmds.parent(jointFollower, moduleGrp, relative=True)
                containedNodes.append(cmds.parentConstraint(stretchyIKJoints[i], jointFollower, maintainOffset=False, n=jointFollower+"_parentConstraint")[0])

                offset = cmds.group(empty=True, n=stretchyIKJoints[i]+"_interpolatorOffset")
                containedNodes.append(offset)
                cmds.parent(offset, jointFollower, relative=True)

                cmds.connectAttr(moduleGrp+".offsetY", offset+".translateY")
                cmds.connectAttr(moduleGrp+".offsetZ", offset+".translateZ")

                name = utils.stripAllNamespaces(joints[i])[1] + "_offsetControl"
                controlObjectInstance = controlObject.ControlObject()
                offsetControlObject = controlObjectInstance.create(name, "cubeLocator.ma", self, lod=2, translation=True, rotation=False, globalScale=False, spaceSwitching=False)[0]
                cmds.parent(offsetControlObject, offset, relative=True)

                offsetCancellation = cmds.group(empty=True, n=stretchyIKJoints[i]+"_interpolatorOffsetCancellation")
                containedNodes.append(offsetCancellation)
                cmds.parent(offsetCancellation, offsetControlObject, relative=True)

                cmds.connectAttr(inverseNode+".outputY", offsetCancellation+".translateY")
                cmds.connectAttr(inverseNode+".outputZ", offsetCancellation+".translateZ")

                interpolators_ikParents.append(offsetCancellation)

            aimChild = cmds.group(empty=True, n=stretchyIKJoints[i]+"_aimChild")
            containedNodes.append(aimChild)
            aimChildren.append(aimChild)

            if i > 1:
                cmds.parent(aimChild, offsetCancellation, relative=True)
            else:
                cmds.parent(aimChild, stretchyIKJoints[i], relative=True)

            cmds.setAttr(aimChild+".translateY", -1)


        for i in range(1, numStretchyIKJoints):
            ikNodes = utils.basic_stretchy_IK(joints[i], joints[i+1], container=moduleContainer,
                                              scaleCorrectionAttribute=self.blueprintNamespace+":module_grp.hierarchicalScale",
                                              lockMinimumLength=False, poleVectorObject=aimChildren[i-1])
            ikHandle = ikNodes["ikHandle"]
            rootLocator = ikNodes["rootLocator"]
            endLocator = ikNodes["endLocator"]

            for loc in [ikHandle, rootLocator]:
                cmds.parent(loc, moduleGrp, absolute=True)

            utils.matchTwistAngle(ikHandle+".twist", [joints[i]], [stretchyIKJoints[i]])

            if i == 1 and createRootControl:
                containedNodes.append(cmds.pointConstraint(rootControlObject, joints[i], maintainOffset=False,
                                                           n=joints[i]+"_pointConstraint")[0])

            cmds.setAttr(endLocator+".translate", 0.0, 0.0, 0.0, type="double3")
            if i < numStretchyIKJoints - 1:
                cmds.parent(endLocator, interpolators_ikParents[i-1], relative=True)
            else:
                cmds.parent(endLocator, endControlObject, relative=True)


        # finish up

        cmds.setAttr(moduleGrp+".lod", 2)

        utils.addNodeToContainer(moduleContainer, containedNodes, ihb=True)

        for joint in stretchyIKJoints:
            jointName = utils.stripAllNamespaces(joint)[1]
            self.publishNameToModuleContainer(joint+".rotate", jointName+"_R", publishToOuterContainers=False)
            self.publishNameToModuleContainer(joint+".translate", jointName+"_T", publishToOuterContainers=False)


    def setupBasicStretchyIK(self, sJoint, eJoint, creationPose_sJoint, controlObject, moduleContainer, moduleGrp):
        scaleCorrAttr = self.blueprintNamespace+":module_grp.hierarchicalScale"
        ikNodes = utils.basic_stretchy_IK(sJoint, eJoint, container=moduleContainer,
                                          scaleCorrectionAttribute=scaleCorrAttr, lockMinimumLength=False)
        ikHandle = ikNodes["ikHandle"]
        rootLocator = ikNodes["rootLocator"]
        endLocator = ikNodes["endLocator"]
        poleVectorLocator = ikNodes["poleVectorObject"]

        for loc in [rootLocator, ikHandle]:
            cmds.parent(loc, moduleGrp, absolute=True)

        cmds.parent(poleVectorLocator, creationPose_sJoint)
        cmds.setAttr(poleVectorLocator+".translateX", 0.0)
        cmds.setAttr(poleVectorLocator+".translateY", 10.0)
        cmds.setAttr(poleVectorLocator+".translateZ", 0.0)

        utils.matchTwistAngle(ikHandle+".twist", [sJoint], [creationPose_sJoint])

        cmds.parent(poleVectorLocator, controlObject, absolute=True)

        return (rootLocator, endLocator)


    def createScaler(self, parentLocator, scaleFactorAttr, containedNodes):
        scaler = cmds.group(empty=True, n=parentLocator+"_scaler")
        containedNodes.append(scaler)
        cmds.parent(scaler, parentLocator, relative=True)

        for attr in [".scaleX",".scaleY",".scaleZ"]:
            cmds.connectAttr(scaleFactorAttr, scaler+attr)

        return scaler


    def createDistanceCalculations(self, rootLocator, endLocator, containedNodes):
        rootLocatorName = utils.stripAllNamespaces(rootLocator)[1]
        endLocatorName = utils.stripAllNamespaces(endLocator)[1]
        distNode = cmds.shadingNode("distanceBetween", asUtility=True,
            n=self.blueprintNamespace+":"+self.moduleNamespace+":distanceBetween_"+rootLocatorName+"__"+endLocatorName)
        containedNodes.append(distNode)

        rootLocShape = rootLocator+"Shape"
        endLocShape = endLocator+"Shape"

        cmds.connectAttr(rootLocShape+".worldPosition[0]", distNode+".point1")
        cmds.connectAttr(endLocShape+".worldPosition[0]", distNode+".point2")

        totalOriginalLength = cmds.getAttr(distNode+".distance")
        totalOriginalLength /= cmds.getAttr(self.blueprintNamespace+":module_grp.hierarchicalScale")

        scaleFactor = cmds.shadingNode("multiplyDivide", asUtility=True, n=distNode+"_scaleFactor")
        containedNodes.append(scaleFactor)

        cmds.setAttr(scaleFactor+".operation", 2) #divide
        cmds.connectAttr(distNode+".distance", scaleFactor+".input1X")
        cmds.setAttr(scaleFactor+".input2X", totalOriginalLength)

        scaleCorrection = cmds.shadingNode("multiplyDivide", asUtility=True, n=scaleFactor+"_correction")
        containedNodes.append(scaleCorrection)

        cmds.setAttr(scaleCorrection+".operation", 2) # divide
        cmds.connectAttr(scaleFactor+".outputX", scaleCorrection+".input1X")
        cmds.connectAttr(self.blueprintNamespace+":module_grp.hierarchicalScale", scaleCorrection+".input2X")

        return scaleCorrection+".outputX"


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
