import pandas as pd
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt
import numpy as np
import os
import csv

def my_scores(estimator, X):
    scores = estimator.score_samples(X)
    # Remove -inf
    scores = scores[scores != float('-inf')]
    # Return the mean values
    return np.mean(scores)

def create_csv(csvfile,fieldnames):
    with open(csvfile, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

def add_row(csvfile,fieldnames,row_data):
    with open(csvfile, 'a', newline='') as file:
        writer = csv.DictWriter(file,fieldnames=fieldnames)
        writer.writerow(row_data)

if __name__ == "__main__":

    resultfile = 'kde_auto_results.csv'
    resheaders = [
            'Filename','Major_Axis_Size_MLE', 'Major_Axis_Size_FWHM', 'Aspect_ratio_MLE', 
            'Aspect_ratio_FWHM', 'Orientation_MLE', 'Orientation_FWHM', 
            'Spacing_MLE', 'Spacing_FWHM','KDE_bandwidth',
        ]
    if not os.path.exists(resultfile):
        create_csv(resultfile,resheaders)

    fullpaths = ['C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/61620A (ID A)/',
                    'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/61620B (ID B)/',
                    'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/63020A (ID C)/',
                    'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/63020B (ID D)/'] # Edit this
    filenames= [[['61620A_IPStacked_Excel_File_MA_AR','Stacked_file_C&D_61620A_IP'],['61620A_TPStacked_Excel_File_MA_AR','Stacked_file_C&D_61620A_TP']],
            [['61620B_IPStacked_Excel_File_MA_AR','Stacked_file_C&D_61620B_IP'],['61620B_TPStacked_Excel_File_MA_AR','Stacked_file_C&D_61620B_TP']],
            [['63020A_IPStacked_Excel_File_MA_AR_','Stacked_file_C&D_63020A_IP'],['63020A_TPStacked_Excel_File_MA_AR_','Stacked_file_C&D_63020A_TP']],
            [['63020B_IPStacked_Excel_File_MA_AR_NormAng_New_NormAbs','Stacked_file_C&D_63020B_IP'],['63020B_TPStacked_Excel_File_MA_AR_NormAng_New_NormAbs','Stacked_file_C&D_63020B_TP']]] ################ Edit this
    # datafiles = [[file1,'Major_Axis_Size'],[file1,'Aspect_ratio'],[file1,'Orientation'],[file2,'Spacing']]
    
    pltfig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 7))_ind = np.arange(4) + 231
    bandwidth = np.arange(0.05, 1.5, .05)
    rowentry = {}
    for i, (path, folder) in enumerate(zip(fullpaths, filenames)):
        for filepair in folder:
            datafiles = [[filepair[0],'Major_Axis_Size'],[filepair[0],'Aspect_ratio'],[filepair[0],'Orientation'],[filepair[1],'Spacing']]
            rowentry['Filename'] = filepair[0].split('S',1)[0]
            for i, (v, axis) in enumerate(zip(datafiles, ax.flatten())):
                df = pd.read_csv(path + v[0] + '.csv')
                data_train = np.abs(df[v[1]].dropna().values.reshape(-1, 1))
                data_test = np.linspace(min(data_train), max(data_train), len(data_train)).reshape(-1, 1)

                kde = KernelDensity(kernel='gaussian')
                grid = GridSearchCV(estimator=kde,
                                    param_grid={'bandwidth': bandwidth},
                                    scoring= None,
                                    refit=True,
                                    cv=5,
                                    verbose=1)
                                    
                grid.fit(data_train)
                kde = grid.best_estimator_
                log_dens = kde.score_samples(data_test)
                
                ## Compute MLE
                peak_index = np.argmax(log_dens)
                x_peak = data_test[peak_index]
                y_peak = np.exp(log_dens[peak_index])
                ## End MLE

                ## Compute FWHM
                peak = max(np.exp(log_dens))
                half_max = peak / 2
                above_half_max = np.where(np.exp(log_dens) >= half_max)[0]
                fwhm = data_test[above_half_max[-1]] - data_test[above_half_max[0]]
                ## End FWHM
                # Plot MLW, FWHM and KDE on the respective subplot
                # axis.vlines(x=x_peak, ymin=0, ymax=y_peak, color='red', linestyle='-')
                # axis.hlines(half_max, data_test[above_half_max[0]], data_test[above_half_max[-1]], colors='blue', linestyles='-', label='FWHM')
                # axis.plot(data_test, np.exp(log_dens), c='green')
                # axis.set_title('KDE ' + v[1] + " | b=" + str(round(kde.bandwidth, 2)) + " | FHWM=" + str(round(fwhm[0],2)))
                ## End Plot
                ## Save to csv
                rowentry[datafiles[i][1]+'_MLE'] = x_peak[0]
                rowentry[datafiles[i][1]+'_FWHM'] = fwhm[0]
                rowentry['KDE_bandwidth'] = round(kde.bandwidth, 2)
            add_row(resultfile,resheaders,rowentry)
                ## End csv write


            ## Show plot
            # fig.subplots_adjust(hspace=0.5, wspace=0.3)
            # fig.suptitle('kde for '+file1.split('S',1)[0], fontsize=16)
            # fig.savefig('kdeauto.png', format='png', dpi=300)
            # plt.show()