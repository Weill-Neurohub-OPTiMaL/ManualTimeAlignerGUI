# Manual Time AlignerGUI
We collected multi-modal time series data where a gesture task was performed by a research subject at the onset of recordings. This gesture creates an artifact in all data streams, which can be used to visually align data collected from multiple devices to a common time. Use this simple GUI to fascilitate time-alignment quickly. 

## Install/Setup
The best way to install this code depends on your use case. 

#### Standalone
If you want to use it as a stand-alone package to manually  verify or perform time alignments, simply clone/download
the repo. Setup a python interpreter and install requirements with.
```bash
pip install -r requirements.txt
```
Point the `example.py` script at your source data and you should be good to go.

#### Package Form
If you want to incorporate this code to perform time alignment in your own projects, the best way to install is as 
a python package using pip. Simply add the following line to your 
`requirements.txt` file:
```bash
aligner @ git+https://https://github.com/Weill-Neurohub-OPTiMaL/ManualTimeAlignerGUI.git@main
```
And the run `pip install -r requirements.txt`.
Any updates to the code will be pulled whenever you re-run the above or run `pip install --upgrade common`

If you would like to use a different branch or commit, simply swap the `@main` for `@<branch>` or `@<commit>`.

You can now import the alignment function (`aligner.gui.manual_align`). This function takes one argument and arbitrarily
many keword args. The first argument should be a dataframe which contains timeseries data aligned to "true" time. 
Each keyword argument should be a dataframe with data that needs to be aligned. 

## GUI Usage

The GUI is designed to facilitate manual alignment of arbitrary timeseries to a timeseries assumed to be in "true" time.
The "true time" timeseries is shown in blue, while the aligning timeseries is shown in orange.


For use to be fast, most GUI controls are setup to be key bindings:

#### Time alignment
  - `z`, `x`: **Zoom in/out** on the time axis. The amount of zoon per button press is controlled by the "zoom factor"
  - `Left`, `Right`: **move the viewing window** left and right. The shift amount is controlled by "shift factor"
  - `Shift+Left`, `Shift+Right`: **shift the timeseries** currently being aligned left or right. The size of this shift is
relative to the size of the window and is controlled by the "shift factor"
  - `Ctrl+Shift+Left`, `Ctrl+Shift+Right`: **Fine shift the timeseries** currently being aligned left or right by one
sampling interval.
  - `Up`, `Down`: **Adjust yscale**. Increases or decreases the y scale of the aligning timeseries relative to the base
timeseries. Note that this is for visualization purposes only and does not affect the saved data.

#### GUI Control
  - `Delete`: **Reset the plot**. Resets the plot and the alignment to the default view (and 0.0 offset).
  - `Enter`: **Accept alignment**. Save the current alignment offset and move on to the next timeseries. If this is the
last timeseries, then close the alignment window. If you started the aligner using it's function form, the function will
return a dictionary of alignments, in seconds.
  - `Backspace`: **Previous timeseries**. Return to aligning the previous timeseries.

#### Set Warning Flags
These flags are intended to serve as warnings during downstream processing that either the data or the alignment itself
is questionable and should be treated with caution. These warnings are: (returned as a dict from manual_align)

  - `d`: **data missing warning**: Enough data was missing that this alignment is uncertain. Do not use this unless the 
    missing data is sufficient to impair your ability to perform alignment
  - `s`: **shift warning**: Suspected data shift, alignments do not match across recording. Use this if aligning one 
    part of the data stream means that another part comes significantly out of alignment
  - `f`: **general warning**: Aligner was generally concerned with the quality of the alignment. Use this is you think
    that something is generically bad with the data or alignment
    
    
## Citing and Authorship 
If you use our code, please cite our Journal of Visualized Experiments [paper](https://www.jove.com/methods-collections/2119). 

This repository was written by [Tomek Fraczek](https://github.com/TomekFraczek) and is overseen by [Jeffrey Herron](https://neurosurgery.uw.edu/bio/jeffrey-herron-phd). 

## Funding 
This work was supported by funding from the Weill Neurohub, the National Institutes of Health (UH3NS100544), and the National Science Foundation (DGE-2140004).  
