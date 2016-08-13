import os

import maya.cmds as cmds
import System.utils as utils
reload(utils)

from functools import partial


class ControlObject:
    def __init__(self, controlObject=None):
        if controlObject:
            self.controlObject = controlObject

            self.translation = []
            self.translation.append(not cmds.getAttr(self.controlObject+".translateX", l=True))
            self.translation.append(not cmds.getAttr(self.controlObject+".translateY", l=True))
            self.translation.append(not cmds.getAttr(self.controlObject+".translateZ", l=True))

            self.rotation = []
            self.rotation.append(not cmds.getAttr(self.controlObject+".rotateX", l=True))
            self.rotation.append(not cmds.getAttr(self.controlObject+".rotateY", l=True))
            self.rotation.append(not cmds.getAttr(self.controlObject+".rotateZ", l=True))

            self.globalScale = not cmds.getAttr(self.controlObject+".scaleY", l=True)


    def create(self, name, controlFile, animationModuleInstance, lod=1, translation=True, rotation=True, globalScale=True, spaceSwitching=False):
        if translation == True or translation == False:
            translation = [translation, translation, translation]

        if rotation == True or rotation == False:
            rotation = [rotation, rotation, rotation]

        self.translation = translation
        self.rotation = rotation
        self.globalScale = globalScale

        animationModuleName = animationModuleInstance.moduleNamespace
        blueprintModuleNamespace = animationModuleInstance.blueprintNamespace
        blueprintModuleUserSpecifiedName = utils.stripAllNamespaces(blueprintModuleNamespace)[1].partition("__")[2]

        animationModuleNamespace = blueprintModuleNamespace+":"+animationModuleName

        controlObjectFile = os.environ["RIGGING_TOOL_ROOT"] + "/ControlObjects/Animation/" + controlFile
        cmds.file(controlObjectFile, i=True)

        self.controlObject = cmds.rename("control", animationModuleNamespace+":"+name)
        self.rootParent = self.controlObject

        self.setupIconScale(animationModuleNamespace)

        cmds.setAttr(self.controlObject+".overrideEnabled", 1)
        cmds.setAttr(self.controlObject+".overrideShading", 0)
        cmds.connectAttr(animationModuleNamespace+":module_grp.overrideColor", self.controlObject+".overrideColor")

        cmds.container(animationModuleNamespace+":module_container", edit=True, addNode=self.controlObject, ihb=True, includeNetwork=True)

        if globalScale:
            cmds.connectAttr(self.controlObject+".scaleY", self.controlObject+".scaleX")
            cmds.connectAttr(self.controlObject+".scaleY", self.controlObject+".scaleZ")
            cmds.aliasAttr("globalScale", self.controlObject+".scaleY")


        attributes = []
        if self.translation == [True, True, True]:
            attributes.append([True, ".translate", "T"])
        else:
            attributes.extend([ [translation[0], ".translateX", "TX"],
                                [translation[1], ".translateY", "TY"],
                                [translation[2], ".translateZ", "TZ"] ])

        if self.rotation == [True, True, True]:
            attributes.append([True, ".rotate", "R"])
        else:
            attributes.extend([ [rotation[0], ".rotateX", "RX"],
                                [rotation[1], ".rotateY", "RY"],
                                [rotation[2], ".rotateZ", "RZ"] ])

        attributes.append( [globalScale, ".globalScale", "scale"] )

        for attrInfo in attributes:
            if attrInfo[0]:
                attributeNiceName = name + "_" + attrInfo[2]
                animationModuleInstance.publishNameToModuleContainer(self.controlObject+attrInfo[1], attributeNiceName, publishToOuterContainers=True)


        cmds.select(self.controlObject, replace=True)
        cmds.addAttr(at="bool", defaultValue=1, k=True, ln="display")
        animationModuleInstance.publishNameToModuleContainer(self.controlObject+".display", "display", publishToOuterContainers=False)


        moduleGrp = animationModuleNamespace+":module_grp"
        visibilityExpressionTxt = self.controlObject+".visibility = " + self.controlObject+".display * (" + moduleGrp+".lod >= "+str(lod) + ");"
        expression = cmds.expression(n=self.controlObject+"_visibility_expression", string=visibilityExpressionTxt)
        utils.addNodeToContainer(animationModuleNamespace+":module_container", expression)

        return (self.controlObject, self.rootParent)


    def setupIconScale(self, animationModuleNamespace):
        clusterNodes = cmds.cluster(self.controlObject, n=self.controlObject+"_icon_scale_cluster", relative=True)
        cmds.container(animationModuleNamespace+":module_container", edit=True, addNode=clusterNodes, ihb=True, includeNetwork=True)

        clusterHandle = clusterNodes[1]

        cmds.setAttr(clusterHandle+".scalePivotX", 0)
        cmds.setAttr(clusterHandle+".scalePivotY", 0)
        cmds.setAttr(clusterHandle+".scalePivotZ", 0)

        cmds.connectAttr(animationModuleNamespace+":module_grp.iconScale", clusterHandle+".scaleX")
        cmds.connectAttr(animationModuleNamespace+":module_grp.iconScale", clusterHandle+".scaleY")
        cmds.connectAttr(animationModuleNamespace+":module_grp.iconScale", clusterHandle+".scaleZ")

        cmds.parent(clusterHandle, self.controlObject, absolute=True)
        cmds.setAttr(clusterHandle+".visibility", 0)