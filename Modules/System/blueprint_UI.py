import datetime
from functools import partial

import maya.cmds as cmds
import System.utils as utils
reload(utils)

class Blueprint_UI:
    def __init__(self):
        self.moduleInstance = None

        self.deleteSymmetryMoveExpressions()

        # Store UI elements in a dictionary
        self.UIElements = {}

        #if cmds.window("blueprint_UI_window", exists=True):
        #    cmds.deleteUI("blueprint_UI_window")

        windowWidth = 400
        windowHeight = 598

        windowtitle = "blueprint_" + datetime.datetime.now().strftime("%H_%M_%S")
        self.UIElements["window"] = cmds.window(windowtitle, #"blueprint_UI_window",
                                                width=windowWidth, height=windowHeight,
                                                title="Blueprint Module UI",
                                                sizeable=True)


        #self.UIElements["topLevelColumn"] = cmds.columnLayout(adj=True, columnAlign="center") #w=windowWidth
        self.UIElements["topLevelColumn"] = cmds.columnLayout(adj=True, columnAlign="center")

        # Set up tabs
        tabHeight = 500
        self.UIElements["tabs"] = cmds.tabLayout(height=tabHeight, innerMarginWidth=5, innerMarginHeight=5)

        tabWidth = cmds.tabLayout(self.UIElements["tabs"], q=True, width=True)
        self.scrollWidth = tabWidth - 40
        #print "scrollWidth = " + str(self.scrollWidth)

        self.initializeModuleTab(tabHeight, tabWidth)
        cmds.tabLayout(self.UIElements["tabs"], edit=True, tabLabelIndex=([1, "Modules"]))


        # buttons
        cmds.setParent(self.UIElements["topLevelColumn"])
        self.UIElements["lockPublishColumn"] = cmds.columnLayout(adj=True, columnAlign="center", rs=3)

        cmds.separator()

        self.UIElements["lockBtn"] = cmds.button(label="Lock", c=self.lock)

        cmds.separator()

        self.UIElements["publishBtn"] = cmds.button(label="Publish")

        cmds.separator()

        # Display window
        cmds.showWindow(self.UIElements["window"])

        self.createScriptJob()


    def createScriptJob(self):
        self.jobNum = cmds.scriptJob(event=["SelectionChanged", self.modifySelected],
                                     runOnce=True,
                                     parent=self.UIElements["window"])


    def deleteScriptJob(self):
        cmds.scriptJob(kill=self.jobNum)


    def initializeModuleTab(self, tabHeight, tabWidth):
        moduleSpecific_scrollHeight = 120
        scrollHeight = tabHeight - moduleSpecific_scrollHeight - 163

        self.UIElements["moduleColumn"] = cmds.columnLayout(adj=True, rs=3)
        self.UIElements["moduleFrameLayout"] = cmds.frameLayout(height=scrollHeight, collapsable=False,
                                                                borderVisible=False, labelVisible=False)
        self.UIElements["moduleList_Scroll"] = cmds.scrollLayout(hst=0)
        self.UIElements["moduleList_column"] = cmds.columnLayout(columnWidth=self.scrollWidth, adj=True, rs=2)

        # First separator
        cmds.separator()

        for module in utils.findAllModules("Modules/Blueprint"):
            self.createModuleInstallButton(module)
            cmds.setParent(self.UIElements["moduleList_column"])
            cmds.separator()

        cmds.setParent(self.UIElements["moduleColumn"])
        cmds.separator()

        # Button Panel
        self.UIElements["moduleName_row"] = cmds.rowLayout(nc=2, columnAttach=(1, "right", 0),
                                                           columnWidth=[(1,80)], adjustableColumn=2)
        cmds.text(label="Module Name :")
        self.UIElements["moduleName"] = cmds.textField(enable=False,
                                                       alwaysInvokeEnterCommandOnReturn=True,
                                                       enterCommand=self.renameModule)

        cmds.setParent(self.UIElements["moduleColumn"])

        columnWidth = 150 #(tabWidth - 20)/3
        self.UIElements["moduleButtons_rowColumn"] = cmds.rowColumnLayout(numberOfColumns=3,
                                                                          ro=[(1, "both", 2), (2, "both", 2), (3, "both", 2)],
                                                                          columnAttach=[(1, "both", 3), (2, "both", 3), (3, "both", 3)],
                                                                          columnWidth=[(1, columnWidth), (2, columnWidth), (3, columnWidth)])

        self.UIElements["rehookBtn"] = cmds.button(enable=False, label="Re-hook", c=self.rehookModule_setup)
        self.UIElements["snapRootBtn"] = cmds.button(enable=False, label="Snap Root > Hook", c=self.snapRootToHook)
        self.UIElements["constrainRootBtn"] = cmds.button(enable=False, label="Constrain Root > Hook", c=self.constrainRootToHook)

        self.UIElements["groupSelectedBtn"] = cmds.button(label="Group Selected", c=self.groupSelected)
        self.UIElements["ungroupBtn"] = cmds.button(enable=False, label="Ungroup", c=self.ungroupSelected)
        self.UIElements["mirrorModuleBtn"] = cmds.button(enable=False, label="Mirror Module", c=self.mirrorSelection)

        cmds.text(label="")
        self.UIElements["deleteModuleBtn"] = cmds.button(enable=False, label="Delete", c=self.deleteModule)
        self.UIElements["symmetryMoveCheckBox"] = cmds.checkBox(enable=True, label="Symmetry Move",
                                                                onc=self.setupSymmetryMoveExpressions_checkbox,
                                                                ofc=self.deleteSymmetryMoveExpressions)

        cmds.setParent(self.UIElements["moduleColumn"])
        cmds.separator()

        # module specific UI

        #self.UIElements["moduleSpecificRowColumnLayout"] = cmds.rowColumnLayout(nr=1, rowAttach=[1, "both", 0], rowHeight=[1, moduleSpecific_scrollHeight])
        self.UIElements["moduleSpecific_Scroll"] = cmds.scrollLayout(hst=0, height=moduleSpecific_scrollHeight)
        self.UIElements["moduleSpecific_column"] = cmds.columnLayout(adj=True, columnWidth=self.scrollWidth, columnAttach=["both", 5], rs=2)

        cmds.setParent(self.UIElements["moduleColumn"])
        cmds.separator()


    def createModuleInstallButton(self, module):
        mod = __import__("Blueprint."+module, {}, {}, [module])
        reload(mod)

        title = mod.TITLE
        description = mod.DESCRIPTION
        icon = mod.ICON

        # Create UI
        buttonSize = 64
        row = cmds.rowLayout(numberOfColumns=2, columnWidth=([1, buttonSize]),
                             adjustableColumn=2, columnAttach=([1, "both", 0],[2, "both", 5]) )
        self.UIElements["module_button_" + module] = \
            cmds.symbolButton(width=buttonSize, height=buttonSize, image=icon,
                              command=partial(self.installModule, module))

        textColumn = cmds.columnLayout(columnAlign="center")

        #cmds.text(align="center", width=self.scrollWidth - buttonSize - 16, label=title)
        #print "text width = " + str(self.scrollWidth - buttonSize - 16)
        cmds.text(align="center", width=300, label=title)
        cmds.scrollField(text=description, editable=False, width=300, wordWrap=True, height=50) #numberOfLines=3)


    def installModule(self, module, *args):
        basename = "instance_"

        cmds.namespace(setNamespace=":")
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)

        for i in range(len(namespaces)):
            if namespaces[i].find("__") != -1:
                namespaces[i] = namespaces[i].partition("__")[2]

        newSuffix = utils.findHighestTrailingNumber(namespaces, basename) + 1
        userSpecName = basename + str(newSuffix)

        hookObj = self.findHookObjectFromSelection()


        mod = __import__("Blueprint."+module, {}, {}, [module])
        reload(mod)

        moduleClass = getattr(mod, mod.CLASS_NAME)
        moduleInstance = moduleClass(userSpecName, hookObj)
        moduleInstance.install()

        moduleTransform = mod.CLASS_NAME + "__" + userSpecName + ":module_transform"
        cmds.select(moduleTransform, replace=True)
        cmds.setToolTo("moveSuperContext")


    def lock(self, *args):
        result = cmds.confirmDialog(messageAlign="center", title="Lock Blueprints",
                                    message="The action of locking a character will convert the current blueprint"
                                            "modules to joints. This action cannot be undone.\n\n"
                                            "Modifications to the blueprint system cannot be made after this point.\n\n"
                                            "Do you want to continue?",
                                    button=["Accept", "Cancel"], defaultButton="Accept", cancelButton="Cancel",
                                    dismissString="Cancel")

        if result != "Accept":
            return

        self.deleteSymmetryMoveExpressions()
        cmds.checkBox(self.UIElements["symmetryMoveCheckBox"], edit=True, value=False)

        self.deleteScriptJob()

        moduleInfo = [] # store (module, userSpecifiedName) pairs

        cmds.namespace(setNamespace=":")
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)

        moduleNameInfo = utils.findAllModuleNames("/Modules/Blueprint")
        validModules = moduleNameInfo[0]
        validModuleNames = moduleNameInfo[1]

        for n in namespaces:
            splitString = n.partition("__")

            if splitString[1] != "":
                module = splitString[0]
                userSpecifiedName = splitString[2]

                if module in validModuleNames:
                    index = validModuleNames.index(module)
                    moduleInfo.append( [validModules[index], userSpecifiedName] )

        if len(moduleInfo) == 0:
            cmds.confirmDialog(messageAlign="center", title="Lock Blueprints",
                               message="There appear to be blueprint module instances in the current scene\n\n"
                                       "Aborting lock.",
                               button=["Accept"], defaultButton="Accept")
            return

        moduleInstances = []
        for module in moduleInfo:
            mod = __import__("Blueprint."+module[0], {}, {}, [module[0]])
            reload(mod)

            moduleClass = getattr(mod, mod.CLASS_NAME)
            moduleInst = moduleClass(module[1], None)

            moduleInfo = moduleInst.lock_phase1()

            moduleInstances.append((moduleInst, moduleInfo))


        for module in moduleInstances:
            module[0].lock_phase2(module[1])


        groupContainer = "Group_container"
        if cmds.objExists(groupContainer):
            cmds.lockNode(groupContainer, lock=False, lockUnpublished=False)
            cmds.delete(groupContainer)


        for module in moduleInstances:
            hookObject = module[1][4]
            module[0].lock_phase3(hookObject)


    def modifySelected(self, *args):
        if cmds.checkBox(self.UIElements["symmetryMoveCheckBox"], q=True, value=True):
            self.deleteSymmetryMoveExpressions()
            self.setupSymmetryMoveExpressions()


        selectedNodes = cmds.ls(selection=True)

        if len(selectedNodes) <= 1:
            self.moduleInstance = None
            selectedModuleNamespace = None
            currentModuleFile = None

            cmds.button(self.UIElements["ungroupBtn"], edit=True, enable=False)
            cmds.button(self.UIElements["mirrorModuleBtn"], edit=True, enable=False)

            if len(selectedNodes) == 1:
                lastSelected = selectedNodes[0]

                if lastSelected.find("Group__") == 0:
                    cmds.button(self.UIElements["ungroupBtn"], edit=True, enable=True)
                    cmds.button(self.UIElements["mirrorModuleBtn"], edit=True, enable=True, label="Mirror Group")

                namespaceAndNode = utils.stripLeadingNamespace(lastSelected)
                if namespaceAndNode != None:
                    namespace = namespaceAndNode[0]

                    moduleNameInfo = utils.findAllModuleNames("/Modules/Blueprint")
                    validModules = moduleNameInfo[0]
                    validModuleNames = moduleNameInfo[1]

                    index = 0
                    for moduleName in validModuleNames:
                        moduleNameIncSuffix = moduleName + "__"
                        if namespace.find(moduleNameIncSuffix) == 0:
                            currentModuleFile = validModules[index]
                            selectedModuleNamespace = namespace
                            break

                        index += 1

            controlEnable = False
            userSpecifiedName = ""
            constrainCommand = self.constrainRootToHook
            constrainLabel = "Constrain Root > Hook"

            if selectedModuleNamespace != None:
                controlEnable = True
                userSpecifiedName = selectedModuleNamespace.partition("__")[2]

                mod = __import__("Blueprint."+currentModuleFile, {}, {}, [currentModuleFile])
                reload(mod)

                moduleClass = getattr(mod, mod.CLASS_NAME)
                self.moduleInstance = moduleClass(userSpecifiedName, None)

                cmds.button(self.UIElements["mirrorModuleBtn"], edit=True, enable=True, label="Mirror Module")

                if self.moduleInstance.isRootConstrained():
                    constrainCommand = self.unconstrainRootFromHook
                    constrainLabel = "Unconstrain Root"


            cmds.button(self.UIElements["rehookBtn"], edit=True, enable=controlEnable)
            cmds.button(self.UIElements["snapRootBtn"], edit=True, enable=controlEnable)
            cmds.button(self.UIElements["constrainRootBtn"], edit=True, enable=controlEnable,
                        label=constrainLabel, c=constrainCommand)

            cmds.button(self.UIElements["deleteModuleBtn"], edit=True, enable=controlEnable)

            cmds.textField(self.UIElements["moduleName"], edit=True, enable=controlEnable, text=userSpecifiedName)

            self.createModuleSpecificControls()

        self.createScriptJob()


    def createModuleSpecificControls(self):
        existingControls = cmds.columnLayout(self.UIElements["moduleSpecific_column"], q=True, childArray=True)
        if existingControls != None:
            cmds.deleteUI(existingControls)

        cmds.setParent(self.UIElements["moduleSpecific_column"])

        if self.moduleInstance != None:
            self.moduleInstance.UI(self, self.UIElements["moduleSpecific_column"])


    def deleteModule(self, *args):
        symmetryMove = cmds.checkBox(self.UIElements["symmetryMoveCheckBox"], q=True, value=True)
        if symmetryMove:
            self.deleteSymmetryMoveExpressions()

        self.moduleInstance.delete()
        cmds.select(clear=True)

        if symmetryMove:
            self.setupSymmetryMoveExpressions_checkbox()


    def renameModule(self, *args):
        newName = cmds.textField(self.UIElements["moduleName"], q=True, text=True)

        symmetryMove = cmds.checkBox(self.UIElements["symmetryMoveCheckBox"], q=True, value=True)
        if symmetryMove:
            self.deleteSymmetryMoveExpressions()

        self.moduleInstance.renameModuleInstance(newName)

        if symmetryMove:
            self.setupSymmetryMoveExpressions_checkbox()


        previousSelection = cmds.ls(selection=True)

        if len(previousSelection) > 0:
            cmds.select(previousSelection, replace=True)
        else:
            cmds.select(clear=True)


    def findHookObjectFromSelection(self, *args):
        selectedObjects = cmds.ls(selection=True, transforms=True)
        hookObj = None

        if len(selectedObjects) > 0:
            hookObj = selectedObjects[-1]

        return hookObj


    def rehookModule_setup(self, *args):
        selectedNodes = cmds.ls(selection=True, transforms=True)
        if len(selectedNodes) == 2:
            newHook = self.findHookObjectFromSelection()
            self.moduleInstance.rehook(newHook)
        else:
            self.deleteScriptJob()
            currentSelection = cmds.ls(selection=True)

            cmds.headsUpMessage("Please selection the joint you wish to re-hook to. Clear selection to un-hook")
            cmds.scriptJob(event=["SelectionChanged", partial(self.rehookModule_callback, currentSelection)], runOnce=True)


    def rehookModule_callback(self, currentSelection):
        newHook = self.findHookObjectFromSelection()

        self.moduleInstance.rehook(newHook)

        if len(currentSelection) > 0:
            cmds.select(currentSelection, replace=True)
        else:
            cmds.select(clear=True)

        self.createScriptJob()


    def snapRootToHook(self, *args):
        self.moduleInstance.snapRootToHook()


    def constrainRootToHook(self, *args):
        self.moduleInstance.constrainRootToHook()
        cmds.button(self.UIElements["constrainRootBtn"], edit=True, label="Unconstrain Root", c=self.unconstrainRootFromHook)


    def unconstrainRootFromHook(self, *args):
        self.moduleInstance.unconstrainRootFromHook()
        cmds.button(self.UIElements["constrainRootBtn"], edit=True, label="Constrain Root > Hook", c=self.constrainRootToHook)


    def groupSelected(self, *args):
        import System.groupSelected as groupSelected
        reload(groupSelected)

        groupSelected.GroupSelected().show_UI()


    def ungroupSelected(self, *args):
        import System.groupSelected as groupSelected
        reload(groupSelected)

        groupSelected.UngroupSelected()


    def mirrorSelection(self, *args):
        import System.mirrorModule as mirrorModule
        reload(mirrorModule)

        mirrorModule.MirrorModule()


    def setupSymmetryMoveExpressions_checkbox(self, *args):
        self.deleteScriptJob()
        self.setupSymmetryMoveExpressions()
        self.createScriptJob()


    def setupSymmetryMoveExpressions(self, *args):
        cmds.namespace(setNamespace=":")
        selection=cmds.ls(selection=True, transforms=True)
        expressionContainer = cmds.container(name="symmetryMove_container")

        if len(selection) == 0:
            return

        linkedObjs = []
        for obj in selection:
            if obj in linkedObjs:
                continue

            if obj.find("Group__") == 0:
                if cmds.attributeQuery("mirrorLinks", n=obj, exists=True):
                    mirrorLinks = cmds.getAttr(obj+".mirrorLinks")
                    groupInfo = mirrorLinks.rpartition("__")
                    mirrorObj = groupInfo[0]
                    axis = groupInfo[2]

                    linkedObjs.append(mirrorObj)

                    self.setupSymmetryMoveForObject(obj, mirrorObj, axis, translation=True, orientation=True, globalScale=True)
            else:
                objNamespaceInfo = utils.stripLeadingNamespace(obj)
                if objNamespaceInfo:
                    if cmds.attributeQuery("mirrorLinks", n=objNamespaceInfo[0]+":module_grp", exists=True):
                        mirrorLinks = cmds.getAttr(objNamespaceInfo[0]+":module_grp.mirrorLinks")
                        moduleInfo = mirrorLinks.rpartition("__")
                        module = moduleInfo[0]
                        axis = moduleInfo[2]

                        if objNamespaceInfo[1].find("translation_control") != -1:
                            mirrorObj = module + ":" + objNamespaceInfo[1]
                            linkedObjs.append(mirrorObj)
                            self.setupSymmetryMoveForObject(obj, mirrorObj, axis, translation=True, orientation=False, globalScale=False)

                        elif objNamespaceInfo[1].find("module_transform") == 0:
                            mirrorObj = module + ":module_transform"
                            linkedObjs.append(mirrorObj)
                            self.setupSymmetryMoveForObject(obj, mirrorObj, axis, translation=True, orientation=True, globalScale=True)

                        elif objNamespaceInfo[1].find("orientation_control") != -1:
                            mirrorObj = module + ":" + objNamespaceInfo[1]
                            linkedObjs.append(mirrorObj)

                            expressionString = mirrorObj + ".rotateX = "+ obj + ".rotateX;\n"
                            expression = cmds.expression(n=mirrorObj+"_symmetryMoveExpression", string=expressionString)
                            utils.addNodeToContainer(expressionContainer, expression)

                        elif objNamespaceInfo[1].find("singleJointOrientation_control") != -1:
                            mirrorObj = module + ":" + objNamespaceInfo[1]
                            linkedObjs.append(mirrorObj)

                            expressionString =  mirrorObj + ".rotateX = " + obj + ".rotateX;\n"
                            expressionString += mirrorObj + ".rotateY = " + obj + ".rotateY;\n"
                            expressionString += mirrorObj + ".rotateZ = " + obj + ".rotateZ;\n"

                            expression = cmds.expression(n=mirrorObj+"_symmetryMoveExpression", string=expressionString)
                            utils.addNodeToContainer(expressionContainer, expression)


        cmds.lockNode(expressionContainer, lock=True)
        cmds.select(selection, replace=True)


    def setupSymmetryMoveForObject(self, obj, mirrorObj, axis, translation=True, orientation=False, globalScale=False):
        duplicateObject = cmds.duplicate(obj, parentOnly=True, inputConnections=True, name=obj+"_mirrorHelper")[0]
        emptyGroup = cmds.group(empty=True, name=obj+"mirror_scale_grp")
        cmds.parent(duplicateObject, emptyGroup, absolute=True)

        scaleAttribute = ".scale" + axis
        cmds.setAttr(emptyGroup+scaleAttribute, -1)

        expressionString = "namespace -setNamespace \":\";\n"
        if translation:
            expressionString += "$worldSpacePos = `xform -q -ws -translation "+obj+"`;\n"
        if orientation:
            expressionString += "$worldSpaceOrient = `xform -q -ws -rotation "+obj+"`;\n"

        attrs = []
        if translation:
            attrs.extend([".translateX", ".translateY", ".translateZ"])
        if orientation:
            attrs.extend([".rotateX", ".rotateY", ".rotateZ"])

        for attr in attrs:
            expressionString += duplicateObject+attr + " = " + obj+attr + ";\n"

        i = 0
        for a in ["X", "Y", "Z"]:
            if translation:
                expressionString += duplicateObject+".translate"+a + " = $worldSpacePos["+str(i)+"];\n"
            if orientation:
                expressionString += duplicateObject+".rotate"+a + " = $worldSpaceOrient["+str(i)+"];\n"
            i += 1

        if globalScale:
            expressionString += duplicateObject+".globalScale = " + obj+".globalScale;\n"

        expression = cmds.expression(n=duplicateObject+"_symmetryMoveExpression", string=expressionString)

        constraint = ""
        if translation and orientation:
            constraint = cmds.parentConstraint(duplicateObject, mirrorObj, maintainOffset=False,
                                               n=mirrorObj+"_symmetryMoveConstraint")[0]
        elif translation:
            constraint = cmds.pointConstraint(duplicateObject, mirrorObj, maintainOffset=False,
                                              n=mirrorObj+"_symmetryMoveConstraint")[0]
        elif orientation:
            constraint = cmds.orientConstraint(duplicateObject, mirrorObj, maintainOffset=False,
                                               n=mirrorObj+"_symmetryMoveConstraint")[0]

        if globalScale:
            cmds.connectAttr(duplicateObject+".globalScale", mirrorObj+".globalScale")

        utils.addNodeToContainer("symmetryMove_container", [duplicateObject, emptyGroup, expression, constraint], ihb=True)


    def deleteSymmetryMoveExpressions(self, *args):
        container = "symmetryMove_container"
        if cmds.objExists(container):
            cmds.lockNode(container, lock=False)

            nodes = cmds.container(container, q=True, nodeList=True)
            nodes = cmds.ls(nodes, type=["parentConstraint", "pointConstraint", "orientConstraint"])

            if nodes:
                cmds.delete(nodes)

            cmds.delete(container)