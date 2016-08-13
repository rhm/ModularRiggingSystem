import os
import maya.cmds as cmds

from functools import partial

import System.utils as utils
reload(utils)

import System.controlObject as controlObject
reload(controlObject)


class Animation_UI:
    def __init__(self):
        self.previousBlueprintListEntry = None
        self.previousBlueprintModule = None
        self.previousAnimationModule = None

        baseIconsDir = os.environ["RIGGING_TOOL_ROOT"] + "/Icons/"

        self.selectedCharacter = self.findSelectedCharacter()
        if not self.selectedCharacter:
            return


        self.characterName = self.selectedCharacter.partition("__")[2]
        self.windowName = self.characterName + "_window"

        self.UIElements = {}

        if cmds.window(self.windowName, exists=True):
            cmds.deleteUI(self.windowName)

        self.windowWidth = 420
        self.windowHeight = 730

        self.UIElements["window"] = cmds.window(self.windowName, width=self.windowWidth, height=self.windowHeight,
                                                title="Animation UI: "+self.characterName, sizeable=True)

        self.UIElements["topColumnLayout"] = cmds.columnLayout(adj=True, rs=3)

        buttonWidth = 32
        columnOffset = 5
        buttonColumnWidth = buttonWidth + (2 * columnOffset)
        textScrollWidth = (self.windowWidth - buttonColumnWidth - 8) /2

        self.UIElements["listBoxRowLayout"] = cmds.rowLayout(nc=3, columnWidth3=[textScrollWidth, textScrollWidth, buttonColumnWidth],
                                                             columnAttach=([1,"both",columnOffset],[2,"both",columnOffset],[3,"both",columnOffset]))

        self.UIElements["blueprintModule_textScroll"] = cmds.textScrollList(numberOfRows=12, allowMultiSelection=False,
                                                                            selectCommand=self.refreshAnimationModuleList)
        self.initialiseBlueprintModuleList()

        self.UIElements["animationModule_textScroll"] = cmds.textScrollList(numberOfRows=12, allowMultiSelection=False)

        self.UIElements["buttonColumnLayout"] = cmds.columnLayout()
        self.UIElements["pinButton"] = cmds.symbolCheckBox(onImage=baseIconsDir+"_pinned.xpm", offImage=baseIconsDir+"_unpinned.xpm",
                                                           width=buttonWidth, height=buttonWidth,
                                                           onCommand=self.deleteScriptJob, offCommand=self.setupScriptJob)

        if cmds.objExists(self.selectedCharacter+":non_blueprint_grp"):
            value = cmds.getAttr(self.selectedCharacter+":non_blueprint_grp.display")
            self.UIElements["nonBlueprintVisibility"] = cmds.symbolCheckBox(image=baseIconsDir+"_shelf_character.xpm", value=value,
                                                                            width=buttonWidth, height=buttonWidth,
                                                                            onCommand=self.toggleNonBlueprintVisibility,
                                                                            offCommand=self.toggleNonBlueprintVisibility)

        value = cmds.getAttr(self.selectedCharacter+":character_grp.animationControlVisibility")
        self.UIElements["animControlVisibility"] = cmds.symbolCheckBox(image=baseIconsDir + "_visibility.xpm", value=value,
                                                                       width=buttonWidth, height=buttonWidth,
                                                                       onCommand=self.toggleAnimControlVisibility,
                                                                       offCommand=self.toggleAnimControlVisibility)

        self.UIElements["deleteModuleButton"] = cmds.symbolButton(image=baseIconsDir+"_shelf_delete.xpm",
                                                                  width=buttonWidth, height=buttonWidth,
                                                                  enable=False)

        self.UIElements["duplicateModuleButton"] = cmds.symbolButton(image=baseIconsDir+"_duplicate.xpm",
                                                                     width=buttonWidth, height=buttonWidth,
                                                                     enable=False)

        cmds.setParent(self.UIElements["topColumnLayout"])
        cmds.separator()

        self.refreshAnimationModuleList()

        self.setupScriptJob()

        cmds.showWindow(self.UIElements["window"])

        self.selectionChanged()


    def initialiseBlueprintModuleList(self):
        cmds.namespace(setNamespace=self.selectedCharacter)
        blueprintNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        self.blueprintModules = {}

        if blueprintNamespaces:
            for namespace in blueprintNamespaces:
                blueprintModule = utils.stripLeadingNamespace(namespace)[1]
                userSpecifiedName = blueprintModule.partition("__")[2]
                cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], edit=True, append=userSpecifiedName)
                self.blueprintModules[userSpecifiedName] = namespace

        cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], edit=True, selectIndexedItem=1)
        selectedBlueprintModule = cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], q=True, selectItem=True)
        self.selectedBlueprintModule = self.blueprintModules[selectedBlueprintModule[0]]


    def refreshAnimationModuleList(self, index=1):
        cmds.textScrollList(self.UIElements["animationModule_textScroll"], edit=True, removeAll=True)

        cmds.symbolButton(self.UIElements["deleteModuleButton"], edit=True, enable=False)
        cmds.symbolButton(self.UIElements["duplicateModuleButton"], edit=True, enable=False)

        selectedBlueprintModule = cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], q=True, selectItem=True)
        self.selectedBlueprintModule = self.blueprintModules[selectedBlueprintModule[0]]

        cmds.namespace(setNamespace=self.selectedBlueprintModule)
        controlModuleNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        cmds.namespace(setNamespace=":")

        if controlModuleNamespaces:
            for module in controlModuleNamespaces:
                moduleName = utils.stripAllNamespaces(module)[1]
                cmds.textScrollList(self.UIElements["animationModule_textScroll"], edit=True, append=moduleName)

            cmds.textScrollList(self.UIElements["animationModule_textScroll"], edit=True, selectIndexedItem=index)

            cmds.symbolButton(self.UIElements["deleteModuleButton"], edit=True, enable=True)
            cmds.symbolButton(self.UIElements["duplicateModuleButton"], edit=True, enable=True)

        self.previousBlueprintListEntry = selectedBlueprintModule


    def findSelectedCharacter(self):
        selection = cmds.ls(selection=True, transforms=True)
        character = None

        if selection:
            selected = selection[0]
            selectedNamespaceInfo = utils.stripLeadingNamespace(selected)
            if selectedNamespaceInfo:
                selectedNamespace = selectedNamespaceInfo[0]
                if selectedNamespace.find("Character__") == 0:
                    character = selectedNamespace

        return character


    def toggleNonBlueprintVisibility(self, *args):
        visibility = not cmds.getAttr(self.selectedCharacter+":non_blueprint_grp.display")
        cmds.setAttr(self.selectedCharacter+":non_blueprint_grp.display", visibility)


    def toggleAnimControlVisibility(self, *args):
        visibility = not cmds.getAttr(self.selectedCharacter+":character_grp.animationControlVisibility")
        cmds.setAttr(self.selectedCharacter+":character_grp.animationControlVisibility", visibility)


    def setupScriptJob(self, *args):
        self.scriptJobNum = cmds.scriptJob(parent=self.UIElements["window"], event=["SelectionChanged", self.selectionChanged])


    def deleteScriptJob(self, *args):
        cmds.scriptJob(kill=self.scriptJobNum)


    def selectionChanged(self):
        selection = cmds.ls(selection=True, transforms=True)
        if selection:
            selectedNode = selection[0]

            characterNamespaceInfo = utils.stripLeadingNamespace(selectedNode)
            if characterNamespaceInfo and characterNamespaceInfo[0] == self.selectedCharacter:
                blueprintNamespaceInfo = utils.stripLeadingNamespace(characterNamespaceInfo[1])

                if blueprintNamespaceInfo:
                    listEntry = blueprintNamespaceInfo[0].partition("__")[2]
                    allEntries = cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], q=True, allItems=True)

                    if listEntry in allEntries:
                        cmds.textScrollList(self.UIElements["blueprintModule_textScroll"], edit=True, selectItem=listEntry)

                        if listEntry != self.previousBlueprintListEntry:
                            self.refreshAnimationModuleList()

                        moduleNamespaceInfo = utils.stripLeadingNamespace(blueprintNamespaceInfo[1])
                        if moduleNamespaceInfo:
                            allEntries = cmds.textScrollList(self.UIElements["animationModule_textScroll"], q=True, allItems=True)
                            if moduleNamespaceInfo[0] in allEntries:
                                cmds.textScrollList(self.UIElements["animationModule_textScroll"], edit=True, selectItem=moduleNamespaceInfo[0])

