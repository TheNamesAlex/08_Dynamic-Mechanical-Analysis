from PyQt5 import QtWidgets, uic, QtGui, QtCore
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import pygraph
from PandasConvert import PandasModel

#design = pygraph.Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('main.ui', self)

        #init variables
        self.filepath = " "


        self.plot()

        #connecting the
        self.selectData.clicked.connect(self.fileSelect)

    def plot(self, hour=[1,2,3,4,5,6], temperature=[1,2,3,4,3,2]):
        self.graphWidget.plot(hour, temperature)

        # Open  the file of a patient and loading the data

    def fileSelect(self):
        # Importing global variables

        global filepath

        # Open a new window to select files - only .mat files will be shown
        dialog = QtGui.QFileDialog(None, "Open File", None, "CSV-files (*.csv)")
        dialog.exec_()

        for file in dialog.selectedFiles():
            filepath = file

        import pandas as pd

        data = pd.read_csv(filepath,header=1)
        model = PandasModel(data)
        self.tableView.setModel(model)

        print(data.head())
    '''
    def btn_clk(self):
        path = self.lineEdit.text()
        df = pd.read_csv(path)
        model = PandasModel(df)
        self.tableView.setModel(model)
    '''

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()