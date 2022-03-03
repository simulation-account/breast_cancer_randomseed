# Jim Sluka 1/6/21 Reddit CC3D v4 of Breast cancer model
from cc3d.core.PySteppables import *
#from PySteppablesExamples import MitosisSteppableBase
from random import uniform
import math
from math import *
import string
import os
from os import getcwd
import os.path
import random
random.seed(12345)
from xml.dom import minidom
import subprocess
import sys
sys.path.append(os.path.dirname("cell_survival_interpolation.py"))
import cell_survival_interpolation
location = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(location,"cancol2.xml")
xmlf = minidom.parse(filename)
items = xmlf.getElementsByTagName('Energy')
e1 = items[22].childNodes[0].data
e = float(e1)
var = 2.0 #RD_coop value
varii = 0.5 #growth rate coefficient
c=0
mcsOut=0

# My addition: write files to track cancer cell number and total cancer volume
cancer_cell_number_str = "mcs,cancer_cell_number"
cancer_volume_str = "mcs,cancer_volume"

##jps## class CellLayoutSteppable(SteppableBasePy):
##jps##     def __init__(self,_simulator,_frequency=1):
##jps##         SteppableBasePy.__init__(self,_simulator,_frequency)
class CellLayoutSteppable(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self,frequency)

        
    def start(self):
#collagen        
        for x in range(5,95,4):
            for y in range(5,95,4):
                self.cellField[x:x+2,y:y+2,0] = self.newCell(self.C1)   
#laminin
        for x in range(37,63,3):
            for y in range(37,63,3):
                self.cellField[x:x+3,y:y+3,0] = self.newCell(self.LAMININ)
#cancer
        for x in range(43,57,4):
            for y in range(43,57,4):
                self.cellField[x:x+4,y:y+4,0] = self.newCell(self.CANCER)
                
    # My addition: stop function
    def stop(self):
        cancer_cell_number_file.close()
        cancer_volume_file.close()

class VolumeParamSteppable(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self,frequency)
        self.fieldNameMMP='MMP'
        self.fieldNameI='I'
        self.fieldNameGF='GF'
    def start(self):
        global c
        global ck
        global c_value
        global mcsOut
        global varii
        c_value=[]
        for cell in self.cellList:
            if cell.type == self.C1:
                cell.targetVolume = 4.0
                cell.lambdaVolume = 20.0
                
            if cell.type == self.LAMININ:
                cell.targetVolume = 9.0
                cell.lambdaVolume = 20.0
                
            if cell.type == self.CANCER:
                cell.targetVolume = 16.0 + 8.0
                cell.lambdaVolume = 20.0
    def step(self,mcs):
        fieldMMP=CompuCell.getConcentrationField(self.simulator,self.fieldNameMMP)
        fieldI=CompuCell.getConcentrationField(self.simulator,self.fieldNameI)
        fieldGF=CompuCell.getConcentrationField(self.simulator,self.fieldNameGF)
        comPt=CompuCell.Point3D()
        state={}
        global c
        global ck
        global mcsOut
        global c_value
        global varii
        global cancer_cell_number_str
        global cancer_volume_str
        
        # My addition: track number of cancer_cells and cancer_volume
        cancer_cells = 0
        cancer_volume = 0
        for cell in self.cellList:
#collagen fibre elongation            
            if cell.type == self.C1 and mcs<5:
                cell.targetVolume+=0.8
 ##               cell.lambdaVolume=20.0
            
            if cell.type == self.CANCER:
                cancer_cells += 1
                cancer_volume += cell.volume 
                neighborList = self.get_cell_neighbor_data_list(cell)           # Changed from deprecated getCellNeighborDataList
                k=neighborList.commonSurfaceAreaWithCellTypes(cell_type_list=[3])
                s=cell.surface
                g= (s-k)/40
                GFc=fieldGF[int(round(cell.xCOM)),int(round(cell.yCOM)),int(round(cell.zCOM))]
                cell.targetVolume+= varii*((g/4 + (GFc/7))/3)
                cell.lambdaVolume=20.0 #this term can be changed in correlation with stiffness of neighbors, as a fn of neighbor type,no etc
                if int(round(cell.xCOM))>97 or int(round(cell.xCOM))<3 or int(round(cell.yCOM))>97 or int(round(cell.yCOM))<3:
                    self.deleteCell(cell)
                    c+=1
                    if c==1:
                        mcsOut = mcs
                    
        ck=c
        if ck!=0 and mcs%5==0:
            c_value.append(ck)
#        print(c_value)
        cancer_cell_number_str += '\n' + str(mcs) + ',' + str(cancer_cells)      # My addition
        cancer_volume_str += '\n' + str(mcs) + ',' + str(cancer_volume)          # My addition
        # Write the cancer cell number and volume info at intervals
        if mcs%10 == 0:
            cancer_cell_number_file = open("cancer_cell_number_2D_Sluka.csv", 'w')   
            cancer_cell_number_file.write(cancer_cell_number_str)
            cancer_cell_number_file.close()
            cancer_volume_file = open("cancer_volume_2D_Sluka.csv", 'w')
            cancer_volume_file.write(cancer_volume_str)
            cancer_cell_number_file.close()
        
        
            

    def finish(self):
        global mcsOut
        global c_value
        # saving number of cells getting deleted at lattice boundary at each mcs
##jps## self.f=open(CompuCellSetup.getScreenshotDirectoryName() + "\cvalue.txt","w+")
##jps## file_obj, file_path = self.open_file_in_simulation_output_folder("\cvalue.txt", mode='w+')
        from pathlib import Path
        if self.output_dir is not None:
            output_path = Path(self.output_dir).joinpath("cvalue.txt")
            # create folder to store data
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                file_handle = open(output_path, 'w+')
            except IOError:
                print ("Could not open file for writing: ",output_path)
                return
        
        print("\n\n\t file_handle: ",file_handle)
        file_handle.write("%d\r\n\n"%mcsOut) #saving the number of MCS when cells start getting deleted
        for ck in c_value:
            file_handle.write("%d\r"%ck)
        file_handle.close()        
                
class MatrixDegradation(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self,frequency)
        self.fieldNameMMP='MMP'
        self.fieldNameI='I'
    def start(self):
        state={}
    def step(self,mcs):
#collagen degradation
        clCell=self.potts.createCell()
        clCell.type=self.C_LYSED
        llCell=self.potts.createCell()
        llCell.type=self.L_LYSED
        state={}
        self.fieldNameMMP='MMP'
        self.fieldNameI='I'
        fieldMMP=CompuCell.getConcentrationField(self.simulator,self.fieldNameMMP)
        fieldI=CompuCell.getConcentrationField(self.simulator,self.fieldNameI)
        global var
        lysed_id= []
        for cell in self.cellList:
            state={}
            cellDict=CompuCell.getPyAttrib(cell)    
            if cell.type == self.C1 or cell.type == self.LAMININ or cell.type ==self.NC1:
                MMPc=fieldMMP[cell.xCOM,cell.yCOM,cell.zCOM]
                Ic=fieldI[cell.xCOM,cell.yCOM,cell.zCOM]
                if Ic>0.0005:
                    T1=(MMPc/Ic)
                    if T1>=var:
                        cell.type=self.C_LYSED
                        lysed_id.append(cell)

        for cell in lysed_id:
            cellDict=CompuCell.getPyAttrib(cell)
            if hasattr(cell,"mcsL")==True:
                cell.targetvolume-=0.005
                cell.lambdaVolume=20.0
            else:
                cellDict=CompuCell.getPyAttrib(cell)
                mcs = self.simulator.getStep()
                mcsL = mcs
                cellDict["mcsL"]=mcsL                            

        mcs=self.simulator.getStep()
        for cell in self.cellList:
            cellDict=CompuCell.getPyAttrib(cell)
            if cell.type==self.C_LYSED:
                for val in cellDict.items():
                    cd1=val[1]

                    if cell.type==self.C_LYSED and mcs==(cd1 +20):
                        cell.type=self.NC1
        
        
class MitosisSteppable(MitosisSteppableBase):
    def __init__(self,frequency=1):
        MitosisSteppableBase.__init__(self,frequency)

    def step(self,mcs):
        cells_to_divide=[]
        for cell in self.cellList:
            if cell.type==self.CANCER:
                if cell.volume>=30: #proliferation volume threshold
                    cells_to_divide.append(cell)
  
                
        for cell in cells_to_divide:
            self.divideCellRandomOrientation(cell)

        
    def updateAttributes(self):
        parentCell=self.mitosisSteppable.parentCell
        childCell=self.mitosisSteppable.childCell
        parentCell.targetVolume/=2.0
        childCell.targetVolume=parentCell.targetVolume
        childCell.lambdaVolume=parentCell.lambdaVolume
        childCell.type=self.CANCER
        parentCell.type=self.CANCER
          
class CellMotilitySteppable(SteppableBasePy):
    def __init__(self,frequency=1):
        SteppableBasePy.__init__(self,frequency)

    def start(self):
        # iterating over all cells in simulation        
        for cell in self.cellList:
            break 
            # Make sure ExternalPotential plugin is loaded
            # negative lambdaVecX makes force point in the positive direction
            cell.lambdaVecX=10.1*uniform(-0.5,0.5) # force component pointing along X axis 
            cell.lambdaVecY=10.1*uniform(-0.5,0.5) # force component pointing along Y axis 
#         cell.lambdaVecZ=0.0 # force component pointing along Z axis 
        
        
    def step(self,mcs):
        for cell in self.cellList:
            if cell.type == self.CANCER:            
                cell.lambdaVecX=10.1*uniform(-1.0,1.0) # force component pointing along X axis 
                cell.lambdaVecY=10.1*uniform(-1.0,1.0) # force component pointing along Y axis 
                # print 'cell.lambdaVecX=',cell.lambdaVecX,' cell.lambdaVecY=',cell.lambdaVecY


class SecretionSteppable(SecretionBasePy):
    def __init__(self,frequency=1):
        SecretionBasePy.__init__(self,frequency)
    def start(self):
        self.fieldNameMMP='MMP'
        self.fieldNameI='I'
    def step(self,mcs):
        global e
        MMPsecretor=self.getFieldSecretor("MMP")
        Isecretor=self.getFieldSecretor("I")
        GFsecretor=self.getFieldSecretor("GF")
        self.fieldNameMMP='MMP'
        self.fieldNameI='I'
        fieldMMP=CompuCell.getConcentrationField(self.simulator,self.fieldNameMMP)
        fieldI=CompuCell.getConcentrationField(self.simulator,self.fieldNameI)
        for cell in self.cellList:
            if cell.type==self.CANCER:
                x=random.randint(0,4)
                MMPc=fieldMMP[int(round(cell.xCOM)),int(round(cell.yCOM)),int(round(cell.zCOM))]
                Ic=fieldI[int(round(cell.xCOM)),int(round(cell.yCOM)),int(round(cell.zCOM))]
                if mcs>5:
                    A= 2-(2*(-MMPc+2*Ic))
                    I1=A
                else:
                    A=x
                    I1=x
                MMPsecretor.secreteOutsideCellAtBoundaryOnContactWith(cell,A,[self.C1])
                Isecretor.secreteOutsideCellAtBoundaryOnContactWith(cell,I1,[self.C1])

                MMPsecretor.secreteOutsideCellAtBoundaryOnContactWith(cell,A,[self.LAMININ])
                Isecretor.secreteOutsideCellAtBoundaryOnContactWith(cell,I1,[self.LAMININ])
                
                GFsecretor.uptakeInsideCell(cell,0.1,0.1)
                
            if cell.type==self.L_LYSED:
                GFsecretor.secreteInsideCell(cell,0.5)
                MMPsecretor.uptakeInsideCell(cell,1.0,1.0)
                Isecretor.uptakeInsideCell(cell,0.5,1.0)
            if cell.type==self.C_LYSED:
                GFsecretor.secreteInsideCellAtBoundary(cell,1.0)
                MMPsecretor.uptakeInsideCell(cell,1.5,1.0)
                Isecretor.uptakeInsideCell(cell,0.5,1.0)
            if cell.type==self.C1:
                GFsecretor.secreteInsideCellAtBoundaryOnContactWith(cell,2.5,[self.C_LYSED])


class OrientedConstraintSteppable(SteppableBasePy):
##jps## def __init__(self,frequency,_OGPlugin):
    def __init__(self,frequency):
        SteppableBasePy.__init__(self,frequency)
##jps## self.OGPlugin = _OGPlugin
        
    def start(self):
        for cell in self.cellList:
            if cell.type==self.C1:
                o=random.randint(2,10)
                print("\to:",o, "  math.cos(math.pi/o):",math.cos(math.pi / o))
                cell.lambdaVolume=500.0  # 20.0  JPS new change
                cell.targetVolume=cell.volume
                
##jps##         self.OGPlugin.setElongationAxis(cell, math.cos(math.pi / o), math.sin(math.pi / o)) # Here, we define the axis of elongatino.
##jps##         self.OGPlugin.setConstraintWidth(cell, 1.0) # And this function gives a 2 pixel width to each cell
##jps##         self.OGPlugin.setElongationEnabled(cell, True) # Make sure to enable or disable elongation in all cells

                self.orientedGrowthPlugin.setElongationAxis(cell, math.cos(math.pi / o), math.sin(math.pi / o)) # Here, we define the axis of elongatino.
                self.orientedGrowthPlugin.setConstraintWidth(cell, 1.0) # And this function gives a 2 pixel width to each cell
                self.orientedGrowthPlugin.setElongationEnabled(cell, True) # Make sure to enable or disable elongation in all cells


class DeathSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        SteppableBasePy.__init__(self, frequency)

    def step(self, mcs):
        global alpha
        global beta
        if mcs == 5000:  # Consider cell death later ???
            pass
        
            





