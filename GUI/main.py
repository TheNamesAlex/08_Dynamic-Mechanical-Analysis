from PyQt5 import QtWidgets, uic, QtGui, QtCore

from pyqtgraph import PlotWidget
import pyqtgraph as pg

import sys
import csv

from PandasConvert import PandasModel
import pandas as pd

from scipy.signal import savgol_filter, butter, sosfilt, detrend

import numpy as np

pg.setConfigOption('background', 'w')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

form = resource_path("UI.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(form)

class MainWindow(QtWidgets.QMainWindow):

    data_in_plot = False
    initial_load = True
    FLAG_stress_strain = False

    calls = {'convertPlotToLoadDisplacement':0,
             'convertPlotToStressStrain':0,
             'calculate_regression_line_stress_strain':0,
             'draw_regression_line':0,
             'reset_indices':0,
             'clear_plot':0,
             'update_model':0,
             'getheader_and_sep':0,
             'update_data':0,
             'fileSelect':0,
             'plot_data':0,
             'baseline_als':0
             }

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        form = resource_path("UI.ui")
        #Ui_MainWindow, QtBaseClass = uic.loadUi(form)
        uic.loadUi(form, self)

        #initialize  variables
        self.startIndex.setText('0')
        self.endIndex.setText('99999')

        #TEXTINPUT INDICES
        self.startIndex.textChanged.connect(self.update_data)
        self.endIndex.textChanged.connect(self.update_data)
        self.decimalSeparatorTextEdit.textChanged.connect(self.update_data)

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

        #connecting the button to select data, when clicked, clear all shown
        self.selectData.clicked.connect(self.clear_plot)
        self.selectData.clicked.connect(self.fileSelect)

        #connecting the button to update data, and clean and redraw figures
        self.clearAndPlotData_button.clicked.connect(self.reset_indices)
        self.clearAndPlotData_button.clicked.connect(self.update_data)
        self.clearAndPlotData_button.clicked.connect(self.plot_data)

        #connecting button to convert displacement_load plot to stress_strain units
        self.convertToStressStrainButton.clicked.connect(self.convertPlotToStressStrain)
        self.convertToLoadDisplacement.clicked.connect(self.convertPlotToLoadDisplacement)

    def convertPlotToLoadDisplacement(self):
        self.clear_plot()
        self.update_data()
        self.FLAG_stress_strain = False
        self.plot_data()

    def convertPlotToStressStrain(self):
        self.clear_plot()
        self.update_data()
        self.FLAG_stress_strain = True
        #after adding data, update model and redraw plot
        self.plot_data()

        #calculate regression line for filtered data
        self.calculate_regression_line_stress_strain()

    def calculate_regression_line_stress_strain(self):
        #x = Strain, y = Stress_N_msquared
        y = self.data['Stress_N_msquared'].values
        x = self.data['Strain'].values

        #solve LLS Optimization problem min ||y - Phi*Theta||_2^2, Phi being [[1, x_0]^T,...,[1,x_N]^T]T
        Phi = np.array([np.ones(len(self.data)),x]).T
        self.Theta = np.linalg.inv(Phi.T @ Phi)@Phi.T @ y

        #print young's modulus to boxes
        self.youngsModulusTextEdit.setText(str(self.Theta[1]))

        #draw regression line into lower plot
        self.draw_regression_line()

    def draw_regression_line(self):
        x = self.data['Strain'].values
        Phi = np.array([np.ones(len(self.data)),x]).T
        y = Phi@self.Theta

        brushScatter = pg.mkBrush(color=(255, 0, 0, 100))
        scatter = pg.ScatterPlotItem(size=2, brush=brushScatter, name='Stress-Strain Data')
        scatter.addPoints(x, y)
        self.loadDisplacementWidget.addItem(scatter)

    def reset_indices(self):
        self.startIndex.setText('0')
        self.endIndex.setText('99999')

    def clear_plot(self):
        self.timeseriesgraphWidget.clear()
        self.loadDisplacementWidget.clear()

        self.data_in_plot = False

    def update_model(self):
        self.model = PandasModel(self.data)
        self.tableView.setModel(self.model)

    def getheader_and_sep(self):
        with open(self.filepath) as f:
            reader = csv.reader(f, delimiter="\t")
            for i, line in enumerate(reader):
                sep=','
                if len(line) > 0:
                    if line[0].find(';') > 0:
                        sep = ';'
                    if line[0].find(',') > 0:
                        sep = ','
                    line = line[0].split(sep)
                    if line[0] == 'Points':
                        #print(i, sep)
                        f.close()
                        break
        return i, sep

    def update_data(self):
        #we might encounter different headers in the file. This part searches for the first occurence in the
        #update current filepath label
        self.currentFilePathLabel.setText(self.filepath[self.filepath.rfind('/')+1:])

        # populate table after loading data
        self.names = ['Point', 'Time_Elapsed', 'Time_Scan', 'Displacement', 'Load', 'E11', 'E12', 'E22', 'Ax_cmd',
                      'Ax_err', 'No_Val']

        self.data = pd.read_csv(self.filepath,
                                header=2
                                ,
                                names=self.names,
                                sep=','
                                )

        # remove duplicate rows
        self.data = self.data.drop_duplicates(subset=['Time_Elapsed'], keep='first')

        # assign walking index
        self.data['Index'] = [i for i in range(1, len(self.data) + 1)]

        self.data['Load_filtered'] = self.data.Load.values

        if not self.initial_load:

            minIndex = int(self.startIndex.toPlainText())
            maxIndex = int(self.endIndex.toPlainText())

            #truncate data to indices
            self.data = self.data.iloc[minIndex:maxIndex]

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



        #add stress strain columns to data
        self.height, self.width, self.length = [float(i) for i in self.heightWidthGaplengthLineEdit.text().split(',')]
        self.data['Stress_N_msquared'] = 1e6 * self.data['Load_filtered'] / (self.height * self.width)
        self.data['Strain'] = self.data['Displacement'] / self.length

        # print data to table
        self.update_model()

        # after loading new data, clear the plot
        self.clear_plot()
        self.initial_load = False

        self.plot_data()

    def fileSelect(self):

        self.FLAG_stress_strain = False
        #init filepath
        self.filepath = ''

        # Open a new window to select files - only .mat files will be shown
        dialog = QtGui.QFileDialog(None, "Open File", None, "CSV-files (*.csv)")
        dialog.exec_()

        for file in dialog.selectedFiles():
            self.filepath = file

        self.update_data()

    def plot_data(self):
        #======================================================================
        #parameters for legends

        legendLabelTextColor = (0, 0, 0)
        legendPen = pg.mkPen(color=(0, 0, 0))
        legendBrush = pg.mkBrush(color=(255, 255, 255))

        #======================================================================
        # plot time series, due to small numerival values, displacement data is plotted in mm and not in m
        self.timeseriesgraphWidget.setTitle('Time Series for Load [N] and Displacement [mm]')
        self.timeseriesgraphWidget.addLegend(labelTextColot = legendLabelTextColor,
                                             pen=legendPen,
                                             brush=legendBrush)

        self.timeseriesgraphWidget.setLabel('left', "Displacement  [mm] and Load [N]")#, units='A')
        self.timeseriesgraphWidget.setLabel('bottom', "Data Point [1]")#, units='A')

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

        self.timeseriesgraphWidget.plot(Index, Displacement, pen=pen1,name='Displacement [mm]')
        self.timeseriesgraphWidget.plot(Index, Load, pen=pen2, name='Load [N]')
        self.timeseriesgraphWidget.plot(Index, Filtered, pen=penFiltered, name='Load Filtered [N]')


    # ======================================================================
    # plot elliptical stress strain curve
        # cant directly plot scatter into plotWidget. Maybe try with a brush passed into plotWidget?
        label_left = ('left', "Load [N]")
        label_bottom = ('bottom', "Displacement [mm]")

        if self.FLAG_stress_strain:
            Displacement = self.data['Strain']
            Filtered = self.data['Stress_N_msquared']
            label_left = ('left', "Stress [N/mm²]")
            label_bottom = ('bottom', "Strain [1]")

        self.loadDisplacementWidget.setTitle('Stress-Strain Data')

        self.loadDisplacementWidget.addLegend(labelTextColot=legendLabelTextColor,
                                               pen=legendPen,
                                               brush=legendBrush)

        self.loadDisplacementWidget.setLabel(*label_left)  # , units='A')
        self.loadDisplacementWidget.setLabel(*label_bottom)  # , units='A')

        brushScatter = pg.mkBrush(color=(50, 50, 255, 100))
        scatter = pg.ScatterPlotItem(size=5, brush=brushScatter, name='Stress-Strain Data')
        scatter.addPoints(Displacement, Filtered)

        self.loadDisplacementWidget.addItem(scatter)



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