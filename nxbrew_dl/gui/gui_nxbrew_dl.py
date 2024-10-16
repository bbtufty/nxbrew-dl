import os
from functools import partial

from PySide6.QtCore import Slot, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
)

import nxbrew_dl
from .gui_about import AboutWindow
from .gui_utils import open_url, get_gui_logger, add_row_to_table
from .layout_nxbrew_dl import Ui_nxbrew_dl
from ..nxbrew_dl import load_yml, save_yml, get_game_dict


def open_game_url(item):
    """If a row title is clicked, open the associated URL"""

    column = item.column()

    # If we're not clicking the name, don't do anything
    if column != 0:
        return

    # Search by URL, so pull that out here
    url = item.toolTip()
    open_url(url)


class MainWindow(QMainWindow):

    def __init__(self):
        """NXBrew-dl Main Window

        TODO:
            - Actually download stuff
            - Region/language priorities
        """

        super().__init__()

        self.ui = Ui_nxbrew_dl()
        self.ui.setupUi(self)

        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), "img", "logo.svg")
        icon = QIcon()
        icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)

        # Load in various config files
        self.mod_dir = os.path.dirname(nxbrew_dl.__file__)
        self.general_config = load_yml(
            os.path.join(self.mod_dir, "configs", "general.yml")
        )
        self.regex_config = load_yml(os.path.join(self.mod_dir, "configs", "regex.yml"))

        # Read in the user config, keeping the filename around so we can save it out later
        self.user_config_file = os.path.join(os.getcwd(), "config.yml")
        if os.path.exists(self.user_config_file):
            self.user_config = load_yml(self.user_config_file)
        else:
            self.user_config = {}
        self.load_config()

        self.logger = get_gui_logger(log_level="INFO")
        self.logger.warning("Do not close this window!")

        # Set up the worker threads for later
        self.nxbrew_thread = None
        self.nxbrew_worker = None

        # Help menu buttons
        documentation = self.ui.actionDocumentation
        documentation.triggered.connect(
            lambda: open_url("https://nxbrew-dl.readthedocs.io")
        )

        issues = self.ui.actionIssues
        issues.triggered.connect(
            lambda: open_url("https://github.com/bbtufty/nxbrew-dl/issues")
        )

        about = self.ui.actionAbout
        about.triggered.connect(lambda: AboutWindow(self).exec())

        # Main window buttons
        run_nxbrew_dl = self.ui.pushButtonRun
        run_nxbrew_dl.clicked.connect(self.run_nxbrew_dl)

        exit_button = self.ui.pushButtonExit
        exit_button.clicked.connect(self.close_all)

        # Directory browing for the download directory
        self.ui.pushButtonDownloadDir.clicked.connect(
            partial(self.set_directory_name, line_edit=self.ui.lineEditDownloadDir)
        )

        self.game_table = self.ui.tableGames
        self.game_dict = {}

        # Add in refresh option
        refresh_button = self.ui.pushButtonRefresh
        refresh_button.clicked.connect(self.load_table)

        # Set up the table so links will open the webpages
        self.game_table.itemDoubleClicked.connect(open_game_url)

        # Set up the search bar
        self.search_bar = self.ui.lineEditSearch
        self.search_bar.textChanged.connect(self.update_display)

        self.load_table()

    def get_game_dict(self):
        """Get game dictionary from NXBrew A-Z page"""

        if "nxbrew" not in self.user_config.get("nxbrew_url", ""):
            self.logger.warning(
                "NXBrew URL not found. Enter one and refresh the game list!"
            )
            return False

        self.game_dict = get_game_dict(
            general_config=self.general_config,
            regex_config=self.regex_config,
            nxbrew_url=self.user_config["nxbrew_url"],
        )

    def update_display(self, text):
        """When using the search bar, show/hide rows

        Args:
            text (str): Text to filter out rows
        """

        for r in range(self.game_table.rowCount()):
            r_text = self.game_table.item(r, 0).text()
            if text.lower() in r_text.lower():
                self.game_table.showRow(r)
            else:
                self.game_table.hideRow(r)

    def load_table(self):
        """Load the game table, disable things until we're done"""

        self.ui.centralwidget.setEnabled(False)

        # Save and load the config
        self.save_config()
        self.load_config()

        self.game_dict = {}
        self.get_game_dict()

        # Clear out the old table and search bar
        self.search_bar.clear()
        self.game_table.setRowCount(0)

        # Add rows to the game dict
        for name in self.game_dict:
            row = add_row_to_table(self.game_table, self.game_dict[name])
            self.game_dict[name].update(
                {
                    "row": row,
                }
            )

        self.ui.centralwidget.setEnabled(True)

    def load_config(
        self,
    ):
        """Apply read in config to the GUI"""

        if "nxbrew_url" in self.user_config:
            self.ui.lineEditNXBrewURL.setText(self.user_config["nxbrew_url"])

        if "download_dir" in self.user_config:
            self.ui.lineEditDownloadDir.setText(self.user_config["download_dir"])

        if "prefer_filetype" in self.user_config:

            prefer_filetype = self.user_config["prefer_filetype"]

            if prefer_filetype == "NSP":
                button = self.ui.radioButtonPreferNSP
            elif prefer_filetype == "XCI":
                button = self.ui.radioButtonPreferXCI
            else:
                raise ValueError(
                    f"Do not understand preferred filetype {prefer_filetype}"
                )

            button.setChecked(True)

        if "download_updates" in self.user_config:
            dl_updates = self.user_config["download_updates"]
            self.ui.checkBoxDownloadUpdates.setChecked(dl_updates)

        if "download_dlc" in self.user_config:
            dl_dlc = self.user_config["download_dlc"]
            self.ui.checkBoxDownloadDLC.setChecked(dl_dlc)

    def save_config(
        self,
    ):
        """Save config to file"""

        self.user_config["nxbrew_url"] = self.ui.lineEditNXBrewURL.text()
        self.user_config["download_dir"] = self.ui.lineEditDownloadDir.text()

        prefer_filetype = self.ui.buttonGroupPreferNSPXCI.checkedButton().text()
        if prefer_filetype == "Prefer NSPs":
            self.user_config["prefer_filetype"] = "NSP"
        elif prefer_filetype == "Prefer XCIs":
            self.user_config["prefer_filetype"] = "XCI"
        else:
            raise ValueError(f"Button {prefer_filetype} not understood")

        self.user_config["download_updates"] = (
            self.ui.checkBoxDownloadUpdates.isChecked()
        )
        self.user_config["download_dlc"] = self.ui.checkBoxDownloadDLC.isChecked()

        save_yml(self.user_config_file, self.user_config)

        return True

    def set_directory_name(
        self,
        line_edit,
    ):
        """Make a button set a directory name

        Args:
            line_edit (QLineEdit): The QLineEdit widget to set the text for
        """

        filename = QFileDialog.getExistingDirectory(
            self,
            caption=self.tr("Select directory"),
            dir=os.getcwd(),
        )
        if filename != "":
            line_edit.setText(filename)

    @Slot()
    def run_nxbrew_dl(self):
        """Run NXBrew-dl"""

        # Start out by saving the config
        self.save_config()

        raise NotImplementedError("Not yet implemented!")

    @Slot()
    def close_all(self):
        """Close the application"""

        self.logger.info("Closing down. Will save config")
        self.save_config()

        QApplication.closeAllWindows()
