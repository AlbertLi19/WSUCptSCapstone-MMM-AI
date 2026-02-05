import pandas as pd
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":

    fullpath = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/Impurity_distributions/63020B (ID D)/' # Edit this
    file1, file2= '63020B_TPStacked_Excel_File_MA_AR_NormAng_New_NormAbs','Stacked_file_C&D_63020B_TP' ################ Edit this
    datafiles = [[file1,'Major_Axis_Size'],[file1,'Aspect_ratio'],[file1,'Orientation'],[file2,'Spacing']]
    fig, ax = plt.subplots(nrows=2, ncols=3, figsize=(10, 7))
    plt_ind = np.arange(6) + 231

    bandwidths = [0.001, 0.01, 0.25, 0.5, 0.75, 1]

    df = pd.read_csv(fullpath + datafiles[0][0] + '.csv')
    data_train = df[datafiles[0][1]].dropna()
    data_test = np.linspace(min(data_train), max(data_train), len(data_train))[:, np.newaxis]
    for b, ind in zip(bandwidths, plt_ind):
        kde_model = KernelDensity(kernel='gaussian', bandwidth=b)
        kde_model.fit(data_train.to_frame())
        score = kde_model.score_samples(data_test) # computes log-likelihood 
        plt.subplot(ind)
        ## Compute and plot MLE
        peak_index = np.argmax(score)
        x_peak = data_test[peak_index]
        y_peak = np.exp(score[peak_index])
        plt.vlines(x=x_peak, ymin=0, ymax=y_peak, color='red', linestyle='-')
        ## End MLE
        plt.plot(data_test, np.exp(score), c='cyan')
        plt.title("bandwidth= "+str(b)+ " | MLE= "+str(round(x_peak[0],3)))
    fig.subplots_adjust(hspace=0.5, wspace=.3)
    # fig.savefig('kdemanual.png', format='png', dpi=300)
    plt.show()