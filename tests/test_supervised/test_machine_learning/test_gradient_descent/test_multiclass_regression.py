# -*- coding:utf-8 -*-
# =========================================================================== #
# Project : MLStudio                                                          #
# File    : \test_regressor copy.py                                           #
# Python  : 3.8.3                                                             #
# --------------------------------------------------------------------------- #
# Author  : John James                                                        #
# Company : nov8.ai                                                           #
# Email   : jjames@nov8.ai                                                    #
# URL     : https://github.com/nov8ai/MLStudio                                #
# --------------------------------------------------------------------------- #
# Created       : Thursday, July 9th 2020, 7:09:25 am                         #
# Last Modified : Thursday, July 9th 2020, 7:09:25 am                         #
# Modified By   : John James (jjames@nov8.ai)                                 #
# --------------------------------------------------------------------------- #
# License : BSD                                                               #
# Copyright (c) 2020 nov8.ai                                                  #
# =========================================================================== #
"""Integration test for GDRegressor class."""
import numpy as np
import pytest
from pytest import mark
from sklearn.linear_model import SGDClassifier
from sklearn.utils.estimator_checks import parametrize_with_checks
from sklearn.utils.estimator_checks import check_estimator

from mlstudio.supervised.machine_learning.gradient_descent import GDClassifier
from mlstudio.supervised.observers.learning_rate import TimeDecay, StepDecay
from mlstudio.supervised.observers.learning_rate import ExponentialDecay
from mlstudio.supervised.observers.learning_rate import ExponentialStepDecay
from mlstudio.supervised.observers.learning_rate import PolynomialDecay
from mlstudio.supervised.observers.learning_rate import PolynomialStepDecay
from mlstudio.supervised.observers.learning_rate import PowerSchedule
from mlstudio.supervised.observers.learning_rate import BottouSchedule
from mlstudio.supervised.observers.learning_rate import Adaptive
from mlstudio.supervised.observers.early_stop import EarlyStop
from mlstudio.supervised.observers.debugging import GradientCheck
from mlstudio.supervised.core.objectives import CategoricalCrossEntropy
from mlstudio.supervised.core.optimizers import GradientDescentOptimizer
from mlstudio.supervised.core.optimizers import Momentum
from mlstudio.supervised.core.optimizers import Nesterov
from mlstudio.supervised.core.optimizers import Adagrad
from mlstudio.supervised.core.optimizers import Adadelta
from mlstudio.supervised.core.optimizers import RMSprop
from mlstudio.supervised.core.optimizers import Adam, AdaMax, Nadam
from mlstudio.supervised.core.optimizers import AMSGrad, AdamW, QHAdam
from mlstudio.supervised.core.optimizers import QuasiHyperbolicMomentum
from mlstudio.supervised.core.regularizers import L1, L2, L1_L2
from mlstudio.supervised.core import scorers
# --------------------------------------------------------------------------  #
count = 0
early_stops = [None,EarlyStop()]
learning_rates = \
            [None, TimeDecay(), StepDecay(), ExponentialDecay(), 
             ExponentialStepDecay(), PolynomialDecay(), PolynomialStepDecay(), 
             PowerSchedule(), BottouSchedule(), Adaptive()]
scorer_objects = [scorers.Accuracy()]
objectives = [CategoricalCrossEntropy(), CategoricalCrossEntropy(regularizer=L1(alpha=0.01)), 
                        CategoricalCrossEntropy(regularizer=L2(alpha=0.01)), 
                        CategoricalCrossEntropy(regularizer=L1_L2(alpha=0.01, ratio=0.5))]
# optimizers = [
#     GradientDescentOptimizer(), Momentum(), Nesterov(),Adagrad(), Adadelta(),
#     RMSprop(), Adam(), AdaMax(), Nadam(), AMSGrad(), AdamW(), QHAdam(),
#     QuasiHyperbolicMomentum()
# ]

scenarios = [[scorer, objective, early_stop, learning_rate] \
    for scorer in scorer_objects
    for objective in objectives
    for early_stop in early_stops
    for learning_rate in learning_rates
        ]

estimators = [GDClassifier(scorer=scenario[0],
                                       objective=scenario[1], 
                                       early_stop=scenario[2],
                                       learning_rate=scenario[3])
                                       for scenario in scenarios]
@mark.gd
@mark.multiclass
@mark.multiclass_regression_skl
#@mark.skip(reason="takes too long")
@parametrize_with_checks(estimators)
def test_multiclass_regression_sklearn(estimator, check):    
    scorer = estimator.scorer.name
    objective = estimator.objective.name
    early_stop = estimator.early_stop.name if estimator.early_stop else None
    learning_rate = estimator.learning_rate if estimator.learning_rate else None
    regularizer = estimator.objective.regularizer.name if estimator.objective.regularizer else\
        None    
    msg = estimator.description
    print(msg)        
    check(estimator)

@mark.gd
@mark.multiclass
@mark.multiclass_regression
#@mark.skip(reason="takes too long")
def test_multiclass_regression(get_multiclass_regression_data_split):
    X_train, X_test, y_train, y_test = get_multiclass_regression_data_split
    n_within_1_pct = 0
    n_within_10_pct = 0    
    s_num = 0
    failed_models = []

    for estimator in estimators:
        s_num += 1
        scorer = estimator.scorer.name
        objective = estimator.objective.name
        early_stop = estimator.early_stop.name if estimator.early_stop else None
        learning_rate = estimator.learning_rate if estimator.learning_rate else None
        regularizer = estimator.objective.regularizer.name if estimator.objective.regularizer else\
            None    
        msg = "Checking scenario {s}: objective : {ob}, regularizer : {r}\
        scorer : {k}".format(
                s=str(count), ob=str(objective), r=str(regularizer), k=str(scorer))        
        # Fit the model
        estimator.fit(X_train,y_train)
        mls_score = estimator.score(X_test, y_test)
        # Fit sklearn's model
        skl = SGDClassifier(loss='log')
        skl.fit(X_train, y_train)
        skl_score = skl.score(X_test, y_test)
        # Compute pct difference in scores
        rel_diff = (skl_score-mls_score) / skl_score 
        if rel_diff <= 0.01:
            n_within_1_pct += 1
            n_within_10_pct += 1
        elif rel_diff <= 0.1:
            n_within_10_pct += 1
        else:
            pct_off = "Scikit-Learn Score: {s} MLStudio Score: {m} Percent Diff {p}".format(
                s=str(skl_score), m=str(mls_score), p=str(round(rel_diff*100,3))
            )
            scenario = scenario + "\n     " + pct_off 
            failed_models.append(scenario)
    msg = "\nThe following models scored poorly relative to Scikit-Learn"
    for m in failed_models:
        print(m)            
    msg = "\nTotal models evaluated: {t}".format(t=str(s_num))
    print(msg)
    msg = "Total models within 1 pct of Scikit-Learn: {t} ({p}%)".format(t=str(n_within_1_pct),
            p=str(round(n_within_1_pct/s_num*100,3)))
    print(msg)                                                                         
    msg = "Total models within 10 pct of Scikit-Learn: {t} ({p}%)".format(t=str(n_within_10_pct),
            p=str(round(n_within_10_pct/s_num*100,3)))                                                     
    print(msg)




