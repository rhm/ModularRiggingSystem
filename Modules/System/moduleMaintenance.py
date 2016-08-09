import maya.cmds as cmds
import System.utils as utils
reload(utils)

from functools import partial



class ModuleMaintenance:
    def __init__(self, shelfTool_inst):
        self.shelfTool_instance = shelfTool_inst
        self.UIElements = {}


    def setModuleMaintenanceVisibility(self, vis=True):
        characters = utils.findInstalledCharacters()

        for c in characters:
            characterContainer = c+":character_container"
            cmds.lockNode(characterContainer, lock=False, lockUnpublished=False)

            characterGroup = c+":character_grp"
            cmds.setAttr(characterGroup+".moduleMaintenanceVisibility", vis)


            cmds.lockNode(characterContainer, lock=True, lockUnpublished=True)


    def objectSelected(self):
        objects = cmds.ls(selection=True)
        cmds.select(clear=True)

        if objects:
            lastSelected = objects[-1]
            lastSelected_stripNS = utils.stripAllNamespaces(lastSelected)

            if lastSelected_stripNS:
                lastSelected_withoutNS = lastSelected_stripNS[1]

                if lastSelected_withoutNS.find("blueprint_") == 0:
                    blueprintModuleNS_incCharNS = lastSelected_stripNS[0]
                    moduleContainer = blueprintModuleNS_incCharNS + ":module_container"
                    print moduleContainer
                    cmds.select(moduleContainer, replace=True)

                    characterNS = utils.stripLeadingNamespace(lastSelected)[0]
                    characterContainer = characterNS + ":character_container"

                    containers = [characterContainer, moduleContainer]
                    for container in containers:
                        cmds.lockNode(container, lock=False, lockUnpublished=False)

                    blueprintJointsGrp = blueprintModuleNS_incCharNS+":blueprint_joints_grp"
                    cmds.setAttr(blueprintJointsGrp+".overrideColor", 13)

                    for container in containers:
                        cmds.lockNode(container, lock=True, lockUnpublished=True)

        self.setupSelectionScriptJob()


    def setupSelectionScriptJob(self):
        scriptJobNum = cmds.scriptJob(event=["SelectionChanged", self.objectSelected], runOnce=True, killWithScene=True)
        self.shelfTool_instance.setScriptJobNum(scriptJobNum)


    def disableSelectionScriptJob(self):
        scriptJobNum = self.shelfTool_instance.getScriptJobNum()
        self.shelfTool_instance.setScriptJobNum(None)
        if cmds.scriptJob(exists=scriptJobNum):
            cmds.scriptJob(kill=scriptJobNum)



