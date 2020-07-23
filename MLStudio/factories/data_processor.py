# -*- coding:utf-8 -*-
# =========================================================================== #
# Project : MLStudio                                                          #
# File    : \data_processor.py                                                #
# Python  : 3.8.3                                                             #
# --------------------------------------------------------------------------- #
# Author  : John James                                                        #
# Company : nov8.ai                                                           #
# Email   : jjames@nov8.ai                                                    #
# URL     : https://github.com/nov8ai/MLStudio                                #
# --------------------------------------------------------------------------- #
# Created       : Thursday, July 23rd 2020, 1:45:17 am                        #
# Last Modified : Thursday, July 23rd 2020, 1:45:41 am                        #
# Modified By   : John James (jjames@nov8.ai)                                 #
# --------------------------------------------------------------------------- #
# License : BSD                                                               #
# Copyright (c) 2020 nov8.ai                                                  #
# =========================================================================== #
"""Inversion of Control: Dependency Injection and Containers for data processors."""
#%%
from pathlib import Path
import site
PROJECT_DIR = Path(__file__).resolve().parents[2]
site.addsitedir(PROJECT_DIR)

import collections
import dependency_injector.containers as containers
import dependency_injector.providers as providers
from sklearn.preprocessing import LabelBinarizer, LabelEncoder

from mlstudio.utils.data_manager import RegressionData
from mlstudio.utils.data_manager import BinaryClassData
from mlstudio.utils.data_manager import MultiClassData
# --------------------------------------------------------------------------- #
class DataProcessors(containers.DeclarativeContainer):
    """IoC container for data processor providers."""

    regression = providers.Factory(RegressionData)

    binary_classification = providers.Factory(BinaryClassData,
                                            encoder=LabelEncoder())

    multiclass_classification = providers.Factory(MultiClassData,
                                        encoder=LabelEncoder(),
                                        binarizer=LabelBinarizer())                             
