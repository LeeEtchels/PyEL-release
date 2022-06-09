"""
Functions called by MainFile.

Version 1.0 (29/03/22)
"""


import math
import datetime
import bisect
import random
import csv
import re
from scipy.interpolate import interp1d
import os
import numpy
from tkinter import messagebox
import tkinter.filedialog
import pandas as pd
from plotly.offline import plot
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def Rotate_2D(a, b, ang, direction):
    """
    Rotating contact points to 0degrees for visualisation.

    It is difficult to compare the 3d visualisations of the output contact
    tracks when the liners are at different orientations.
    The contact points therefore need to be rotated back to 0 degrees so
    that they can all be viewed side by side.

    :param a: DESCRIPTION
    :type a: TYPE
    :param b: DESCRIPTION
    :type b: TYPE
    :param ang: DESCRIPTION
    :type ang: TYPE
    :param direction: DESCRIPTION
    :type direction: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    ang *= direction
    a_rot = a * numpy.cos(ang) - b * numpy.sin(ang)
    b_rot = a * numpy.sin(ang) + b * numpy.cos(ang)
    return a_rot, b_rot


def ContactCalculator_AxisymPointCloud_IVT(CupData, LatMaxDynSep, AntMaxDynSep,
                                           LatSpringF, AntSpringF, ContactIts,
                                           HeadRad, CupOrient, LoadSections,
                                           AAFun, FEFun, IEFun, caseNum,
                                           ActivityTData, StartID, meshSize,
                                           CupGeomFile, startTime, CaseName,
                                           ActivityFile, LipAngle, linerPath,
                                           misc_dict):
    """
    Take inputs and solves for contact points, forces, and times.

    Parameters
    ----------
    CupData : list
        Liner geometry.
    LatMaxDynSep : float
        Lateral mismatch (mm).
    AntMaxDynSep : float
        Anterior mismatch (mm).
    LatSpringF : float
        Lateral spring stiffness (N/mm).
    AntSpringF : float
        Anterior spring stiffness (N/mm).
    ContactIts : int
        Number of separation positions to evaluate forces at.
    HeadRad : float
        Radius of the head (mm).
    CupOrient : list
        Rotation angles describing the cup orientation (radians).
    LoadSections : list
        Functions for each section of the load profile.
    AAFun : interp1d?
        Function describing Ab/Ad rotation through time.
    FEFun : interp1d?
        Function describing F/E rotation through time.
    IEFun : interp1d?
        Function describing I/E rotation through time.
    LoadType : string
        Description of the general load profile shape.
    caseNum : int
        Unique ID for each case.
    ActivityTData : list
        Load and motion data.
    StartID : int
        ID of the first point to search from for contact.
    meshSize : float
        Approximate point spacing of the point cloud (mm).
    CupGeomFile : string
        File path to the point cloud.
    startTime : datetime?
        Time that this case was started.
    CaseName : string
        Study name.
    ActivityFile : string
        file path to the load profile.
    LipAngle : float
        Rotation angle describing lip orientation (radians).
    linerPath: str
        File path for where to place the results in the directory.

    Returns
    -------
    ContactForceTimeList : list
        Contains each contact location and associated force and time.
    df : DataFrame
        Contains same data as ContactForceTimeList but in DataFrame format
    CaseNamePath : str
        Location for putting raw data and charts

    """
    # Setting inital location of head
    LatInc = LatMaxDynSep / ContactIts
    AntInc = AntMaxDynSep / ContactIts

    IncCount = 0
    vertd = 99999999
    ContactList = []
    Headers = ('Contact Point ID', 'Old Point ID', 'Nx', 'Ny', 'Nz', 'SNx',
               'SNy', 'SNz', 'Anterior Mismatch', 'Lateral Mismatch',
               'Location', 'Edge?')
    ContactList.append(Headers)
    CPointID = 1

    LatMM = (LatMaxDynSep - IncCount * LatInc)
    AntMM = (AntMaxDynSep - IncCount * AntInc)

    hour = datetime.datetime.now().hour
    mins = datetime.datetime.now().minute
    sec = datetime.datetime.now().second
    time = str(hour) + ':' + str(mins) + ':' + str(sec)
    print('Done setting the initial head location' + ': ' + time)

    if AntMaxDynSep < 0:
        AntMMCheck = AntMM * (-1)
        AntCheckInc = AntInc * (-1)
    else:
        AntMMCheck = AntMM
        AntCheckInc = AntInc

    CupData = CupData[0]
    OldPIDSortedCupData = sorted(CupData, key=lambda x: x[1])
    JustPointsIDs = [row[1] for row in OldPIDSortedCupData]
    OldCP = StartID
    while (LatMM >= 0) and (AntMMCheck >= 0):
        hc = ((AntMaxDynSep - (IncCount * AntInc)), -100, (LatMaxDynSep
                                                           - (IncCount
                                                              * LatInc)))
        hx = hc[0]
        hy = hc[1]
        hz = hc[2]
        i = 0
        improved = 'Y'
        BestPoint = 0
        vertdbest = 999999
        i = bisect.bisect_left(JustPointsIDs, OldCP)
        point = CupData[i]
        Nbrs = point[10]
        while improved == 'Y':
            improved = 'N'
            TestList = []
            for line in Nbrs:
                TestList.append(line)
                index = bisect.bisect_left(JustPointsIDs, line)
                PointID = CupData[index][1]
                Nbrs2 = CupData[index][10]
                for i in Nbrs2:
                    if i not in TestList:
                        TestList.append(i)
            BestNeighbours = []
            for line in TestList:
                index = bisect.bisect_left(JustPointsIDs, line)
                PointID = CupData[index][1]
                Nx = CupData[index][2]
                Ny = CupData[index][3]
                Nz = CupData[index][4]
                SNx = CupData[index][5]
                SNy = CupData[index][6]
                SNz = CupData[index][7]
                Location = CupData[index][8]
                Edge = CupData[index][9]
                xd = Nx - hx
                zd = Nz - hz
                totald = math.sqrt(math.pow(xd, 2) + math.pow(zd, 2))
                overH = 'Y'
                if totald <= HeadRad:
                    yhead = (math.sqrt(math.pow(HeadRad, 2)
                             - math.pow(Nx - hx, 2)
                             - math.pow(Nz - hz, 2))) + hy
                    vertd = Ny - yhead
                else:
                    vertd = 999999
                    overH = 'N'
                if (vertd < vertdbest) and (overH == 'Y'):
                    vertdbest = vertd
                    BestPoint = PointID
                    NxBest = Nx
                    NyBest = Ny
                    NzBest = Nz
                    SNxBest = SNx
                    SNyBest = SNy
                    SNzBest = SNz
                    LocationBest = Location
                    EdgeBest = Edge
                    index = bisect.bisect_left(JustPointsIDs, BestPoint)
                    BestNeighbours = CupData[index][10]
                    improved = 'Y'
                elif overH == 'N':
                    if BestNeighbours == []:
                        Neighbours = CupData[index][10]
                        distBest = HeadRad * 2
                        for nbr in Neighbours:
                            index2 = bisect.bisect_left(JustPointsIDs, nbr)
                            Nx = CupData[index2][2]
                            Nz = CupData[index2][4]
                            dist = math.sqrt(math.pow(AntMM - Nx, 2)
                                             + math.pow(LatMM - Nz, 2))
                            if dist < distBest:
                                BestNeighbours = CupData[index2][10]
                                distBest = dist
                        improved = 'Y'
                    else:
                        rge = len(CupData)
                        BestNeighbours = CupData[random.randint(
                            0, rge - 1)][10]
                        improved = 'Y'
            Nbrs = BestNeighbours

        OldCP = BestPoint
        if AntMaxDynSep < 0:
            AntMMCheck = AntMM * (-1)
            AntCheckInc = AntInc * (-1)
        else:
            AntMMCheck = AntMM
            AntCheckInc = AntInc
        AntMMCheck = AntMMCheck - AntCheckInc
        ContactList.append((CPointID, BestPoint, NxBest, NyBest, NzBest,
                            SNxBest, SNyBest, SNzBest, AntMM, LatMM,
                            LocationBest, EdgeBest))
        vertd = 99999999
        CPointID = CPointID + 1
        IncCount = IncCount + 1
        LatMM = (LatMaxDynSep - (IncCount * LatInc))
        AntMM = (AntMaxDynSep - (IncCount * AntInc))

    ContactForceList = []
    Headers = ('Contact Point ID', 'Old Point ID', 'Nx', 'Ny', 'Nz', 'SNx',
               'SNy', 'SNz', 'Anterior Mismatch', 'Lateral Mismatch',
               'Location', 'Edge?', 'AxialForce', 'ResultantForce')
    ContactForceList.append(Headers)

    # Calculating the force associated with each contact point
    for line in ContactList:
        if line[0] == 'Contact Point ID':
            pass
        else:
            CPID = line[0]
            OPID = line[1]
            Nx = line[2]
            Ny = line[3]
            Nz = line[4]
            SNx = line[5]
            SNy = line[6]
            SNz = line[7]
            AM = line[8]
            LM = line[9]
            Location = line[10]
            Edge = line[11]
            Op = SNy
            A = math.sqrt(math.pow(SNx, 2) + math.pow(SNz, 2))
            angle1 = math.atan2(Op, A)
            MLF = (LatMaxDynSep - LM) * LatSpringF
            APF = (AntMaxDynSep - AM) * AntSpringF
            TF = math.sqrt(math.pow(APF, 2) + math.pow(MLF, 2))
            AF = abs(TF * math.tan(angle1))
            RF = math.sqrt(math.pow(TF, 2) + math.pow(AF, 2))
            ContactForceList.append((CPID, OPID, Nx, Ny, Nz, SNx, SNy, SNz, AM,
                                     LM, Location, Edge, AF, RF))

    # Calculating the time for each contact point
    ContactForceTimeList = TimePoints_IdealisedTwoPeak_AxisymPointCloud(
        LoadSections, ContactForceList)
    TimeList = []
    for line in ContactForceTimeList[0]:
        if line[0] == 'Contact Point ID':
            pass
        else:
            T = line[14]
            TimeList.append(T)

    """
    Creating points between the end of toe off and the beginning of heel
    strike, where the unadjusted contact point doesn't change but time passes
    and therefore the head rotates to different positions.
    """
    if len(TimeList) != 0:
        MaxTime = max(TimeList)
        if MaxTime < max(ActivityTData):
            diff = max(ActivityTData) - MaxTime
            increment = diff / 10
            i = 1
            CPID1 = CPointID
            OPID = ContactForceTimeList[0][-1][1]
            Nx = ContactForceTimeList[0][-1][2]
            Ny = ContactForceTimeList[0][-1][3]
            Nz = ContactForceTimeList[0][-1][4]
            SNx = ContactForceTimeList[0][-1][5]
            SNy = ContactForceTimeList[0][-1][6]
            SNz = ContactForceTimeList[0][-1][7]
            AM = ContactForceTimeList[0][-1][8]
            LM = ContactForceTimeList[0][-1][9]
            Loc = ContactForceTimeList[0][-1][10]
            Edge = ContactForceTimeList[0][-1][11]
            AF = ContactForceTimeList[0][-1][12]
            RF = ContactForceTimeList[0][-1][13]
            while i <= 10:
                T = MaxTime + (increment * i)
                CPID = (CPID1 + i)
                ContactForceTimeList[0].append((CPID, OPID, Nx, Ny, Nz, SNx,
                                                SNy, SNz, AM, LM, Loc, Edge,
                                                AF, RF, T))
                i = i + 1

    TidiedCFTL = {'Contact Point ID': [], 'Old Point ID': [], 'Nx': [],
                  'Ny': [], 'Nz': [], 'SNx': [], 'SNy': [], 'SNz': [],
                  'Anterior Mismatch': [], 'Lateral Mismatch': [],
                  'Location': [], 'Edge?': [], 'Axial Force (N)': [],
                  'ResultantForce': [], 'Time (s)': []}

    maxNumRegions = 0
    for line in ContactForceTimeList[0]:
        if line[0] == 'Contact Point ID':
            pass
        else:
            Loc = line[10]
            if type(Loc) == str:
                Loc = [Loc]
            numRegions = len(Loc)
            if numRegions > maxNumRegions:
                maxNumRegions = numRegions
    for line in ContactForceTimeList[0]:
        if line[0] == 'Contact Point ID':
            pass
        else:
            Loc = line[10]
            if type(Loc) == str:
                Loc = [Loc]
            while len(Loc) < maxNumRegions:
                Loc.append('NA')
            TidiedCFTL['Contact Point ID'].append(line[0])
            TidiedCFTL['Old Point ID'].append(line[1])
            TidiedCFTL['Nx'].append(line[2])
            TidiedCFTL['Ny'].append(line[3])
            TidiedCFTL['Nz'].append(line[4])
            TidiedCFTL['SNx'].append(line[5])
            TidiedCFTL['SNy'].append(line[6])
            TidiedCFTL['SNz'].append(line[7])
            TidiedCFTL['Anterior Mismatch'].append(line[8])
            TidiedCFTL['Lateral Mismatch'].append(line[9])
            TidiedCFTL['Location'].append(Loc)
            TidiedCFTL['Edge?'].append(line[11])
            TidiedCFTL['Axial Force (N)'].append(line[12])
            TidiedCFTL['ResultantForce'].append(line[13])
            TidiedCFTL['Time (s)'].append(line[14])

    # For creating traces of contact points with relative size/colour
    PointCount = {}
    for item in TidiedCFTL['Old Point ID']:
        if item in PointCount:
            pass
        else:
            PointCount.update({item: (TidiedCFTL['Old Point ID'].count(item))})

    # Conversion to DataFrame for Plotly plotting
    Contact_df = pd.DataFrame(TidiedCFTL)

    # Adding point_count to DataFrame
    length = [0] * len(Contact_df['Nx'])
    Contact_df.insert(2, "point_count", length, True)
    for key, value in PointCount.items():
        filt = Contact_df['Old Point ID'] == key
        Contact_df.loc[filt, 'point_count'] = value

    time = datetime.datetime.now()
    runTime = time - startTime
    runTime = runTime.total_seconds()

    # Manages if this is a copy of another file
    if 'copy_num' in misc_dict:
        CaseName = CaseName + '(' + str(misc_dict['copy_num']) + ')'

    # Insertion of raw data into correct location
    if linerPath[-4] == '.':
        linerPath = linerPath[:-4]
    if not os.path.exists(linerPath + '\\' + CaseName):
        os.makedirs(linerPath + '\\' + CaseName)
    if not os.path.exists(linerPath + '\\' + CaseName + '\\Raw Data'):
        os.makedirs(linerPath + '\\' + CaseName + '\\Raw Data')

    CaseNamePath = linerPath + '\\' + CaseName

    OutputFile = (CaseNamePath + '\\Raw Data\\'
                  + str(caseNum) + '_' + CaseName + '_Results.txt')

    # Writes file with headers only
    output = open(OutputFile, 'w')
    line = ('Axisym Geom, PointCloud = ' + str(CupGeomFile) + ', HeadRad = '
            + str(HeadRad) + ', I/V/T = ' + str(math.degrees(CupOrient[0]))
            + '/' + str(math.degrees(CupOrient[1])) + '/'
            + str(math.degrees(CupOrient[2])) + ', Lip Angle = '
            + str(math.degrees(LipAngle)) + ', AM/AMK/LM/LMK = '
            + str(AntMaxDynSep) + '/' + str(AntSpringF) + '/'
            + str(LatMaxDynSep) + '/' + str(LatSpringF) + ', CupMeshSize = '
            + str(meshSize) + ', runtime = ' + str(runTime) + 's'
            + ', ActivityFile = ' + str(ActivityFile))
    output.write(str(line) + '\n')
    output.close()

    # Appends data into .csv fle created above (efficiency measure)
    Contact_df.to_csv(OutputFile, mode='a', index=False)

    return [ContactForceTimeList], Contact_df, CaseNamePath


def CupGeom_AxisymPointCloud(geomFile, HeadRad):
    """
    Read in point cloud text file, formats it, and exports as list.

    Parameters
    ----------
    geomFile : string
        File path to the point cloud geometry file.
    HeadRad : float or 'd'
        Radius of the head, if 'd' read the default radius from geomFile.

    Returns
    -------
    list
        list[0] is a list of the geometry data, list[1] is the head radius.

    """
    try:
        file = open(geomFile, 'r')
    except FileNotFoundError:
        print('Could not open file. Please check that the file name and '
              'directory path are correct inside the config folder Settings '
              'file.')
    inputData = file.readlines()
    lengthData = len(inputData)
    outData = []
    for i in range(0, lengthData):
        if i == 0:
            if HeadRad == 'd':
                row = inputData[i]
                row1 = row.split("=")
                HeadRad = int(row1[1][1:3])
            else:
                continue
        else:
            row = inputData[i]
            row1 = row.split('[')
            row2 = row1[0].split('(')
            row3 = row2[1].split(',')
            NodeID = int(row3[0])
            Nx = float(row3[1])
            Ny = float(row3[2])
            Nz = float(row3[3])
            SNx = float(row3[4])
            SNy = float(row3[5])
            SNz = float(row3[6])
            row4 = (row1[1].split(']'))
            Location = row4[0].replace("'", "")
            Loc = Location.split(',')
            Location = []
            for loc in Loc:
                loc.replace(" ", "")
                Location.append(loc)
            if len(Location) == 2:
                boundary_location = 'Yes'
            else:
                boundary_location = 'No'
            row5 = row4[1].split(',')
            Edge = row5[1].replace('"', '').replace(' ', '').replace("'", '')
            row6 = row1[2].split(']')
            row7 = row6[0].split(',')
            numNeighbours = len(row7)
            Neighbours = []
            for j in range(0, numNeighbours):
                Neighbours.append(float(row7[j]))
            line = [NodeID, Nx, Ny, Nz, SNx, SNy, SNz, Location, Edge,
                    Neighbours, boundary_location]

            outData.append(line)

    file.close()

    return [outData, HeadRad]


def CupRotation_IVTseq_AxisymPointCloud(sin_Lip, cos_Lip, sin_Inc, cos_Inc,
                                        sin_Ver, cos_Ver, sin_Tilt, cos_Tilt,
                                        CupData, LipAngle_degrees,
                                        CupIncAngle_degrees,
                                        CupAVersionAngle_degrees,
                                        CupOVersionAngle_degrees):
    """
    Rotates cup data around the AP, SI, and ML axes.

    The rotations are applied sequentially. Note that this release is not
    designed to work with version rotations so only inclinations should be
    used.

    Parameters
    ----------
    sin_Lip : float
        Sine of the lip rotation angle in radians.
    cos_Lip : float
        Cosine of the lip rotation angle in radians.
    sin_Inc : float
        Sine of the inclination rotation angle in radians.
    cos_Inc : float
        Cosine of the inclination rotation angle in radians.
    sin_Ver : float
        Sine of the version rotation angle in radians.
    cos_Ver : float
        Cosine of the version rotation angle in radians.
    sin_Tilt : float
        Sine of the tilt rotation angle in radians.
    cos_Tilt : float
        Cosine of the tilt rotation angle in radians.
    CupData : list
        Cup geometry data.
    LipAngle_degrees : float
        lip rotation angle in degrees.
    CupIncAngle_degrees : float
        Inclination angle in degrees.
    CupAVersionAngle_degrees : float
        Version angle in degrees.
    CupOVersionAngle_degrees : float
        Tilt angle in degrees.

    Returns
    -------
    list
        list[0] = rotated cup geometry, list[1] = rotated edge points only.

    """
    CupDataRotated = []
    EdgeListRotated = []
    justIDs = []
    EdgeListRotated.append(['NodeID', 'Nx3', 'Ny3', 'Nz3', 'SNx3', 'SNy3',
                            'SNz3', 'Location', 'EdgeNeighbours'])
    for line in CupData:
        if line[0] == 'NodeID':
            CupDataRotated.append(line)
        else:
            NodeID = line[0]
            Nx = line[1]
            Ny = line[2]
            Nz = line[3]
            SNx = line[4]
            SNy = line[5]
            SNz = line[6]
            Location = line[7]
            Edge = line[8]
            Neighbours = line[9]
            if abs(LipAngle_degrees) != 0:
                Nxi = Nx * cos_Lip - Nz * sin_Lip
                Nyi = Ny
                Nzi = Nx * sin_Lip + Nz * cos_Lip
                SNxi = SNx * cos_Lip - SNz * sin_Lip
                SNyi = SNy
                SNzi = SNx * sin_Lip + SNz * cos_Lip
            else:
                Nxi = Nx
                Nyi = Ny
                Nzi = Nz
                SNxi = SNx
                SNyi = SNy
                SNzi = SNz
            if abs(CupIncAngle_degrees) != 0:
                Nx1 = Nxi
                Ny1 = Nzi * sin_Inc + Nyi * cos_Inc
                Nz1 = Nzi * cos_Inc - Nyi * sin_Inc
                SNx1 = SNxi
                SNy1 = SNzi * sin_Inc + SNyi * cos_Inc
                SNz1 = SNzi * cos_Inc - SNyi * sin_Inc
            else:
                Nx1 = Nxi
                Ny1 = Nyi
                Nz1 = Nzi
                SNx1 = SNxi
                SNy1 = SNyi
                SNz1 = SNzi
            if abs(CupAVersionAngle_degrees) != 0:
                Nx2 = Nx1 * cos_Ver - Nz1 * sin_Ver
                Ny2 = Ny1
                Nz2 = Nx1 * sin_Ver + Nz1 * cos_Ver
                SNx2 = SNx1 * cos_Ver - SNz1 * sin_Ver
                SNy2 = SNy1
                SNz2 = SNx1 * sin_Ver + SNz1 * cos_Ver
            else:
                Nx2 = Nx1
                Ny2 = Ny1
                Nz2 = Nz1
                SNx2 = SNx1
                SNy2 = SNy1
                SNz2 = SNz1
            if abs(CupOVersionAngle_degrees) != 0:
                Nx3 = Nx2 * cos_Tilt - Ny2 * sin_Tilt
                Ny3 = Nx2 * sin_Tilt + Ny2 * cos_Tilt
                Nz3 = Nz2
                SNx3 = SNx2 * cos_Tilt - SNy2 * sin_Tilt
                SNy3 = SNx2 * sin_Tilt + SNy2 * cos_Tilt
                SNz3 = SNz2
            else:
                Nx3 = Nx2
                Ny3 = Ny2
                Nz3 = Nz2
                SNx3 = SNx2
                SNy3 = SNy2
                SNz3 = SNz2
            CupDataRotated.append([NodeID, Nx3, Ny3, Nz3, SNx3, SNy3, SNz3,
                                   Location, Edge, Neighbours])
            justIDs.append(NodeID)
    hour = datetime.datetime.now().hour
    mins = datetime.datetime.now().minute
    sec = datetime.datetime.now().second
    time = str(hour) + ':' + str(mins) + ':' + str(sec)
    print('Done rotating the cup into its final position' + ': ' + time)
    for l in CupDataRotated:
        Edge = l[8]
        if Edge == 'Y':
            eN = []
            NodeID = l[0]
            neighbours = l[9]
            Nx3 = l[1]
            Ny3 = l[2]
            Nz3 = l[3]
            SNx3 = l[4]
            SNy3 = l[5]
            SNz3 = l[6]
            Location = l[7]
            for n in neighbours:
                i = bisect.bisect_left(justIDs, n)
                if ((CupDataRotated[i + 1][8] == 'Y') and (
                        int(CupDataRotated[i + 1][0]) == int(n))):
                    eN.append(n)
            EdgeListRotated.append([NodeID, Nx3, Ny3, Nz3, SNx3, SNy3, SNz3,
                                    Location, eN])

    return [CupDataRotated, EdgeListRotated]


def Inputs_JobList(JobFile):
    """
    Read an input job list to set up the range of cases to be analysed.

    Parameters
    ----------
    JobFile : string
        File path to the job list.

    Returns
    -------
    list
        A list of lists, each index corresponds to all values of one variable
        across all cases.

    """
    CupIncAngleList = []
    CupAVersionAngleList = []
    CupOVersionAngleList = []
    HeadRadList = []
    LatMaxDynSepList = []
    AntMaxDynSepList = []
    LatSpringFList = []
    AntSpringFList = []
    ActivityFileList = []
    CupLipAngleList = []

    with open(JobFile, 'rt') as csvfile:
        fileread = csv.reader(csvfile, dialect=csv.excel)
        FirstLine = 1
        for row in fileread:
            if FirstLine == 1:
                h1 = row[0]
                FirstLine = 0
            elif (row[0] != '') and (h1 == 'case_num'):
                if os.path.isdir(row[8]):
                    for filename in os.listdir(row[8]):
                        CupIncAngleList.append(float(row[1]))
                        CupAVersionAngleList.append(float(row[2]))
                        CupOVersionAngleList.append(float(row[3]))
                        if (row[4][0] == 'dflt'):
                            HeadRadList.append('d')
                        else:
                            HeadRadList.append(float(row[4]))
                        LatMaxDynSepList.append(float(row[5]))
                        AntMaxDynSepList.append(float(row[6]))
                        LatSpringFList.append(float(row[7]))
                        AntSpringFList.append(float(row[8]))
                        ActivityFileList.append(row[9] + '\\' + filename)
                        CupLipAngleList.append(float(row[10]))
                else:
                    CupIncAngleList.append(float(row[1]))
                    CupAVersionAngleList.append(float(row[2]))
                    CupOVersionAngleList.append(float(row[3]))
                    if (row[4][0] == 'd') or (row[4][0] == 'D'):
                        HeadRadList.append('d')
                    else:
                        HeadRadList.append(float(row[4]))
                    LatMaxDynSepList.append(float(row[5]))
                    AntMaxDynSepList.append(float(row[6]))
                    LatSpringFList.append(float(row[7]))
                    AntSpringFList.append(float(row[8]))
                    ActivityFileList.append(row[9])
                    CupLipAngleList.append(float(row[10]))
    if max(CupAVersionAngleList) != 0:
        print('Warning: non-zeo anteversion angles recorded. These'
              ' will not be used in this PyEL release')
    if max(CupOVersionAngleList) != 0:
        print('Warning: non-zeo operative version angles recorded. These'
              ' will not be used in this PyEL release')
    if max(AntMaxDynSepList) != 0:
        print('Warning: non-zeo anterior mismatches recorded. These'
              ' will not be used in this PyEL release')
    if max(CupLipAngleList) != 0:
        print('Warning: non-zeo lip angles recorded. These'
              ' will not be used in this PyEL release')

    return [CupIncAngleList, CupAVersionAngleList, CupOVersionAngleList,
            HeadRadList, LatMaxDynSepList, AntMaxDynSepList, LatSpringFList,
            AntSpringFList, ActivityFileList, CupLipAngleList]


def Load_IdealisedTwoPeak(ActivityData):
    """
    Generate functions from parts of a two peak load profile.

    Identifies the start and end of each region in the load profile and
    creates functions that can be used to interpolate the times at which a
    given load occurs.

    Parameters
    ----------
    ActivityData : list
        Load profile.

    Returns
    -------
    list
        List of interpolation functions, one function per load section.

    """
    # Defining the start and end of each load section.
    i = 1
    minLoad1 = ActivityData[1][0]

    check = 0
    while check != 1:
        Load = ActivityData[1][i]
        pastLoad = ActivityData[1][i - 1]
        if Load >= pastLoad:
            i = i + 1
        else:
            maxLoad1 = pastLoad
            section1End = i - 1
            check = 1
    i = section1End + 1
    check = 0
    while check != 1:
        Load = ActivityData[1][i]
        pastLoad = ActivityData[1][i - 1]
        if Load < pastLoad:
            i = i + 1
        else:
            minLoad2 = pastLoad
            section2End = i - 1
            check = 1
    i = section2End + 1
    check = 0
    while check != 1:
        Load = ActivityData[1][i]
        pastLoad = ActivityData[1][i - 1]
        if Load > pastLoad:
            i = i + 1
        else:
            maxLoad2 = pastLoad
            section3End = i - 1
            check = 1
    i = section3End + 1
    check = 0
    while check != 1:
        Load = ActivityData[1][i]
        pastLoad = ActivityData[1][i - 1]
        if Load < pastLoad:
            i = i + 1
        else:
            minLoad3 = pastLoad
            section4End = i - 1
            check = 1

    # Creating data lists of force vs time for each individual load section.
    Section1Time = []
    Section1Force = []
    Section2Time = []
    Section2Force = []
    Section3Time = []
    Section3Force = []
    Section4Time = []
    Section4Force = []

    i = 0
    while i <= section4End:
        if i < section1End:
            Section1Time.append(ActivityData[0][i])
            Section1Force.append(ActivityData[1][i])
            i = i + 1
        elif i == section1End:
            Section1Time.append(ActivityData[0][i])
            Section1Force.append(ActivityData[1][i])
            Section2Time.append(ActivityData[0][i])
            Section2Force.append(ActivityData[1][i])
            i = i + 1
        elif i < section2End:
            Section2Time.append(ActivityData[0][i])
            Section2Force.append(ActivityData[1][i])
            i = i + 1
        elif i == section2End:
            Section2Time.append(ActivityData[0][i])
            Section2Force.append(ActivityData[1][i])
            Section3Time.append(ActivityData[0][i])
            Section3Force.append(ActivityData[1][i])
            i = i + 1
        elif i < section3End:
            Section3Time.append(ActivityData[0][i])
            Section3Force.append(ActivityData[1][i])
            i = i + 1
        elif i == section3End:
            Section3Time.append(ActivityData[0][i])
            Section3Force.append(ActivityData[1][i])
            Section4Time.append(ActivityData[0][i])
            Section4Force.append(ActivityData[1][i])
            i = i + 1
        elif i < section4End:
            Section4Time.append(ActivityData[0][i])
            Section4Force.append(ActivityData[1][i])
            i = i + 1
        else:
            i = i + 1
    k = -1
    CurrentLoad = ActivityData[1][k]

    while CurrentLoad == minLoad3:
        k = k - 1
        CurrentLoad = ActivityData[1][k]

    Section4Time.append(ActivityData[0][k + 1])
    Section4Force.append(ActivityData[1][k + 1])

    # Creating functions for the different load sections.
    Section1Fun = interp1d(Section1Force, Section1Time, kind='linear')
    Section2Fun = interp1d(Section2Force, Section2Time, kind='cubic')
    Section3Fun = interp1d(Section3Force, Section3Time, kind='cubic')
    Section4Fun = interp1d(Section4Force, Section4Time, kind='linear')
    minLoad = min(ActivityData[1])
    LoadSections = [minLoad1, maxLoad1, minLoad2, maxLoad2, minLoad3, minLoad]
    return [Section1Fun, Section2Fun, Section3Fun, Section4Fun, LoadSections]


def ReadActivity(ActivityFile):
    """
    Read the provided load activity file and formats the data for the solver.

    Parameters
    ----------
    ActivityFile : string
        File path to the load profile.

    Returns
    -------
    ActivityData : list
        Force and rotation data with time for the load profile.
    """
    ActTData = []
    ActFData = []
    ActAAData = []
    ActFEData = []
    ActIEData = []

    with open(ActivityFile, 'rt') as csvfile:
        fileread = csv.reader(csvfile, dialect=csv.excel)
        rowcount = 1
        Continue = 1
        for row in fileread:
            if rowcount == 1:
                if row[0] != ('Data formatted for PyEL Edge Loading Geometric '
                              + 'Model'):
                    print('Error, Activity profile data file provided does \
                        not have correct header information')
                    Continue = 0
                    # from PyEL_Functions import ReadActivity_Fail
                    ActivityData = ReadActivity_Fail()
            if rowcount == 2:
                if Continue == 1:
                    if row != ['Time (s)', 'Axial Force (N)', 'AA (degrees)',
                               'FE (degrees)', 'IE (degrees)']:
                        print('Error, Activity profile data file provided \
                              does not have correct column title information')
                        Continue = 0
                        # from PyEL_Functions import ReadActivity_Fail
                        ActivityData = ReadActivity_Fail()
            if rowcount > 2:
                if Continue == 1:
                    ActTData.append(float(row[0]))
                    ActFData.append(float(row[1]))
                    ActAAData.append(math.radians(float(row[2])))
                    ActFEData.append(math.radians(float(row[3])))
                    ActIEData.append(math.radians(float(row[4])))
            rowcount = rowcount + 1
    if Continue == 1:
        ActivityData = [ActTData, ActFData, ActAAData, ActFEData, ActIEData]
    return ActivityData


def ReadActivity_Fail():
    """
    Call if ReadActivity failed.

    Gives the user an opportunity to correct the activity file or path before
    the analysis fails.

    Returns
    -------
    ActivityData : list
        Force and rotation data with time for the load profile.

    """
    ActTData = []
    ActFData = []
    ActAAData = []
    ActFEData = []
    ActIEData = []

    #root = tkinter.Tk() # TODO Check if this is actually needed.
    cdir = os.getcwd()
    ActivityFile = tkinter.filedialog.askopenfilename(
        filetypes=(("CSV files", "*.csv"), ("Spreadsheets", "*.xlsx;*.xls;*.\
        xlsm"), ("Text files", "*.txt")), initialdir=cdir,
        title='Please select the csv file including the activity profile \
        data in the required format')
    with open(ActivityFile, 'rt') as csvfile:
        fileread = csv.reader(csvfile, dialect=csv.excel)
        rowcount = 1
        for row in fileread:
            if rowcount == 1:
                if row[0] != ('Data formatted for PyEL Edge Loading '
                              + 'Geometric Model'):
                    print('Error, Activity profile data file provided does \
                        not have correct header information')
            if rowcount == 2:
                if row != ['Time (s)', 'Axial Force (N)', 'AA (degrees)',
                           'FE (degrees)', 'IE (degrees)']:
                    print('Error, Activity profile data file provided \
                          does not have correct column title information')
            if rowcount > 2:
                ActTData.append(float(row[0]))
                ActFData.append(float(row[1]))
                ActAAData.append(math.radians(float(row[2])))
                ActFEData.append(math.radians(float(row[3])))
                ActIEData.append(math.radians(float(row[4])))
        rowcount = rowcount + 1
    ActivityData = [ActTData, ActFData, ActAAData, ActFEData, ActIEData]
    return ActivityData


def RemoveCupPoints_AxisymPointCloud(CupData, LatMaxDynSep, AntMaxDynSep,
                                     CupIncAngle, CupAVersionAngle,
                                     CupOVersionAngle, CupFilletRad,
                                     CupMeshSize):
    """
    Remove unnecessary cup points from the cup data.

    Some points in the cup data are not going to be contacted due to their
    position once the rotations are applied. These are removed so that
    they do not later slow down the contact searches and to minimise
    memory usage.

    Parameters
    ----------
    CupData : list
        Liner geometry.
    LatMaxDynSep : float
        Lateral mismatch (mm).
    AntMaxDynSep : float
        Anterior mismatch (mm).
    CupIncAngle : float
        liner inclination rotation angle in radians.
    CupAVersionAngle : float
        Liner version rotation angle in radians.
    CupOVersionAngle : float
        Liner tilt rotation angle in radians.
    CupFilletRad : float
        Assumed to be 2mm in current version.
    StripeWearEstimator : string
        'Y' or 'N' identifying whether stripe wear region is requested.
    CupMeshSize : float
        Approximate point spacing of the liner point cloud.

    Returns
    -------
    list
        list[0] = reduced size cup data with correct neighbouring points info,
        list[1] = point ID of a point on the edge in the direction of the
        spring force.

    """
    # Finding the angle to the maximum mismatch head location.

    EdgeList = CupData[1]
    CupData = CupData[0]
    baseline = ((0, 0), (0, -1))
    mismatchline = ((0, 0), (AntMaxDynSep, LatMaxDynSep))
    u1 = baseline[1][0] - baseline[0][0]
    u2 = baseline[1][1] - baseline[0][1]
    v1 = mismatchline[1][0] - mismatchline[0][0]
    v2 = mismatchline[1][1] - mismatchline[0][1]
    dotproductuv = (u1 * v1 + u2 * v2)
    umag = math.sqrt(math.pow(u1, 2) + math.pow(u2, 2))
    vmag = math.sqrt(math.pow(v1, 2) + math.pow(v2, 2))
    dotproductuvmag = numpy.dot(umag, vmag)
    AngleToHeadCentre = numpy.arccos(dotproductuv / dotproductuvmag)

    SPoint = EdgeList[1]
    PointID = SPoint[0]
    x = SPoint[1]
    y = SPoint[2]
    z = SPoint[3]
    Neighbours = SPoint[8]
    CurrentMinAngle = 9999999
    CurrentBestAngle = CurrentMinAngle
    CurrentBestPoint = PointID
    LastPoint = PointID
    CurrentTargetY = y
    v1 = x
    v2 = z
    dotproductuv = (u1 * v1 + u2 * v2)

    umag = math.sqrt(math.pow(u1, 2) + math.pow(u2, 2))
    vmag = math.sqrt(math.pow(v1, 2) + math.pow(v2, 2))

    dotproductuvmag = numpy.dot(umag, vmag)

    # Iterating through the list of edge points around the rim to find the one
    # closest to the head centre location (in terms of the angle in the
    # transverse plane)

    AngleToCurrentPoint = numpy.arccos(dotproductuv / dotproductuvmag)
    CurrentMinAngle = abs(AngleToHeadCentre - AngleToCurrentPoint)
    CurrentBestAngle = CurrentMinAngle
    endFlag = 0
    JustValsEdgeList = [row[0] for row in EdgeList]
    JustValsEdgeList = JustValsEdgeList[1:]
    while endFlag == 0:
        for point in Neighbours:
            if point != LastPoint:
                PointID = point
                index = bisect.bisect_left(JustValsEdgeList, PointID)
                x = EdgeList[index + 1][1]
                y = EdgeList[index + 1][2]
                z = EdgeList[index + 1][3]
                CurrentNeighbours = EdgeList[index + 1][8]
                v1 = x
                v2 = z
                dotproductuv = (u1 * v1 + u2 * v2)
                umag = math.sqrt(math.pow(u1, 2) + math.pow(u2, 2))
                vmag = math.sqrt(math.pow(v1, 2) + math.pow(v2, 2))
                dotproductuvmag = numpy.dot(umag, vmag)
                AngleToCurrentPoint = numpy.arccos(dotproductuv
                                                   / dotproductuvmag)
                CurrentMinAngle = abs(AngleToHeadCentre - AngleToCurrentPoint)
                if CurrentMinAngle < CurrentBestAngle:
                    CurrentBestAngle = CurrentMinAngle
                    CurrentBestPoint = PointID
                    NextNeighbours = CurrentNeighbours
                    CurrentTargetY = y
        if CurrentBestPoint == LastPoint:
            TargetPointy = CurrentTargetY
            endFlag = 1
        else:
            Neighbours = NextNeighbours
            LastPoint = CurrentBestPoint
    StartID = CurrentBestPoint

    # Finding the height of the point on the rim that is in the direction
    # of the cup and using that to select an appropriate cut off point, below
    # which all points are removed.

    ReducedCupList = []
    NewPointID = 1
    ReducedCupList.append(('New Point ID', 'Old Point ID', 'Nx', 'Ny', 'Nz',
                           'SNx', 'SNy', 'SNz', 'Location', 'Edge?',
                           'Neighbours'))
    if TargetPointy < (3 + 2 * CupFilletRad):
        Cutoff = TargetPointy - 3 - (2 * CupFilletRad)
    else:
        Cutoff = 0
        print(True)
    for point in CupData:
        if point[0] == 'NodeID':
            pass
        else:
            PointID = point[0]
            Nx = point[1]
            Ny = point[2]
            Nz = point[3]
            SNx = point[4]
            SNy = point[5]
            SNz = point[6]
            Location = point[7]
            Edge = point[8]
            Neighbours = point[9]
            if (Ny >= Cutoff) and (Nz >= 0):
                ReducedCupList.append((NewPointID, PointID, Nx, Ny, Nz, SNx,
                                       SNy, SNz, Location, Edge, Neighbours))
                NewPointID = NewPointID + 1

    # If the stripe wear analysis is not used far fewer points are required. A
    # vertical plane is created between the head centre when fully mismatched
    # and the cup centre. The distance of each point from this plane is found
    # and any point that is far enough away that it will never be the contact
    # point is removed.

    PlaneCupList = []
    PlaneCupList.append(ReducedCupList[0])
    NewPointID = 1
    for i in ReducedCupList:
        if i[0] == 'New Point ID':
            pass
        else:
            x1 = i[2]
            y1 = i[3]
            z1 = i[4]
            x0 = AntMaxDynSep
            y0 = 0
            z0 = LatMaxDynSep
            p1 = (0, 0, 0)
            p2 = (AntMaxDynSep, 0, LatMaxDynSep)
            p3 = (0, 10, 0)
            p1tp2 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            p1tp3 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
            planeNormal = numpy.cross(p1tp2, p1tp3)
            A = planeNormal[0]
            B = planeNormal[1]
            C = planeNormal[2]
            D = (-A * x0) - (B * y0) - (C * z0)
            top = (A * x1) + (B * y1) + (C * z1) + D
            modtop = abs(top)
            bottom = math.pow(A, 2) + math.pow(B, 2) + math.pow(C, 2)
            sqrtbottom = math.sqrt(bottom)
            d = modtop / sqrtbottom
            if d <= (CupMeshSize * 10):
                PointID = i[1]
                Nx = i[2]
                Ny = i[3]
                Nz = i[4]
                SNx = i[5]
                SNy = i[6]
                SNz = i[7]
                Location = i[8]
                Edge = i[9]
                Neighbours = i[10]
                PlaneCupList.append((NewPointID, PointID, Nx, Ny, Nz,
                                     SNx, SNy, SNz, Location, Edge,
                                     Neighbours))
                NewPointID = NewPointID + 1
        ReducedCupList = PlaneCupList
    RemainingNodeIDs = [row[1] for row in ReducedCupList]
    RemainingNodeIDs.pop(0)
    UpdatedNeighboursList = []
    RemainingNodeIDs = set(RemainingNodeIDs)
    minRemainingNodeID = min(RemainingNodeIDs)
    maxRemainingNodeID = max(RemainingNodeIDs)

    # Updating the neighbour list to only include points that are still
    # included in the cup geometry.

    for line in ReducedCupList:
        if line[0] == 'New Point ID':
            pass
        else:
            NewNeighbours = []
            NewPointID = line[0]
            PointID = line[1]
            Nx = line[2]
            Ny = line[3]
            Nz = line[4]
            SNx = line[5]
            SNy = line[6]
            SNz = line[7]
            Location = line[8]
            Edge = line[9]
            Neighbours = line[10]
            for neighbour in Neighbours:
                if (neighbour >= minRemainingNodeID) and (
                        neighbour <= maxRemainingNodeID):
                    if neighbour in RemainingNodeIDs:
                        NewNeighbours.append(neighbour)
            UpdatedNeighboursList.append((NewPointID, PointID, Nx, Ny, Nz,
                                          SNx, SNy, SNz, Location, Edge,
                                          NewNeighbours))
    return [UpdatedNeighboursList, StartID]


def TimePoints_IdealisedTwoPeak_AxisymPointCloud(LoadSections,
                                                 ContactForceList):
    """
    Calculate time points for loads.

    Uses the load section interpolation to calculate the times associated
    with each axial load magnitude.

    Parameters
    ----------
    LoadSections : list
        Interpolation functions for each portion of the load profile.
    ContactForceList : list
        Contact positions and the calculated associated force.

    Returns
    -------
    list
        list[0] = contact locations, forces, and times. list[1] = string
        describing whether edge loading occured and what type.

    """
    ContactForceTimeList = []
    Headers = ('Contact Point ID', 'Old Point ID', 'Nx', 'Ny', 'Nz', 'SNx',
               'SNy', 'SNz', 'Anterior Separation', 'Lateral Separation',
               'Location1', 'Location2', 'Edge?', 'AxialForce',
               'ResultantForce', 'Time')
    ContactForceTimeList.append(Headers)
    minLoad1 = LoadSections[4][0]
    maxLoad1 = LoadSections[4][1]
    minLoad2 = LoadSections[4][2]
    maxLoad2 = LoadSections[4][3]
    minLoad3 = LoadSections[4][4]
    Section1Fun = LoadSections[0]
    Section2Fun = LoadSections[1]
    Section3Fun = LoadSections[2]
    Section4Fun = LoadSections[3]
    AF = 0
    AF2 = 0
    AF3 = 0
    ELType = ['No EL', 'Constant EL']
    tempT = 0

    for line in ContactForceList:
        location = line[10]
        if line[0] == 'Contact Point ID':
            pass
        else:
            AForce = line[12]
            if (AForce >= minLoad1) and (AForce <= maxLoad1):
                if tempT == 0:
                    if len(location) == 1:
                        location = [location[0], 'NA']
                    ContactForceTimeList.append((line[0], line[1], line[2],
                                                 line[3], line[4], line[5],
                                                 line[6], line[7], line[8],
                                                 line[9], location, line[11],
                                                 line[12], line[13], tempT))
                tempT = float(Section1Fun(AForce))
                if len(location) == 1:
                    location = [location[0], 'NA']
                ContactForceTimeList.append((line[0], line[1], line[2],
                                             line[3], line[4], line[5],
                                             line[6], line[7], line[8],
                                             line[9], location, line[11],
                                             line[12], line[13], tempT))
                if (location[0][:2] == 'EL') or (location[1][:2] == 'EL'):
                    ELType[0] = 'EL During Swing Phase'
                if (location[0][:2] != 'EL') and (location[0][:2] != 'EL'):
                    ELType[1] = 'Not constant EL'
                AF = AForce

    for line in reversed(ContactForceList):
        location = line[10]
        if line[0] == 'Contact Point ID':
            pass
        else:
            AForce2 = line[12]
            if (AForce2 >= minLoad2) and (AForce2 < maxLoad1):
                if AForce2 != AF:
                    tempT = float(Section2Fun(AForce2))
                    if len(location) == 1:
                        location = [location[0], 'NA']
                    ContactForceTimeList.append((line[0], line[1], line[2],
                                                 line[3], line[4], line[5],
                                                 line[6], line[7], line[8],
                                                 line[9], location, line[11],
                                                 line[12], line[13], tempT))
                    AF2 = AForce2
                    if (location[0][:2] == 'EL') or (location[1][:2] == 'EL'):
                        ELType[0] = 'EL During Stance Phase'
                else:
                    pass

    for line in ContactForceList:
        location = line[10]
        if line[0] == 'Contact Point ID':
            pass
        else:
            AForce3 = line[12]
            if (AForce3 > minLoad2) and (AForce3 <= maxLoad2):
                if AForce3 != AF2:
                    tempT = float(Section3Fun(AForce3))
                    if len(location) == 1:
                        location = [location[0], 'NA']
                    ContactForceTimeList.append((line[0], line[1], line[2],
                                                 line[3], line[4], line[5],
                                                 line[6], line[7], line[8],
                                                 line[9], location, line[11],
                                                 line[12], line[13], tempT))
                    AF3 = AForce3
                    if (location[0][:2] == 'EL') or (location[1][:2] == 'EL'):
                        ELType[0] = 'EL During Stance Phase'
                else:
                    pass

    for line in reversed(ContactForceList):
        location = line[10]
        if line[0] == 'Contact Point ID':
            pass
        else:
            AForce4 = line[12]
            if (AForce4 >= minLoad3) and (AForce4 < maxLoad2):
                if AForce4 != AF3:
                    tempT = float(Section4Fun(AForce4))
                    if len(location) == 1:
                        location = [location[0], 'NA']
                    ContactForceTimeList.append((line[0], line[1], line[2],
                                                 line[3], line[4], line[5],
                                                 line[6], line[7], line[8],
                                                 line[9], location, line[11],
                                                 line[12], line[13], tempT))
                    if (minLoad3 < minLoad1 and ELType[0] == 'No EL' and (
                            location[0][:2] == 'EL') or (
                                location[1][:2] == 'EL')):
                        ELType[0] = 'EL During Swing Phase'
                else:
                    pass
    return [ContactForceTimeList, ELType]


def create_fig_subplots(num_jobs, per_page, CaseName, caseNum):
    """
    Summary.

    Description

    :param num_jobs: DESCRIPTION
    :type num_jobs: TYPE
    :param per_page: DESCRIPTION
    :type per_page: TYPE
    :param CaseName: DESCRIPTION
    :type CaseName: TYPE
    :param caseNum: DESCRIPTION
    :type caseNum: TYPE
    :return: DESCRIPTION
    :rtype: TYPE

    """
    sub_titles = []
    fig_tot = numpy.ceil(num_jobs / per_page)
    for x in range(per_page):
        sub_titles.append(CaseName + str(caseNum + x))
    rows = int((per_page)**0.5)
    cols = int(numpy.ceil((per_page**0.5)))
    num_elems = rows * cols
    while num_elems < per_page:
        rows += 1
        num_elems = rows * cols
    specs = [[{"type": "scene"}] * cols] * rows
    fig = make_subplots(rows=rows, cols=cols, start_cell="top-left",
                        specs=specs, subplot_titles=tuple(sub_titles))

    return fig, fig_tot, rows, cols


def create_models(df, CupData_df, caseNum, graph_info, fig, CaseName, rows,
                  cols, row, col, fig_no, fig_tot, num_jobs, path):
    """
    Summary.

    Creation of 3D models of liner geometries. Overlaid is the edge boundary
    and the contact point location with associated force.

    Parameters
    ----------
    df : DataFrame
        Details of contact points: location; force etc..
    CupData_df : DataFrame
        Liner geometry information for 3D mesh plot.
    caseNum : int
        Case number for naming of model.
    graph_info : dict
        Information from Graph Control UI on what parameters are to be plotted,
        and how many models per file.
    specs : list
        List of list of dictionaries, equivalent to 2D array. Used to calibrate
        each cell created for the model file to allow multiple 3D plots.
    sub_titles : list
        Contains list of titles for each subplot.
    fig : plotly.graph_object
        Figure where each model is plotted.
    CaseName : str
        Name of the case being run, used for organisation and naming files.
    rows : int
        Max number of rows for fig.
    cols : int
        Max number of columns for fig.
    row : int
        Current row. Designates which cell the model will placed in.
    col : int
        Current column. Designates which cell the model will placed in.
    fig_no : int
        Counter for figures, used to name model files if more than one is
        created.
    fig_tot : int
        Number of files to be created.
    num_jobs : int
        Number of cases in job file. Used to check plotting within bounds of
        rows and columns.

    Returns
    -------
    row : int
        Current row. Designates which cell the model will placed in. Updated.
    col : int
        Current column. Designates which cell the model will placed in.
        Updated.
    fig_no : int
        Counter for figures, used to name model files if more than one is
        created. Updated.
    Geometry-Force 3D Mesh : .html file
        .html file of plotly interactive plot of geometry with contact points
        overlaid with associated force, for each case.

    NOTE: code for using point_count for force trace plot remains, replaces
    arbitrary size=2
    """
    # Projecting mesh and contact points onto 3D model
    # Reducing meshing to every tenth point
    Red_Cup_df = CupData_df.iloc[::30, :]
    trace1 = go.Mesh3d(x=Red_Cup_df['Nx'],
                       y=Red_Cup_df['Nz'],
                       z=Red_Cup_df['Ny'],
                       opacity=0.8,
                       hoverinfo='none',
                       color='rgb(253,193,199)')

    # Calibrating for force trace
    df = df.drop_duplicates(subset='Old Point ID', keep='first', inplace=False)
    if caseNum == 0:
        colorbar = dict(thickness=10, tickmode="auto", nticks=5, x=1.2)
    else:
        colorbar = None

    if graph_info['graph_force'] == 'Axial':
        force = df['Axial Force (N)']
        force_name = 'Axial Force (N)'
    elif graph_info['graph_force'] == 'Resultant':
        force = df['ResultantForce']
        force_name = 'Resultant Force (N)'

    trace2 = go.Scatter3d(x=df['Nx'],
                          y=df['Nz'],
                          z=df['Ny'],
                          mode='markers',
                          marker=dict(size=2,
                                      color=force,
                                      colorscale='Viridis',
                                      colorbar=colorbar,
                                      opacity=1),
                          name='Case' + str(caseNum),
                          text=force,
                          hovertemplate=force_name + ": %{text:.0f}",
                          showlegend=False)

    # Determining where the boundaries are for visual display
    filt = CupData_df['boundary_location'] == 'Yes'
    boundaries = CupData_df.loc[filt]

    trace3 = go.Scatter3d(x=boundaries['Nx'],
                          y=boundaries['Nz'],
                          z=boundaries['Ny'],
                          mode='markers',
                          marker=dict(
                              size=0.4,
                              color='black',
                              symbol='square',
                              opacity=0.6),
                          name='Edge Boundary',
                          text='Edge Boundary',
                          showlegend=False)

    # Check for which cell to use to plot 3D model
    if col <= cols and row <= rows:
        fig.add_trace(trace1, row=row, col=col)
        fig.add_trace(trace2, row=row, col=col)
        fig.add_trace(trace3, row=row, col=col)
        col += 1
    elif col > cols and row <= rows:
        row += 1
        col = 1
        fig.add_trace(trace1, row=row, col=col)
        fig.add_trace(trace2, row=row, col=col)
        fig.add_trace(trace3, row=row, col=col)
        col += 1

    # Adds traces to the same plot or creates new figure and plots traces
    # there.
    if col > cols and row == rows or caseNum + 1 == num_jobs or (
            caseNum + 2) / fig_no / graph_info['per_page'] > 1:
        fig.update_layout(title='Contact Path with ' + force_name,
                          autosize=True, margin=dict(l=65, r=50, b=65, t=70))
        for i in range(num_jobs):
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)
            fig.update_scenes(camera_eye=dict(x=0, y=2.5, z=0))
        plot(fig, filename=path + 'Geometry-Force ' + CaseName + str(fig_no)
             + '.html', auto_open=False)
        if fig_no < fig_tot:
            fig.data = []
            row = 1
            col = 1
            fig_no += 1

    return row, col, fig_no


def summarise_results(CaseNamePath, JobFile, CupGeomFile, CaseName,
                      graph_info):
    """
    Summary.

    Creation of bar chart for preselected parameters (or default) for all
    cases. Also, creates .csv file which all important results are placed.

    Parameters
    ----------
    CaseNamePath : str
        Location for putting raw data and charts
    JobFile : str
        Location of file containing all of the cases for the analysis to run.
    CupGeomFile : str
        Location of liner geometry file for analysis.
    CaseName : str
        Name of the case being run, used for organisation and naming files.
    graph_info : dict
        Information from Graph Control UI on what parameters are to be plotted,
        and how many models per file.

    Returns
    -------
    Lateral Separation Bar Chart : .html file
        .html file of bar chart for maximum lateral separation of all cases.

    """
    path = (os.getcwd()[:-11] + '\\output\\'
            + os.path.basename(CupGeomFile[:-4]) + '\\' + CaseName
            + '\\Raw Data')

    Summary = [{}]
    maxLatSep = {'max_lat_sep': []}
    j = 0

    df = pd.read_csv(JobFile)
    df.set_index('case_num')
    df['load_file'] = df['load_file'].apply(lambda x: os.path.basename(x))
    df['lat_mm'] = df['lat_mm'].apply(lambda x: str(x))
    df['lat_spr'] = df['lat_spr'].apply(lambda x: str(x))

    files = os.listdir(path)
    stop_index = len(CaseName)
    sorted_files = sorted(files, key=lambda x: int(re.sub(
        r'\D', '', x.strip())[: stop_index]))
    for filename in sorted_files:
        with open(path + '\\' + filename, 'r', newline='') as results:
            res = csv.reader(results, delimiter=',')

            Summary[j]['File'] = filename
            i = 0

            for row in res:
                if i == 0:
                    Inc = -math.radians(float(row[3][9:13]))
                elif i == 1:
                    pass
                elif i == 2:
                    Summary[j].update({'Max Lateral Separation': float(
                        row[10])})
                    Summary[j].update({'Peak Axial Force': float(row[14])})
                    Summary[j].update({'Contact Points with Inc': (
                        float(row[3]), float(row[4]), float(row[5]))})
                else:
                    if float(row[10]) > Summary[j]['Max Lateral Separation']:
                        Summary[j]['Max Lateral Separation'] = float(row[10])
                        Summary[j]['Contact Points with Inc'] = (
                            float(row[3]), float(row[4]), float(row[5]))
                    if 'EL_' in row[11]:
                        Summary[j]['Edge Loading?'] = 'Yes'
                        if float(row[14]) > Summary[j]['Peak Axial Force']:
                            Summary[j]['Peak Axial Force'] = float(row[14])

                    else:
                        continue
                i += 1

            RotNz = Summary[j]['Contact Points with Inc'][2] * math.cos(Inc) \
                - Summary[j]['Contact Points with Inc'][1] * math.sin(Inc)
            RotNy = Summary[j]['Contact Points with Inc'][2] * math.sin(Inc) \
                + Summary[j]['Contact Points with Inc'][1] * math.cos(Inc)

            Summary[j]['Rotated Contact Points 0\u00B0'] = (
                float(row[3]), RotNy, RotNz)

            if 'Edge Loading?' not in Summary[j]:
                Summary[j]['Edge Loading?'] = 'No'
                Summary[j]['Peak Axial Force'] = 'N/A'

            maxLatSep['max_lat_sep'].append(Summary[j][
                'Max Lateral Separation'])
            j += 1
            Summary.append({})

    try:
        df['max_lat_sep'] = maxLatSep['max_lat_sep']
    except ValueError:
        messagebox.showerror('Check Raw Data Folder', 'If the current settings'
                             ' file is an overwrite of a previous file, check'
                             ' to see if the total cases is equal to the '
                             'number of raw data files. If this is not the '
                             'case, delete the extra files. \nThis occurs '
                             'because the raw data is placed in the same '
                             'location as the old files.')

    with open(path[:-9] + '\\Analysis Summary ' + CaseName
              + '.csv', 'w', newline='') as csvfile:
        fieldnames = list(Summary[0])
        writer = csv.DictWriter(csvfile, fieldnames, dialect='excel')
        writer.writeheader()
        writer.writerows(Summary)

    params = []
    if graph_info['params'] != ['dflt_bar_chart']:
        params = graph_info['params']

        x = df[params[0]]
        if len(params) == 1:
            clr = None
            col = None
            row = None
        elif len(params) == 2:
            clr = df[params[1]]
            col = None
            row = None
        elif len(params) == 3:
            clr = df[params[1]]
            col = df[params[2]]
            row = None
        elif len(params) == 4:
            clr = df[params[1]]
            col = df[params[2]]
            row = df[params[3]]

        fig = px.bar(df, x=x,
                     y="max_lat_sep",
                     color=clr,
                     barmode="group",
                     facet_row=row,
                     facet_col=col,
                     color_discrete_sequence=px.colors.qualitative.Safe,)
    elif graph_info['params'] == ['dflt_bar_chart']:
        # Default bar chart settings
        fig = px.bar(df, x=df['lat_spr'],
                     y="max_lat_sep",
                     color=df['lat_mm'],
                     barmode="group",
                     facet_row=df['load_file'],
                     facet_col=df['sim_inc'],
                     color_discrete_sequence=px.colors.qualitative.Safe,
                     labels={'lat_spr': 'Lateral Spring Stiffness N/mm',
                             'lat_mm': 'Lateral Mismatch (mm)',
                             'max_lat_sep': 'Max. Lateral Separation (mm)',
                             'load_file': 'LP',
                             'sim_inc': 'Simulator Inclination (\u00B0)'})
    ymax = df['lat_mm'].max()
    fig.update_layout(xaxis_type='category',
                      yaxis=dict(range=(0, ymax),
                                 constrain='domain'),
                      title_text='Maximum Lateral Separation across all Cases')
    i = 0
    while i < 10:
        fig.update_xaxes(type='category')
        i += 1

    plot(fig, filename=path[:-9] + '\\Charts\\'
         + 'Max Lateral Separation ' + CaseName + '.html')


if __name__ == '__main__':
    print("\n\nThis file can only be run in tandem with an analysis model")
