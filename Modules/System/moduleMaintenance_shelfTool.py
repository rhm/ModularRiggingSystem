import maya.cmds as cmds


scriptJobNum = None

class ModuleMaintenance_ShelfTool:
    def __init__(self):
        global scriptJobNum

        import System.moduleMaintenance as modMaint
        reload(modMaint)

        modMaintentance_inst = modMaint.ModuleMaintenance(self)

        if scriptJobNum == None:
            modMaintentance_inst.setModuleMaintenanceVisibility(True)

            scriptJobNum = 10

        else:
            modMaintentance_inst.setModuleMaintenanceVisibility(False)

            if cmds.scriptJob(exists=scriptJobNum):
                cmds.scriptJob(kill=scriptJobNum)

            scriptJobNum = None


    def setScriptJobNum(self, num):
        global scriptJobNum
        scriptJobNum = num


    def getScriptJobNum(self):
        global scriptJobNum
        return scriptJobNum