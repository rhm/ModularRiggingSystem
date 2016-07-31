import os
import maya.cmds as cmds
from functools import partial

import System.utils as utils
reload(utils)


class GroupSelected:
    def __init__(self):
        self.objectsToGroup = []

    def show_UI(self):
        self.findSelectionToGroup()

        if not self.objectsToGroup:
            return

        self.UIElements = {}

        if cmds.window("groupSelected_UI_window", exists=True):
            cmds.deleteUI("groupSelected_UI_window")

        windowWidth = 300
        windowHeight = 150

        self.UIElements["window"] = cmds.window("groupSelected_UI_window",
                                                width=windowWidth,
                                                height=windowHeight,
                                                title="Group Selected",
                                                sizeable=True)

        self.UIElements["topLevelColumn"] = cmds.columnLayout(adj=True, columnAlign="center", rs=3)

        self.UIElements["groupName_rowColumn"] = cmds.rowColumnLayout(nc=2, columnAttach=(1,"right",0),
                                                                      columnWidth=[(1,80),(2,windowWidth-80)])
        cmds.text(label="Group Name :")
        self.UIElements["groupName"] = cmds.textField(text="group")

        cmds.setParent(self.UIElements["topLevelColumn"])

        self.UIElements["createAt_rowColumn"] = cmds.rowColumnLayout(nc=3, columnAttach=(1,"right",0),
                                                                     columnWidth=[(1,80),(2,windowWidth-170),(3,80)])
        cmds.text(label="Position at :")
        cmds.text(label="")
        cmds.text(label="")

        cmds.text(label="")
        self.UIElements["createAt_lastSelected"] = cmds.button(label="Last Selected", c=self.createAtLastSelected)
        cmds.text(label="")

        cmds.text(label="")
        self.UIElements["createAt_averagePosition"] = cmds.button(label="Average Position", c=self.createAtAveragePosition)
        cmds.text(label="")

        cmds.setParent(self.UIElements["topLevelColumn"])
        cmds.separator()

        columnWidth = (windowWidth/2) - 5
        self.UIElements["button_row"] = cmds.rowLayout(nc=2, columnWidth=[(1,columnWidth),(2,columnWidth)],
                                                       cat=[(1,"both",10),(2,"both",10)],
                                                       columnAlign=[(1,"center"),(2,"center")])
        cmds.button(label="Accept", c=self.acceptWindow)
        cmds.button(label="Cancel", c=self.cancelWindow)

        cmds.showWindow(self.UIElements["window"])

        self.createTemporaryGroupRepresentation()
        self.createAtLastSelected()

        cmds.select(self.tempGroupTransform)
        cmds.setToolTo("moveSuperContext")

    def findSelectionToGroup(self):
        selectedObjects = cmds.ls(selection=True, transforms=True)

        self.objectsToGroup = []
        for obj in selectedObjects:
            valid = False

            if obj.find("module_transform") != -1:
                splitString = obj.rsplit("module_transform")
                if splitString[1] == "":
                    valid = True

            if not valid and obj.find("Group__") == 0:
                valid = True

            if valid:
                self.objectsToGroup.append(obj)


    def createTemporaryGroupRepresentation(self):
        controlGrpFile = os.environ["RIGGING_TOOL_ROOT"] + "/ControlObjects/Blueprint/controlGroup_control.ma"
        cmds.file(controlGrpFile, i=True)

        self.tempGroupTransform = cmds.rename("controlGroup_control", "Group__tempGroupTransform__")

        cmds.connectAttr(self.tempGroupTransform+".scaleY", self.tempGroupTransform+".scaleX")
        cmds.connectAttr(self.tempGroupTransform+".scaleY", self.tempGroupTransform+".scaleZ")

        for attr in ["scaleX", "scaleZ", "visibility"]:
            cmds.setAttr(self.tempGroupTransform+"."+attr, l=True, k=False)

        cmds.aliasAttr("globalScale", self.tempGroupTransform+".scaleY")


    def createAtLastSelected(self, *args):
        controlPos = cmds.xform(self.objectsToGroup[-1], q=True, worldSpace=True, translation=True)
        cmds.xform(self.tempGroupTransform, worldSpace=True, absolute=True, translation=controlPos)


    def createAtAveragePosition(self, *args):
        controlPos = [0.0, 0.0, 0.0]
        for obj in self.objectsToGroup:
            objPos = cmds.xform(obj, q=True, worldSpace=True, translation=True)
            controlPos[0] += objPos[0]
            controlPos[1] += objPos[1]
            controlPos[2] += objPos[2]

        numObjects = len(self.objectsToGroup)
        controlPos[0] /= numObjects
        controlPos[1] /= numObjects
        controlPos[2] /= numObjects

        cmds.xform(self.tempGroupTransform, worldSpace=True, absolute=True, translation=controlPos)


    def cancelWindow(self, *args):
        cmds.deleteUI(self.UIElements["window"])
        cmds.delete(self.tempGroupTransform)


    def acceptWindow(self, *args):
        groupName = cmds.textField(self.UIElements["groupName"], q=True, text=True)

        if self.createGroup(groupName):
            cmds.deleteUI(self.UIElements["window"])


    def createGroup(self, groupName):
        fullGroupName = "Group__"+groupName
        if cmds.objExists(fullGroupName):
            cmds.confirmDialog(title="Name Conflict", message="Group \""+groupName+"\" already exists",
                               button="Accept", defaultButton="Accept")
            return None

        groupTransform = cmds.rename(self.tempGroupTransform, fullGroupName)

        groupContainer = "Group_container"
        if not cmds.objExists(groupContainer):
            cmds.container(name=groupContainer)

        containers = [groupContainer]

        for obj in self.objectsToGroup:
            if obj.find("Group__") == 0:
                continue

            objNamespace = utils.stripLeadingNamespace(obj)[0]
            containers.append(objNamespace+":module_container")

        for c in containers:
            cmds.lockNode(c, lock=False, lockUnpublished=False)

        if self.objectsToGroup:
            tempGroup = cmds.group(self.objectsToGroup, absolute=True)
            groupParent = cmds.listRelatives(tempGroup, parent=True)

            if groupParent:
                cmds.parent(groupTransform, groupParent[0], absolute=True)

            cmds.parent(self.objectsToGroup, groupTransform, absolute=True)
            cmds.delete(tempGroup)

        self.addGroupToContainer(groupTransform)

        for c in containers:
            cmds.lockNode(c, lock=True, lockUnpublished=True)

        cmds.setToolTo("moveSuperContext")
        cmds.select(groupTransform, replace=True)

        return groupTransform


    def addGroupToContainer(self, group):
        groupContainer = "Group_container"
        utils.addNodeToContainer(groupContainer, group, includeShapes=True)

        groupName = group.partition("Group__")[2]
        cmds.container(groupContainer, edit=True, publishAndBind=[group+".translate", groupName+"_t"])
        cmds.container(groupContainer, edit=True, publishAndBind=[group+".rotate", groupName+"_r"])
        cmds.container(groupContainer, edit=True, publishAndBind=[group+".globalScale", groupName+"_globalScale"])


    def createGroupAtSpecified(self, name, targetGroup, parent):
        self.createTemporaryGroupRepresentation()

        parentConstraint = cmds.parentConstraint(targetGroup, self.tempGroupTransform, maintainOffset=False)[0]
        cmds.delete(parentConstraint)

        scale = cmds.getAttr(targetGroup+".globalScale")
        cmds.setAttr(self.tempGroupTransform+".globalScale", scale)

        if parent:
            cmds.parent(self.tempGroupTransform, parent, absolute=True)

        newGroup = self.createGroup(name)

        return newGroup


class UngroupSelected:
    def __init__(self):
        selectedObjects = cmds.ls(selection=True, transforms=True)

        filteredGroups = []
        for obj in selectedObjects:
            if obj.find("Group__") == 0:
                filteredGroups.append(obj)

        if not filteredGroups:
            return

        groupContainer = "Group_container"
        modules = []
        for group in filteredGroups:
            modules.extend(self.findChildModules(group))

        moduleContainers = [groupContainer]
        for module in modules:
            moduleContainer = module + ":module_container"
            moduleContainers.append(moduleContainer)

        for container in moduleContainers:
            cmds.lockNode(container, lock=False, lockUnpublished=False)

        for group in filteredGroups:
            numChildren = len(cmds.listRelatives(group, children=True))
            if numChildren > 1:
                cmds.ungroup(group, absolute=True)

            for attr in ["t", "r", "globalScale"]:
                cmds.container(groupContainer, edit=True, unbindAndUnpublish=group+"."+attr)

            parentGroup = cmds.listRelatives(group, parent=True)

            cmds.delete(group)

            if parentGroup:
                parentGroup = parentGroup[0]
                children = cmds.listRelatives(parentGroup, children=True)
                children = cmds.ls(children, transforms=True)

                if len(children) == 0:
                    cmds.select(parentGroup, replace=True)
                    UngroupSelected()

        for container in moduleContainers:
            if cmds.objExists(container):
                cmds.lockNode(container, lock=True, lockUnpublished=True)


    def findChildModules(self, group):
        modules = []
        children = cmds.listRelatives(group, children=True)

        if children:
            for child in children:
                moduleNamespaceInfo = utils.stripLeadingNamespace(child)
                if moduleNamespaceInfo:
                    modules.append(moduleNamespaceInfo[0])
                elif child.find("Group__") != -1:
                    modules.extend(self.findChildModules(child))

        return modules
