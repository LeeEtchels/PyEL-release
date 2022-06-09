"""
Summary.

Produces the UI panel to ask for the input conditions
that the user wants to use to create a joblist and run. It includes error
catching and can drive the analysis model script to complete the run.

Version 1.0 (29/03/22)

Created by Isaac Campbell
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from PIL import ImageTk, Image
import csv
import glob
import os
import shutil
import PyEL_1Spring_MainFile as _1Spr


class UI:
    """
    Creates widgets and puts them into a grid the master window.

    params:
    ------
    master: str
        Window name
    widtyp: str
        Type of widget to be created. Must use tk. for correct attribute.
    row, col: int
        For placement of widget on the grid.
    """

    def __init__(self, master, widtyp, row, col, colspan=None, labtext=None,
                 bdwdth=3, state=tk.NORMAL, var=None, command=None, width=15,
                 dflt=0, anchor=None):
        self.master = master
        self.widtyp = widtyp
        self.row = row
        self.col = col
        self.colspan = colspan
        self.labtext = labtext
        self.bdwdth = bdwdth
        self.state = state
        self.var = var
        self.command = command
        self.width = width
        self.dflt = dflt
        self.anchor = anchor
        self.wid_create()

    def wid_create(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        if self.widtyp == tk.Label:
            self.widget = self.widtyp(self.master, text=self.labtext,
                                      anchor=self.anchor)
        elif self.widtyp == tk.Entry:
            self.widget = self.widtyp(self.master, borderwidth=self.bdwdth,
                                      width=self.width)
            self.widget.insert(0, self.dflt)
            self.widget.config(state=self.state)
        elif self.widtyp == tk.Checkbutton:
            self.widget = self.widtyp(self.master, text=self.labtext,
                                      var=self.var)
            self.widget.config(state=self.state)
        elif self.widtyp == tk.Button:
            self.widget = self.widtyp(self.master, text=self.labtext,
                                      command=self.command, state=self.state)

        self.widget.grid(row=self.row, column=self.col,
                         columnspan=self.colspan, padx=5, pady=5)


class Buttons(UI):
    """Functions of the buttons within the UI."""

    global VarDict, errorCount
    VarDict = {}
    errorCount = 0

    def open_help():
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        Help = tk.Toplevel()
        Help.title("Help")
        help_txt = tk.Label(Help, anchor="n",
                            text=r"""
        To Begin:

        Store the script files, load profiles, geometry files, and
        config files in the same locations as in the original download.

        This user interface will create a complete case list for analysis
        with the values entered. Insert a name for the case list.

        When selecting any options, tick the relevant checkbox and click
        'Confirm'.

        For a range of values, enter the minimum, maximum and interval values.
        Where the option is given, multiple values can be entered. If no
        value is entered, default values will be used. These are present in
        the entry boxes. If a single case is desired for a particular
        parameter, leave the zeroes in the entryboxes in place.

        Either a directory or file(s) can be used for Load Profile and a
        file for the Liner Geometry.

        Once all requirements have been satisfied, select the 'Check' button.
        This will ensure there are no errors in the entries and will enable
        the 'OK' button. Once finished, press the 'OK' button for the case
        list to be generated.

        Next Steps:

        A folder is created inside the config\From_UI directory
        containing the required files. You can continue to analyse all the
        cases from within the UI or you can run them manually.
        To run these manually move them to the config\Manual_Run folder, open
        the script "PyEL_1Spring_MainFile.py" and press the play button.
        Folders for each liner geometry, as well as files containing raw
        data and selected charts are created for each case in the output
        folder.

        It is possible to create your own load profiles and liner geometries.
        In both cases the formatting should be identical to the provided
        example files.
        For load profiles, only simple, smooth, two-peak profiles can be
        used without modification to the code.
        For liner geometries the point cloud information can be generated
        in any convenient way as long as the required information is included.
        This is more involved though and we have an abaqus script which
        generates them from a meshed liner, so feel free to get in touch if
        you would like to try it out.

        Note:

        This version creates a 3D plot for each case, with four figures
        shown in each html file.

        For more info on how the model operates, see:
            https://www.sciencedirect.com/science/article/pii/S0021929019305020

        For typical parameter ranges, see:
            https://onlinelibrary.wiley.com/doi/full/10.1002/jbm.b.33991

        """)
        help_txt.pack(side="left", fill="both", expand="yes")

        img_path = os.getcwd() + "\\parameter_table.png"
        img = ImageTk.PhotoImage(Image.open(img_path))
        tab = tk.Label(Help, image=img)
        tab.image = img
        tab.pack(side="right", fill="both", expand="5")

    @staticmethod
    def spring_entry(SprType):
        """
        Summary.

        Places lateral spring labels on the UI. Adds entry widgets for later
        input extraction.

        """
        global LatSprmin, LatSprmax, LatSprStep
        global LatSpr, LatSpr1, LatSpr2, LatSpr3, LatSpr4
        LatSprmin.widget.destroy()
        LatSprmax.widget.destroy()
        LatSprStep.widget.destroy()
        LatSpr.widget.destroy()
        LatSpr1.widget.destroy()
        LatSpr2.widget.destroy()
        LatSpr3.widget.destroy()
        LatSpr4.widget.destroy()
        UI(window, tk.Label, 6, 0,
           labtext="Lateral Spring Stiffness (N/mm)")
        if RangeLS.var.get() == 1 and ValueLS.var.get() == 0:
            if 'LatSprValue' in VarDict:
                del VarDict['LatSprValue']
            UI(window, tk.Label, 6, 2, labtext="to")
            UI(window, tk.Label, 6, 4, labtext="in intervals of (N/mm)")
            LatSprmin = UI(window, tk.Entry, 6, 1, dflt=100)
            LatSprmax = UI(window, tk.Entry, 6, 3)
            LatSprStep = UI(window, tk.Entry, 6, 5)
            globals()['VarDict']['LatSprRange'] = [LatSprmin, LatSprmax,
                                                   LatSprStep]
        elif ValueLS.var.get() == 1 and RangeLS.var.get() == 0:
            if 'LatSprRange' in VarDict:
                del VarDict['LatSprRange']
            LatSpr = UI(window, tk.Entry, 6, 1, dflt=100)
            LatSpr1 = UI(window, tk.Entry, 6, 2)
            LatSpr2 = UI(window, tk.Entry, 6, 3)
            LatSpr3 = UI(window, tk.Entry, 6, 4)
            LatSpr4 = UI(window, tk.Entry, 6, 5)
            globals()['VarDict']['LatSprValue'] = [LatSpr, LatSpr1,
                                                   LatSpr2, LatSpr3,
                                                   LatSpr4]
        else:
            pass

    @staticmethod
    def file_direc_type(typ):
        """
        Summary.

        Handles whether directory or files are to be selected and places
        relevant widgets in the window.

        Parameters
        ----------
        typ : str
            Dictates whether the input is for Load profiles or Geometry files.

        """
        if typ == 'Loads':
            global DirecLab, LoadDirec, LoadLab, AddLoad, LoadName
            LoadLab.widget.destroy()
            AddLoad.widget.destroy()
            LoadDirec.widget.destroy()
            DirecLab.widget.destroy()
            LoadName = UI(window, tk.Entry, 17, 1,
                          dflt="Insert File(s)/Directory", width=20)
            if LoadFileName.var.get() == 1 and LoadDir.var.get() == 0:
                LoadLab = UI(window, tk.Label, 17, 0,
                             labtext="Load Profile File Name(s)")
                AddLoad = UI(window, tk.Button, 17, 2, labtext="Choose",
                             command=lambda: Buttons.choose_file_direc(
                                 typ, 'files'))
            elif LoadFileName.var.get() == 0 and LoadDir.var.get() == 1:
                DirecLab = UI(window, tk.Label, 17, 0,
                              labtext="Load Directory Name")
                LoadDirec = UI(window, tk.Button, 17, 2, labtext="Choose",
                               command=lambda: Buttons.choose_file_direc(
                                   typ, 'direc'))
            elif LoadFileName.var.get() == 1 and LoadDir.var.get() == 1:
                pass
        if typ == 'Geoms':
            global GeomLab, AddGeom, GeomDirec, GeomDirLab, GeomName
            GeomLab.widget.destroy()
            AddGeom.widget.destroy()
            GeomDirec.widget.destroy()
            GeomDirLab.widget.destroy()
            GeomName = UI(window, tk.Entry, 17, 4,
                          dflt="Insert File(s)/Directory", width=20)
            if GeomFileName.var.get() == 1:
                GeomLab = UI(window, tk.Label, 17, 3,
                             labtext="Enter Geometry File Location")
                AddGeom = UI(window, tk.Button, 17, 5, labtext="Choose",
                             command=lambda: Buttons.choose_file_direc
                             (typ, 'files'))

    @staticmethod
    def choose_file_direc(typ, loc):
        """
        Summary.

        Uses file dialogue for the user to select files or directory for either
        load profiles or liner geometries.

        Parameters
        ----------
        typ : str
            Dictates whether the input is for Load profiles or Geometry files.
        loc : str
            Dictates whether the type of input is to be a directory or
            specific files.


        """
        path = os.getcwd()
        inpath = path[:-10] + 'data\\external'
        if typ == 'Loads':
            VarDict[typ] = []
            if loc == 'direc':
                direcname = filedialog.askdirectory(initialdir=inpath,
                                                    title='Select a Directory')
                LoadName.widget.delete(0, 'end')
                LoadName.widget.insert(0, direcname)
                if direcname != '':
                    for file in os.listdir(direcname):
                        if '.csv' not in file:
                            pass
                        else:
                            globals()['VarDict'][typ].append(
                                direcname + '\\' + file)
            elif loc == 'files':
                filenames = filedialog.askopenfilenames(
                    initialdir=inpath, title='Select a File',
                    filetypes=(('csv Files', "*.csv"), ("All Types", "*.*")))
                if filenames != '':
                    LoadName.widget.delete(0, 'end')
                    LoadName.widget.insert(0, os.path.basename(filenames[0]))
                    for i in range(len(filenames)):
                        if i < 4:
                            UI(window, tk.Label, 18 + i, 1, colspan=2,
                               labtext=os.path.basename(filenames[i]))
                        elif i == 4:
                            UI(window, tk.Label, 18 + i, 1,
                               labtext='+ ' + str(
                                   len(filenames) - i) + ' more')
                        globals()['VarDict'][typ].append(filenames[i])
                else:
                    pass
        if typ == 'Geoms':
            VarDict[typ] = []
            if loc == 'direc':
                direcname = filedialog.askdirectory(initialdir=inpath,
                                                    title='Select a Directory')
                GeomName.widget.delete(0, 'end')
                GeomName.widget.insert(0, direcname)
                if direcname != '':
                    globals()['VarDict'][typ] = [direcname]
            elif loc == 'files':
                filenames = filedialog.askopenfilenames(
                    initialdir=inpath, title='Select a File',
                    filetypes=(('txt Files', "*.txt"), ("All Types", "*.*")))
                if filenames != '':
                    GeomName.widget.delete(0, 'end')
                    GeomName.widget.insert(0, os.path.basename(filenames[0]))
                    for i in range(len(filenames)):
                        if i < 4:
                            UI(window, tk.Label, 18 + i, 4, colspan=2,
                               labtext=os.path.basename(filenames[i]))
                        elif i == 4:
                            UI(window, tk.Label, 18 + i, 4,
                               labtext='+ ' + str(
                                   len(filenames) - i) + ' more')
                        globals()['VarDict'][typ].append(filenames[i])

    @staticmethod
    def check_button():
        """
        Summary.

        Takes the values inputted into the GUI and creates a list. Checks
        are made for valid entry values. If values are in the correct format,
        the lists are placed in a dictionary.

        Returns
        -------
        VarDict: Dictionary
            Contains lists of parameter values.

        """
        globals()['errorCount'] = 0

        if 'Model' not in VarDict:
            VarDict['Model'] = '2D'
        VarDict['Ver'] = []
        VarDict["Tilt"] = []
        VarDict["AntMM"] = []
        VarDict["LipAng"] = []

        if CaseName.widget.get() == 'Example_Case_Name_':
            response = messagebox.askokcancel(
                "Continue?", "No Case Name has been entered."
                "\n'Example_Case_Name_' will be used "
                "to name the files. \n\nContinue?")
            if response == 1:
                pass
            elif response == 0:
                globals()['errorCount'] += 1

        # Checks on input files for load profiles and liners
        if 'Loads' in VarDict:
            if VarDict['Loads'] == []:
                messagebox.showerror(
                    "Error", "Please Enter a Geometry File or Directory.")
                globals()['errorCount'] += 1
            else:
                for load in VarDict['Loads']:
                    if load.strip(" ") == 'Insert File(s)/Directory':
                        messagebox.showerror(
                            "Error", "Please Enter a Load File or Directory.")
                        globals()['errorCount'] += 1
                        break
                if 'Geoms' in VarDict:
                    if VarDict['Geoms'] == []:
                        messagebox.showerror("Error",
                                             "Please Enter a Geometry File "
                                             "or Directory.")
                        globals()['errorCount'] += 1
                    else:
                        for geom in VarDict['Geoms']:
                            if geom.strip(" ") == 'Insert File(s)/Directory':
                                messagebox.showerror("Error",
                                                     "Please Enter a Geometry "
                                                     "File or Directory.")
                                globals()['errorCount'] += 1
                                break
                else:
                    messagebox.showerror("Error",
                                         "Please Enter Geometry File or "
                                         "Directory.")
                    globals()['errorCount'] += 1
        else:
            messagebox.showerror("Error",
                                 "Please Enter a Load File or Directory.")
            globals()['errorCount'] += 1

        # Checks on both spring parameter inputs
        if 'LatSprRange' in VarDict:
            LatSpr = Check(VarDict['LatSprRange'][0],
                           VarDict['LatSprRange'][1],
                           VarDict['LatSprRange'][2])
            VarDict['LatSpr'] = LatSpr.List
            if globals()['errorCount'] == 0:
                del VarDict['LatSprRange']
        elif 'LatSprValue' in VarDict:
            VarDict['LatSpr'] = []
            for f in VarDict['LatSprValue']:
                if f.widget.get() == '0':
                    pass
                else:
                    VarDict['LatSpr'].append(int(f.widget.get()))
            if globals()['errorCount'] == 0:
                del VarDict['LatSprValue']
        else:
            VarDict['LatSpr'] = [100]

        if 'AntSprRange' in VarDict:
            AntSpr = Check(VarDict['AntSprRange'][0],
                           VarDict['AntSprRange'][1],
                           VarDict['AntSprRange'][2])
            VarDict['AntSpr'] = AntSpr.List
            if globals()['errorCount'] == 0:
                del VarDict['AntSprRange']
        elif 'AntSprValue' in VarDict:
            VarDict['AntSpr'] = []
            for f in VarDict['AntSprValue']:
                if f.widget.get() == '0':
                    pass
                else:
                    VarDict['AntSpr'].append(int(f.widget.get()))
            if globals()['errorCount'] == 0:
                del VarDict['AntSprValue']
        else:
            VarDict['AntSpr'] = [0]

        # Entry values sent through checking prodedure
        LatMM = Check(LatMMmin, LatMMmax, LatMMStep)
        Inc = Check(Incmin, Incmax, IncStep)
        HeadRad = Check(HeadRadmin, HeadRadmax, HeadRadStep)

        if NumEval.widget.get().isnumeric() is False:
            messagebox.showerror("Error",
                                 "Enter only integers for Contact Iterations")
            globals()['errorCount'] += 1
        else:
            if int(NumEval.widget.get()) < 500:
                messagebox.showerror("Error",
                                     "At least 500 points should be analysed.")
                globals()['errorCount'] += 1

        # Once checking procedure completed, dictionary is created to
        # store lists.
        if globals()['errorCount'] != 0:
            pass
        elif globals()['errorCount'] == 0:
            VarDict["Case Name"] = CaseName.widget.get()
            VarDict["LatMM"] = LatMM.List
            numCases = len(LatMM.List)
            VarDict["Inc"] = Inc.List
            VarDict["HeadRad"] = HeadRad.List

            for i in range(0, numCases):
                VarDict["Ver"].append(0)
                VarDict["Tilt"].append(0)
                VarDict["AntMM"].append(0)
                VarDict["LipAng"].append(0)
            VarDict["Points"] = int(NumEval.widget.get())
            VarDict["mainPath"] = os.getcwd()

            print(str(VarDict) + "\n")

            # 'OK' button enabled
            endWindow.widget.config(state=tk.NORMAL)
            UI(window, tk.Label, 19, 9, labtext='\u2705')


class Check(UI):
    """
    Summary.

    Checking procedure for ensuring only valid entry values are passed into
    lists. Checks are sequential, only passing to next check if each is ok'ed.
    Error messages pop up with information for the user on what entry value
    needs to be changed.

    Returns
    -------
    self.List: list
        List of range of values for each instance.

    """

    def __init__(self, Min=None, Max=None, Step=None):
        """
        Summary.

        :param Min: DESCRIPTION, defaults to None
        :type Min: TYPE, optional
        :param Max: DESCRIPTION, defaults to None
        :type Max: TYPE, optional
        :param Step: DESCRIPTION, defaults to None
        :type Step: TYPE, optional
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.Min = Min.widget.get()
        self.MinWid = Min
        self.Max = Max.widget.get()
        self.MaxWid = Max
        self.Step = Step.widget.get()
        self.StepWid = Step
        self.List = []
        self.check_numeric()

    def check_numeric(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        # Checks only numerical values are entered, excluding decimal points
        # for floats
        if self.Min == 'dflt':
            self.List = [self.Min]
        else:
            try:
                self.Min = float(self.Min)
            except AttributeError:
                self.MinWid.widget.config(bg='pink')
                messagebox.showerror(
                    "Error", """Please ensure values are numerical only.""")
                globals()['errorCount'] += 1
            try:
                self.Max = float(self.Max)
            except AttributeError:
                self.MaxWid.widget.config(bg='pink')
                messagebox.showerror(
                    "Error", """Please ensure values are numerical only.""")
                globals()['errorCount'] += 1
            try:
                self.Step = float(self.Step)
            except AttributeError:
                self.StepWid.widget.config(bg='pink')
                messagebox.showerror(
                    "Error", """Please ensure values are numerical only.""")
                globals()['errorCount'] += 1
            if errorCount == 0 and self.Min != 'dflt':
                self.check_range_errors()

    def check_range_errors(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        # Checks values of minimum, maximum and interval are sensible.
        if self.Max != 0 and self.Step == 0 and self.Max != self.Min:
            self.StepWid.widget.config(bg='pink')
            messagebox.showerror("Error", "Please enter interval.")
            globals()['errorCount'] += 1
        elif self.Max == 0 and self.Step != 0 and self.Min > 0:
            self.MaxWid.widget.config(bg='pink')
            messagebox.showerror(
                "Error", "Please enter maximum value.")
            globals()['errorCount'] += 1
        elif self.Min > self.Max and self.Max != 0:
            self.MinWid.widget.config(bg='pink')
            messagebox.showerror(
                "Error", "Minimum cannot be greater than maximum value.")
            globals()['errorCount'] += 1
        elif self.Step < 0:
            self.StepWid.widget.config(bg='pink')
            messagebox.showerror(
                "Error", "Interval must be greater than zero.")
            globals()['errorCount'] += 1
        elif self.Step != 0:
            interval = (self.Max - self.Min) / self.Step
            if interval < 1 and self.Max != 0:
                self.StepWid.widget.config(bg='pink')
                messagebox.showerror(
                    "Error", "Interval cannot be greater than maximum value.")
                globals()['errorCount'] += 1

        if globals()['errorCount'] == 0:
            self.create_lists()
        else:
            pass

    def create_lists(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        # Forms list of range of values.
        if self.Max == 0 or self.Min == self.Max:
            self.List = [self.Min]
        elif self.Min < self.Max:
            while self.Min <= self.Max:
                self.List.append(self.Min)
                self.Min += self.Step


class ExitUI():
    """
    Summary.

    Activated on "OK" button being clicked. Creates a list of dictionaries,
    each one a case to be analysed, and exports them as an excel file.

    """

    def __init__(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.JobDict = [{}]
        self.gen_joblist()
        self.param_list()
        self.end_window()

    def gen_joblist(self):
        """
        Summary.

        Takes global variable VarDict and iterates through each list to form
        a list of dictionaries in the correct priority for parameters.

        Returns
        -------
        JobDict: List of dictionaries.
            Each dictionary contains a unique casse to be analysed.

        """
        VarDict['AntMM'] = [0]
        VarDict['AntSpr'] = [0]
        VarDict['Ver'] = [0]
        VarDict['Tilt'] = [0]
        VarDict['LipAng'] = [0]
        self.NumJobs = (len(VarDict['LatMM']) * len(VarDict['AntMM'])
                        * len(VarDict['Loads']) * len(VarDict['Geoms'])
                        * len(VarDict['AntSpr']) * len(VarDict['LatSpr'])
                        * len(VarDict['Inc']) * len(VarDict['Ver'])
                        * len(VarDict['Tilt']) * len(VarDict['HeadRad'])
                        * len(VarDict['LipAng']))

        print("Number of Cases --> " + str(self.NumJobs) + "\n")

        i = 0

        for inc in VarDict["Inc"]:
            for ver in VarDict["Ver"]:
                for tilt in VarDict["Tilt"]:
                    for head in VarDict["HeadRad"]:
                        for latMM in VarDict["LatMM"]:
                            for antMM in VarDict["AntMM"]:
                                for latSpr in VarDict["LatSpr"]:
                                    for antSpr in VarDict["AntSpr"]:
                                        for lip in VarDict["LipAng"]:
                                            for load in VarDict["Loads"]:
                                                self.JobDict[i][
                                                    'case_num'] = i
                                                self.JobDict[i][
                                                    'sim_inc'] = inc
                                                self.JobDict[i][
                                                    'ver_ang'] = ver
                                                self.JobDict[i][
                                                    'tilt_ang'] = tilt
                                                self.JobDict[i][
                                                    'head_rad'] = head
                                                self.JobDict[i][
                                                    'lat_mm'] = latMM
                                                self.JobDict[i][
                                                    'ant_mm'] = antMM
                                                self.JobDict[i][
                                                    'lat_spr'] = latSpr
                                                self.JobDict[i][
                                                    'ant_spr'] = antSpr
                                                self.JobDict[i][
                                                    'load_file'] = load
                                                self.JobDict[i][
                                                    'lip_ang'] = lip
                                                self.JobDict[0][
                                                    'num_jobs'] = self.NumJobs
                                                self.JobDict[0][
                                                    'model'] = VarDict['Model']
                                                i += 1
                                                if i + 1 > self.NumJobs:
                                                    continue
                                                else:
                                                    self.JobDict.append({})
        if self.JobDict[-1] == {}:
            self.JobDict.remove(self.JobDict[-1])

    def param_list(self):
        """
        Summary.

        Check through inputs to see if other files or folders of the same
        name have been created. Offer user options for
        renaming/overwriting/adding a copy.

        """
        copy_response = 'Response required'
        mainDir = os.getcwd()[:-11]

        self.mainPath = VarDict['mainPath']
        self.results_dir = mainDir + '\\output'
        geom = os.path.basename(VarDict["Geoms"][0])
        linerDir = self.results_dir + '\\' + geom[:-4]
        caseDir = linerDir + '\\' + VarDict['Case Name']

        # Removing files from Anaylsis Parameter Files folder
        path = caseDir + '\\Analysis Parameter Files'
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            for filename in os.listdir(path):
                os.remove(path + '\\' + filename)

        # Copy any existing files from previous run to 'Saved_Files'
        archDir = mainDir + '\\config\\Saved_Files'
        inDir = mainDir + '\\config\\From_UI'

        for f in os.listdir(inDir):
            ext = f[-4:]
            fname = f[:-4]
            if os.path.exists(archDir + '\\' + fname + '01' + ext) is False:
                shutil.move(inDir + '\\' + f,
                            archDir + '\\' + fname + '01' + ext)
            elif fname[:9] == 'Settings_':
                allFiles = glob.glob(archDir + '\\' + fname + '*')
                l = []
                for appFile in allFiles:
                    aFname = os.path.basename(appFile)
                    try:
                        l.append(int(aFname[-6:-4]))
                    except ValueError:
                        pass
                appendText = str(max(l) + 1)
                if len(appendText) == 1:
                    appendText = '0' + appendText
                shutil.move(inDir + '\\' + f,
                            archDir + '\\' + fname
                            + str(appendText) + ext)
                jbFname = 'Joblist_' + f[9:]
                shutil.move(inDir + '\\' + jbFname,
                            archDir + '\\' + jbFname[:-4]
                            + str(appendText) + ext)

        settings_file = 'Settings_' + VarDict['Case Name']
        job_file = 'Joblist_' + VarDict['Case Name']

        for geom in VarDict["Geoms"]:
            liner_file = os.path.basename(geom)[:-4]
            index = liner_file.find('_ms')
            index2 = index + 1
            while liner_file[index2] != '_':
                index2 += 1
            mesh_size = liner_file[index + 3:index2].replace('p', '.')

            # Setting folder pathway
            self.liner = liner_file

            # Collecting parameters for settings files
            self.MainParams = []
            self.MainParams.append(['CaseName', VarDict['Case Name']])
            self.MainParams.append(['CupGeomFile', geom])
            self.MainParams.append(['CupGeomFolder', self.liner])
            self.MainParams.append(['ApproximateMeshSize', float(mesh_size)])
            self.MainParams.append(['ContactIterations', VarDict["Points"]])
            self.MainParams.append(['ActivityDataFile', 'In job file'])

            if (os.path.exists(
                    path + '\\' + settings_file + '.csv')
                    and copy_response == 'Response required'):
                copy_response = messagebox.askyesno(
                    "Files Already Exists", "At least one of settings files "
                    "already exists i.e. the geometry \nfile and case name "
                    "have been used previously.\n\nWould you like to create a "
                    "copy of the settings files?\n\nResponding 'No' will "
                    "result in the files being overwritten.")

            # Setting copy number
            if os.path.exists(path + '\\' + settings_file + '.csv'):
                if copy_response is True:
                    i = 1
                    settings_file = settings_file + '(' + str(i) + ')'
                    job_file = job_file + '(' + str(i) + ')'
                    while i <= 10:
                        if os.path.isfile(path + '\\'
                                          + settings_file + '.csv'):
                            settings_file = (settings_file[:-3]
                                             + '(' + str(i) + ')')
                            job_file = job_file[:-3] + '(' + str(i) + ')'
                            i += 1
                        else:
                            self.create_files(settings_file, job_file, geom,
                                              path)
                            break
                elif copy_response is False:
                    self.create_files(settings_file, job_file, geom, path)
                else:
                    pass
            else:
                self.create_files(settings_file, job_file, geom, path)

    def create_files(self, settings_file, job_file, geom, path):
        """
        Summary.

        Creates Settings files and Joblist files. Also, second copy of
        settings file placed in Analysis Parameter Files folder.

        """
        self.MainParams.append(['JobFile',
                                path + '\\' + job_file + '.csv'])

        mainDir = os.getcwd()[:-11]
        configPath = mainDir + '\\config\\From_UI\\'
        settings_file = 'Settings_' + VarDict['Case Name']
        settDir = (mainDir + '\\output\\'
                   + os.path.basename(geom)[:-4]
                   + '\\' + VarDict['Case Name']
                   + '\\Analysis Parameter Files')
        with open(settDir + '\\' + settings_file + '.csv', 'w',
                  newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerows(self.MainParams)

        with open(settDir + '\\' + job_file + '.csv', 'w',
                  newline='') as joblist:
            fieldnames = list(self.JobDict[0])
            writer = csv.DictWriter(joblist, fieldnames=fieldnames,
                                    dialect='excel')
            writer.writeheader()
            writer.writerows(self.JobDict)

        # Write a second copy grouping Main file parameters into generic
        # location for loop

        with open(configPath + settings_file + '.csv', 'w',
                  newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerows(self.MainParams)

        with open(configPath + '\\' + job_file + '.csv', 'w',
                  newline='') as joblist:
            fieldnames = list(self.JobDict[0])
            writer = csv.DictWriter(joblist, fieldnames=fieldnames,
                                    dialect='excel')
            writer.writeheader()
            writer.writerows(self.JobDict)

    def end_window(self):
        """
        Summary.

        :return: DESCRIPTION
        :rtype: TYPE

        """
        # Link to integrate analysis script into UI
        response = messagebox.askokcancel(
            title="Run Analysis?", message="Do you want to run analysis code"
            " now?")
        if response == 1:
            window.destroy()
            topDir = VarDict['mainPath'][:-11]
            inFilesDir = topDir + '\\config\\From_UI'
            linerPath = topDir + '\\output\\' + os.path.basename(
                VarDict['Geoms'][0])

            with open(inFilesDir + '\\Settings_'
                      + VarDict['Case Name'] + '.csv',
                      'r', newline='') as csvfile:
                setupData = csv.reader(csvfile, delimiter=',', dialect='excel')
                for line in setupData:
                    parameterType = line[0]
                    parameterVal = line[1]
                    if parameterType == 'ApproximateMeshSize':
                        CupMeshSize = float(parameterVal)
                    else:
                        pass

            _1Spr.run_analysis_2D(VarDict['Case Name'],
                                  inFilesDir + '\\Joblist_'
                                  + VarDict['Case Name'] + '.csv',
                                  VarDict['Geoms'][0],
                                  CupMeshSize,
                                  VarDict['Points'],
                                  linerPath,
                                  'Yes')
        else:
            window.destroy()


# List of all the widgets to pack into the grid with relevant parameters
window = tk.Tk()
window.title("User Interface")
window.geometry("1100x600")
UserMessage = UI(window, tk.Label, 0, 0, 6, "Input Specifications: ")

HelpButton = UI(window, tk.Button, 0, 8, labtext='Help',
                command=Buttons.open_help)

CNLab = UI(window, tk.Label, 2, 0,
           labtext="Enter a Case Name\nPlease use the following format.")
CaseName = UI(window, tk.Entry, 2, 1, dflt='Example_Case_Name_', width=20)

LatMMlab = UI(window, tk.Label, 3, 0, labtext="Lateral Mismatch Range (mm)")
LatMMran = UI(window, tk.Label, 3, 2, labtext="to")
LabMMinter = UI(window, tk.Label, 3, 4, labtext="in intervals of (mm)")
LatMMmin = UI(window, tk.Entry, 3, 1, dflt=4)
LatMMmax = UI(window, tk.Entry, 3, 3)
LatMMStep = UI(window, tk.Entry, 3, 5)

RanValLS = UI(window, tk.Label, 5, 0, colspan=1,
              labtext="Lateral Spring Stiffness")
RangeLS = UI(window, tk.Checkbutton, 5, 1, labtext="Range", var=tk.IntVar())
ValueLS = UI(window, tk.Checkbutton, 5, 3, labtext="Multiple Values",
             var=tk.IntVar())
LatSprType = UI(window, tk.Button, 5, 4, labtext="Confirm",
                command=lambda: Buttons.spring_entry('Lat'))

Inclab = UI(window, tk.Label, 9, 0,
            labtext="Simulator Inclination (\u00B0)")
Incran = UI(window, tk.Label, 9, 2, labtext="to")
Incinter = UI(window, tk.Label, 9, 4,
              labtext="in intervals of (\u00B0)")
Incmin = UI(window, tk.Entry, 9, 1, dflt=55)
Incmax = UI(window, tk.Entry, 9, 3)
IncStep = UI(window, tk.Entry, 9, 5)

HeadRadlab = UI(window, tk.Label, 12, 0, labtext="Head Radius (mm)")
HeadRadran = UI(window, tk.Label, 12, 2, labtext="to")
HeadRadinter = UI(window, tk.Label, 12, 4, labtext="in intervals of (mm)")
HeadRadmin = UI(window, tk.Entry, 12, 1, dflt='dflt')
HeadRadmax = UI(window, tk.Entry, 12, 3)
HeadRadStep = UI(window, tk.Entry, 12, 5)

NumEvalLab = UI(window, tk.Label, 14, 0,
                labtext="Contact Iterations to Evaluate")
NumEval = UI(window, tk.Entry, 14, 1, dflt=2000)

LoadDirecFile = UI(window, tk.Label, 15, 0, colspan=2,
                   labtext="Choose directory or file names for Load Profile.")
LoadDir = UI(window, tk.Checkbutton, 15, 3, labtext="Directory",
             var=tk.IntVar())
LoadFileName = UI(window, tk.Checkbutton, 15, 4, labtext="File Names",
                  var=tk.IntVar())
GeomDirecFile = UI(window, tk.Label, 16, 0, colspan=2,
                   labtext="Choose file name for Geometry File.")
GeomFileName = UI(window, tk.Checkbutton, 16, 4, labtext="File Name",
                  var=tk.IntVar())

LoadFileDirecType = UI(window, tk.Button, 15, 5, labtext="Confirm",
                       command=lambda: Buttons.file_direc_type('Loads'))
GeomFileDirecType = UI(window, tk.Button, 16, 5, labtext="Confirm",
                       command=lambda: Buttons.file_direc_type('Geoms'))

# Placeholder widgets
LatSprmin = UI(window, tk.Label, 17, 1)
LatSprmax = UI(window, tk.Label, 17, 1)
LatSprStep = UI(window, tk.Label, 17, 1)

LatSpr = UI(window, tk.Label, 17, 1)
LatSpr1 = UI(window, tk.Label, 17, 1)
LatSpr2 = UI(window, tk.Label, 17, 1)
LatSpr3 = UI(window, tk.Label, 17, 1)
LatSpr4 = UI(window, tk.Label, 17, 1)

LoadDirec = UI(window, tk.Label, 17, 1)
DirecLab = UI(window, tk.Label, 17, 0, labtext=' ')
LoadLab = UI(window, tk.Label, 17, 0, labtext=' ')
AddLoad = UI(window, tk.Label, 17, 2)

GeomLab = UI(window, tk.Label, 17, 3, labtext="")
AddGeom = UI(window, tk.Label, 17, 3, labtext="")
GeomDirLab = UI(window, tk.Label, 17, 3, labtext="")
GeomDirec = UI(window, tk.Label, 17, 4, labtext="")

# Finalise inputs widgets
CheckBut = UI(window, tk.Button, 19, 7, labtext="Check",
              command=Buttons.check_button)
endWindow = UI(window, tk.Button, 19, 8, labtext="OK", command=ExitUI,
               state=tk.DISABLED)

window.mainloop()
