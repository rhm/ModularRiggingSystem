import maya.cmds as cmds

import System.utils as utils
reload(utils)


class MirrorModule:
    def __init__(self):
        selection = cmds.ls(selection=True, transforms=True)
        if not selection:
            return

        firstSelected = selection[0]

        self.modules = []
        self.group = None
        if firstSelected.find("Group__") == 0:
            self.group = firstSelected
            self.modules = self.findSubModules(firstSelected)
        else:
            moduleNamespaceInfo = utils.stripLeadingNamespace(firstSelected)
            if moduleNamespaceInfo:
                self.modules.append(moduleNamespaceInfo[0])

        tempModuleList = []
        for module in self.modules:
            if self.isModuleAMirror(module):
                cmds.confirmDialog(title="Mirror Module(s)",
                                   message="Cannot mirror a previously mirrored module, aborting mirror",
                                   button=["Accept"], defaultButton="Accept")
                return

            if not self.canModuleBeMirrored(module):
                print "Module \"" + module + "\" is of a type that cannot be mirrored. Skipping module"
            else:
                tempModuleList.append(module)

        self.modules = tempModuleList

        if self.modules:
            self.mirrorModuleUI()



    def findSubModules(self, group):
        returnModules = []

        children = cmds.listRelatives(group, children=True)
        children = cmds.ls(children, transforms=True)

        for child in children:
            if child.find("Group__") == 0:
                returnModules.extend(self.findSubModules(child))
            else:
                namespaceInfo = utils.stripAllNamespaces(child)
                if namespaceInfo and namespaceInfo[1] == "module_transform":
                    module = namespaceInfo[0]
                    returnModules.append(module)

        return returnModules


    def isModuleAMirror(self, module):
        moduleGroup = module+":module_grp"
        return cmds.attributeQuery("mirrorLinks", node=moduleGroup, exists=True)


    def canModuleBeMirrored(self, module):
        moduleNameInfo = utils.findAllModuleNames("/Modules/Blueprint")
        validModules = moduleNameInfo[0]
        validModuleNames = moduleNameInfo[1]

        moduleName = module.partition("__")[0]

        if not moduleName in validModuleNames:
            return false

        index = validModuleNames.index(moduleName)
        mod = __import__("Blueprint."+validModules[index], {}, {}, validModules[index])
        reload(mod)

        moduleClass = getattr(mod, mod.CLASS_NAME)
        moduleInstance = moduleClass("null", None)

        return moduleInstance.canModuleBeMirrored()


    def mirrorModuleUI(self):
        self.moduleNames = []
        for module in self.modules:
            self.moduleNames.append(module.partition("__")[2])

        self.sameMirrorSettingsForAll = False
        if len(self.modules) > 1:
            result = cmds.confirmDialog(title="Mirror Multiple Modules",
                                        message=str(len(self.modules))+" modules selected for mirror.\n"
                                                "How would you like to apply mirror settings?",
                                        button=["Same for all", "Individually", "Cancel"],
                                        defaultButton="Same for all",
                                        cancelButton="Cancel",
                                        dismissString="Cancel")
            if result == "Cancel":
                return

            if result == "Same for all":
                self.sameMirrorSettingsForAll = True

        self.UIElements = {}

        if cmds.window("mirrorModule_UI_window", exists=True):
            cmds.deleteUI("mirrorModule_UI_window")

        windowWidth = 400
        windowHeight = 300
        self.UIElements["window"] = cmds.window("mirrorModule_UI_window", width=windowWidth, height=windowHeight,
                                                title="Mirror Module(s)", sizeable=True)

        self.UIElements["scrollLayout"] = cmds.scrollLayout(hst=0)
        self.UIElements["topColumnLayout"] = cmds.columnLayout(adj=True, rs=3)

        scrollWidth = windowWidth - 30

        mirrorPlane_textWidth = 80
        mirrorPlane_columnWidth = (scrollWidth - mirrorPlane_textWidth) / 3
        self.UIElements["mirrorPlane_rowColumn"] = \
            cmds.rowColumnLayout(nc=4, columnAttach=(1,"right",0), columnWidth=[(1,mirrorPlane_textWidth),
                                                                                (2,mirrorPlane_columnWidth),
                                                                                (3,mirrorPlane_columnWidth),
                                                                                (4,mirrorPlane_columnWidth)])
        cmds.text(label="Mirror Plane: ")
        self.UIElements["mirrorPlane_radioCollection"] = cmds.radioCollection()
        cmds.radioButton("XY", label="XY", select=False)
        cmds.radioButton("YZ", label="YZ", select=True)
        cmds.radioButton("XZ", label="XZ", select=False)

        cmds.setParent(self.UIElements["topColumnLayout"])
        cmds.separator()

        cmds.text(label="Mirrored Name(s):")

        columnWidth = scrollWidth/2
        self.UIElements["moduleName_rowColumn"] = cmds.rowColumnLayout(nc=2, columnAttach=(1,"right",0),
                                                                       columnWidth=[(1,columnWidth),(2,columnWidth)])
        for module in self.moduleNames:
            cmds.text(label=module+" >> ")
            self.UIElements["moduleName_"+module] = cmds.textField(enable=True, text=module+"_mirror")

        cmds.setParent(self.UIElements["topColumnLayout"])
        cmds.separator()

        if self.sameMirrorSettingsForAll:
            self.generateMirrorFunctionControls(None, scrollWidth)
        else:
            for module in self.moduleNames:
                cmds.setParent(self.UIElements["topColumnLayout"])
                self.generateMirrorFunctionControls(module, scrollWidth)

        cmds.setParent(self.UIElements["topColumnLayout"])
        cmds.separator()

        self.UIElements["button_row"] = cmds.rowLayout(nc=2,
                                                       columnWidth=[(1,columnWidth),(2,columnWidth)],
                                                       cat=[(1,"both",10),(2,"both",10)],
                                                       columnAlign=[(1,"center"),(2,"center")])
        cmds.button(label="Accept", c=self.acceptWindow)
        cmds.button(label="Cancel", c=self.cancelWindow)


        cmds.showWindow(self.UIElements["window"])


    def generateMirrorFunctionControls(self, moduleName, scrollWidth):
        rotationRadioCollection = "rotation_radioCollection_all"
        translationRadioCollection = "translation_radioCollection_all"
        textLabel = "Mirror Settings:"

        behaviourName = "behaviour__"
        orientationName = "orientation__"
        mirroredName = "mirrored__"
        worldSpaceName = "worldSpace__"

        if moduleName:
            rotationRadioCollection = "rotation_radioCollection_" + moduleName
            translationRadioCollection = "translation_radioCollection_" + moduleName
            textLabel = moduleName + " Mirror Settings:"

            behaviourName = "behaviour__" + moduleName
            orientationName = "orientation__" + moduleName
            mirroredName = "mirrored__" + moduleName
            worldSpaceName = "worldSpace__" + moduleName

        cmds.text(label=textLabel)

        mirrorSettings_textWidth = 150
        mirrorSettings_columnWidth = (scrollWidth - mirrorSettings_textWidth)/2

        cmds.rowColumnLayout(nc=3, columnAttach=(1,"right",0),
                             columnWidth=[(1,mirrorSettings_textWidth),
                                          (2,mirrorSettings_columnWidth),
                                          (3,mirrorSettings_columnWidth)])

        cmds.text(label="Rotation Mirror Function: ")
        self.UIElements[rotationRadioCollection] = cmds.radioCollection()
        cmds.radioButton(behaviourName, label="Behaviour", select=True)
        cmds.radioButton(orientationName, label="Orientation", select=False)

        cmds.text(label="Translation Mirror Function: ")
        self.UIElements[translationRadioCollection] = cmds.radioCollection()
        cmds.radioButton(mirroredName, label="Mirrored", select=True)
        cmds.radioButton(worldSpaceName, label="World Space", select=False)

        cmds.setParent(self.UIElements["topColumnLayout"])
        cmds.text(label="")


    def cancelWindow(self, *args):
        cmds.deleteUI(self.UIElements["window"])


    def acceptWindow(self, *args):
        # a moduleInfo entry = (originalModule, mirroredModuleName, mirrorPlane, rotationFunction, translationFunction)
        self.moduleInfo = []

        self.mirrorPlane = cmds.radioCollection(self.UIElements["mirrorPlane_radioCollection"], q=True, select=True)

        for i in range(len(self.modules)):
            originalModule = self.modules[i]
            originalModuleName = self.moduleNames[i]

            originalModulePrefix = originalModule.partition("__")[0]
            mirroredModuleUserSpecifiedName = cmds.textField(self.UIElements["moduleName_"+originalModuleName], q=True, text=True)
            mirroredModuleName = originalModulePrefix+"__"+mirroredModuleUserSpecifiedName

            if utils.doesBlueprintUserSpecifiedNameExist(mirroredModuleUserSpecifiedName):
                cmds.confirmDialog(title="Name Conflict",
                                   message="Name \""+mirroredModuleUserSpecifiedName+"\" already exists, aborting mirror",
                                   button=["Accept"], defaultButton="Accept")
                return

            rotationFunction = ""
            translationFunction = ""

            if self.sameMirrorSettingsForAll:
                rotationFunction = cmds.radioCollection(self.UIElements["rotation_radioCollection_all"], q=True, select=True)
                translationFunction = cmds.radioCollection(self.UIElements["translation_radioCollection_all"], q=True, select=True)
            else:
                rotationFunction = cmds.radioCollection(self.UIElements["rotation_radioCollection_"+originalModuleName], q=True, select=True)
                translationFunction = cmds.radioCollection(self.UIElements["translation_radioCollection_"+originalModuleName], q=True, select=True)

            rotationFunction = rotationFunction.partition("__")[0]
            translationFunction = translationFunction.partition("__")[0]

            self.moduleInfo.append( [originalModule, mirroredModuleName, self.mirrorPlane, rotationFunction, translationFunction] )

        cmds.deleteUI(self.UIElements["window"])

        self.mirrorModules()


    def mirrorModules(self):
        mirrorModulesProgress_UI = cmds.progressWindow(title="Mirroring Module(s)",
                                                       status="This may take a few minutes...",
                                                       isInterruptable=False)
        mirrorModulesProgress = 0

        mirrorModulesProgress_stage1_proportion = 15
        mirrorModulesProgress_stage2_proportion = 70
        mirrorModulesProgress_stage3_proportion = 10

        moduleNameInfo = utils.findAllModuleNames("/Modules/Blueprint")
        validModules = moduleNameInfo[0]
        validModuleNames = moduleNameInfo[1]

        for module in self.moduleInfo:
            moduleName = module[0].partition("__")[0]

            if moduleName in validModuleNames:
                index = validModuleNames.index(moduleName)
                module.append(validModules[index])


        mirrorModulesProgress_progressIncrement = mirrorModulesProgress_stage1_proportion / len(self.moduleInfo)
        for module in self.moduleInfo:
            userSpecifiedName = module[0].partition("__")[2]
            mod = __import__("Blueprint."+module[5], {}, {}, [module[5]])
            reload(mod)

            moduleClass = getattr(mod, mod.CLASS_NAME)
            moduleInst = moduleClass(userSpecifiedName, None)

            hookObject = moduleInst.findHookObject()
            newHookObject = None

            hookModule = utils.stripLeadingNamespace(hookObject)[0]

            hookFound = False
            for m in self.moduleInfo:
                if hookModule == m[0]:
                    hookFound = True

                    if m == module:
                        continue

                    hookObjectName = utils.stripLeadingNamespace(hookObject)[1]
                    newHookObject = m[1] + ":" + hookObjectName

            if not hookFound:
                newHookObject = hookObject

            module.append(newHookObject)

            hookConstrained = moduleInst.isRootConstrained()
            module.append(hookConstrained)

            mirrorModulesProgress += mirrorModulesProgress_progressIncrement
            cmds.progressWindow(mirrorModulesProgress_UI, edit=True, pr=mirrorModulesProgress)



        cmds.progressWindow(mirrorModulesProgress_UI, edit=True, endProgress=True)
        utils.forceSceneUpdate()