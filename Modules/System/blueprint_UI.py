import datetime
from functools import partial

import maya.cmds as cmds
import System.utils as utils
reload(utils)

class Blueprint_UI:
    def __init__(self):
        self.moduleInstance = None

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

        self.UIElements["rehookBtn"] = cmds.button(enable=False, label="Re-hook")
        self.UIElements["snapRootBtn"] = cmds.button(enable=False, label="Snap Root > Hook")
        self.UIElements["constrainRootBtn"] = cmds.button(enable=False, label="Constrain Root > Hook")

        self.UIElements["groupSelectedBtn"] = cmds.button(label="Group Selected")
        self.UIElements["ungroupBtn"] = cmds.button(enable=False, label="Ungroup")
        self.UIElements["mirrorModuleBtn"] = cmds.button(enable=False, label="Mirror Module")

        cmds.text(label="")
        self.UIElements["deleteModuleBtn"] = cmds.button(enable=False, label="Delete", c=self.deleteModule)
        self.UIElements["symmetryMoveCheckBox"] = cmds.checkBox(enable=True, label="Symmetry Move")

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


    def modifySelected(self, *args):
        selectedNodes = cmds.ls(selection=True)

        if len(selectedNodes) <= 1:
            self.moduleInstance = None
            selectedModuleNamespace = None
            currentModuleFile = None

            if len(selectedNodes) == 1:
                lastSelected = selectedNodes[0]

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

            if selectedModuleNamespace != None:
                controlEnable = True
                userSpecifiedName = selectedModuleNamespace.partition("__")[2]

                mod = __import__("Blueprint."+currentModuleFile, {}, {}, [currentModuleFile])
                reload(mod)

                moduleClass = getattr(mod, mod.CLASS_NAME)
                self.moduleInstance = moduleClass(userSpecifiedName, None)


            cmds.button(self.UIElements["mirrorModuleBtn"], edit=True, enable=controlEnable)

            cmds.button(self.UIElements["rehookBtn"], edit=True, enable=controlEnable)
            cmds.button(self.UIElements["snapRootBtn"], edit=True, enable=controlEnable)
            cmds.button(self.UIElements["constrainRootBtn"], edit=True, enable=controlEnable)

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
        self.moduleInstance.delete()
        cmds.select(clear=True)


    def renameModule(self, *args):
        newName = cmds.textField(self.UIElements["moduleName"], q=True, text=True)
        self.moduleInstance.renameModuleInstance(newName)

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