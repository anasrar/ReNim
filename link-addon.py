#!/usr/bin/env python
# script for link directory ReNimNode to Blender addon

import os

if __name__ == '__main__':
    print("Blender Path: ")
    blenderPathAddon = input()
    src = os.path.join(os.path.dirname(__file__), "ReNimNode")
    dst = os.path.join(blenderPathAddon, "ReNimNode")
    os.symlink(src, dst)
