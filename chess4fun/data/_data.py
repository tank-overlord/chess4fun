# -*- coding: utf-8 -*-

# Author: Tank Overlord <TankOverLord88@gmail.com>
#
# License: LGPL-3.0

import pathlib

data_root_path = pathlib.Path.home() / ".chess4fun"

if not data_root_path.exists():
    try:
        data_root_path.mkdir(parents=True, exist_ok=True)
    except:
        raise IOError(f"cannot create data root path: {data_root_path}")
