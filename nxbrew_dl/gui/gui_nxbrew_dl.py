import os
import sys
import time
import traceback
from functools import partial
from urllib.parse import urlparse

import requests
from PySide6.QtCore import (
    Slot,
    Signal,
    QObject,
    QThread,
    QSize,
    Qt,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMessageBox,
    QMainWindow,
    QFileDialog,
)
from myjdapi.exception import MYJDException
from packaging.version import Version

import nxbrew_dl
from .gui_about import AboutWindow
from .gui_regions_languages import RegionLanguageWindow
from .gui_utils import (
    open_url,
    add_row_to_table,
    get_ordered_list,
)
from .layout_nxbrew_dl import Ui_nxbrew_dl
from ..nxbrew_dl import NXBrew
from ..util import (
    check_github_version,
    get_game_dict,
    NXBrewLogger,
    load_yml,
    save_yml,
    load_json,
)


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

        This is the main GUI for NXBrew-dl. It's where the magic happens!
        """

        super().__init__()

        # Load in main GUI
        self.ui = Ui_nxbrew_dl()
        self.ui.setupUi(self)

        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), "img", "logo.svg")
        icon = QIcon()
        icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)

        # Set up the logger
        self.logger = NXBrewLogger(log_level="INFO")
        self.logger.warning("Do not close this window!")

        # Check for version updates
        self.logger.info("Checking for new versions online")
        github_version, github_url = check_github_version()
        local_version = nxbrew_dl.__version__

        new_version_available = False
        if Version(local_version) < Version(github_version):
            self.logger.info("New version of NXBrew-dl available!")
            new_version_available = True
        else:
            self.logger.info("You have the latest version of NXBrew-dl")

        self.update_notification = self.setup_update_notification(
            new_version_available,
            url=github_url,
        )

        # Load in various config files
        self.mod_dir = os.path.dirname(nxbrew_dl.__file__)

        general_config_filename = os.path.join(self.mod_dir, "configs", "general.yml")
        self.general_config = load_yml(general_config_filename)

        regex_config_filename = os.path.join(self.mod_dir, "configs", "regex.yml")
        self.regex_config = load_yml(regex_config_filename)

        # Read in the user config, keeping the filename around so we can save it out later
        self.user_config_file = os.path.join(os.getcwd(), "config.yml")
        if os.path.exists(self.user_config_file):
            self.user_config = load_yml(self.user_config_file)
        else:
            self.user_config = {}

        # Load in regions/languages popup
        self.regions_languages = RegionLanguageWindow(
            general_config=self.general_config,
            user_config=self.user_config,
        )
        reg_lang_button = self.ui.pushButtonRegionLanguage
        reg_lang_button.clicked.connect(lambda: self.regions_languages.show())

        # Read in user cache, keeping the filename around so we can save it out later
        self.user_cache_file = os.path.join(os.getcwd(), "cache.json")
        if os.path.exists(self.user_cache_file):
            self.user_cache = load_json(self.user_cache_file)
        else:
            self.user_cache = {}

        # Do an initial load of the config
        self.load_config()

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
        exit_button.clicked.connect(self.close)

        # Directory browsing for the download directory
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

    def setup_update_notification(
        self,
        new_version_available,
        url,
    ):
        """Create a message box to open up to the latest GitHub release"""

        if not new_version_available:
            return None

        # Open up a dialogue box to go to the webpage
        update_box = QMessageBox()
        reply = update_box.question(
            self,
            "Version update!",
            "Open latest GitHub release?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Opening GitHub, and closing down")
            open_url(url)
            sys.exit()

        return update_box

    def get_game_dict(self):
        """Get game dictionary from NXBrew A-Z page"""

        if "nxbrew" not in self.user_config.get("nxbrew_url", ""):
            self.logger.warning(
                "NXBrew URL not found. Enter one and refresh the game list!"
            )
            return False

        try:
            _ = requests.get(self.user_config["nxbrew_url"])
        except (requests.exceptions.SSLError, requests.exceptions.MissingSchema) as e:
            self.logger.warning(
                "Error found in NXBrew URL! Enter one that works and refresh the game list!"
            )
            return False

        try:
            self.game_dict = get_game_dict(
                general_config=self.general_config,
                regex_config=self.regex_config,
                nxbrew_url=self.user_config["nxbrew_url"],
            )
        except Exception as e:
            self.logger.warning(
                "Error found retreiving game list, try another URL"
            )
            return False

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

    def update_progressbar_value(self, value):
        self.nxbrew_worker.progress_bar.setValue(value)

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

        # If in cache, check the row here
        for cache_item in self.user_cache:
            found_cache_item = False

            cache_item_path = urlparse(cache_item).path

            for r in range(self.game_table.rowCount()):

                table_item_path = urlparse(self.game_table.item(r, 0).toolTip()).path

                if table_item_path == cache_item_path:
                    self.game_table.item(r, 1).setCheckState(Qt.CheckState.Checked)
                    found_cache_item = True
                    break

            if found_cache_item:
                continue

        self.ui.centralwidget.setEnabled(True)

    def load_config(
        self,
    ):
        """Apply read in config to the GUI"""

        text_fields = {
            "nxbrew_url": self.ui.lineEditNXBrewURL,
            "download_dir": self.ui.lineEditDownloadDir,
            "jd_device": self.ui.lineEditJDownloaderDevice,
            "jd_user": self.ui.lineEditJDownloaderUser,
            "jd_pass": self.ui.lineEditJDownloaderPass,
            "discord_url": self.ui.lineEditDiscordURL,
        }

        bool_switches = {
            "download_update": self.ui.checkBoxDownloadUpdates,
            "download_dlc": self.ui.checkBoxDownloadDLC,
            "dry_run": self.ui.checkBoxDryRun,
        }

        # Set text fields
        for field in text_fields:
            if field in self.user_config:
                text_fields[field].setText(self.user_config[field])

        # Set preferred filetypes
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

        # Set the boolean switches
        for bool_switch in bool_switches:
            if bool_switch in self.user_config:
                bool_val = self.user_config[bool_switch]
                bool_switches[bool_switch].setChecked(bool_val)

        # And finally, load the region/language list
        self.regions_languages.load_config()

    def save_config(
        self,
    ):
        """Save config to file"""

        text_fields = {
            "nxbrew_url": self.ui.lineEditNXBrewURL.text(),
            "download_dir": self.ui.lineEditDownloadDir.text(),
            "jd_device": self.ui.lineEditJDownloaderDevice.text(),
            "jd_user": self.ui.lineEditJDownloaderUser.text(),
            "jd_pass": self.ui.lineEditJDownloaderPass.text(),
            "discord_url": self.ui.lineEditDiscordURL.text(),
        }

        bool_switches = {
            "download_update": self.ui.checkBoxDownloadUpdates,
            "download_dlc": self.ui.checkBoxDownloadDLC,
            "dry_run": self.ui.checkBoxDryRun,
        }

        for field in text_fields:
            self.user_config[field] = text_fields[field]

        # Set the NSP/XCI preferences
        prefer_filetype = self.ui.buttonGroupPreferNSPXCI.checkedButton().text()
        if prefer_filetype == "Prefer NSPs":
            self.user_config["prefer_filetype"] = "NSP"
        elif prefer_filetype == "Prefer XCIs":
            self.user_config["prefer_filetype"] = "XCI"
        else:
            raise ValueError(f"Button {prefer_filetype} not understood")

        # Set the boolean switches
        for bool_switch in bool_switches:
            self.user_config[bool_switch] = bool_switches[bool_switch].isChecked()

        # Set region/language priorities (only if there are some!)
        regions = get_ordered_list(
            self.regions_languages.ui.listWidgetConfigRegionsLanguagesRegions
        )
        if len(regions) > 0:
            self.user_config["regions"] = regions

        languages = get_ordered_list(
            self.regions_languages.ui.listWidgetConfigRegionsLanguagesLanguages
        )
        if len(languages) > 0:
            self.user_config["languages"] = languages

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

        # Close any other windows
        self.regions_languages.close()

        # Get a list of things to download
        to_download = {}

        for r in range(self.game_table.rowCount()):
            if self.game_table.item(r, 1).checkState() == Qt.CheckState.Checked:

                url = self.game_table.item(r, 0).toolTip()

                for g in self.game_dict:
                    if self.game_dict[g]["url"] == url:
                        n = self.game_dict[g]["short_name"]
                        to_download.update({n: url})

        # Set up everything so the GUI doesn't hang
        self.nxbrew_thread = QThread()
        self.nxbrew_worker = NXBrewWorker(
            to_download=to_download,
            progress_bar=self.ui.progressBar,
            progress_bar_label=self.ui.labelProgressBar,
            user_config=self.user_config,
            user_cache=self.user_cache,
            logger=self.logger,
        )

        self.nxbrew_worker.moveToThread(self.nxbrew_thread)
        self.nxbrew_thread.started.connect(self.nxbrew_worker.run)
        self.nxbrew_worker.update_progressBar.connect(self.update_progressbar_value)

        # Delete the thread once we're done
        self.nxbrew_worker.finished.connect(self.nxbrew_thread.quit)
        self.nxbrew_worker.finished.connect(self.nxbrew_worker.deleteLater)
        self.nxbrew_thread.finished.connect(self.nxbrew_thread.deleteLater)

        # When finished, re-enable the UI
        self.nxbrew_thread.finished.connect(
            lambda: self.enable_disable_ui(mode="enable")
        )

        # Start the thread
        self.nxbrew_thread.start()

        # Disable the UI
        self.enable_disable_ui(mode="disable")

        return True

    def closeEvent(self, event):
        """Close the application"""

        # Check if we've fully loaded, else just close it down
        loaded = hasattr(self, "user_config")

        if loaded:
            self.logger.info("Closing down. Will save config")
            self.save_config()

        event.accept()

    def enable_disable_ui(self, mode="disable"):
        """Selective enable/disable parts of the UI

        Args:
            mode: Whether to 'enable' or 'disable'. Defaults
                to disable
        """

        # Disable the various UI elements
        ui_elements = [
            self.ui.lineEditNXBrewURL,
            self.ui.lineEditDownloadDir,
            self.ui.pushButtonDownloadDir,
            self.ui.lineEditJDownloaderDevice,
            self.ui.lineEditJDownloaderUser,
            self.ui.lineEditJDownloaderPass,
            self.ui.radioButtonPreferNSP,
            self.ui.radioButtonPreferXCI,
            self.ui.checkBoxDownloadUpdates,
            self.ui.checkBoxDownloadDLC,
            self.ui.pushButtonRegionLanguage,
            self.ui.checkBoxDryRun,
            self.ui.lineEditDiscordURL,
            self.ui.tableGames,
            self.ui.pushButtonRefresh,
            self.ui.pushButtonRun,
            self.ui.pushButtonExit,
        ]

        for e in ui_elements:
            if mode == "disable":
                e.setEnabled(False)
            elif mode == "enable":
                e.setEnabled(True)
            else:
                raise ValueError(
                    f"Button {mode} should be one of 'disable' or 'enable'"
                )

        return True


class NXBrewWorker(QObject):
    """Handles running NXBrew so GUI doesn't hang"""

    finished = Signal()
    update_progressBar = Signal(int)

    def __init__(
        self,
        to_download,
        progress_bar=None,
        progress_bar_label=None,
        general_config=None,
        regex_config=None,
        user_config=None,
        user_cache=None,
        logger=None,
    ):
        """Initialise the NXBrew downloader

        Args:
            to_download (dict): Dictionary of ROMs to download
            progress_bar (QProgressBar, optional): Progress bar widget.
                Defaults to None, which will do nothing fancy with the
                progress bar
            progress_bar_label (QLabel, optional): If set, will put
                the game title in a progress bar label. Defaults to
                None
            general_config (dict): Dictionary of general configuration.
                Defaults to None, which will load in from expected path
            regex_config (dict): Dictionary of regex configuration.
                Defaults to None, which will load in from expected path
            user_config (dict): Dictionary of user configuration.
                Defaults to None, which will load in from expected path
            user_cache (dict): Dictionary of user cache configuration.
                Defaults to None, which will load in from expected path
            logger (logging.Logger): Logger instance. Defaults to None,
                which will set up its own logger
        """
        super().__init__()

        self.to_download = to_download
        self.progress_bar = progress_bar
        self.progress_bar_label = progress_bar_label
        self.general_config = general_config
        self.regex_config = regex_config
        self.user_config = user_config
        self.user_cache = user_cache
        self.logger = logger

    def run(self):
        """Run NXBrew-dl"""

        try:
            nx = NXBrew(
                to_download=self.to_download,
                progress_bar=self.progress_bar,
                progress_bar_label=self.progress_bar_label,
                general_config=self.general_config,
                regex_config=self.regex_config,
                user_config=self.user_config,
                user_cache=self.user_cache,
                logger=self.logger,
                update_progressBar=self.update_progressBar,
            )
            nx.run()
        except (Exception, MYJDException):

            tb = traceback.format_exc()
            for line in tb.splitlines():
                self.logger.warning(line)

        # Sleep a little to avoid potential hangups
        time.sleep(1)

        self.finished.emit()
