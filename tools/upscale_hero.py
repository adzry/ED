#!/usr/bin/env python3
"""Upscale the hook hero image 4x with OpenCV EDSR super-resolution (model: EDSR_x4.pb, path in $EDSR_MODEL).

The source panel on the reference board is only ~150 px wide; plain resizing to a half-screen hero looks soft,
so it is super-resolved once here and the result is committed as assets/inserts/hook_hero.png.
"""
import os
import sys

import cv2

src, dst = sys.argv[1], sys.argv[2]
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(os.environ.get("EDSR_MODEL", "models/EDSR_x4.pb"))
sr.setModel("edsr", 4)
img = cv2.imread(src)
up = sr.upsample(img)
# Gentle unsharp mask to restore edge contrast after upscaling.
blur = cv2.GaussianBlur(up, (0, 0), 1.2)
up = cv2.addWeighted(up, 1.25, blur, -0.25, 0)
cv2.imwrite(dst, up)
print(f"{src} {img.shape[1]}x{img.shape[0]} → {dst} {up.shape[1]}x{up.shape[0]}")
