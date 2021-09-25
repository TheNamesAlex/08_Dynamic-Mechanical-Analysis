from PyQt5 import QtWidgets, uic, QtGui, QtCore

from pyqtgraph import PlotWidget
import pyqtgraph as pg
import pygraph

import sys

from PandasConvert import PandasModel
import pandas as pd

from scipy.signal import savgol_filter, butter, sosfilt, detrend

import numpy as np

pg.setConfigOption('background', 'w')

class MainWindow(QtWidgets.QMainWindow):

    data_in_plot = False
    initial_load = True

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('main.ui', self)

        #initialize  variables
        self.startIndex.setText('0')
        self.endIndex.setText('99999')

        #TEXTINPUT INDICES
        self.startIndex.textChanged.connect(self.update_data)
        self.endIndex.textChanged.connect(self.update_data)

        #INPUT SAVGOL
        self.savitzkyOrder.setValue(3)
        self.labelSavitzkyOrder.setText('3')

        self.savitzkyLength.setValue(15)
        self.labelSavitzkyLength.setText('15')

        self.savitzkyOrder.valueChanged.connect(self.update_data)
        self.savitzkyLength.valueChanged.connect(self.update_data)
        self.savitzkyCheckbox.stateChanged.connect(self.update_data)

        #INPUT HIGH PASS
        self.highpassCutoff.setValue(0)
        self.labelHighpassCutoff.setText('0')
        self.highpassCutoff.valueChanged.connect(self.update_data)
        self.highpassCheckbox.stateChanged.connect(self.update_data)

        #detrend checkbox
        self.detrendCheckbox.stateChanged.connect(self.update_data)
        self.detrendBreakpointsLineEdit.textChanged.connect(self.update_data)

        #asymmetric least squares
        self.alsCheckbox.stateChanged.connect(self.update_data)
        self.alsLineEdit.textChanged.connect(self.update_data)

        #connecting the button to select some data
        self.selectData.clicked.connect(self.fileSelect)
        self.button_Update.clicked.connect(self.update_data)

        #connect "print raw data"-button to corresp. method
        self.printRawData.clicked.connect(self.plot_data)

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

        self.data['Load_filtered'] = self.data.Load.values

        if self.savitzkyCheckbox.isChecked():

            #update labels
            self.labelSavitzkyOrder.setText(str(self.savitzkyOrder.value()))
            self.labelSavitzkyLength.setText(str(self.savitzkyLength.value()))

            #update filtered data
            self.data['Load_filtered'] = savgol_filter(self.data.Load_filtered.values,
                                                       self.savitzkyLength.value(),
                                                       self.savitzkyOrder.value())

        if self.highpassCheckbox.isChecked():
            #update labels
            self.labelHighpassCutoff.setText(str(self.highpassCutoff.value()))

            #create butterworth filer
            sos = butter(10, self.highpassCutoff.value()*2/len(self.data), btype='highpass', output='sos')

            #update filtered data
            self.data.Load_filtered = filtered = sosfilt(sos, self.data.Load_filtered)

        if self.detrendCheckbox.isChecked():

            breakpoints = [int(i) for i in self.detrendBreakpointsLineEdit.text().split(',')]
            self.data['Load_filtered'] = detrend(self.data['Load_filtered'],bp=breakpoints)

        if self.alsCheckbox.isChecked():
            parameters = [float(i) for i in self.alsLineEdit.text().split(',')]
            self.data['Load_filtered'] = self.data['Load_filtered']-self.baseline_als(self.data['Load_filtered'],
                                                                        parameters[0],
                                                                        parameters[1])
        if not self.initial_load:

            minIndex = int(self.startIndex.toPlainText())
            maxIndex = int(self.endIndex.toPlainText())

            #truncate data to indices
            self.data = self.data.iloc[minIndex:maxIndex]

        # print data to table
        self.model = PandasModel(self.data)
        self.tableView.setModel(self.model)

        # after loading new data, clear the plot
        self.clear_plot()
        self.initial_load = False

        self.plot_data()

    def fileSelect(self):

        #init filepath
        self.filepath = ''

        # Open a new window to select files - only .mat files will be shown
        dialog = QtGui.QFileDialog(None, "Open File", None, "CSV-files (*.csv)")
        dialog.exec_()

        for file in dialog.selectedFiles():
            self.filepath = file

        self.update_data()

    def plot_data(self):

        self.graphWidget.setTitle(self.filepath)
        self.graphWidget.addLegend(pen=pg.mkPen(color=(0, 0, 0)),
                                   brush=pg.mkBrush(color=(255, 255, 255)))

        pen1 = pg.mkPen(color=(255, 136, 0),
                        width=2,
                        alpha=0.5)

        pen2 = pg.mkPen(color=(200, 200, 255),
                        width=1,
                        alpha=0.5)

        penFiltered = pg.mkPen(color=(50, 50, 50),
                        width=1,
                        alpha=0.25)


        if self.data_in_plot:
            self.clear_plot()

        Load = self.data['Load'].values
        Filtered = self.data.Load_filtered.values
        Displacement = self.data['Displacement'].values
        Index = self.data['Index'].values

        self.graphWidget.plot(Index, Displacement, pen=pen1,name='Displacement')
        self.graphWidget.plot(Index, Load, pen=pen2, name='Load')
        self.graphWidget.plot(Index, Filtered, pen=penFiltered, name='Load Filtered')

        self.data_in_plot = True

    def baseline_als(self, y, lam, p, niter=10):
        from scipy import sparse
        from scipy.sparse.linalg import spsolve
        L = len(y)
        D = sparse.csc_matrix(np.diff(np.eye(L), 2))
        w = np.ones(L)
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = spsolve(Z, w * y)
            w = p * (y > z) + (1 - p) * (y < z)
        return z



def main():

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()