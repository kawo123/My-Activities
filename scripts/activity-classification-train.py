# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 16:02:58 2016

@author: cs390mb

Assignment 2 : Activity Recognition

This is the starter script used to train an activity recognition
classifier on accelerometer data.

See the assignment details for instructions. Basically you will train
a decision tree classifier and vary its parameters and evalute its
performance by computing the average accuracy, precision and recall
metrics over 10-fold cross-validation. You will then train another
classifier for comparison.

Once you get to part 4 of the assignment, where you will collect your
own data, change the filename to reference the file containing the
data you collected. Then retrain the classifier and choose the best
classifier to save to disk. This will be used in your final system.

Make sure to chek the assignment details, since the instructions here are
not complete.

"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn import svm
from features import extract_features # make sure features.py is in the same directory
from util import slidingWindow, reorient, reset_vars
from sklearn import cross_validation
from sklearn.metrics import confusion_matrix
import pickle


# %%---------------------------------------------------------------------------
#
#		                 Load Data From Disk
#
# -----------------------------------------------------------------------------

print("Loading data...")
sys.stdout.flush()
data_file = os.path.join('data', 'all-data.csv')
data = np.genfromtxt(data_file, delimiter=',')
print("Loaded {} raw labelled activity data samples.".format(len(data)))
sys.stdout.flush()

# %%---------------------------------------------------------------------------
#
#		                    Pre-processing
#
# -----------------------------------------------------------------------------

print("Reorienting accelerometer data...")
sys.stdout.flush()
reset_vars()
reoriented = np.asarray([reorient(data[i,1], data[i,2], data[i,3]) for i in range(len(data))])
reoriented_data_with_timestamps = np.append(data[:,0:1],reoriented,axis=1)
data = np.append(reoriented_data_with_timestamps, data[:,-1:], axis=1)


# %%---------------------------------------------------------------------------
#
#		                Extract Features & Labels
#
# -----------------------------------------------------------------------------

# you may want to play around with the window and step sizes
window_size = 20
step_size = 20

# sampling rate for the sample data should be about 25 Hz; take a brief window to confirm this
n_samples = 1000
time_elapsed_seconds = (data[n_samples,0] - data[0,0]) / 1000
sampling_rate = n_samples / time_elapsed_seconds

feature_names = ["std_magnitude", "medianX", "medianY", "medianZ", "meanX", "meanY", "meanZ", "stdX", "stdY", "stdZ", "mean_magnitude", "meancrossX", "meancrossY", "meancrossZ"]
class_names = ["Stationary", "Walking", "Running", "Jumping"]

print("Extracting features and labels for window size {} and step size {}...".format(window_size, step_size))
sys.stdout.flush()

n_features = len(feature_names)

X = np.zeros((0,n_features))
y = np.zeros(0,)

for i,window_with_timestamp_and_label in slidingWindow(data, window_size, step_size):
    # omit timestamp and label from accelerometer window for feature extraction:
    window = window_with_timestamp_and_label[:,1:-1]
    # extract features over window:
    x = extract_features(window)
    # append features:
    X = np.append(X, np.reshape(x, (1,-1)), axis=0)
    # append label:
    y = np.append(y, window_with_timestamp_and_label[10, -1])

print("Finished feature extraction over {} windows".format(len(X)))
print("Unique labels found: {}".format(set(y)))
sys.stdout.flush()

# %%---------------------------------------------------------------------------
#
#		                    Plot data points
#
# -----------------------------------------------------------------------------

# We provided you with an example of plotting two features.
# We plotted the mean X acceleration against the mean Y acceleration.
# It should be clear from the plot that these two features are alone very uninformative.
print("Plotting data points...")
sys.stdout.flush()
plt.figure()
formats = ['bo', 'go', 'yo', 'ro']
for i in range(0,len(y),10): # only plot 1/10th of the points, it's a lot of data!
    # Graph 1: std_magnitude vs medianZ
    # plt.plot(X[i,0], X[i,3], formats[int(y[i])])
    # Graph 2: meanX vs stdX
    plt.plot(X[i,4], X[i,7], formats[int(y[i])])
    # Graph 3: mean_magnitude vs meanCrossingZ
    # plt.plot(X[i,10], X[i,13], formats[int(y[i])])

plt.show()

# %%---------------------------------------------------------------------------
#
#		                Train & Evaluate Classifier
#
# -----------------------------------------------------------------------------

n = len(y)
n_classes = len(class_names)

totalPrec =[0,0,0,0]
totalRecall = [0,0,0,0]
totalAcc = 0

# TODO: Train and evaluate your decision tree classifier over 10-fold CV.
# Report average accuracy, precision and recall metrics.
cv = cross_validation.KFold(n, n_folds=10, shuffle=True, random_state=None)

tree = DecisionTreeClassifier(criterion ="entropy",max_depth=10,max_features=10)

for i, (train_indexes, test_indexes) in enumerate(cv):
    X_train = X[train_indexes, :]
    y_train = y[train_indexes]
    X_test = X[test_indexes, :]
    y_test = y[test_indexes]
    tree.fit(X_train, y_train)
    y_pred = tree.predict(X_test)
    conf = confusion_matrix(y_test,y_pred)
    print("Fold {}".format(i))
    print conf
    totalDiag=0.0
    total = 0.0
    sumCol = []
    prec = []
    sumRow = []
    recall = []

    for x in range(conf.shape[0]):
        totalDiag += conf[x][x]
        total += sum(conf[x])
        sumCol.append((float)(sum(conf[:,x])))
        sumRow.append((float)(sum(conf[x,:])))
        if np.isnan(conf[x][x]/sumCol[x]):
            prec.append(0)
        else:
            prec.append(conf[x][x]/sumCol[x])
            totalPrec[x] += conf[x][x]/sumCol[x]
        if np.isnan(conf[x][x]/sumRow[x]):
            recall.append(0)
        else:
            recall.append(conf[x][x]/sumRow[x])
            totalRecall[x] +=conf[x][x]/sumRow[x]

    acc = totalDiag / total

    print("\n")



# TODO: Output the average accuracy, precision and recall over the 10 folds
    print "Accuracy: ",acc
    print "Precision: ",prec
    print "Recall: ",recall
    print("\n")
    totalAcc += acc


print "Avg Accuracy: ", totalAcc/10
print "Avg Precision: ", [x / 10 for x in totalPrec]
print "Avg Recall: ", [x / 10 for x in totalRecall]
tree.fit(X, y)

export_graphviz(tree, out_file='tree.dot', feature_names = feature_names)

########################################################################
# TODO: Evaluate another classifier, i.e. SVM, Logistic Regression, k-NN, etc.
# TODO: Once you have collected data, train your best model on the entire
# dataset. Then save it to disk as follows:
# print "LinearSVC"
#
# totalPrec =[0,0,0]
# totalRecall = [0,0,0]
# totalAcc = 0
#
# liney = svm.LinearSVC()
# for i, (train_indexes, test_indexes) in enumerate(cv):
#     X_train = X[train_indexes, :]
#     y_train = y[train_indexes]
#     X_test = X[test_indexes, :]
#     y_test = y[test_indexes]
#     liney.fit(X_train, y_train)
#     y_pred = liney.predict(X_test)
#     conf = confusion_matrix(y_test,y_pred)
#     print("Fold {}".format(i))
#     print conf
#     totalDiag=0.0
#     total = 0.0
#     sumCol = []
#     prec = []
#     sumRow = []
#     recall = []
#
#     for x in range(conf.shape[0]):
#         totalDiag += conf[x][x]
#         total += sum(conf[x])
#         sumCol.append((float)(sum(conf[:,x])))
#         sumRow.append((float)(sum(conf[x,:])))
#         if np.isnan(conf[x][x]/sumCol[x]):
#             prec.append(0)
#         else:
#             prec.append(conf[x][x]/sumCol[x])
#             totalPrec[x] += conf[x][x]/sumCol[x]
#         if np.isnan(conf[x][x]/sumRow[x]):
#             recall.append(0)
#         else:
#             recall.append(conf[x][x]/sumRow[x])
#             totalRecall[x] +=conf[x][x]/sumRow[x]
#
#     acc = totalDiag / total
#
#     print("\n")
#
#     print "Accuracy: ",acc
#     print "Precision: ",prec
#     print "Recall: ",recall
#     print("\n")
#     totalAcc += acc
#
#
# print "Avg Accuracy: ", totalAcc/10
# print "Avg Precision: ", [x / 10 for x in totalPrec]
# print "Avg Recall: ", [x / 10 for x in totalRecall]
# liney.fit(X, y)
################################################



# when ready, set this to the best model you found, trained on all the data:
best_classifier = tree

with open('classifier.pickle', 'wb') as f: # 'wb' stands for 'write bytes'
    pickle.dump(best_classifier, f)
