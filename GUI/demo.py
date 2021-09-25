from PyQt5 import QtWidgets, uic, QtGui, QtCore
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import pygraph
from PandasConvert import PandasModel
import pandas as pd
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


import matplotlib
matplotlib.use('Qt5Agg')

pg.setConfigOption('background', 'w')
#pg.setConfigOption('foreground', 'k')


class MainWindow(QtWidgets.QMainWindow):

    data_in_plot = False

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('main.ui', self)

        #initialize  variables
        self.forceColumn.setText('4')
        self.displacementColumn.setText('3')

        #connecting the button to select some data
        self.selectData.clicked.connect(self.fileSelect)

        #connect "print raw data"-button to corresp. method
        self.printRawData.clicked.connect(self.plot_raw_data)

        # connect "print raw data"-button to corresp. method
        self.printNormalizedData.clicked.connect(self.plot_normalized_data)


    def plot(self, x, y, pen):
        self.graphWidget.plot(x, y, pen=pen)

    def clear_plot(self):
        self.graphWidget.clear()
        self.data_in_plot = False

    def update_data(self):
        # populate table after loading data
        self.names = ['Point', 'Time_Elapsed', 'Time_Scan', 'Displacement', 'Load', 'E11', 'E12', 'E22', 'Ax_cmd',
                      'Ax_err', 'No_Val']

        self.data = pd.read_csv(self.filepath, header=2, names=self.names)

        # remove duplicate rows
        self.data = self.data.drop_duplicates(subset=['Time_Elapsed'], keep='first')

        # assign walking index
        self.data['Index'] = [i for i in range(1, len(self.data) + 1)]

        # add normalized data
        self.data['Displacement_normalized'] = self.data['Displacement'] / max(self.data['Displacement'])
        self.data['Load_normalized'] = self.data['Load'] / max(self.data['Load'])

        # print data to table
        self.model = PandasModel(self.data)
        self.tableView.setModel(self.model)

        # after loading new data, clear the plot
        self.clear_plot()

    def fileSelect(self):

        #init filepath
        self.filepath = ''

        # Open a new window to select files - only .mat files will be shown
        dialog = QtGui.QFileDialog(None, "Open File", None, "CSV-files (*.csv)")
        dialog.exec_()

        for file in dialog.selectedFiles():
            self.filepath = file

        self.update_data()


    def plot_raw_data(self):

        if self.data_in_plot:
            self.clear_plot()

        Load = self.data['Load'].values
        Displacement = self.data['Displacement'].values
        Index = self.data['Index'].values

        pen = pg.mkPen(color=(255,136,0), width=1, alpha=0.25)
        self.plot(Index,Displacement,pen)

        pen = pg.mkPen(color=(200, 200, 255), width=1, alpha=0.25)
        self.plot(Index,Load,pen)

        self.data_in_plot = True

    def plot_normalized_data(self):

        if self.data_in_plot:
            self.clear_plot()

        Load = self.data['Load_normalized'].values
        Displacement = self.data['Displacement_normalized'].values
        Index = self.data['Index'].values

        pen = pg.mkPen(color=(255,136,0), width=1, alpha=0.25)
        self.plot(Index,Displacement,pen)

        pen = pg.mkPen(color=(200, 200, 255), width=1, alpha=0.25)
        self.plot(Index,Load,pen)

        self.data_in_plot = True




def main():

    #global filepath
    #global forceColumn
    #global displacementColumn

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()