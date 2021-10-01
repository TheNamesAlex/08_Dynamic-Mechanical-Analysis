import os
from os.path import join
import numpy as np

def getFileContent(path_dir):
    return_Dict = {}
    for root, dirs, files in os.walk(path_dir):
        for file in files:
            if file[-3:].lower() == "csv":
                return_Dict[file] = os.path.join(root,file)  
    return return_Dict
	
def filter_fourier(x, mask):
    result = x.copy()
    result = np.fft.fft(result)
    result = result*mask
    result = np.real(np.fft.ifft(result))
    return result