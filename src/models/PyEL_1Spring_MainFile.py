"""
PyEL Function-Based Edge Loading Geometric Model.

-MAIN FILE: This file selects and calls the required functions for the model to
run an analysis. Either driven directly or through the UI provided by
PyEL_Interface.py

Version 1.0 (29/03/22)

Created by Lee Etchels

Working for the University of Leeds
Institute of Medical and Biological Engineering

in collaboration with

Alison Jones
Ruth Wilcox
Mazen Al-Hajjar
Murat Ali
Sophie Williams
Louise Jennings
Jonathan Thompson
Graham Isaac
Lin Wang
John Fisher
Isaac Campbell

Funded by:
EPSRC Centre for Innovative Manufacturing in Medical Devices
DePuy Synthes
Leeds Musculoskeletal Biomedical Research Unit
ERC
HIP hip grant

Developed using:
Python version 3.9
Anaconda version 2021.11

Tested using:

Known issue list:

To do list:
* Allow selection of a generated ISO style load with a requested swing phase
    load.
* Put in a first pass that gets an idea of which locations sit within the load
    profile and then apply the contact iterations within that region instead.
* Remove references to 2spring model.
* Tidy up code to follow style conventions.
* Pare down graph options.
* Move all imports to the top of the functions file

* NB:
    * The x direction is anteroposterior, positive anteriorly
    * The y direction is superoinferior, positive superiorly
    * The z direction is mediolateral, positive medially

"""

import math
import datetime
import csv
from scipy.interpolate import interp1d
import os
import pandas as pd
import shutil

import PyEL_Functions as ELF


def run_analysis_2D(CaseName, JobFile, CupGeomFile, CupMeshSize, ContactIts,
                    linerPath, first_geom):
    """
    Run the analysis with the given inputs.

    Send all of the cases for a specific run to this function,
    it should then drive the analysis of all of them and then also deal
    with output plots etc.

    Parameters
    ----------
    CaseName : str
        Name of the case being run, used for organisation and naming files.
    JobFile : str
        Location of file containing all of the cases for the analysis to run.
    CupGeomFile : str
        Location of liner geometry file for analysis.
    CupMeshSize : TYPE
        DESCRIPTION.
    ContactIts : int
        Number of iterations to check for contact points, between centre of
        liner and maximum mismatch.
    ActivityFile : str
        How the load profile is listed for the analysis.
    linerPath : str
        Location of liner geometry folder, into which all results and charts
        are placed.
    first_geom : str
        Identifies if this is the first geometry. If it is, the Graph
        Interface will be displayed.

    Returns
    -------
    Raw Data : .csv file
        .csv file of all the raw data, specific to each case in the job file.
    Geometry-Force 3D Mesh : .html file
        .html file of plotly interactive plot of geometry with contact points
        overlaid with associated force, for each case.
    Lateral Separation Bar Chart : .html file
        .html file of bar chart for maximum lateral separation of all cases.

    """
    misc_dict = {}

    # Importing Case Data from Job list
    CaseData = ELF.Inputs_JobList(JobFile)
    HeadRad = CaseData[3][0]
    num_jobs = len(CaseData[0])

    hour = datetime.datetime.now().hour
    mins = datetime.datetime.now().minute
    sec = datetime.datetime.now().second
    time = str(hour) + ':' + str(mins) + ':' + str(sec)

    print('Done collecting setup parameters and cases' + ': ' + time)

    # User Interface for graph production
    graph_info = {"graph_force": "Axial",
                  "params": ['dflt_bar_chart'],
                  "per_page": 4,
                  "row_col_params": ['sim_inc', 'ver_ang', 'tilt_ang',
                                     'lip_ang', 'head_rad', 'load_file'],
                  "x_params": ['lat_mm', 'ant_mm', 'lat_spr', 'ant_spr']}

    per_page = graph_info['per_page']

    # Creating cup geometry

    CupData = ELF.CupGeom_AxisymPointCloud(CupGeomFile, HeadRad)
    # NOTE: MasterCupData used to save the geometry instead of reloading.
    # Will be updated if CupData list reference changed to
    # direct relation due to python's pass-by-reference
    HeadRad = CupData[1]
    MasterCupData = CupData[0]

    # Conversion to DataFrame for plotly plotting
    CupData_df = pd.DataFrame(MasterCupData)
    CupData_df.rename(columns={0: 'NodeID', 1: 'Nx', 2: 'Ny', 3: 'Nz',
                               4: 'SNx', 5: 'SNy', 6: 'SNz', 7: 'Location',
                               8: 'Edge?', 9: 'Neighbours',
                               10: 'boundary_location'},
                      inplace=True)

    hour = datetime.datetime.now().hour
    mins = datetime.datetime.now().minute
    sec = datetime.datetime.now().second
    time = str(hour) + ':' + str(mins) + ':' + str(sec)
    print('Done creating cup data from the geometrical information'
          + ': ' + time + '\n\n')

    # Create subplots in figure for 3D mesh plots
    fig_no = 1
    row = 1
    col = 1
    num_figures = math.ceil(num_jobs / per_page)
    figs = []
    for i in range(num_figures):
        fig, fig_tot, rows, cols = ELF.create_fig_subplots(
            num_jobs, per_page, CaseName, caseNum=4 * i)
        figs.append(fig)

    # Starting loop through cases
    caseNum = 0
    dfs = []
    for line in CaseData[0]:
        startTime = datetime.datetime.now()
        CupIncAngle_degrees = CaseData[0][caseNum]
        CupAVersionAngle_degrees = 0
        CupOVersionAngle_degrees = 0
        LatMaxDynSep = CaseData[4][caseNum]
        AntMaxDynSep = 0
        LatSpringF = CaseData[6][caseNum]
        AntSpringF = 0
        ActivityFile = CaseData[8][caseNum]
        LipAngle_degrees = 0

        # Reading activity data
        ActivityData = ELF.ReadActivity(ActivityFile)

        # Turning activity profile into load sections
        LoadSections = ELF.Load_IdealisedTwoPeak(ActivityData)

        hour = datetime.datetime.now().hour
        mins = datetime.datetime.now().minute
        sec = datetime.datetime.now().second
        time = str(hour) + ':' + str(mins) + ':' + str(sec)
        print('Done reading activity data' + ': ' + time)

        # Rotating the cup to its final orientation
        LipAngle = 0
        CupIncAngle = math.radians(CupIncAngle_degrees)
        CupAVersionAngle = math.radians(CupAVersionAngle_degrees)
        CupOVersionAngle = math.radians(CupOVersionAngle_degrees)
        sin_Lip = math.sin(LipAngle)
        cos_Lip = math.cos(LipAngle)
        sin_Inc = math.sin(CupIncAngle)
        cos_Inc = math.cos(CupIncAngle)
        cos_Ver = math.cos((-1) * CupAVersionAngle)
        sin_Ver = math.sin((-1) * CupAVersionAngle)
        cos_Tilt = math.cos(CupOVersionAngle)
        sin_Tilt = math.sin(CupOVersionAngle)
        CupData = ELF \
            .CupRotation_IVTseq_AxisymPointCloud(sin_Lip, cos_Lip, sin_Inc,
                                                 cos_Inc, sin_Ver, cos_Ver,
                                                 sin_Tilt, cos_Tilt,
                                                 MasterCupData,
                                                 LipAngle_degrees,
                                                 CupIncAngle_degrees,
                                                 CupAVersionAngle_degrees,
                                                 CupOVersionAngle_degrees)
        if CupData == MasterCupData:
            SystemError('Please check the liner has been rotated. If this is '
                        'correct, MasterCupData has been changed erroneously.'
                        ' Please ensure MasterCupData = CupData[0], else '
                        'following cases will be incorrect. \n(Excepting all '
                        'angles being 0 degrees)')
        else:
            pass

        hour = datetime.datetime.now().hour
        mins = datetime.datetime.now().minute
        sec = datetime.datetime.now().second
        time = str(hour) + ':' + str(mins) + ':' + str(sec)
        print('Done creating an edge list' + ': ' + time)

        # Removing unnecessary points from the cup
        CupFilletRad = 2
        CupData = ELF \
            .RemoveCupPoints_AxisymPointCloud(CupData, LatMaxDynSep,
                                              AntMaxDynSep, CupIncAngle,
                                              CupAVersionAngle,
                                              CupOVersionAngle,
                                              CupFilletRad, CupMeshSize)
        StartID = CupData[1]
        CupData = [CupData[0]]

        hour = datetime.datetime.now().hour
        mins = datetime.datetime.now().minute
        sec = datetime.datetime.now().second
        time = str(hour) + ':' + str(mins) + ':' + str(sec)
        print('Done removing unnecessary points from the cup definition'
              + ': ' + time)

        # Loop to find contact points
        AAFun = interp1d(ActivityData[0], ActivityData[2])
        FEFun = interp1d(ActivityData[0], ActivityData[3])
        IEFun = interp1d(ActivityData[0], ActivityData[4])

        hour = datetime.datetime.now().hour
        mins = datetime.datetime.now().minute
        sec = datetime.datetime.now().second
        time = str(hour) + ':' + str(mins) + ':' + str(sec)
        print('Done creating interpolation functions for the head rotations'
              + ': ' + time)

        CupOrient = [CupIncAngle, CupAVersionAngle, CupOVersionAngle]
        ContactList, df, CaseNamePath = ELF \
            .ContactCalculator_AxisymPointCloud_IVT(CupData, LatMaxDynSep,
                                                    AntMaxDynSep, LatSpringF,
                                                    AntSpringF, ContactIts,
                                                    HeadRad, CupOrient,
                                                    LoadSections, AAFun, FEFun,
                                                    IEFun, caseNum,
                                                    ActivityData[0], StartID,
                                                    CupMeshSize, CupGeomFile,
                                                    startTime, CaseName,
                                                    ActivityFile, LipAngle,
                                                    linerPath, misc_dict)
        ContactList = ContactList[0][0]

        hour = datetime.datetime.now().hour
        mins = datetime.datetime.now().minute
        sec = datetime.datetime.now().second
        time = str(hour) + ':' + str(mins) + ':' + str(sec)
        print('Done calculating the final list of contact points'
              + ': ' + time)

        # Creation of pathway for graphs
        mainDir = os.getcwd()[:-11]
        resDir = mainDir + '\\output'
        geom = os.path.basename(CupGeomFile)
        linerDir = resDir + '\\' + geom[:-4]
        caseDir = linerDir + '\\' + CaseName + '\\'
        if not os.path.exists(caseDir + 'Charts'):
            os.makedirs(caseDir + 'Charts')

        # Rotating contact points to 0degrees for visualisation
        df['Nz'], df['Ny'] = ELF.Rotate_2D(df['Nz'], df['Ny'], CupIncAngle,
                                           direction=-1)
        dfs.append(df)
        caseNum += 1
        print('\n')
    fig_no = 1
    rc = [[1, 1], [1, 2], [2, 1], [2, 2]]
    rc_count = 0
    caseNum = 0
    numCases = len(dfs) - 1
    for fig in figs:
        for i in range(4):
            if caseNum <= numCases:
                row, col, fig_no = ELF.create_models(
                    dfs[caseNum], CupData_df, caseNum,
                    graph_info, fig,
                    CaseName, rows,
                    cols, rc[rc_count][0], rc[rc_count][1], fig_no, fig_no,
                    num_jobs,
                    caseDir + 'Charts\\')
                caseNum += 1
                rc_count += 1
            fig_no += 1
            rc_count = 0

    # Summarizing results of case list for geometry file
    ELF.summarise_results(CaseNamePath, JobFile, CupGeomFile, CaseName,
                          graph_info)


def main(mainPath=os.getcwd()):
    r"""
    Drive the analysis without using UI.

    If you already have csv files to specify the case (eg the geometry, given
    in the settings file) and the case list (eg inclinations, mismatches etc,
    given in the joblist file) you can skip the UI and run the analysis
    by running this script file directly. The config files should be placed in
    config\Manual_Run.
    The setting file name should start with 'Settings_' and the joblist
    file name should start with 'Joblist_'.

    Version angles and anterior mismatches/spring stiffnesses will
    be set to 0 in this release as it is only designed for ML
    separation cases.

    :param mainPath: DESCRIPTION, defaults to os.getcwd()
    :type mainPath: TYPE, optional
    :return: DESCRIPTION
    :rtype: TYPE

    """
    mainPath = mainPath[:-11]
    path = mainPath + '\\config\\Manual_Run'
    file_list = os.listdir(path)

    flagFirst = 1
    for filename in file_list:
        if filename[0:9] == 'Settings_':
            with open(path + '\\' + filename, 'r', newline='') as csvfile:
                setupData = csv.reader(csvfile, delimiter=',', dialect='excel')
                for line in setupData:
                    parameterType = line[0]
                    parameterVal = line[1]
                    if parameterType == 'CaseName':
                        CaseName = parameterVal
                    elif parameterType == 'JobFile':
                        JobFile = parameterVal
                    elif parameterType == 'CupGeomFile':
                        CupGeomFile = parameterVal
                    elif parameterType == 'ApproximateMeshSize':
                        CupMeshSize = float(parameterVal)
                    elif parameterType == 'ContactIterations':
                        ContactIts = int(parameterVal)
                    elif parameterType == 'CupGeomFolder':
                        CupGeomFolder = parameterVal
                    else:
                        continue

                if flagFirst == 1:
                    first_geom = 'Yes'
                    flagFirst = 0
                else:
                    first_geom = 'No'

                linerPath = mainPath + '\\output\\' + CupGeomFolder
                if linerPath[-4] == '.':
                    linerPath = linerPath[:-4]
                if not os.path.exists(linerPath):
                    os.makedirs(linerPath)
                caseDir = linerPath + '\\' + CaseName
                if not os.path.exists(caseDir):
                    os.makedirs(caseDir)
                if not os.path.exists(caseDir + '\\Raw Data'):
                    os.makedirs(caseDir + '\\Raw Data')
                if not os.path.exists(caseDir + '\\Analysis Parameter Files'):
                    os.makedirs(caseDir + '\\Analysis Parameter Files')
                settFile = path + '\\' + filename
                jobFile = path + '\\Joblist_' + filename[9:]
                shutil.copy(settFile, caseDir + '\\Analysis Parameter Files')
                shutil.copy(jobFile, caseDir + '\\Analysis Parameter Files')
                run_analysis_2D(CaseName, JobFile, CupGeomFile, CupMeshSize,
                                ContactIts, linerPath, first_geom)


if __name__ == '__main__':
    main()
