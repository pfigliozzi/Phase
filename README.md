# Phase
A GUI for creating and displaying phase masks for a Liquid Crystal on Silicon (LCoS) Spatial Light Modulator (SLM)

## Features
* Can load a multiple image files from a text file or a Hamamatsu .lst file (bitmap images only)
* Phase maks can be modified with Zernike functions (e.g. astigmatism, coma, lens...)
* A bounding box can be selected so the Zernike function is applied only to that area
* Modified masks can be saved for later use or use in other software (bitmap images only)
* The phase function can be displayed on a second monitor to display on the SLM (Windows Only)

![Phase Screenshot](https://i.imgur.com/Zq2KUgC.png)

## Getting Started
1. To start the GUI, download this repository and navigate a CMD Prompt to the "Phase" directory. The GUI can be started with the command "python main_gui.py" entered in the command prompt. (Note: you must have python installed in order for the software to run. I recommend using the [Anaconda Python Distribution](https://store.continuum.io/cshop/anaconda/).)
2. Start by loading a list of images (File-> Open Image List...) and use the dialog to select the image list file (see the examples folder for an idea on how to structure a list file). 
3. The file names of all the images are listed in the list pane on the left. Selecting one will automatically load that image and display it in the pane on the very right.
4. The right pane displays two masks, the Base Mask is a copy of the image file currently selected in the left list box, while the Modified Mask shows your Base Mask with any Zernike functions added to it.
5. The middle pane allows you to add or subtract Zernike functions from your base mask. As changes are made, the Modified Mask image will update to show you what the mask will look like with the applied function(s). The Zernike function boxes must contain only numbers. While the cursor is in entry box for one of the Zernike functions, the UP and DOWN arrow keys can be used to increment and decrement the value to the left of the cursor.
6. Once you are satisfied with the changes to your mask, you can save it as a bitmap using File->Save Mask Bitmap... and follow the dialog window to save.
