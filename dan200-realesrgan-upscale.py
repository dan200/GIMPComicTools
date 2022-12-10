#!/usr/bin/env python

# --------------------
# Real-ESRGAN Upscaler
# This plugin will upscale images using the Real-ESGRAN upscaling engine
# --------------------

from gimpfu import *
import math
import subprocess
import os

# The location of the Real-ESRGAN EXE
# Edit these variables if realesgran is installed in a different location
# Real-ESRGAN can be downloaded from: https://github.com/xinntao/Real-ESRGAN
REALESRGAN_EXE = "realesrgan-ncnn-vulkan.exe"
REALESRGAN_PATH = os.path.dirname(__file__) + "\\realesrgan\\" + REALESRGAN_EXE

def upscale_layer(img, layer, scale) :
    if gimp.pdb.gimp_item_is_group(layer):
        # Upscale children
        numChildren, childIDs = gimp.pdb.gimp_item_get_children(layer)
        for childID in childIDs:
            child = gimp.Item.from_id(childID)
            upscale_layer(img, child, scale)

    else:
        # Get layer box
        x, y = gimp.pdb.gimp_drawable_offsets(layer)
        w, h = layer.width, layer.height

        if gimp.pdb.gimp_item_is_text_layer(layer):
            # Scale the bounding box
            gimp.pdb.gimp_layer_set_offsets(layer, x * scale, y * scale)
            gimp.pdb.gimp_text_layer_resize(layer, w * scale, h * scale)

            # Scale the text properties
            fontSize, fontSizeUnit = gimp.pdb.gimp_text_layer_get_font_size(layer)
            gimp.pdb.gimp_text_layer_set_font_size(layer, fontSize * scale, fontSizeUnit)

            indent = gimp.pdb.gimp_text_layer_get_indent(layer)
            gimp.pdb.gimp_text_layer_set_indent(layer, indent * scale)

            lineSpacing = gimp.pdb.gimp_text_layer_get_line_spacing(layer)
            gimp.pdb.gimp_text_layer_set_line_spacing(layer, lineSpacing * scale)

            letterSpacing = gimp.pdb.gimp_text_layer_get_letter_spacing(layer)
            gimp.pdb.gimp_text_layer_set_letter_spacing(layer, letterSpacing * scale)

        else:
            # Save the layer to disk
            tempImagePath = gimp.pdb.gimp_temp_name("png")
            gimp.pdb.file_png_save_defaults( img, layer, tempImagePath, tempImagePath )

            # Upscale it
            tempOutputImagePath = gimp.pdb.gimp_temp_name("png")
            subprocess.call([REALESRGAN_EXE, "-i", tempImagePath, "-o", tempOutputImagePath, "-s", str(scale)], executable=REALESRGAN_PATH)

            # Load it back in
            tempImage = gimp.pdb.file_png_load(tempOutputImagePath, tempOutputImagePath)
            tempLayer = tempImage.layers[0]

            # Resize and clear the original layer
            gimp.pdb.gimp_layer_resize(layer, w * scale, h * scale, 0, 0)
            gimp.pdb.gimp_layer_set_offsets(layer, x * scale, y * scale)
            gimp.pdb.gimp_edit_clear(layer)

            # Copy the loaded image into the original layer
            gimp.pdb.gimp_edit_copy(tempLayer)
            fltLayer = gimp.pdb.gimp_edit_paste(layer, False)
            gimp.pdb.gimp_floating_sel_anchor(fltLayer)

            # Clean up
            gimp.pdb.gimp_image_delete(tempImage)
            os.remove(tempImagePath)
            os.remove(tempOutputImagePath)

def dan200_realesrgan_upscale(img, layer, scale) :
    # Check realesrgan is installed
    if not os.path.exists(REALESRGAN_PATH):
        gimp.message("Could not find " + REALESRGAN_PATH + "\Real-ESRGAN can be downloaded from https://github.com/xinntao/Real-ESRGAN")
        return

    # Start
    gimp.progress_init("Please wait ...")
    gimp.pdb.gimp_image_undo_group_start(img)

    try:
        # Resize each layer
        gimp.pdb.gimp_selection_none(img)
        for layer in img.layers:
            upscale_layer(img, layer, scale)

        # Resize the image
        gimp.pdb.gimp_image_resize_to_layers(img)

    except Exception as err:
        gimp.message("Unexpected error: " + str(err))

    # Finish
    pdb.gimp_image_undo_group_end(img)
    pdb.gimp_progress_end()

register(
    "dan200-realesgran-upscale",
    "Upscale images using the Real-ESGRAN upscaling engine",
    "Upscale images using the Real-ESGRAN upscaling engine",
    "Daniel Ratcliffe",
    "Daniel Ratcliffe",
    "2022",
    "<Image>/Tools/ComicTools/Real-ESRGAN Upscale",
    "RGB*, GRAY*",
    [
        (PF_SPINNER, "scale", "Scale", 4, (2, 4, 1)),
    ],
    [],
    dan200_realesrgan_upscale)

main()
