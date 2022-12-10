#!/usr/bin/env python

# --------------------
# MIRROR BLEED
# This plugin will add a mirrored bleed margin to any image
# --------------------

from gimpfu import *
import math

def copy_move_and_flip(img, layer, x, y, w, h, newX, newY, flipAxis) :
    # Make sure the region requested is in range
    iw, ih = img.width, img.height
    if x < 0:
        w = w + x
        newX = newX - x
        x = 0
    if y < 0:
        h = h + y
        newY = newY - y
        y = 0        
    w = min(w, iw - x)
    h = min(h, ih - y)

    # Perform the copy/flip/paste
    if w > 0 and h > 0:
        gimp.pdb.gimp_image_select_rectangle(img, CHANNEL_OP_REPLACE, x, y, w, h)
        gimp.pdb.gimp_edit_copy(layer)
        fltLayer = gimp.pdb.gimp_edit_paste(layer, False)
        gimp.pdb.gimp_item_transform_flip_simple(fltLayer, flipAxis, True, 0)
        gimp.pdb.gimp_layer_set_offsets(fltLayer, newX, newY)
        gimp.pdb.gimp_floating_sel_anchor(fltLayer)


def add_bleed_to_layer(img, layer, left, right, top, bottom) :
    if gimp.pdb.gimp_item_is_group(layer):
        # Bleed children
        numChildren, childIDs = gimp.pdb.gimp_item_get_children(layer)
        for childID in childIDs:
            child = gimp.Item.from_id(childID)
            add_bleed_to_layer(img, child, left, right, top, bottom)

    else:
        # Get layer box
        x, y = gimp.pdb.gimp_drawable_offsets(layer)
        w, h = layer.width, layer.height
        iw, ih = img.width, img.height

        # Move the layer into the center
        gimp.pdb.gimp_layer_set_offsets(layer, x + left, y + top)
        x = x + left
        y = y + top

        if not gimp.pdb.gimp_item_is_text_layer(layer):
            gimp.pdb.gimp_context_set_feather(False)

            # Calculate how much bleed to add
            leftMargin = 0
            rightMargin = 0
            topMargin = 0
            bottomMargin = 0
            if x > 0 and x <= left:
                leftMargin = x
            if (x + w) >= (iw - right) and (x + w) < iw:
                rightMargin = iw - (x + w)
            if y > 0 and y <= top:
                 topMargin = y
            if (y + h) >= (ih - bottom) and (y + h) < ih:
                bottomMargin = ih - (y + h)

            if (leftMargin + rightMargin + topMargin + bottomMargin) > 0:
                # Resize and reposition the layer
                gimp.pdb.gimp_layer_resize(layer, w + leftMargin + rightMargin, h + topMargin + bottomMargin, leftMargin, topMargin)

                # Add left margin
                if leftMargin > 0:
                    copy_move_and_flip(img, layer, x + 1, y, leftMargin, h, x - leftMargin, y, ORIENTATION_HORIZONTAL)

                # Add right margin
                if rightMargin > 0:
                    copy_move_and_flip(img, layer, x + w - rightMargin - 1, y, rightMargin, h, x + w, y, ORIENTATION_HORIZONTAL)

                x = x - leftMargin
                w = w + leftMargin + rightMargin

                # Add top margin
                if topMargin > 0:
                    copy_move_and_flip(img, layer, x, y + 1, w, topMargin, x, y - topMargin, ORIENTATION_VERTICAL)

                # Add bottom margin
                if bottomMargin > 0:
                    copy_move_and_flip(img, layer, x, y + h - bottomMargin - 1, w, bottomMargin, x, y + h, ORIENTATION_VERTICAL)

def dan200_mirror_bleed(img, layer, left, right, top, bottom) :
    # Start
    gimp.progress_init("Please wait ...")
    gimp.pdb.gimp_image_undo_group_start(img)

    try:
        # Resize the image canvas
        gimp.pdb.gimp_image_resize(img, img.width + left + right, img.height + top + bottom, 0, 0)

        # Add bleed to each layer
        gimp.pdb.gimp_selection_none(img)
        for layer in img.layers:
            add_bleed_to_layer(img, layer, left, right, top, bottom)

        # Move all guides
        new_guides = []
        guide = gimp.pdb.gimp_image_find_next_guide(img, 0)
        while guide != 0:
            if guide not in new_guides:
                orientation = gimp.pdb.gimp_image_get_guide_orientation(img, guide)
                pos = gimp.pdb.gimp_image_get_guide_position(img, guide)
                gimp.pdb.gimp_image_delete_guide(img, guide)
                if orientation == ORIENTATION_HORIZONTAL:
                    new_guides.append( gimp.pdb.gimp_image_add_hguide(img, pos + top) )
                else:
                    new_guides.append( gimp.pdb.gimp_image_add_vguide(img, pos + left) )
                guide = gimp.pdb.gimp_image_find_next_guide(img, 0)
            else:
                guide = gimp.pdb.gimp_image_find_next_guide(img, guide)

        # Add some new guides
        if top > 0:
            gimp.pdb.gimp_image_add_hguide(img, top)
        if bottom > 0:
            gimp.pdb.gimp_image_add_hguide(img, img.height - bottom)
        if left > 0:
            gimp.pdb.gimp_image_add_vguide(img, left)
        if right > 0:
            gimp.pdb.gimp_image_add_vguide(img, img.width - right)

    except Exception as err:
        gimp.message("Unexpected error: " + str(err))

    # Finish
    pdb.gimp_image_undo_group_end(img)
    pdb.gimp_progress_end()

register(
    "dan200-mirror-bleed",
    "Add a mirrored bleed margin to any image",
    "Add a mirrored bleed margin to any image",
    "Daniel Ratcliffe",
    "Daniel Ratcliffe",
    "2022",
    "<Image>/Tools/Comic Tools/Add Mirror Bleed",
    "RGB*, GRAY*",
    [
        (PF_INT, "left", "Left", 43),
        (PF_INT, "right", "Right", 43),
        (PF_INT, "top", "Top", 43),
        (PF_INT, "bottom", "Bottom", 43),
    ],
    [],
    dan200_mirror_bleed)

main()
