import sys
from pathlib import Path
from typing import Optional

import laspy
from pydantic import ValidationError
from pydantic.fields import ModelField
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QEventLoop, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from three_d_fin.gui.expert_dlg import Ui_Dialog
from three_d_fin.gui.main_window import Ui_MainWindow
from three_d_fin.processing.abstract_processing import FinProcessing
from three_d_fin.processing.configuration import FinConfiguration


class ApplicationWorker(QObject):
    """Simple worker to handle FinProcessing in a dedicated QThread."""

    finished = pyqtSignal()
    error = pyqtSignal()

    def __init__(self, processing_object: FinProcessing, parent=None):
        """Construct the Worker.

        Parameters
        ----------
        processing_object : FinProcessing
            An implementation of the abstract FinProcessing class.
            it is responsible for the computing logic.
            Its process() method is triggered by the "compute" button of the GUI.
        parent : Optional[QWidget]
            An optional parent. Should be None if runned as standalone but could
            be a parent QWidget from the base application if runned as a plugin
        """
        super().__init__(parent)
        self.processing_object = processing_object

    def run(self):
        """Run the FinProcessing object.

        This method is called by the QThread
        """
        try:
            self.processing_object.process()
        except Exception:
            self.error.emit()  # TODO: emit something usefull
        self.finished.emit()


class ExpertDialog(QDialog):
    """Create the expert / about dialog.

    For now, it's an empty shell but it is left as is for further
    programatically added parameters.
    """

    def __init__(self, parent=None):
        """Init the dialog."""
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)


class Application(QMainWindow):
    """The GUI Application."""

    params: FinConfiguration = FinConfiguration()

    event_loop: QEventLoop = None

    def __init__(
        self,
        processing_object: FinProcessing,
        file_externally_defined: bool = False,
        cloud_fields: Optional[set[str]] = None,
        parent: QWidget = None,
    ):
        """Construct the 3DFin GUI Application.

        Parameters
        ----------
        processing_object : FinProcessing
            An implementation of the abstract FinProcessing class.
            it is responsible for the computing logic.
            Its process() method is triggered by the "compute" button of the GUI.
        file_externally_defined : bool
            Whether or not the file/filename was already defined by a third party.
            if True, input_las input and buttons will be disabled.
        cloud_fields : Optional[list[str]]
            List of candidates fields for the Z0 field. If present (not None),
            the z0_entry will be turned into a dropdown menu. If present but void,
            height normalization radio buttons will be disabled.
        parent : Optional[QWidget]
            An optional parent. Should be None if runned as standalone but could
            be a parent QWidget from the base application if runned as a plugin
        """
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.processing_object = processing_object
        self.file_externally_defined = file_externally_defined
        self.cloud_fields = cloud_fields

        # Force current index to be 0, since QT creator could change that
        self.ui.tabWidget.setCurrentIndex(0)
        self.setWindowIcon(QtGui.QIcon(":/assets/three_d_fin/assets/icon_window.ico"))

        # Click on the "documentation"
        self.ui.documentation_link_btn.clicked.connect(self._show_documentation)

        # Click on the "?" button on the expert table
        self.ui.expert_info_btn.clicked.connect(self._show_expert_dialog)

        # Click on input
        self.ui.input_file_btn.clicked.connect(self._ask_input_file)

        # Click on output
        self.ui.output_dir_btn.clicked.connect(self._ask_output_dir)

        # Click on compute
        self.ui.compute_btn.clicked.connect(self._compute_clicked)

        # Connect is_normalized
        self.ui.is_normalized_chk.toggled.connect(self._normalize_toggled)

        # Handle the case of a predefined and limited choice of cloud_fields
        if self.cloud_fields is not None:
            layout = self.ui.z0_name_in.parent().layout()
            field_combo = QComboBox(self)
            field_combo.addItems(self.cloud_fields)
            layout.replaceWidget(self.ui.z0_name_in, field_combo)
            self.ui.z0_name_in.setParent(None)
            self.ui.z0_name_in = field_combo

        # Handle the case where the input file is defined by another mean
        if self.file_externally_defined:
            self.ui.input_file_lbl.setDisabled(True)
            self.ui.input_file_lbl.setText("File already set by the application")
            self.ui.input_file_btn.setDisabled(True)
            self.ui.input_file_in.setDisabled(True)

        self._load_config_or_default()
        self._populate_fields()

    def _load_config_or_default(self):
        """Try to load a config file or fallback to default.

        TODO: Maybe it should be migrated into the FinProcessing constructor
        """
        try:
            # Reading config file only if it is available under name '3DFinconfig.ini'
            config_file_path = Path("3DFinconfig.ini")
            self.params = FinConfiguration.From_config_file(
                config_file_path.resolve(strict=True), init_misc=True
            )
            print("Configuration file found. Setting default parameters from the file")
        except ValidationError:
            print("Configuration file error")
            self.params = FinConfiguration()
        except FileNotFoundError:
            # No error message in this case, fallback to default parameters
            self.params = FinConfiguration()
        self.params = FinConfiguration()

    def _populate_fields(self):
        """Populate fields with default value, labels, tooltips based on FinConfiguration."""
        # params and QT fields have the same name, we take advantage of that
        config_dict = self.params.dict()
        for config_section in config_dict:
            for key_param, value_param in config_dict[config_section].items():
                # Default z0_name should match one of the supplied list if present.
                tooltip_text = FinConfiguration.field_tooltip(config_section, key_param)
                if key_param == "z0_name" and self.cloud_fields is not None:
                    if value_param in self.cloud_fields:
                        id_default = self.cloud_fields.index(value_param)
                        self.ui.z0_name_in.setCurrentIndex(id_default)
                    self.ui.z0_name_in.setToolTip(tooltip_text)
                    self.ui.z0_name_lbl.setToolTip(tooltip_text)
                # Fix a minor presentation issue when no file is defined
                elif key_param == "input_file" and value_param is None:
                    self.ui.input_file_in.setText("")
                    self.ui.input_file_lbl.setToolTip(tooltip_text)
                    self.ui.input_file_in.setToolTip(tooltip_text)
                elif key_param == "is_normalized":
                    self.ui.is_normalized_chk.setChecked(not value_param)
                    self.ui.is_normalized_chk.setToolTip(tooltip_text)
                elif key_param == "is_noisy":
                    self.ui.is_noisy_chk.setChecked(value_param)
                    self.ui.is_noisy_chk.setToolTip(tooltip_text)
                elif key_param == "export_txt":
                    self.ui.export_txt_rb_1.setChecked(value_param)
                    self.ui.export_txt_rb_2.setChecked(not value_param)
                    self.ui.export_txt_lbl.setToolTip(tooltip_text)
                else:
                    getattr(self.ui, key_param + "_in").setText(str(value_param))
                    getattr(self.ui, key_param + "_in").setToolTip(tooltip_text)
                    getattr(self.ui, key_param + "_lbl").setToolTip(tooltip_text)

    def _show_expert_dialog(self):
        """Show the expert help/about dialog."""
        dialog = ExpertDialog(self)
        dialog.show()

    def _show_documentation(self):
        """Show the documentation.

        Open the default PDF viewer to show the documentation.
        """
        try:
            base_path = Path(sys._MEIPASS)
        except Exception:
            base_path = Path(__file__).absolute().parents[1] / "documentation"
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(
                str(Path(base_path / "documentation.pdf").resolve())
            )
        )

    def _ask_input_file(self):
        """Ask for a proper input las file.

        Current selected file is checked for validity (existence and type)
        in order to setup the initial dir and the initial file in
        the dialog. If a file is selected then it is checked to be a valid
        Las file before adding its path to the related input field.
        the output directory is changed accordingly (default to input las file
        parent directory)
        """
        initial_path = Path(self.ui.input_file_in.text())
        is_initial_file = (
            True if initial_path.exists() and initial_path.is_file() else False
        )
        initial_dir = initial_path.parent.resolve() if is_initial_file else Path.home()
        las_file, _ = QFileDialog.getOpenFileName(
            self,
            "3DFin input file",
            str(initial_dir),
            "las files (*.las *.Las *.Laz *.laz)",
        )

        if las_file == "" or None:
            return

        try:
            laspy.open(las_file, read_evlrs=False)
        except laspy.LaspyException:
            QMessageBox.critical(self, "3DFin Error", "Invalid input file")
            return

        self.ui.input_file_in.setText(str(Path(las_file).resolve()))
        self.ui.output_dir_in.setText(str(Path(las_file).parent.resolve()))

    def _ask_output_dir(self):
        """Ask for a proper output directory."""
        initial_path = Path(self.ui.output_dir_in.text())
        has_valid_initial_dir = (
            True if initial_path.exists() and initial_path.is_dir() else False
        )
        initial_dir = initial_path if has_valid_initial_dir else Path.home()
        self.ui.output_dir_in.setText(str(initial_dir.resolve()))

        output_dir = QFileDialog.getExistingDirectory(
            self, "3DFin output directory", str(initial_dir)
        )

        # If the dialog was not closed/canceled
        if output_dir != "" and not None:
            self.ui.output_dir_in.setText(str(Path(output_dir).resolve()))

    def _get_parameters(self):
        """Get parameters from widgets and return them organized in a dictionary.

        Returns
        -------
        options : dict[str, dict[str, str]]
            Dictionary of parameters. It is organized following the
            3DFinconfig.ini file: Each parameters are sorted in a sub-dict
            ("basic", "expert", "advanced", "misc").
        """
        config_dict: dict[str, dict[str, str]] = dict()
        for category_name, category_field in FinConfiguration.__fields__.items():
            category_dict: dict[str, str] = dict()
            for key_param in category_field.type_().__fields__:
                if key_param == "z0_name" and self.cloud_fields is not None:
                    category_dict[key_param] = self.ui.z0_name_in.currentText()
                # When file is externally defined, force it to None to avoid validation errors
                elif key_param == "input_file" and self.file_externally_defined:
                    category_dict[key_param] = None
                elif key_param == "is_normalized":
                    category_dict[key_param] = not self.ui.is_normalized_chk.isChecked()
                elif key_param == "is_noisy":
                    category_dict[key_param] = self.ui.is_noisy_chk.isChecked()
                elif key_param == "export_txt":
                    category_dict[key_param] = not self.ui.export_txt_rb_1.isChecked()
                else:
                    category_dict[key_param] = getattr(
                        self.ui, key_param + "_in"
                    ).text()
            config_dict[category_name] = category_dict
        return config_dict

    def _compute_clicked(self):
        """Validate I/O entries and run the processing callback."""
        params = self._get_parameters()

        # define a local function in order to popup errors
        def _show_error(error_msg: str) -> str:
            return QMessageBox.critical(self, "3DFin Error", error_msg)

        # Pydantic checks, we check the validity of the data
        try:
            fin_config = FinConfiguration.parse_obj(params)
        except ValidationError as validation_errors:
            final_msg: str = "Invalid Parameters:\n\n"
            for error in validation_errors.errors():
                error_loc: list[str] = error["loc"]
                # Get the human readable value for the field by introspection
                # (stored in "title "attribute)
                field: ModelField = (
                    FinConfiguration.__fields__[error_loc[0]]
                    .type_()
                    .__fields__[error_loc[1]]
                )
                title = field.field_info.title
                # formatting
                final_msg = final_msg + f"{title} \n"
                final_msg = final_msg + f"""\t -> {error["msg"]} \n"""
            _show_error(final_msg)
            return

        self.processing_object.set_config(fin_config)

        # Here we will check in an astract way if the output could collide
        # with previous computations... and ask if we want to overwrite them.
        if self.processing_object.check_already_computed_data():
            overwrite = QMessageBox.question(
                self,
                "3DFin",
                "The output target already contains results from a previous 3DFin computation, do you want to overwrite them?",
            )
            if overwrite == QMessageBox.No:
                return

        # Handle changes in the GUI when compute is launch/finished
        def _disable_btn():
            self.ui.compute_btn.setDisabled(True)
            self.ui.compute_btn.setText("Computing...")

        def _enable_btn():
            self.ui.compute_btn.setDisabled(False)
            self.ui.compute_btn.setText("Compute")

        def _error_handling():
            _enable_btn()
            QMessageBox.critical(self, "3DFin error", "Something went wrong!")

        # Now we do the processing in itself
        self.thread = QThread()
        # Create a worker object
        self.worker = ApplicationWorker(self.processing_object)
        _disable_btn()
        # Move the worker to the thread
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # TODO: handle exception in processing here
        self.worker.finished.connect(_enable_btn)
        self.worker.error.connect(_error_handling)
        self.thread.start()

    def _normalize_toggled(self):
        self.ui.is_noisy_chk.setEnabled(self.ui.is_normalized_chk.isChecked())
        self.ui.z0_name_in.setEnabled(not self.ui.is_normalized_chk.isChecked())
        self.ui.z0_name_lbl.setEnabled(not self.ui.is_normalized_chk.isChecked())

    def set_event_loop(self, loop):
        """Set an optional event loop.

        In some context (e.g. CloudCompare plugin), we need to set a dedicated
        event loop to the application.

        Parameters
        ----------
        loop : QEventLoop
            The event loop to set
        """
        self.event_loop = loop

    def closeEvent(self, a0):
        """Close the application.

        The event loop is exited if it was set.

        Parameters
        ----------
        a0 : QCloseEvent
            The close event
        """
        super().closeEvent(a0)
        if self.event_loop is not None:
            self.event_loop.exit()
        # TODO: quit thread without messing with the event loop
        # if self.thread is not None and self.thread.isRunning():
        #    self.thread.exit()
