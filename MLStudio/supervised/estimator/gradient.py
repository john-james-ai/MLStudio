#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# ============================================================================ #
# Project : MLStudio                                                           #
# Version : 0.1.0                                                              #
# File    : estimator.py                                                       #
# Python  : 3.8.2                                                              #
# ---------------------------------------------------------------------------- #
# Author  : John James                                                         #
# Company : DecisionScients                                                    #
# Email   : jjames@decisionscients.com                                         #
# URL     : https://github.com/decisionscients/MLStudio                        #
# ---------------------------------------------------------------------------- #
# Created       : Sunday, March 15th 2020, 7:15:36 pm                          #
# Last Modified : Sunday, March 15th 2020, 7:15:46 pm                          #
# Modified By   : John James (jjames@decisionscients.com)                      #
# ---------------------------------------------------------------------------- #
# License : BSD                                                                #
# Copyright (c) 2020 DecisionScients                                           #
# ============================================================================ #
"""Gradient Descent base class, from which regression and classification inherit."""
from abc import ABC, abstractmethod, ABCMeta
import sys
import copy
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.base import RegressorMixin, ClassifierMixin
from sklearn.utils.validation import check_array
from sklearn.utils.validation import check_X_y, check_is_fitted
from sklearn.preprocessing import LabelBinarizer

from mlstudio.supervised.estimator.callbacks import CallbackList, Callback
from mlstudio.supervised.estimator.early_stop import EarlyStop
from mlstudio.supervised.estimator.debugging import GradientCheck
from mlstudio.supervised.estimator.monitor import BlackBox, Progress, summary
from mlstudio.supervised.estimator.scorers import R2, Accuracy
from mlstudio.supervised.estimator.optimizers import Standard
from mlstudio.supervised.regression import LinearRegression
from mlstudio.supervised.logistic_regression import LogisticRegression
from mlstudio.utils.data_manager import batch_iterator, data_split, shuffle_data
from mlstudio.utils.validation import check_y
# --------------------------------------------------------------------------- #
#                          GRADIENT DESCENT                                   #
# --------------------------------------------------------------------------- #
class GradientDescent(ABC, BaseEstimator):
    """Base class gradient descent estimator."""

    @property
    def variant(self):
        if self.batch_size is None:
            variant = 'Batch Gradient Descent'
        elif self.batch_size == 1:
            variant = 'Stochastic Gradient Descent'
        else:
            variant = 'Minibatch Gradient Descent'
        return variant

    @property
    def description(self):
        """Returns the estimator description."""
        return self.algorithm.name + ' with ' + self.variant    

    @property
    def learning_rate(self):
        return self._learning_rate

    @learning_rate.setter  
    def learning_rate(self, x):
        self._learning_rate = x

    @abstractmethod
    def _prepare_data(self, X, y):
        """Prepares X and y data for training."""
        self.X_train_ = self.X_val_ = self.y_train_ = self.y_val_ = None
        # Validate inputs
        self.X_train_, self.y_train_ = check_X_y(X, y)
        # Add a column of ones to create the X design matrix
        self.X_train_ = np.insert(self.X_train_, 0, 1.0, axis=1)      

    @abstractmethod
    def _init_weights(self):
        """Initializes weights"""       
        pass

    @abstractmethod
    def _evaluate_epoch(self, log=None):
        """Computes training (and validation) costs and scores for each epoch."""
        pass
    
    def _init_callbacks(self):
        # Initialize callback list
        self._cbks = CallbackList()        
        # BlackBox callback
        self.blackbox_ = BlackBox()
        self._cbks.append(self.blackbox_)
        # Progress callback
        self._progress = Progress()        
        self._cbks.append(self._progress)
        # Add early stop if object injected.
        if self.early_stop:
            self._cbks.append(self.early_stop)
        # Add gradient checking if object injected.
        if self.gradient_check:
            self._cbks.append(self.gradient_check)        
        # Initialize all callbacks.
        self._cbks.set_params(self.get_params())
        self._cbks.set_model(self)


    def _begin_training(self, log=None):
        """Performs initializations required at the beginning of training."""
        self._epoch = 0
        self._batch = 0        
        self.converged_ = False
        self.is_fitted_ = False        
        self._learning_rate = self.learning_rate_0
        self._prepare_data(log.get("X"),log.get("y"))
        self._init_weights()            
        self._init_callbacks()
        self._cbks.on_train_begin(log)
        
    def _end_training(self, log=None):
        """Closes history callout and assign final and best weights."""
        self._cbks.on_train_end()
        self.intercept_ = self.theta_[0]
        self.coef_ = self.theta_[1:]
        self.n_iter_ = self._epoch
        self.is_fitted_ = True

    def _begin_epoch(self, log=None):
        """Increment the epoch count and shuffle the data."""
        self._epoch += 1
        self.X_train_, self.y_train_ = shuffle_data(self.X_train_, self.y_train_) 
        self._cbks.on_epoch_begin(self._epoch, log)

    def _end_epoch(self, log=None):        
        """Performs end-of-epoch evaluation and scoring."""
        log = log or {}
        # Update log with current learning rate and parameters theta
        log['epoch'] = self._epoch
        log['learning_rate'] = self.learning_rate
        log['theta'] = self.theta_.copy()     
        # Compute performance statistics for epoch and post to history
        log = self._evaluate_epoch(log)
        # Call 'on_epoch_end' methods on callbacks.
        self._cbks.on_epoch_end(self._epoch, log)

    def _begin_batch(self, log=None):
        self._batch += 1
        self._cbks.on_batch_begin(self._batch, log)

    def _end_batch(self, log=None):
        self._cbks.on_batch_end(self._batch, log)

    def fit(self, X, y):
        """Trains model until stop condition is met.
        
        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            Training data

        y : numpy array, shape (n_samples,)
            Target values 

        Returns
        -------
        self : returns instance of self._
        """
        train_log = {'X': X, 'y': y}
        self._begin_training(train_log)

        while (self._epoch < self.epochs and not self.converged_):

            self._begin_epoch()

            for X_batch, y_batch in batch_iterator(self.X_train_, self.y_train_, batch_size=self.batch_size):

                self._begin_batch()
                
                # Compute model output
                y_out = self.algorithm.compute_output(X_batch, self.theta_)

                # Compute costs
                J = self.algorithm.compute_cost(y_batch, y_out, self.theta_)                
                
                # Format batch log with weights and cost
                batch_log = {'batch': self._batch, 'batch_size': X_batch.shape[0],
                             'theta': self.theta_.copy(), 'train_cost': J}

                # Compute gradient
                gradient = self.algorithm.compute_gradient(X_batch, y_batch, y_out, self.theta_)

                # Update parameters.
                self.theta_ = self.optimizer.update_parameters(self.theta_, gradient, self._learning_rate)                

                # Update batch log
                self._end_batch(batch_log)

            # Wrap up epoch
            self._end_epoch()

        self._end_training()
        return self         

    def predict(self, X):
        """Computes prediction.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The input data

        Returns
        -------
        y_pred : prediction
        """
        check_is_fitted(self)        
        X = check_array(X, accept_sparse=True, accept_large_sparse=True, estimator=self)
        return self.algorithm.predict(X, self.theta_)
    
    def score(self, X, y):
        """Computes scores using the scorer parameter.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The input data

        y : array_like of shape (n_samples,) or (n_samples, n_classes)
            The target variable.

        Returns
        -------
        score based upon the scorer object.
        
        """
        y_pred = self.predict(X)
        return self.scorer(y, y_pred)

    def summary(self, features=None):
        summary(self.blackbox_, features)

# --------------------------------------------------------------------------- #
#                     GRADIENT DESCENT REGRESSOR                              #
# --------------------------------------------------------------------------- #
class GradientDescentRegressor(GradientDescent, RegressorMixin):
    """Gradient descent estimator for regression."""

    def __init__(self, learning_rate_0=0.01, batch_size=None, 
                 theta_init=None,  epochs=1000, algorithm=LinearRegression(),
                 optimizer=Standard(), scorer=R2(), early_stop=False, 
                 verbose=False, checkpoint=100,  random_state=None, 
                 gradient_check=False):

        self.learning_rate_0 = learning_rate_0        
        self.batch_size = batch_size
        self.theta_init = theta_init
        self.epochs = epochs
        self.algorithm = algorithm
        self.optimizer = optimizer
        self.scorer = scorer
        self.early_stop = early_stop
        self.verbose = verbose
        self.checkpoint = checkpoint
        self.random_state = random_state
        self.gradient_check = gradient_check   

    def _prepare_data(self, X, y):
        """Creates the X design matrix and saves data as attributes."""
        super(GradientDescentRegressor, self)._prepare_data(X,y)
        # If early stopping, set aside a proportion of the data for the validation set    
        if self.early_stop:            
            if self.early_stop.val_size:                
                self.X_train_, self.X_val_, self.y_train_, self.y_val_ = \
                    data_split(self.X_train_, self.y_train_, stratify=False,
                    test_size=self.early_stop.val_size, random_state=self.random_state)   

    def _init_weights(self):
        """Initializes parameters."""
        if self.theta_init is not None:
            assert self.theta_init.shape == (self.X_train_.shape[1],), \
                    "Initial parameters theta must have shape (n_features+1,)."
            self.theta_ = self.theta_init
        else:
            rng = np.random.RandomState(self.random_state)                
            self.theta_ = rng.randn(self.X_train_.shape[1])            

    def _evaluate_epoch(self, log=None):
        """Computes training (and validation) costs and scores."""
        log = log or {}
        # Init variables, such as the scorer, may not be mutated during fit. 
        # Behind the scenes, sklearn clones estimators to do parallel 
        # processing in functions such as GridSearchCV. We therefore make a 
        # copy of the scorer to avoid mutating the original parameter. 
        scorer = copy.copy(self.scorer)        
        # Compute costs 
        y_out = self.algorithm.compute_output(self.X_train_, self.theta_)
        log['train_cost'] = self.algorithm.compute_cost(self.y_train_, y_out, self.theta_)
        y_pred = self.algorithm.predict(self.X_train_, self.theta_)
        log['train_score'] = scorer(self.y_train_, y_pred)
        # If early stop object is provided, get validation cost and score
        if self.early_stop:
            if self.early_stop.val_size:
                y_out_val = self.algorithm.compute_output(self.X_val_, self.theta_)
                log['val_cost'] = self.algorithm.compute_cost(self.y_val_, y_out_val, self.theta_)        
                y_pred_val = self.algorithm.predict(self.X_val_, self.theta_)
                log['val_score'] = scorer(self.y_val_, y_pred_val)

        return log



# --------------------------------------------------------------------------- #
#                     GRADIENT DESCENT CLASSIFIFER                            #
# --------------------------------------------------------------------------- #
class GradientDescentClassifier(GradientDescent, ClassifierMixin):
    """Gradient descent estimator for classification."""

    def __init__(self, learning_rate_0=0.01, batch_size=None, 
                 theta_init=None,  epochs=1000, algorithm=LogisticRegression(),
                 optimizer=Standard(), scorer=Accuracy(), early_stop=False, 
                 verbose=False, checkpoint=100, random_state=None, 
                 gradient_check=False):

        self.learning_rate_0 = learning_rate_0        
        self.batch_size = batch_size
        self.theta_init = theta_init
        self.epochs = epochs
        self.algorithm = algorithm
        self.optimizer = optimizer
        self.scorer = scorer
        self.early_stop = early_stop
        self.verbose = verbose
        self.checkpoint = checkpoint
        self.random_state = random_state
        self.gradient_check = gradient_check    

    def _prepare_binary_classification_data(self, X, y):
        """Prepare data for binary classification."""
        super(GradientDescentClassifier, self)._prepare_data(X,y)    
        # If early stopping, set aside a proportion of the data for the validation set    
        if self.early_stop:            
            if self.early_stop.val_size:                
                self.X_train_, self.X_val_, self.y_train_, self.y_val_ = \
                    data_split(self.X_train_, self.y_train_, stratify=True,
                    test_size=self.early_stop.val_size, random_state=self.random_state)   

    def _prepare_multiclass_data(self, X, y):
        """Prepare data for multiclass logistic regression."""
        super(GradientDescentClassifier, self)._prepare_data(X,y)    
        # If early stopping, set aside a proportion of the data for the validation set            
        if self.early_stop:            
            if self.early_stop.val_size:                
                self.X_train_, self.X_val_, self.y_train_, self.y_val_ = \
                    data_split(self.X_train_, self.y_train_, stratify=True,
                    test_size=self.early_stop.val_size, random_state=self.random_state)           
        # One-hot encode the y variable. Save the original for evaluation purposes.
        enc = LabelBinarizer()
        self._y_train_orig = self.y_train_
        self.y_train_ = enc.fit_transform(self.y_train_)
        if self.early_stop:            
            if self.early_stop.val_size:    
                self._y_val_orig = self.y_val_
                self.y_val_ = enc.fit_transform(self.y_val_)

 
    def _prepare_data(self, X, y):
        """Prepares data for binary or multiclass classification."""
        if len(np.unique(y)) == 2:
            self._prepare_binary_classification_data(X, y)
        else:
            self._prepare_multiclass_data(X, y)

    def _init_weights_binary_classification(self):
        """Initializes weights for binary classification."""
        n_features = self.X_train_.shape[1]
        if self.theta_init is not None:
            assert self.theta_init.shape == (n_features,), \
                "Initial parameters theta must have shape (n_features+1)."
            self.theta_ = self.theta_init
        else:
            rng = np.random.RandomState(self.random_state)                
            self.theta_ = rng.randn(n_features)   

    def _init_weights_multiclass(self):
        """Initializes weights for multiclass classification."""
        n_features = self.X_train_.shape[1]
        n_classes = self.y_train_.shape[1]
        if self.theta_init is not None:
            assert self.theta_init.shape == (n_features, n_classes), \
                "Initial parameters theta must have shape (n_features+1, n_classes)."
            self.theta_ = self.theta_init
        else:
            rng = np.random.RandomState(self.random_state)                
            self.theta_ = rng.randn(n_features, n_classes)        

    def _init_weights(self):
        """Initializes model parameters."""        
        if self.y_train_.ndim == 1:
            self._init_weights_binary_classification()
        else:
            self._init_weights_multiclass()

    def _evaluate_epoch_binary_classification(self, log=None):
        """Computes training (and validation) costs and scores for binary classification."""
        log = log or {}
        # Init variables, such as the scorer, may not be mutated during fit. 
        # Behind the scenes, sklearn clones estimators to do parallel 
        # processing in functions such as GridSearchCV. We therefore make a 
        # copy of the scorer to avoid mutating the original parameter. 
        scorer = copy.copy(self.scorer)        
        # Compute training costs and scores
        y_out = self.algorithm.compute_output(self.X_train_, self.theta_)
        log['train_cost'] = self.algorithm.compute_cost(self.y_train_, y_out, self.theta_)
        y_pred = self.algorithm.predict(self.X_train_, self.theta_)
        log['train_score'] = scorer(self.y_train_, y_pred)
        # If early stop object is provided, get validation cost and score
        if self.early_stop:
            if self.early_stop.val_size:
                y_out_val = self.algorithm.compute_output(self.X_val_, self.theta_)
                log['val_cost'] = self.algorithm.compute_cost(self.y_val_, y_out_val, self.theta_)        
                y_pred_val = self.algorithm.predict(self.X_val_, self.theta_)
                log['val_score'] = scorer(self.y_val_, y_pred_val)

        return log

    def _evaluate_epoch_multiclass(self, log=None):
        """Computes training (and validation) costs and scores for multiclass classification."""
        log = log or {}
        # Init variables, such as the scorer, may not be mutated during fit. 
        # Behind the scenes, sklearn clones estimators to do parallel 
        # processing in functions such as GridSearchCV. We therefore make a 
        # copy of the scorer to avoid mutating the original parameter. 
        scorer = copy.copy(self.scorer)        
        # Compute training costs and scores
        y_out = self.algorithm.compute_output(self.X_train_, self.theta_)
        log['train_cost'] = self.algorithm.compute_cost(self.y_train_, y_out, self.theta_)
        y_pred = self.algorithm.predict(self.X_train_, self.theta_)
        log['train_score'] = scorer(self._y_train_orig, y_pred)

        # If early stop object is provided, get validation cost and score
        if self.early_stop:
            if self.early_stop.val_size:
                y_out_val = self.algorithm.compute_output(self.X_val_, self.theta_)
                log['val_cost'] = self.algorithm.compute_cost(self.y_val_, y_out_val, self.theta_)        
                y_pred_val = self.algorithm.predict(self.X_val_, self.theta_)
                log['val_score'] = scorer(self._y_val_orig, y_pred_val)

        return log        

    def _evaluate_epoch(self, log=None):
        """Computes training costs, and optionally scores, for each epoch."""
        if self.y_train_.ndim == 1:
            log = self._evaluate_epoch_binary_classification(log)
        else:
            log = self._evaluate_epoch_multiclass(log)
        return log