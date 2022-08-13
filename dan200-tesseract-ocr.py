#!/usr/bin/env python

# --------------------
# TESSERACT OCR
# This plugin will quickly convert images of text into text layers using the Tesseract OCR engine
# --------------------

from gimpfu import *
import math
import subprocess
import os
import xml.etree.ElementTree as ET

# The location of tesseract.exe
# Edit these variables if tesseeract is installed in a different location
TESSERACT_EXE = "tesseract.exe"
TESSERACT_PATH = "C:\\Program Files\\Tesseract-OCR\\" + TESSERACT_EXE

OCR_MODE_WORDS = 0
OCR_MODE_LINES = 1
OCR_MODE_BLOCKS = 2

def add_text_layer(img, parentLayer, text, fontName, fontSize, x, y, w, h, letterSpacing, lineSpacing) :
    # Add the text
    textLayer = gimp.pdb.gimp_text_layer_new(img, text, fontName, fontSize, PIXELS)
    gimp.pdb.gimp_image_insert_layer(img, textLayer, parentLayer, 0)
    gimp.pdb.gimp_layer_set_offsets(textLayer, x, y)
    gimp.pdb.gimp_text_layer_resize(textLayer, w, h)
    gimp.pdb.gimp_text_layer_set_justification(textLayer, TEXT_JUSTIFY_CENTER)
    gimp.pdb.gimp_text_layer_set_letter_spacing(textLayer, letterSpacing)
    gimp.pdb.gimp_text_layer_set_line_spacing(textLayer, lineSpacing)

def measure_font_metrics(fontName, testText) :
    # Draw a line of text to an offscreen image
    testFontSize = 100
    padding = 1
    w,h,a,d = gimp.pdb.gimp_text_get_extents_fontname(testText, testFontSize, PIXELS, fontName)
    tempImage = gimp.pdb.gimp_image_new(w + 2 * padding, h + 2 * padding, RGB)
    tempLayer = gimp.pdb.gimp_layer_new(tempImage, w + 2 * padding, h + 2 * padding, RGB_IMAGE, "temp", 100, 0)
    gimp.pdb.gimp_image_insert_layer(tempImage, tempLayer, None, 0)
    gimp.pdb.gimp_drawable_fill(tempLayer, FILL_WHITE)
    tempFlt = gimp.pdb.gimp_text_fontname(tempImage, tempLayer, padding, padding, testText, -1, FALSE, testFontSize, PIXELS, fontName)
    gimp.pdb.gimp_floating_sel_anchor(tempFlt)

    # Measure how many pixels the drawn text actually covers
    gimp.pdb.gimp_image_select_contiguous_color(tempImage, CHANNEL_OP_REPLACE, tempLayer, 0, 0)
    gimp.pdb.gimp_selection_invert(tempImage)
    nonEmpty, x1, y1, x2, y2 = gimp.pdb.gimp_selection_bounds(tempImage)
    x1 = x1 - padding
    x2 = x2 - padding
    y1 = y1 - padding
    y2 = y2 - padding
    headerHeight = y1
    textHeight = (y2 - y1)
    footerHeight = (h - y2)

    # Cleanup
    gimp.pdb.gimp_image_delete(tempImage)

    # Calculate and return some metrics to help with calculations
    result = {}
    result["headerLineHeightFraction"] = float(headerHeight) / float(h)
    result["textLineHeightFraction"] = float(textHeight) / float(h)
    result["footerLineHeightFraction"] = float(footerHeight) / float(h)
    result["lineHeightToFontSize"] = float(testFontSize) / float(h)
    return result

def add_text_in_box(img, parentLayer, text, fontName, x, y, w, h) :
    # Split the text into lines
    lines = text.splitlines()

    # Determine the font size
    if len(lines) <= 1:
        firstLineFontMetrics = measure_font_metrics(fontName, text)
        lastLineFontMetrics = firstLineFontMetrics
    else:
        firstLineFontMetrics = measure_font_metrics(fontName, text[0])
        lastLineFontMetrics = measure_font_metrics(fontName, text[len(lines) - 1])
    visibleLines = len(lines) - firstLineFontMetrics["headerLineHeightFraction"] - lastLineFontMetrics["footerLineHeightFraction"]
    lineHeight = h / visibleLines
    header = lineHeight * firstLineFontMetrics["headerLineHeightFraction"]
    footer = lineHeight * lastLineFontMetrics["footerLineHeightFraction"]
    fontSize = int( round( lineHeight * firstLineFontMetrics["lineHeightToFontSize"] ) )

    # Determine the letter spacing
    if len(lines) <= 1:
        longestLine = text
        longestLineWidth,_,_,_ = gimp.pdb.gimp_text_get_extents_fontname(text, fontSize, PIXELS, fontName)
    else:
        longestLine = ""
        longestLineWidth = 0
        for line in lines:
            lineWidth,_,_,_ = gimp.pdb.gimp_text_get_extents_fontname(line, fontSize, PIXELS, fontName)
            if lineWidth > longestLineWidth:
                longestLine = line
                longestLineWidth = lineWidth
    numLetterSpacesInLongestLine = len(longestLine) - 1
    if numLetterSpacesInLongestLine > 0:
        letterSpacing = float(w - longestLineWidth) / float(numLetterSpacesInLongestLine)
    else:
        letterSpacing = 0

    # Determine the line spacing
    fullHeight = h + header + footer
    if len(lines) <= 1:
        lineSpacing = 0
    else:
        numLineSpaces = len(lines) - 1
        _,outputTextHeight,_,_ = gimp.pdb.gimp_text_get_extents_fontname(text, fontSize, PIXELS, fontName)
        lineSpacing = float(fullHeight - outputTextHeight) / float(numLineSpaces)

    # Add the text
    xPadding = 10
    yPadding = 5
    add_text_layer(img, parentLayer, text, fontName, fontSize, x - xPadding, y - header, w + 2 * xPadding, fullHeight + yPadding, letterSpacing, lineSpacing)

def get_box_from_xml_element(element) :
    x = int(element.get("HPOS"))
    y = int(element.get("VPOS"))
    w = int(element.get("WIDTH"))
    h = int(element.get("HEIGHT"))
    return x, y, w, h

def OCR_current_selection(img, inputLayer, outputLayerGroup, bgLayer, fontName, mode) :
    # Get selection bounds
    _, x1, y1, _, _ = gimp.pdb.gimp_selection_bounds(img)

    # Copy the selection to a new image
    gimp.pdb.gimp_edit_copy(inputLayer)
    tempImage = gimp.pdb.gimp_edit_paste_as_new_image()

    # Draw the background
    gimp.pdb.gimp_drawable_edit_fill(bgLayer, FILL_BACKGROUND)
    gimp.pdb.gimp_displays_flush()

    # Save it to disk
    tempImagePath = gimp.pdb.gimp_temp_name("png")
    gimp.pdb.file_png_save_defaults( tempImage, tempImage.active_drawable, tempImagePath, tempImagePath )

    # OCR it
    tempXMLPath = gimp.pdb.gimp_temp_name("xml")
    process = subprocess.call([TESSERACT_EXE, tempImagePath, tempXMLPath[:-4], "alto"], executable=TESSERACT_PATH)

    # Read in the OCR xml output
    ocrResults = ""
    ns = { "alto" : "http://www.loc.gov/standards/alto/ns-v3#" }
    ocrXML = ET.parse(tempXMLPath)
    rootObj = ocrXML.getroot()
    layoutObj = rootObj.find("alto:Layout", ns)

    # Add the text
    if mode == OCR_MODE_WORDS:
        # Extract each word individually
        for pageObj in layoutObj.findall("alto:Page", ns):
            for printSpaceObj in pageObj.findall("alto:PrintSpace", ns):
                for composedBlockObj in printSpaceObj.findall("alto:ComposedBlock", ns):
                    for textBlockObj in composedBlockObj.findall("alto:TextBlock", ns):
                        for textLineObj in textBlockObj.findall("alto:TextLine", ns):
                            for stringObj in textLineObj.findall("alto:String", ns):
                                content = stringObj.get("CONTENT")
                                x, y, w, h = get_box_from_xml_element(stringObj)
                                add_text_in_box(img, outputLayerGroup, content, fontName, x1 + x, y1 + y, w, h)
                                gimp.pdb.gimp_displays_flush()

    elif mode == OCR_MODE_LINES:
        # Extract each line individually
        for pageObj in layoutObj.findall("alto:Page", ns):
            for printSpaceObj in pageObj.findall("alto:PrintSpace", ns):
                for composedBlockObj in printSpaceObj.findall("alto:ComposedBlock", ns):
                    for textBlockObj in composedBlockObj.findall("alto:TextBlock", ns):
                        for textLineObj in textBlockObj.findall("alto:TextLine", ns):
                            content = ""
                            x, y, w, h = get_box_from_xml_element(textLineObj)
                            for stringObj in textLineObj.findall("alto:String", ns):
                                content = content + stringObj.get("CONTENT") + " "
                            content = content.strip(" ")
                            add_text_in_box(img, outputLayerGroup, content, fontName, x1 + x, y1 + y, w, h)
                            gimp.pdb.gimp_displays_flush()

    elif mode == OCR_MODE_BLOCKS:
        # Extract each block individually
        for pageObj in layoutObj.findall("alto:Page", ns):
            for printSpaceObj in pageObj.findall("alto:PrintSpace", ns):
                for composedBlockObj in printSpaceObj.findall("alto:ComposedBlock", ns):
                    content = ""
                    x, y, w, h = get_box_from_xml_element(composedBlockObj)
                    for textBlockObj in composedBlockObj.findall("alto:TextBlock", ns):
                        for textLineObj in textBlockObj.findall("alto:TextLine", ns):                                
                            for stringObj in textLineObj.findall("alto:String", ns):
                                content = content + stringObj.get("CONTENT") + " "                                    
                            content = content.strip(" ") + "\n"
                    content = content.strip("\n")
                    add_text_in_box(img, outputLayerGroup, content, fontName, x1 + x, y1 + y, w, h)
                    gimp.pdb.gimp_displays_flush()

    # Clean up
    os.remove(tempImagePath)
    os.remove(tempXMLPath)

def dan200_tesseract_ocr(img, layer, fontName, outputGroupName, lineByLine) :
    # Check tesseract is installed
    if not os.path.exists(TESSERACT_PATH):
        gimp.message("Could not find " + TESSERACT_PATH + "\nSee README.md for install instructions.")
        return

    # Check the current selection
    nonEmpty, _, _, _, _ = gimp.pdb.gimp_selection_bounds(img)
    if nonEmpty == False:
        gimp.message("Nothing selected")
        return

    # Check the current layer
    if gimp.pdb.gimp_item_is_text_layer(layer):
        gimp.message("OCR can only be performed on bitmap layers")
        return

    # Start
    gimp.progress_init("Please wait ...")
    gimp.pdb.gimp_image_undo_group_start(img)

    try:
        # Create a layer group for storing the OCR output
        ocrLayerGroup = gimp.pdb.gimp_image_get_layer_by_name(img, outputGroupName) 
        if ocrLayerGroup == None:
            ocrLayerGroup = gimp.pdb.gimp_layer_group_new(img)
            gimp.pdb.gimp_layer_set_name(ocrLayerGroup, "OCR")
            gimp.pdb.gimp_image_insert_layer(img, ocrLayerGroup, None, 0)

        # Create a layer for drawing the background
        bgLayer = None
        numChildren, childIDs = gimp.pdb.gimp_item_get_children(ocrLayerGroup)
        for childID in childIDs:
            child = gimp.Item.from_id(childID)
            if gimp.pdb.gimp_item_is_layer(child) and gimp.pdb.gimp_item_get_name(child) == "Background":
                bgLayer = child
                break
        if bgLayer == None:
            bgLayer = gimp.pdb.gimp_layer_new(img, img.width, img.height, RGBA_IMAGE, "Background", 100, 0)
            gimp.pdb.gimp_image_insert_layer(img, bgLayer, ocrLayerGroup, 0)

        # Convert the selection to a path
        gimp.pdb.plug_in_sel2path(img, layer)
        wholeSelectionPath = img.vectors[0]

        singleIslandPath = gimp.Vectors(img, "Selection Island")
        gimp.pdb.gimp_image_add_vectors(img, singleIslandPath, 0)
        
        # For each stroke in the path
        for wholeSelectionStroke in wholeSelectionPath.strokes:
            # Convert the stroke to a new path
            points, closed = wholeSelectionStroke.points
            singleIslandStroke = gimp.VectorsBezierStroke(singleIslandPath, points, closed)

            # Create a selection from the new path
            gimp.pdb.gimp_image_select_item(img, CHANNEL_OP_REPLACE, singleIslandPath)
            gimp.pdb.gimp_selection_shrink(img, 1)

            # Delete the new path
            singleIslandPath.remove_stroke(singleIslandStroke)

            # OCR the new selection
            ocrMode = OCR_MODE_LINES if lineByLine else OCR_MODE_BLOCKS
            OCR_current_selection(img, layer, ocrLayerGroup, bgLayer, fontName, ocrMode)

        # Delete the temporary paths
        gimp.pdb.gimp_image_remove_vectors(img, wholeSelectionPath)
        gimp.pdb.gimp_image_remove_vectors(img, singleIslandPath)

        # Deselect all
        gimp.pdb.gimp_selection_none(img)

    except Exception as err:
        gimp.message("Unexpected error: " + str(err))

    # Finish
    pdb.gimp_image_undo_group_end(img)
    pdb.gimp_progress_end()

register(
    "dan200-tesseract-ocr",
    "Quickly convert images of text into text layers using the Tesseract OCR engine",
    "Quickly convert images of text into text layers using the Tesseract OCR engine",
    "Daniel Ratcliffe",
    "Daniel Ratcliffe",
    "2022",
    "<Image>/Tools/Tesseract OCR",
    "RGB*, GRAY*",
    [
        (PF_FONT, "fontName", "Output font", "Arial"),
        (PF_STRING, "outputGroupName", "Output layer group name", "OCR"),
        (PF_BOOL, "lineByLine", "Output each line seperately", False),
    ],
    [],
    dan200_tesseract_ocr)

main()
