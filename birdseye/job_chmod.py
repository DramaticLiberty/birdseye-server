# -*- coding: utf-8 -*-
'''
Hack jobs of all sizes
----------------------

'''
import os
import stat


def chmod_file(file_path):
    st = os.stat(file_path)
    os.chmod(file_path, st.st_mode | stat.S_IRGRP)
    return True
