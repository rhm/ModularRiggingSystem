import os
import maya.cmds as cmds

import System.blueprint as bpmod
import Blueprint.finger as finger


import System.utils as utils
reload(utils)



CLASS_NAME = 'Thumb'

TITLE = "Thumb"
DESCRIPTION = "Creates 4 joints, defining a thumb. Ideal use: thumb"
ICON = os.environ["RIGGING_TOOL_ROOT"] + "/Icons/_thumb.xpm"


class Thumb(finger.Finger):
    def __init__(self, userSpecifiedName, hookObject):
        jointInfo = [
            ["root_joint",      [0.0, 0.0, 0.0]],
            ["knuckle_1_joint", [4.0, 0.0, 0.0]],
            ["knuckle_2_joint", [8.0, 0.0, 0.0]],
            ["end_joint", [12.0, 0.0, 0.0]]
        ]

        bpmod.Blueprint.__init__(self, CLASS_NAME, userSpecifiedName, jointInfo, hookObject)
