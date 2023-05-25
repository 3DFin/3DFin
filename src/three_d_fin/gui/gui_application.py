import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog
from PyQt5 import QtCore, QtGui

from three_d_fin.gui.main_window import Ui_MainWindow
from three_d_fin.gui.expert_dlg import Ui_Dialog

class ExpertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Force current index to be 0, since QT creator could change that
        self.ui.tabWidget.setCurrentIndex(0)
        self.setWindowIcon(QtGui.QIcon(":/assets/three_d_fin/assets/icon_window.ico"))

        # Click on the "documentation"
        self.ui.documentation_link_btn.clicked.connect(self.show_documentation)
        
        # Click on the "?" button on the expert table
        self.ui.expert_info_btn.clicked.connect(self.show_expert_dialog)

        # Click on input
        self.ui.input_file_btn.clicked.connect(self.input_file_clicked)
    
        # Click on output
        self.ui.output_dir_btn.clicked.connect(self.output_dir_clicked)

        # Click on compute
        self.ui.compute_btn.clicked.connect(self.compute_clicked)

    def show_expert_dialog(self):
        """Show the expert help/warning dialog"""
        dialog = ExpertDialog(self)
        dialog.show()

    def show_documentation(self):
        """Show the documentation.

        Open the default PDF viewer to show the documentation.
        """
        try:
            base_path = Path(sys._MEIPASS)
        except Exception:
            base_path = Path(__file__).absolute().parents[1] / "documentation"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(Path(base_path / "documentation.pdf"))));

    def input_file_clicked(self):
        input_dialog = QFileDialog(self)
        if input_dialog.exec_():
            self.ui.input_file_in.setText(input_dialog.selectedFiles()[0])
    
    def output_dir_clicked(self):
        input_dialog = QFileDialog(self)
        if input_dialog.exec_():
            self.ui.output_dir_in.setText(input_dialog.selectedFiles()[0])

    def compute_clicked(self):
        placeholder = QDialog(self)
        placeholder.show()

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
