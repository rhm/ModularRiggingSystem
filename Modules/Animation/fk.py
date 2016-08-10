import maya.cmds as cmds

import System.utils as utils
reload(utils)


CLASS_NAME="FK"
TITLE="Forward Kinematics"
DESCRIPTION="This module provides FK rotational controls for every joint in the blueprint it is installed on"


class FK:
    def __init__(self, moduleNamespace):
        self.moduleContainer = None

        if not moduleNamespace:
            return

        moduleNamespaceInfo = utils.stripAllNamespaces(moduleNamespace)

        self.blueprintNamespace = moduleNamespaceInfo[0]
        self.moduleNamespace = moduleNamespaceInfo[1]
        self.characterNamespaceOnly = utils.stripLeadingNamespace(self.blueprintNamespace)[0]

        self.moduleContainer = self.blueprintNamespace+":"+self.moduleNamespace+":module_container"

        self.publishedNames = []


    def compatibleBlueprintModules(self):
        return ["Finger", "HingeJoint", "LegFoot", "SingleJointSegment", "SingleOrientableJoint", "Spline", "Thumb"]


    def install(self):
        self.install_init()


    def install_init(self):
        cmds.namespace(setNamespace=self.blueprintNamespace)
        cmds.namespace(add=self.moduleNamespace)
        cmds.namespace(setNamespace=":")

        characterContainer = self.characterNamespaceOnly+":character_container"
        blueprintContainer = self.blueprintNamespace+":module_container"

        containers = [characterContainer, blueprintContainer]
        for c in containers:
            cmds.lockNode(c, lock=False, lockUnpublished=False)

        self.joints = self.duplicateAndRenameCreationPose()
        moduleJointsGrp = self.joints[0]

        moduleGrp = cmds.group(empty=True, name=self.blueprintNamespace+":"+self.moduleNamespace+":module_grp")
        hookIn = self.blueprintNamespace+":HOOK_IN"
        cmds.parent(moduleGrp, hookIn, relative=True)
        cmds.parent(moduleJointsGrp, moduleGrp, absolute=True)

        cmds.select(moduleGrp)
        cmds.addAttr(at="float", ln="iconScale", min=0.001, softMaxValue=10.0, defaultValue=1.0, k=True)
        cmds.setAttr(moduleGrp+".overrideEnabled", 1)
        cmds.setAttr(moduleGrp+".overrideColor", 6)

        utilityNodes = self.setupBlueprintWeightBasedBlending()



    def duplicateAndRenameCreationPose(self):
        joints = cmds.duplicate(self.blueprintNamespace+":creationPose_joints_grp", renameChildren=True)

        for i in range(len(joints)):
            nameSuffix = joints[i].rpartition("creationPose_")[2]
            joints[i] = cmds.rename(joints[i], self.blueprintNamespace+":"+self.moduleNamespace+":"+nameSuffix)

        return joints


    def setupBlueprintWeightBasedBlending(self):
        settingsLocator = self.blueprintNamespace+":SETTINGS"

        attributes = cmds.listAttr(settingsLocator, keyable=False)
        weightAttributes = []
        for attr in attributes:
            if attr.find("_weight") != -1:
                weightAttributes.append(attr)

        value = 0
        if len(weightAttributes)==0:
            value = 1
            cmds.setAttr(settingsLocator+".creationPoseWeight", 0)

        cmds.select(settingsLocator)
        weightAttributeName = self.moduleNamespace+"_weight"
        cmds.addAttr(ln=weightAttributeName, at="double", min=0.0, max=1.0, defaultValue=value, keyable=False)

        cmds.container(self.blueprintNamespace+":module_container", edit=True,
                       publishAndBind=[settingsLocator+"."+weightAttributeName, weightAttributeName])

        currentEntries = cmds.attributeQuery("activeModule", n=settingsLocator, listEnum=True)
        newEntry = self.moduleNamespace
        if currentEntries[0] == "None":
            cmds.addAttr(settingsLocator+".activeModule", edit=True, enumName=newEntry)
            cmds.setAttr(settingsLocator+".activeModule", 0)
        else:
            cmds.addAttr(settingsLocator+".activeModule", edit=True, enumName=currentEntries[0]+":"+newEntry)

        utilityNodes = []
        for i in range(1, len(self.joints)):
            joint = self.joints[i]

            nameSuffix = utils.stripAllNamespaces(joint)[1]
            blueprintJoint = self.blueprintNamespace+":blueprint_"+nameSuffix
            weightNodeAttr = settingsLocator+"."+weightAttributeName

            if i < len(self.joints)-1 or len(self.joints)==2:
                multiplyRotations = cmds.shadingNode("multiplyDivide", n=joint+"_multiplyRotationsWeight", asUtility=True)
                utilityNodes.append(multiplyRotations)
                cmds.connectAttr(joint+".rotate", multiplyRotations+".input1", force=True)

                for attr in [".input2X", ".input2Y", ".input2Z"]:
                    cmds.connectAttr(weightNodeAttr, multiplyRotations+attr, force=True)

                #index = utils.findFirstFreeConnection(blueprintJoint+"_addRotations.input3D")
                index = 1
                cmds.connectAttr(multiplyRotations+".output", blueprintJoint+"_addRotations.input3D["+str(index)+"]", force=True)

            if i == 1:
                print "Check root transform"
            else:
                multiplyTranslation = cmds.shadingNode("multiplyDivide", n=joint+"_multiplyTranslationWeight", asUtility=True)
                utilityNodes.append(multiplyTranslation)

                cmds.connectAttr(joint+".translateX", multiplyTranslation+".input1X", force=True)
                cmds.connectAttr(weightNodeAttr, multiplyTranslation+".input2X", force=True)

                addNode = blueprintJoint+"_addTx"
                #index = utils.findFirstFreeConnection(addNode+".input1D")
                index = 1
                cmds.connectAttr(multiplyTranslation+".outputX", addNode+".input1D["+str(index)+"]", force=True)

        return utilityNodes
