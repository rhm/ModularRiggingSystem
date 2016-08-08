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



