


CLASS_NAME="FK"
TITLE="Forward Kinematics"
DESCRIPTION="This module provides FK rotational controls for every joint in the blueprint it is installed on"


class FK:
    def __init__(self, moduleNamespace):
        print moduleNamespace


    def compatibleBlueprintModules(self):
        return ["Finger", "HingeJoint", "LegFoot", "SingleJointSegment", "SingleOrientableJoint", "Spline", "Thumb"]


    def install(self):
        print "INSTALL" + CLASS_NAME
