import csv
import os
import pandas as pd
import scipy.stats as ss
import matplotlib.pyplot as plt
import numpy as np
import fitter

# This uses the underlining fit function in scipy which uses MLE!
def find_fit(path,filename,colname):
    # Finds best fit statistical distribution for data
    df = pd.read_csv(path+filename+'.csv')

    data = df[colname].dropna()
    # Find Best Statistical Model that fits dataset
    f = fitter.Fitter(data)
    f.distributions = ['weibull_min','weibull_max']
    f.fit()
    return f.get_best() # Returns best fit distribution

def find_MLE(distname,parameters,start,end):
    x = np.linspace(start, end, 1000)
    dist = getattr(ss, distname)
    pdf_values = dist.pdf(x=x, **parameters)
    max_index = np.argmax(pdf_values)
    
    return x[max_index]

def find_FWHM(distname,parameters,start,end):
    x = np.linspace(start, end, 1000)
    distname = getattr(ss, distname)
    y = distname.pdf(x=x,**parameters)
    peak = max(y)
    half_max = peak / 2
    # # Find the indices where y crosses half_max
    above_half_max = np.where(y >= half_max)[0]
    # # FWHM is the difference between the last and first index crossing half_max
    fwhm = x[above_half_max[-1]] - x[above_half_max[0]]
    return fwhm

def plot(data,distname,parameters,mle):
    distname = getattr(ss, distname)
    dist = ss.fit(distname,data,parameters)
    dist.plot()
    plt.axvline(x=mle, color='red', linestyle='-', label='MLE')
    x = np.linspace(min(data), max(data), 1000)
    y = distname.pdf(x=x,**parameters)
    peak = max(y)
    half_max = peak / 2
    above_half_max = np.where(y >= half_max)[0]
    plt.hlines(half_max, x[above_half_max[0]], x[above_half_max[-1]], colors='blue', linestyles='-', label='FWHM')
    plt.show()

def create_csv(csvfile,fieldnames):
    with open(csvfile, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

def add_row(csvfile,fieldnames,row_data):
    with open(csvfile, 'a', newline='') as file:
        writer = csv.DictWriter(file,fieldnames=fieldnames)
        writer.writerow(row_data)

if __name__ == "__main__":
    # setup file to write results to
    resultfile = 'weibull_results.csv'
    resheaders = [
            'Filename','Major_Axis_Size_MLE', 'Major_Axis_Size_FWHM', 'Aspect_ratio_MLE', 
            'Aspect_ratio_FWHM', 'Orientation_MLE', 'Orientation_FWHM', 
            'Spacing_MLE', 'Spacing_FWHM'
        ]
    if not os.path.exists(resultfile):
        create_csv(resultfile,resheaders)

    # Setup reading from file
    fullpath = 'C:/Users/dougl/Documents/github/-wsum-pythonapps/src/Data_Driven_Model/' # Edit this
    file1 = 'combined_data_63020B_IP' ################ Edit this
    datafiles = [[file1,'Size'],[file1,'Aspect_Ratio'],[file1,'Orientation'],[file1,'Distance']]
    dist = []

    # Read from file and desired column and find best fit and save
    for i, v in enumerate(datafiles):
        dist.append(find_fit(fullpath,datafiles[i][0],datafiles[i][1]))

    # Use fit to calculate MLE and FWHM
    rowentry = {}
    rowentry['Filename'] = file1.split('S',1)[0]
    for i, inst in enumerate(dist):
        for distname in dist[i].keys(): # only one key
            prameters = dist[i][distname]
            df = pd.read_csv(fullpath+datafiles[i][0]+'.csv')
            data = df[datafiles[i][1]].dropna()
            mle = find_MLE(distname,prameters,min(data),max(data))
            fwhm = find_FWHM(distname,prameters,min(data),max(data))
            plot(data,distname,prameters,mle)
            #################### Write to files ####################
    #         rowentry[datafiles[i][1]+'_MLE'] = mle
    #         rowentry[datafiles[i][1]+'_FWHM'] = fwhm
    # add_row(resultfile,resheaders,rowentry)
    # with open("weibullmappin.txt","a") as file:
    #     file.write("\n\nfullpath = "+fullpath+"\nfile1,file2 = '"+file1+"','"+file2+"'"+"\n"+str(dist))