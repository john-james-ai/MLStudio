# -*- coding:utf-8 -*-
# =========================================================================== #
# Project : MLStudio                                                          #
# File    : \tasks.py                                                         #
# Python  : 3.8.3                                                             #
# --------------------------------------------------------------------------- #
# Author  : John James                                                        #
# Company : nov8.ai                                                           #
# Email   : jjames@nov8.ai                                                    #
# URL     : https://github.com/nov8ai/MLStudio                                #
# --------------------------------------------------------------------------- #
# Created       : Friday, July 17th 2020, 12:34:48 am                         #
# Last Modified : Friday, July 17th 2020, 12:34:49 am                         #
# Modified By   : John James (jjames@nov8.ai)                                 #
# --------------------------------------------------------------------------- #
# License : BSD                                                               #
# Copyright (c) 2020 nov8.ai                                                  #
# =========================================================================== #
"""Inversion of Control: Dependency Injection and Containers for Tasks."""
#%%
from pathlib import Path
import site
PROJECT_DIR = Path(__file__).resolve().parents[2]
site.addsitedir(PROJECT_DIR)

import collections
import dependency_injector.containers as containers
import dependency_injector.providers as providers

from mlstudio.supervised.algorithms.optimization.services import activations
from mlstudio.supervised.algorithms.optimization.services import loss
from mlstudio.supervised.algorithms.optimization.services import regularizers
from mlstudio.supervised.algorithms.optimization.services import tasks
from mlstudio.factories.data import DataProcessors
# --------------------------------------------------------------------------- #
class Task(containers.DeclarativeContainer):
    """IoC container for task providers."""

    regression = providers.Factory(tasks.LinearRegression,
                                          loss=loss.Quadratic(),
                                          data_processor=DataProcessors.regression(),
                                          activation=None)

    binaryclass = providers.Factory(tasks.LogisticRegression,
                                          loss=loss.CrossEntropy(),
                                          data_processor=DataProcessors.binaryclass(),
                                          activation=activations.Sigmoid())     

    multiclass = providers.Factory(tasks.MulticlassClassification,
                                          loss=loss.CategoricalCrossEntropy(),
                                          data_processor=DataProcessors.multiclass(),
                                          activation=activations.Softmax())

