from PyQt5 import QtWidgets, uic, QtGui, QtCore
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import pygraph
from PandasConvert import PandasModel
import pandas as pd
import numpy as np

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

#design = pygraph.Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):

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


    def plot(self, x, y):
        self.graphWidget.clear()
        self.graphWidget.plot(x, y)

    def fileSelect(self):
        # Importing global variables

        global filepath, forceColumn, displacementColumn

        # Open a new window to select files - only .mat files will be shown
        dialog = QtGui.QFileDialog(None, "Open File", None, "CSV-files (*.csv)")
        dialog.exec_()

        for file in dialog.selectedFiles():
            filepath = file

        #populate table after loading data
        self.names =  ['Point','Time_Elapsed','Time_Scan','Displacement','Load','E11','E12','E22','Ax_cmd','Ax_err','No_Val']
        self.data = pd.read_csv(filepath,header=2,names=self.names)

        #print data to table
        model = PandasModel(self.data)
        self.tableView.setModel(model)


    def plot_raw_data(self):

        # update column names
        forceColumn = int(self.forceColumn.toPlainText())
        displacementColumn = int(self.displacementColumn.toPlainText())

        print(self.names[forceColumn], self.names[displacementColumn])

        #forceTag = self.data['Displacement']
        #displacementTag = self.data.columns['Displacement']

        y = self.data['Load'].values
        x = self.data['Displacement'].values

        #print(forceTag,displacementTag)
        print(y,x)

        self.plot(x,y)


def main():

    global filepath
    global forceColumn
    global displacementColumn

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()