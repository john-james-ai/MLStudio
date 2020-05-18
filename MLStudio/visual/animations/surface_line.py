#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# =========================================================================== #
# Project : ML Studio                                                         #
# Version : 0.1.0                                                             #
# File    : gradient_descent_.py                                              #
# Python  : 3.8.2                                                             #
# --------------------------------------------------------------------------  #
# Author  : John James                                                        #
# Company : DecisionScients                                                   #
# Email   : jjames@decisionscients.com                                        #
# URL     : https://github.com/decisionscients/MLStudio                       #
# --------------------------------------------------------------------------  #
# Created       : Thursday, May 14th 2020, 3:02:34 am                         #
# Last Modified : Thursday, May 14th 2020, 3:02:35 am                         #
# Modified By   : John James (jjames@decisionscients.com)                     #
# --------------------------------------------------------------------------  #
# License : BSD                                                               #
# Copyright (c) 2020 DecisionScients                                          #
# =========================================================================== #
"""Animates gradient descent with surface and line plots."""
import os

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go 
import plotly.io as pio 
import plotly.offline as py
from plotly.subplots import make_subplots

from mlstudio.utils.data_manager import todf
# --------------------------------------------------------------------------  #
class SurfaceLine:
    """Animates gradient descent with a surface and line plot."""
    def __init__(self):
        pass

    def _cost_mesh(self,X, y, THETA):
        return(np.sum((X.dot(THETA) - y)**2)/(2*len(y)))        

    def animate(self, models, directory=None, filename=None):

        # Extract model blackbox
        gd = models[0].blackbox_
        sgd = models[1].blackbox_
        mbgd = models[2].blackbox_

        # Extract the theta, x=theta0, y=theta1 and cost history
        theta = gd.epoch_log.get('theta')
        weights = todf(gd.epoch_log['theta'], stub='theta_')        
        theta0 = np.array(weights['theta_0'])
        theta1 = np.array(weights['theta_1'])
        cost = gd.epoch_log.get('train_cost')

        # Establish boundaries of plot
        theta0_min = min(theta0)
        theta1_min = min(theta1)
        theta0_max = max(theta0) 
        theta1_max = max(theta1) 
        theta0_mesh = np.linspace(theta0_min, theta0_max, 50)
        theta1_mesh = np.linspace(theta1_min, theta1_max, 50)
        theta0_mesh, theta1_mesh = np.meshgrid(theta0_mesh, theta1_mesh)

        # Extract Data
        X_train_ = models[0].X_train_
        y_train_ = models[0].y_train_

        # Create z axis grid based upon X,y and the grid of thetas
        Js = np.array([self._cost_mesh(X_train_, y_train_, THETA)
                    for THETA in zip(np.ravel(theta0_mesh), np.ravel(theta1_mesh))])
        Js = Js.reshape(theta0_mesh.shape)  

        # Create regression line data
        n_frames = len(theta0) 
        def f(x, theta):
            return theta[0] + x * theta[1]
        
        X = X_train_
        x = X[:,1]        
        xm = np.min(x)
        xM = np.max(x)
        xx = np.linspace(xm, xM)
        
        lines = {}
        est = ['BGD', 'SGD', 'MBGD'] 
        for i, m in enumerate(models):
            yy = []
            for j in range(n_frames):
                ym = f(xm, m.blackbox_.epoch_log.get('theta')[j])
                yM = f(xM, m.blackbox_.epoch_log.get('theta')[j])
                yy.append(np.linspace(ym, yM))      
            lines[est[i]] = yy
    
        # Initialize figure with 2 subplots
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Gradient Descent", "Linear Regression"),
                            specs=[[{'type': "surface"}, {"type": "scatter"}]])      

        # Add surface and scatter plot
        fig.add_trace(
            go.Surface(x=theta0, y=theta1, z=Js, colorscale="YlGnBu", showscale=False),
            row=1, col=1)

        fig.add_trace(
            go.Scatter(x=X_train_[:,1], y=y_train_,
                       name="points2",
                       mode="markers",
                       marker=dict(color="#1560bd")), row=1, col=2)                       

        # Create frames definition                       
        frames = [go.Frame(
            dict(
                name = k,
                data = [                    
                    go.Scatter3d(x=[theta0[k]], y=[theta1[k]], z=[cost[k]], mode='markers', marker=dict(color="red", size=10)),
                    go.Scatter(x=xx, y=lines['BGD'][k], mode="lines", marker=dict(color="red")),
                    go.Scatter(x=xx, y=lines['SGD'][k], mode="lines", marker=dict(color="green")),
                    go.Scatter(x=xx, y=lines['MBGD'][k], mode="lines", marker=dict(color="orange")),
                ],
                traces=[0,1,2,3])
            ) for k in range(n_frames)]

        # Update the menus
        updatemenus = [dict(type='buttons',
                            buttons=[dict(label="Play",
                                          method="animate",
                                          args=[[f'{k}' for k in range(n_frames)],
                                            dict(frame=dict(duration=100, redraw=False),
                                                 transition=dict(duration=0),
                                                 easing="linear",
                                                 fromcurrent=True,
                                                 mode="immediate")])],
                            direction="left",
                            pad=dict(r=10, t=85),
                            showactive=True, x=0.1, y=0, xanchor="right", yanchor="top")]

        sliders = [{"yanchor": "top",
                   "xanchor": "left",
                   "currentvalue": {"font": {"size": 16}, "prefix": "Iteration: ", "visible":True, "xanchor": "right"},
                   'transition': {'duration': 100.0, 'easing': 'linear'},
                   'pad': {'b': 10, 't': 50}, 
                   'len': 0.9, 'x': 0.1, 'y': 0, 
                   'steps': [{'args': [[k], {'frame': {'duration': 100.0, 'easing': 'linear', 'redraw': False},
                                      'transition': {'duration': 0, 'easing': 'linear'}}], 
                       'label': k, 'method': 'animate'} for k in range(n_frames)       
                    ]}]

        fig.update(frames=frames)
        fig.update_layout(
            xaxis=dict(range=[theta0_min, theta0_max], autorange=False, zeroline=False),
            yaxis=dict(range=[theta1_min, theta1_max], autorange=False, zeroline=False),            
            title=dict(xanchor='center', yanchor='top', x=0.5, y=0.9),        
            font=dict(family="Open Sans"),    
            updatemenus=updatemenus, 
            showlegend=False,
            sliders=sliders, 
            template='plotly_white')


        fig.add_trace(
            go.Scatter(x=X_train_[:,1], y=y_train_,
                       name="points2",
                       mode="markers",
                       marker=dict(color="#1560bd")), row=1, col=2)   

        fig.add_trace(
            go.Surface(x=theta0, y=theta1, z=Js, colorscale="YlGnBu", showscale=False),
            row=1, col=1)         
                                                   
        fig.add_trace(
            go.Scatter(x=X_train_[:,1], y=y_train_,
                       name="points2",
                       mode="markers",
                       marker=dict(color="#1560bd")), row=1, col=2)

        fig.add_trace(
            go.Surface(x=theta0, y=theta1, z=Js, colorscale="YlGnBu", showscale=False),
            row=1, col=1)     

        if directory and filename:
            filepath = os.path.join(directory, filename)
            fig.write_html(filepath, include_mathjax='cdn')
        pio.renderers.default = "browser"
        fig.show()
