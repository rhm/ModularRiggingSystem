import maya.cmds as cmds
from functools import partial

import System.utils as utils
reload(utils)


class AttachGeoToBlueprint_shelfTool:
    def __init__(self):
        self.title="Attach Geometry to Blueprint"


    def attachWithParenting(self):
        self.parenting = True
        self.skinning = False
        self.processInitialSelection()


    def attachWithSkinning(self):
        self.parenting = False
        self.skinning = True
        self.processInitialSelection()


    def processInitialSelection(self):
        selection = cmds.ls(selection=True)
        self.blueprintJoints = []
        self.geometry = []

        self.blueprintJoints = self.findBlueprintJoints(selection)
        self.geometry = self.findGeometry(selection)

        if not self.blueprintJoints:
            cmds.headsUpMessage("Please select the blueprint joint(s) you wish to attach geometry to.")
            cmds.scriptJob(event=["SelectionChanged", self.selectBlueprintJoint_callback], runOnce=True)
        elif not self.geometry:
            cmds.headsUpMessage("Please select the geometry you wish to attach to the specified blueprint joint(s)")
            cmds.scriptJob(event=["SelectionChanged", self.selectGeometry_callback], runOnce=True)
        else:
            self.attachGeoToBlueprint_attachment()


    def selectBlueprintJoint_callback(self, *args):
        selection = cmds.ls(selection=True)
        self.blueprintJoints = self.findBlueprintJoints(selection)
        if not self.blueprintJoints:
            cmds.confirmDialog(title=self.title,
                               message="Blueprint joint selection invalid, terminating tool",
                               button=["Accept"], defaultButton="Accept")
        elif not self.geometry:
            cmds.headsUpMessage("Please select the geometry you wish to attach to the specified blueprint joint(s)")
            cmds.scriptJob(event=["SelectionChanged", self.selectGeometry_callback], runOnce=True)
        else:
            self.attachGeoToBlueprint_attachment()


    def selectGeometry_callback(self, *args):
        selection = cmds.ls(selection=True)
        self.geometry = self.findGeometry(selection)

        if not self.geometry:
            cmds.confirmDialog(title=self.title,
                               message="Geometry selection invalid, terminating tool",
                               button=["Accept"], defaultButton="Accept")
        else:
            self.attachGeoToBlueprint_attachment()


    def findBlueprintJoints(self, selection):
        selectedBlueprintJoints = []

        for object in selection:
            if cmds.objectType(object, isType="joint"):
                jointNameInfo = utils.stripAllNamespaces(object)
                if jointNameInfo:
                    jointName = jointNameInfo[1]
                    if jointName.find("blueprint_") == 0:
                        selectedBlueprintJoints.append(object)

        return selectedBlueprintJoints


    def findGeometry(self, selection):
        selection = cmds.ls(selection, transforms=True)

        nonJointSelection = []
        for node in selection:
            if not cmds.objectType(node, isType="joint"):
                nonJointSelection.append(node)

        return nonJointSelection


    def attachGeoToBlueprint_attachment(self):
        print "Attach"
