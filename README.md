# framecropper
python quick crop tool
Enables quick rotation, mirror, brightness/contrast, and then cropping of photos
Input can be raw images in CR2/CR3 format or JPEG/PNG/etc.
Output in .jpg (change default parameters in saveCrop function for different filetype/compression)

Requirements
 - Python 3+
 - Numpy
 - Qt6
 - OpenCV
 - rawpy
 - Mouse with left click and scroll wheel

# Screenshot
![demo](https://github.com/SunDude/framecropper/blob/main/exampleCrop.png)

# Installation
Install python and requirements
1. Install python [python.org](https://www.python.org/downloads/)
   - Make sure you tick add to environment variable on windows
3. In powershell/CMD/Terminal run:
 - `pip install numpy`
 - `pip install pyside6`
 - `pip install opencv-python`
 - `pip install rawpy`
 - `pip install PyQt6`

# Usage
In powershell/CMD/Terminal navigate to the location of framecrop.py
run the sript
`python framecrop.py`

 1. Run the python script
 2. Select files to crop from top left (can select multiple)
 3. Select ratio of descired output
 4. Use mouse + mousewheel to define crop, left click to crop
 5. Output files saved to /out folder starting from 0 (manually adjust this bottom left)
