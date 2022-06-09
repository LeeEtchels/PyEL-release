PyEL

Edge Loading Geometric Model

Version 1.0 (27/05/22)

Created by Lee Etchels

Working for the University of Leeds
Institute of Medical and Biological Engineering
in collaboration with:

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
Anaconda version 2021.11 64-bit

Anaconda includes the majority of the
libraries required for the code to run.
In addition you need to install plotly
and plotly kaleido. This can be done from
the command line by entering
1)
conda install -c plotly plotly

and 2)
conda install -c conda-forge python-kaleido

The Deletable.txt files included in the
repository can be deleted, they just make
sure that the required folder structure is
included.

The example geometry point cloud file in
the repository is reasonably large (~180MB)
and has therefore been zipped. Unzip it to the
same location to be able to use it in an
analysis.

Known issue list:

Conventions:

    The x direction is anteroposterior, positive anteriorly.  
    The y direction is superoinferior, positive superiorly.  
    The z direction is mediolateral, positive laterally.  
	Nx, Ny, Nz refer to the x,y,z coordinates of a point on the cup.  
	SNx,SNy,SNz is a vector representing the surface normal at a point.  
	AdjX,AdjY,AdjZ is the contact point transformed to the head frame of reference  
	and rotated according the head orientation at that time.

Libraries used (no known license issues/purchase requirements as of 27/05/22):

* plotly (https://plotly.com/python/) (MIT)
* plotly kaleido (https://github.com/plotly/Kaleido/blob/master/LICENSE.txt) MIT
* pandas (BSD)
* numpy (https://numfocus.salsalabs.org/donate-to-numpy/index.html) (BSD 3-Clause)
* scipy (https://numfocus.salsalabs.org/donate-to-scipy/index.html) (BSD 3-Clause)
* spyder (https://opencollective.com/spyder/donate) (MIT)