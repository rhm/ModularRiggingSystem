import maya.cmds as cmds
import System.utils as utils
reload(utils)


class DeleteCharacter_ShelfTool:
    def __init__(self):
        character = self.findSelectedCharacter()
        if not character:
            return

        niceName = character.partition("__")[2]

        result = cmds.confirmDialog(title="Delete Character",
                                    message="Are you sure you want to delete the character \"" + niceName + "\"?\n\n"
                                            "Character deletion cannot be undone.",
                                    button=["Yes", "Cancel"], defaultButton="Yes", cancelButton="Cancel",
                                    dismissString="Cancel")
        if result == "Cancel":
            return

        characterContainer = character+":character_container"

        cmds.lockNode(characterContainer, lock=False, lockUnpublished=False)
        cmds.delete(characterContainer)

        cmds.namespace(setNamespace=character)
        bpNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for bpNS in bpNamespaces:
            cmds.namespace(setNamespace=":")
            cmds.namespace(setNamespace=bpNS)

            modNamespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
            cmds.namespace(setNamespace=":")

            if modNamespaces:
                for modNS in modNamespaces:
                    cmds.namespace(removeNamespace=modNS)

            cmds.namespace(removeNamespace=bpNS)

        cmds.namespace(removeNamespace=character)


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

        return  character