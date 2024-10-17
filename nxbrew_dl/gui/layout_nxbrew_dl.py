# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout_nxbrew_dl.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QButtonGroup,
    QCheckBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_nxbrew_dl(object):
    def setupUi(self, nxbrew_dl):
        if not nxbrew_dl.objectName():
            nxbrew_dl.setObjectName(u"nxbrew_dl")
        nxbrew_dl.resize(1187, 721)
        self.actionDocumentation = QAction(nxbrew_dl)
        self.actionDocumentation.setObjectName(u"actionDocumentation")
        self.actionIssues = QAction(nxbrew_dl)
        self.actionIssues.setObjectName(u"actionIssues")
        self.actionAbout = QAction(nxbrew_dl)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(nxbrew_dl)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayoutConfigGames = QHBoxLayout()
        self.horizontalLayoutConfigGames.setObjectName(u"horizontalLayoutConfigGames")
        self.verticalLayoutConfig = QVBoxLayout()
        self.verticalLayoutConfig.setObjectName(u"verticalLayoutConfig")
        self.verticalSpacerConfigTop = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacerConfigTop)

        self.labelNXBrewURL = QLabel(self.centralwidget)
        self.labelNXBrewURL.setObjectName(u"labelNXBrewURL")

        self.verticalLayoutConfig.addWidget(self.labelNXBrewURL)

        self.lineEditNXBrewURL = QLineEdit(self.centralwidget)
        self.lineEditNXBrewURL.setObjectName(u"lineEditNXBrewURL")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEditNXBrewURL.sizePolicy().hasHeightForWidth())
        self.lineEditNXBrewURL.setSizePolicy(sizePolicy)

        self.verticalLayoutConfig.addWidget(self.lineEditNXBrewURL)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacer)

        self.labelDownloadDir = QLabel(self.centralwidget)
        self.labelDownloadDir.setObjectName(u"labelDownloadDir")

        self.verticalLayoutConfig.addWidget(self.labelDownloadDir)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lineEditDownloadDir = QLineEdit(self.centralwidget)
        self.lineEditDownloadDir.setObjectName(u"lineEditDownloadDir")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEditDownloadDir.sizePolicy().hasHeightForWidth())
        self.lineEditDownloadDir.setSizePolicy(sizePolicy1)
        self.lineEditDownloadDir.setMinimumSize(QSize(250, 0))

        self.horizontalLayout.addWidget(self.lineEditDownloadDir)

        self.pushButtonDownloadDir = QPushButton(self.centralwidget)
        self.pushButtonDownloadDir.setObjectName(u"pushButtonDownloadDir")

        self.horizontalLayout.addWidget(self.pushButtonDownloadDir)


        self.verticalLayoutConfig.addLayout(self.horizontalLayout)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacer_3)

        self.labelJDownloaderDevice = QLabel(self.centralwidget)
        self.labelJDownloaderDevice.setObjectName(u"labelJDownloaderDevice")

        self.verticalLayoutConfig.addWidget(self.labelJDownloaderDevice)

        self.lineEditJDownloaderDevice = QLineEdit(self.centralwidget)
        self.lineEditJDownloaderDevice.setObjectName(u"lineEditJDownloaderDevice")
        sizePolicy1.setHeightForWidth(self.lineEditJDownloaderDevice.sizePolicy().hasHeightForWidth())
        self.lineEditJDownloaderDevice.setSizePolicy(sizePolicy1)

        self.verticalLayoutConfig.addWidget(self.lineEditJDownloaderDevice)

        self.labelJDownloaderUser = QLabel(self.centralwidget)
        self.labelJDownloaderUser.setObjectName(u"labelJDownloaderUser")

        self.verticalLayoutConfig.addWidget(self.labelJDownloaderUser)

        self.lineEditJDownloaderUser = QLineEdit(self.centralwidget)
        self.lineEditJDownloaderUser.setObjectName(u"lineEditJDownloaderUser")
        sizePolicy1.setHeightForWidth(self.lineEditJDownloaderUser.sizePolicy().hasHeightForWidth())
        self.lineEditJDownloaderUser.setSizePolicy(sizePolicy1)

        self.verticalLayoutConfig.addWidget(self.lineEditJDownloaderUser)

        self.labelJDownloaderPass = QLabel(self.centralwidget)
        self.labelJDownloaderPass.setObjectName(u"labelJDownloaderPass")

        self.verticalLayoutConfig.addWidget(self.labelJDownloaderPass)

        self.lineEditJDownloaderPass = QLineEdit(self.centralwidget)
        self.lineEditJDownloaderPass.setObjectName(u"lineEditJDownloaderPass")
        sizePolicy1.setHeightForWidth(self.lineEditJDownloaderPass.sizePolicy().hasHeightForWidth())
        self.lineEditJDownloaderPass.setSizePolicy(sizePolicy1)
        self.lineEditJDownloaderPass.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayoutConfig.addWidget(self.lineEditJDownloaderPass)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacer_4)

        self.labelGameDLOptions = QLabel(self.centralwidget)
        self.labelGameDLOptions.setObjectName(u"labelGameDLOptions")

        self.verticalLayoutConfig.addWidget(self.labelGameDLOptions)

        self.radioButtonPreferNSP = QRadioButton(self.centralwidget)
        self.buttonGroupPreferNSPXCI = QButtonGroup(nxbrew_dl)
        self.buttonGroupPreferNSPXCI.setObjectName(u"buttonGroupPreferNSPXCI")
        self.buttonGroupPreferNSPXCI.addButton(self.radioButtonPreferNSP)
        self.radioButtonPreferNSP.setObjectName(u"radioButtonPreferNSP")
        self.radioButtonPreferNSP.setChecked(True)

        self.verticalLayoutConfig.addWidget(self.radioButtonPreferNSP)

        self.radioButtonPreferXCI = QRadioButton(self.centralwidget)
        self.buttonGroupPreferNSPXCI.addButton(self.radioButtonPreferXCI)
        self.radioButtonPreferXCI.setObjectName(u"radioButtonPreferXCI")

        self.verticalLayoutConfig.addWidget(self.radioButtonPreferXCI)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacer_2)

        self.labelGameAdditionalFiles = QLabel(self.centralwidget)
        self.labelGameAdditionalFiles.setObjectName(u"labelGameAdditionalFiles")

        self.verticalLayoutConfig.addWidget(self.labelGameAdditionalFiles)

        self.checkBoxDownloadUpdates = QCheckBox(self.centralwidget)
        self.checkBoxDownloadUpdates.setObjectName(u"checkBoxDownloadUpdates")
        self.checkBoxDownloadUpdates.setChecked(True)

        self.verticalLayoutConfig.addWidget(self.checkBoxDownloadUpdates)

        self.checkBoxDownloadDLC = QCheckBox(self.centralwidget)
        self.checkBoxDownloadDLC.setObjectName(u"checkBoxDownloadDLC")
        self.checkBoxDownloadDLC.setChecked(True)

        self.verticalLayoutConfig.addWidget(self.checkBoxDownloadDLC)

        self.verticalSpacerConfigBottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutConfig.addItem(self.verticalSpacerConfigBottom)


        self.horizontalLayoutConfigGames.addLayout(self.verticalLayoutConfig)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutConfigGames.addItem(self.horizontalSpacer)

        self.verticalLayoutGames = QVBoxLayout()
        self.verticalLayoutGames.setObjectName(u"verticalLayoutGames")
        self.horizontalLayoutSearch = QHBoxLayout()
        self.horizontalLayoutSearch.setObjectName(u"horizontalLayoutSearch")
        self.labelSearch = QLabel(self.centralwidget)
        self.labelSearch.setObjectName(u"labelSearch")

        self.horizontalLayoutSearch.addWidget(self.labelSearch)

        self.horizontalSpacerSearch = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutSearch.addItem(self.horizontalSpacerSearch)

        self.lineEditSearch = QLineEdit(self.centralwidget)
        self.lineEditSearch.setObjectName(u"lineEditSearch")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lineEditSearch.sizePolicy().hasHeightForWidth())
        self.lineEditSearch.setSizePolicy(sizePolicy2)

        self.horizontalLayoutSearch.addWidget(self.lineEditSearch)

        self.horizontalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutSearch.addItem(self.horizontalSpacer_2)

        self.pushButtonRefresh = QPushButton(self.centralwidget)
        self.pushButtonRefresh.setObjectName(u"pushButtonRefresh")
        icon = QIcon(QIcon.fromTheme(u"view-refresh"))
        self.pushButtonRefresh.setIcon(icon)

        self.horizontalLayoutSearch.addWidget(self.pushButtonRefresh)


        self.verticalLayoutGames.addLayout(self.horizontalLayoutSearch)

        self.tableGames = QTableWidget(self.centralwidget)
        if (self.tableGames.columnCount() < 6):
            self.tableGames.setColumnCount(6)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableGames.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        self.tableGames.setObjectName(u"tableGames")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableGames.sizePolicy().hasHeightForWidth())
        self.tableGames.setSizePolicy(sizePolicy3)
        self.tableGames.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tableGames.setFrameShadow(QFrame.Shadow.Sunken)
        self.tableGames.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableGames.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableGames.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableGames.setProperty(u"showDropIndicator", False)
        self.tableGames.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tableGames.setSortingEnabled(True)

        self.verticalLayoutGames.addWidget(self.tableGames)


        self.horizontalLayoutConfigGames.addLayout(self.verticalLayoutGames)


        self.verticalLayout.addLayout(self.horizontalLayoutConfigGames)

        self.verticalSpacerConfigButtons = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacerConfigButtons)

        self.verticalLayoutBottomButtons = QVBoxLayout()
        self.verticalLayoutBottomButtons.setObjectName(u"verticalLayoutBottomButtons")
        self.horizontalLayoutBottomButtons = QHBoxLayout()
        self.horizontalLayoutBottomButtons.setObjectName(u"horizontalLayoutBottomButtons")
        self.pushButtonExit = QPushButton(self.centralwidget)
        self.pushButtonExit.setObjectName(u"pushButtonExit")
        self.pushButtonExit.setMinimumSize(QSize(130, 30))

        self.horizontalLayoutBottomButtons.addWidget(self.pushButtonExit)

        self.horizontalSpacerBottomButtons = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutBottomButtons.addItem(self.horizontalSpacerBottomButtons)

        self.pushButtonRun = QPushButton(self.centralwidget)
        self.pushButtonRun.setObjectName(u"pushButtonRun")
        self.pushButtonRun.setMinimumSize(QSize(130, 30))

        self.horizontalLayoutBottomButtons.addWidget(self.pushButtonRun)


        self.verticalLayoutBottomButtons.addLayout(self.horizontalLayoutBottomButtons)


        self.verticalLayout.addLayout(self.verticalLayoutBottomButtons)

        nxbrew_dl.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(nxbrew_dl)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1187, 33))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        nxbrew_dl.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(nxbrew_dl)
        self.statusbar.setObjectName(u"statusbar")
        nxbrew_dl.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuHelp.addAction(self.actionDocumentation)
        self.menuHelp.addAction(self.actionIssues)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(nxbrew_dl)

        QMetaObject.connectSlotsByName(nxbrew_dl)
    # setupUi

    def retranslateUi(self, nxbrew_dl):
        nxbrew_dl.setWindowTitle(QCoreApplication.translate("nxbrew_dl", u"NXBrew-dl", None))
        self.actionDocumentation.setText(QCoreApplication.translate("nxbrew_dl", u"Documentation", None))
#if QT_CONFIG(statustip)
        self.actionDocumentation.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"View online documentation", None))
#endif // QT_CONFIG(statustip)
        self.actionIssues.setText(QCoreApplication.translate("nxbrew_dl", u"Issues", None))
#if QT_CONFIG(statustip)
        self.actionIssues.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Open a GitHub issue", None))
#endif // QT_CONFIG(statustip)
        self.actionAbout.setText(QCoreApplication.translate("nxbrew_dl", u"About", None))
#if QT_CONFIG(statustip)
        self.actionAbout.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"See About page", None))
#endif // QT_CONFIG(statustip)
        self.labelNXBrewURL.setText(QCoreApplication.translate("nxbrew_dl", u"NXBrew URL:", None))
#if QT_CONFIG(statustip)
        self.lineEditNXBrewURL.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Input NXBrew URL here. This program will not provide this.", None))
#endif // QT_CONFIG(statustip)
        self.lineEditNXBrewURL.setInputMask("")
        self.lineEditNXBrewURL.setText("")
        self.labelDownloadDir.setText(QCoreApplication.translate("nxbrew_dl", u"Download directory:", None))
#if QT_CONFIG(statustip)
        self.lineEditDownloadDir.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Where to download files to", None))
#endif // QT_CONFIG(statustip)
        self.lineEditDownloadDir.setPlaceholderText(QCoreApplication.translate("nxbrew_dl", u"/path/to/downloads", None))
        self.pushButtonDownloadDir.setText(QCoreApplication.translate("nxbrew_dl", u"Browse", None))
        self.labelJDownloaderDevice.setText(QCoreApplication.translate("nxbrew_dl", u"JDownloader device name:", None))
#if QT_CONFIG(statustip)
        self.lineEditJDownloaderDevice.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Device name for JDownloader", None))
#endif // QT_CONFIG(statustip)
        self.labelJDownloaderUser.setText(QCoreApplication.translate("nxbrew_dl", u"JDownloader username:", None))
#if QT_CONFIG(statustip)
        self.lineEditJDownloaderUser.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"JDownloader username", None))
#endif // QT_CONFIG(statustip)
        self.labelJDownloaderPass.setText(QCoreApplication.translate("nxbrew_dl", u"JDownloader password:", None))
#if QT_CONFIG(statustip)
        self.lineEditJDownloaderPass.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"JDownloader password", None))
#endif // QT_CONFIG(statustip)
        self.lineEditJDownloaderPass.setText("")
        self.labelGameDLOptions.setText(QCoreApplication.translate("nxbrew_dl", u"Base download options:", None))
        self.radioButtonPreferNSP.setText(QCoreApplication.translate("nxbrew_dl", u"Prefer NSPs", None))
        self.radioButtonPreferXCI.setText(QCoreApplication.translate("nxbrew_dl", u"Prefer XCIs", None))
        self.labelGameAdditionalFiles.setText(QCoreApplication.translate("nxbrew_dl", u"Additional files:", None))
#if QT_CONFIG(statustip)
        self.checkBoxDownloadUpdates.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"If available, will download update files", None))
#endif // QT_CONFIG(statustip)
        self.checkBoxDownloadUpdates.setText(QCoreApplication.translate("nxbrew_dl", u"Download Updates", None))
#if QT_CONFIG(statustip)
        self.checkBoxDownloadDLC.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"If available, will download DLCs", None))
#endif // QT_CONFIG(statustip)
        self.checkBoxDownloadDLC.setText(QCoreApplication.translate("nxbrew_dl", u"Download DLCs", None))
        self.labelSearch.setText(QCoreApplication.translate("nxbrew_dl", u"Search:", None))
        self.pushButtonRefresh.setText(QCoreApplication.translate("nxbrew_dl", u"Refresh", None))
        ___qtablewidgetitem = self.tableGames.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("nxbrew_dl", u"Name", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Game Name (double-click to open URL)", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem1 = self.tableGames.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("nxbrew_dl", u"DL?", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem1.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Download Game?", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem2 = self.tableGames.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("nxbrew_dl", u"NSP", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem2.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Game has NSP", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem3 = self.tableGames.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("nxbrew_dl", u"XCI", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem3.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Game has XCI", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem4 = self.tableGames.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("nxbrew_dl", u"Updates", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem4.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Game has Updates", None));
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem5 = self.tableGames.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("nxbrew_dl", u"DLC", None));
#if QT_CONFIG(tooltip)
        ___qtablewidgetitem5.setToolTip(QCoreApplication.translate("nxbrew_dl", u"Game has DLC", None));
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.pushButtonExit.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Exit NXBrew-dl", None))
#endif // QT_CONFIG(statustip)
        self.pushButtonExit.setText(QCoreApplication.translate("nxbrew_dl", u"Exit", None))
#if QT_CONFIG(statustip)
        self.pushButtonRun.setStatusTip(QCoreApplication.translate("nxbrew_dl", u"Run NXBrew-dl", None))
#endif // QT_CONFIG(statustip)
        self.pushButtonRun.setText(QCoreApplication.translate("nxbrew_dl", u"Run", None))
        self.menuHelp.setTitle(QCoreApplication.translate("nxbrew_dl", u"Help", None))
    # retranslateUi

