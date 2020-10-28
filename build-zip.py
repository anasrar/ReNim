#!/usr/bin/env python
# script for build ReNimNode.zip

import os
import zipfile

if __name__ == '__main__':
    zipf = zipfile.ZipFile('ReNimNode.zip', 'w', zipfile.ZIP_DEFLATED)

    for dirname, subdirs, files in os.walk('ReNimNode'):
        if '__pycache__' in subdirs:
            subdirs.remove('__pycache__')
        zipf.write(dirname)
        for filename in files:
            zipf.write(os.path.join(dirname, filename))

    zipf.close()