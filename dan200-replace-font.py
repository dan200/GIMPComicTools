#!/usr/bin/env python

# --------------------
# REPLACE FONT
# This plugin will quickly replace the font of all text layers in the image
# --------------------

from gimpfu import *
import math
import subprocess
import os

def replace_font_in_layer(img, layer, newFontName, resetSpacing) :
    if gimp.pdb.gimp_item_is_group(layer):
        # Upscale children
        numChildren, childIDs = gimp.pdb.gimp_item_get_children(layer)
        for childID in childIDs:
            child = gimp.Item.from_id(childID)
            replace_font_in_layer(img, child, newFontName, resetSpacing)

    elif gimp.pdb.gimp_item_is_text_layer(layer):
        gimp.pdb.gimp_text_layer_set_font(layer, newFontName)
        if resetSpacing:
            gimp.pdb.gimp_text_layer_set_letter_spacing(layer, 0.0)
            gimp.pdb.gimp_text_layer_set_line_spacing(layer, 0.0)


def dan200_replace_font(img, layer, fontName, resetSpacing, currentLayerOnly) :
    # Start
    gimp.progress_init("Please wait ...")
    gimp.pdb.gimp_image_undo_group_start(img)

    # Do the replacement
    if currentLayerOnly:
        replace_font_in_layer(img, layer, fontName, resetSpacing)
    else:
        for layer in img.layers:
            replace_font_in_layer(img, layer, fontName, resetSpacing)

    # Finish
    pdb.gimp_image_undo_group_end(img)
    pdb.gimp_progress_end()

register(
    "dan200-replace-font",
    "Quickly replace the font of all text layers in the image",
    "Quickly replace the font of all text layers in the image",
    "Daniel Ratcliffe",
    "Daniel Ratcliffe",
    "2025",
    "<Image>/Tools/Comic Tools/Replace Font",
    "RGB*, GRAY*",
    [
        (PF_FONT, "fontName", "New font", "Arial"),
        (PF_BOOL, "resetSpacing", "Reset spacing", False),
        (PF_BOOL, "currentLayerOnly", "Current layer (or group) only", False)
    ],
    [],
    dan200_replace_font)

main()
