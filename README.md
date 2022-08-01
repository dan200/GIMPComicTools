# Tesseract OCR for GIMP

A GIMP plugin to quickly convert images of text into text layers using the [Tesseract](https://github.com/tesseract-ocr/tesseract) OCR engine.

# Demonstration

<iframe width="560" height="315" src="https://www.youtube.com/embed/fCOGOqIhByM" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

# Install Instructions

1. Download this GitHub repository (by clicking "Code" then "Download ZIP" in the top right corner of this page)
2. Extract the contents to your GIMP "plug-ins" folder. On Windows, this will be something like: *C:\Users\your_name_in\AppData\Roaming\GIMP\2.10\plug-ins*
3. Download and install the Tesseract OCR engine. Prebuilt binaries are available for download [here](https://tesseract-ocr.github.io/tessdoc/Home.html#binaries).
4. (Optional) If you installed Tesseract to a custom location, or you're not using Windows, open *dan200-tesseract-ocr.py* in a text editor and change *TESSERACT_PATH* to your new install location. Otherwise, you can safely ignore this step.
