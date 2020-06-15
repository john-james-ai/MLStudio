#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ============================================================================ #
# Project : MLStudio                                                           #
# Version : 0.1.0                                                              #
# File    : observers.py                                                       #
# Python  : 3.8.2                                                              #
# ---------------------------------------------------------------------------- #
# Author  : John James                                                         #
# Company : DecisionScients                                                    #
# Email   : jjames@decisionscients.com                                         #
# URL     : https://github.com/decisionscients/MLStudio                        #
# ---------------------------------------------------------------------------- #
# Created       : Sunday, March 15th 2020, 7:27:16 pm                          #
# Last Modified : Sunday, March 15th 2020, 7:37:00 pm                          #
# Modified By   : John James (jjames@decisionscients.com)                      #
# ---------------------------------------------------------------------------- #
# License : BSD                                                                #
# Copyright (c) 2020 DecisionScients                                           #
# ============================================================================ #
"""Module containing functionality called during the training process.

Note: The ObserverList and Observer abstract base classes were inspired by
the Keras implementation.  
"""
from abc import ABC, abstractmethod, ABCMeta

import datetime
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

from mlstudio.utils.validation import validate_int, validate_zero_to_one
from mlstudio.utils.validation import validate_metric
# --------------------------------------------------------------------------- #
#                             CALLBACK LIST                                   #
# --------------------------------------------------------------------------- #
class ObserverList:
    """Container of observers."""

    def __init__(self, observers=None):
        """ObserverList constructor
        
        Parameters
        ----------
        observers : list
            List of 'Observer' instances.        
        """
        observers = observers or []
        self.observers = [c for c in observers]        
        self.params = {}
        self.model = None

    def append(self, observer):
        """Appends observer to list of observers.
        
        Parameters
        ----------
        observer : Observer instance            
        """
        self.observers.append(observer)

    def set_params(self, params):
        """Sets the parameters variable, and in list of observers.
        
        Parameters
        ----------
        params : dict
            Dictionary containing model parameters
        """
        self.params = params
        for observer in self.observers:
            observer.set_params(params)

    def set_model(self, model):
        """Sets the model variable, and in the list of observers.
        
        Parameters
        ----------
        model : Estimator or subclass instance 
        
        """
        self.model = model
        for observer in self.observers:
            observer.set_model(model)

    def on_batch_begin(self, batch, log=None):
        """Calls the `on_batch_begin` methods of its observers.

        Parameters
        ----------
        batch : int
            Current training batch

        log: dict
            Currently no data is set to this parameter for this class. This may
            change in the future.
        """
        log = log or {}
        for observer in self.observers:
            observer.on_batch_begin(batch, log)

    def on_batch_end(self, batch, log=None):
        """Calls the `on_batch_end` methods of its observers.
        
        Parameters
        ----------
        batch : int
            Current training batch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """
        log = log or {}
        for observer in self.observers:
            observer.on_batch_end(batch, log)

    def on_epoch_begin(self, epoch, log=None):
        """Calls the `on_epoch_begin` methods of its observers.

        Parameters
        ----------        
        epoch: integer
            Current training epoch

        log: dict
            Currently no data is passed to this argument for this method
            but that may change in the future.
        """
        log = log or {}
        for observer in self.observers:
            observer.on_epoch_begin(epoch, log)

    def on_epoch_end(self, epoch, log=None):
        """Calls the `on_epoch_end` methods of its observers.
        This function should only be called during train mode.

        Parameters
        ----------
        epoch: int
            Current training epoch
        
        log: dict
            Metric results for this training epoch, and for the
            validation epoch if validation is performed.
        """
        log = log or {}
        for observer in self.observers:
            observer.on_epoch_end(epoch, log)

    def on_train_begin(self, log=None):
        """Calls the `on_train_begin` methods of its observers.

        Parameters
        ----------
        log: dict
            Currently no data is passed to this argument for this method
                but that may change in the future.
        """
        for observer in self.observers:
            observer.on_train_begin(log)

    def on_train_end(self, log=None):
        """Calls the `on_train_end` methods of its observers.

        Parameters
        ----------
        log: dict
            Currently no data is passed to this argument for this method
                but that may change in the future.
        """
        for observer in self.observers:
            observer.on_train_end(log)

    def __iter__(self):
        return iter(self.observers)

# --------------------------------------------------------------------------- #
#                             CALLBACK CLASS                                  #
# --------------------------------------------------------------------------- #
class Observer(ABC, BaseEstimator):
    """Abstract base class used to build new observers."""
    def __init__(self):
        """Observer class constructor."""
        self.params = None
        self.model = None

    def set_params(self, params):
        """Sets parameters from estimator.

        Parameters
        ----------
        params : dict
            Dictionary containing estimator parameters
        """ 
        self.params = params

    def set_model(self, model):
        """Stores model in Observer object.

        Parameters
        ----------
        model : Estimator
            Estimator object
        """
        self.model = model

    def on_batch_begin(self, batch, log=None):
        """Logic executed at the beginning of each batch.

        Parameters
        ----------
        batch : int
            Current training batch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """        
        pass

    def on_batch_end(self, batch, log=None):   
        """Logic executed at the end of each batch.
        
        Parameters
        ----------
        batch : int
            Current training batch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """                
        pass

    def on_epoch_begin(self, epoch, log=None):
        """Logic executed at the beginning of each epoch.
        
        Parameters
        ----------
        epoch : int
            Current epoch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """                
        pass

    def on_epoch_end(self, epoch, log=None):
        """Logic executed at the end of each epoch.
        
        Parameters
        ----------
        epoch : int
            Current epoch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """                      
        pass

    def on_train_begin(self, log=None):
        """Logic executed at the beginning of training.
        
        Parameters
        ----------        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """                      
        pass

    def on_train_end(self, log=None):
        """Logic executed at the end of training.
        
        Parameters
        ----------        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """               
        pass
# --------------------------------------------------------------------------- #
#                             PERFORMANCE BASE                                #
# --------------------------------------------------------------------------- #
class PerformanceObserver(Observer):
    """Base class for performance observers."""

    def __init__(self, metric='train_cost', scorer=None, 
                 epsilon=1e-3, patience=5): 
        super(PerformanceObserver, self).__init__()       
        self.name = "Performance Base Observer"
        self.metric = metric        
        self.scorer = scorer
        self.epsilon = epsilon
        self.patience = patience        

    @property
    def stabilized(self):
        return self._stabilized

    @property
    def best_results(self):
        return self._best_results

    @property
    def critical_points(self):
        return self._critical_points

    def get_performance_data(self):
        d = {'Epoch': self._epoch_log, 'Performance': self._performance_log,
             'Baseline': self._baseline_log, 'Relative Change': self._relative_change_log,
             'Improvement': self._improvement_log,'Iters No Change': self._iter_no_improvement_log,
             'Stability': self._stability_log, 'Best Epochs': self._best_epochs_log}
        df = pd.DataFrame(data=d)
        return df
       
    def _validate(self):        
        validate_zero_to_one(param=self.epsilon, param_name='epsilon',
                             left='closed', right='closed')       
        validate_int(param=self.patience, param_name='patience',
                     minimum=0, left='open', right='open')

    def on_train_begin(self, log=None):                
        """Sets key variables at beginning of training.        
        
        Parameters
        ----------
        log : dict
            Contains no information
        """        
        log = log or {}        
        self._validate()
        # Private variables
        self._baseline = None        
        self._iter_no_improvement = 0
        self._better = None   
        self._stabilized = False
        self._significant_improvement = False

        # Implicit dependencies
        if 'score' in self.metric:
            try:                
                self._scorer = self.model.scorer
                self._better = self._scorer.better
            except:
                e = self.name + " requires a scorer object for 'score' metrics."
                raise TypeError(e)
        else:
            self._better = np.less

        # Validation
        validate_metric(self.metric)
        validate_zero_to_one(param=self.epsilon, param_name='epsilon',
                             left='open', right='open')
        validate_int(param=self.patience, param_name='patience')

        # log data
        self._epoch_log = []
        self._performance_log = []
        self._baseline_log = []
        self._relative_change_log = []
        self._improvement_log = []
        self._iter_no_improvement_log = []
        self._stability_log = []
        self._best_epochs_log = []                       

    def _update_log(self, current, log):
        """Creates log dictionary of lists of performance results."""
        self._epoch_log.append(log.get('epoch'))
        self._performance_log.append(log.get(self.metric))
        self._baseline_log.append(self._baseline)
        self._relative_change_log.append(self._relative_change)
        self._improvement_log.append(self._significant_improvement)
        self._iter_no_improvement_log.append(self._iter_no_improvement)
        self._stability_log.append(self._stabilized)
        self._best_epochs_log.append(self._best_epoch)

    def _metric_improved(self, current):
        """Returns true if the direction and magnitude of change indicates improvement"""
        # Determine if change is in the right direction.
        if self._better(current, self._baseline):
            return True
        else:
            return False

    def _significant_relative_change(self, current):        
        self._relative_change = abs(current-self._baseline) / abs(self._baseline)
        return self._relative_change > self.epsilon                

    def _process_improvement(self, current, log=None):
        """Sets values of parameters and attributes if improved."""
        self._iter_no_improvement = 0            
        self._stabilized = False
        self._baseline = current 
        self._best_epoch = log.get('epoch')        

    def _process_no_improvement(self, log=None):
        """Sets values of parameters and attributes if no improved."""    
        self._iter_no_improvement += 1  
        if self._iter_no_improvement >= self.patience:
            self._stabilized = True               

    def _get_current_value(self, log):
        """Obtain the designated metric from the log."""
        current = log.get(self.metric)
        if not current:
            msg = "{m} was not found in the log.".format(m=self.metric)
            raise KeyError(msg)     
        return current

    def on_epoch_end(self, epoch, log=None):
        """Logic executed at the end of each epoch.
        
        Parameters
        ----------
        epoch : int
            Current epoch
        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """                  
        log = log or {}   
        
        # Initialize state variables        
        self._significant_improvement = False
        self._relative_change = 0
        
        # Obtain current performance
        current = self._get_current_value(log)

        # Handle first iteration as an improvement by default
        if self._baseline is None:                             # First iteration
            self._significant_improvement = True
            self._process_improvement(current, log)    

        # Otherwise, evaluate the direction and magnitude of the change        
        else:
            self._significant_improvement = self._metric_improved(current) and \
                self._significant_relative_change(current)

            if self._significant_improvement:
                self._process_improvement(current, log)
            else:
                self._process_no_improvement()

        # Log results
        self._update_log(current, log)


    def on_train_end(self, log=None):
        """Logic executed at the end of training.
        
        Parameters
        ----------        
        log: dict
            Dictionary containing the data, cost, batch size and current weights
        """    
        self._best_results = self._best_epochs_log[-1]
        self._critical_points = np.where(self._stability_log)[0].tolist()
        self._critical_points = [self._best_epochs_log[i] for i in self._critical_points] 
        
