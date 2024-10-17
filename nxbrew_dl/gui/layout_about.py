# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout_about.ui'
##
## Created by: Qt User Interface Compiler version 6.7.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(332, 191)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(About.sizePolicy().hasHeightForWidth())
        About.setSizePolicy(sizePolicy)
        About.setMinimumSize(QSize(332, 191))
        About.setMaximumSize(QSize(332, 191))
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout))
        About.setWindowIcon(icon)
        About.setModal(True)
        self.verticalLayout = QVBoxLayout(About)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.aboutLargeTitle = QLabel(About)
        self.aboutLargeTitle.setObjectName(u"aboutLargeTitle")
        font = QFont()
        font.setPointSize(16)
        self.aboutLargeTitle.setFont(font)
        self.aboutLargeTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.aboutLargeTitle)

        self.aboutURL = QLabel(About)
        self.aboutURL.setObjectName(u"aboutURL")
        font1 = QFont()
        font1.setPointSize(12)
        self.aboutURL.setFont(font1)
        self.aboutURL.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.aboutURL.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.aboutURL)


        self.retranslateUi(About)

        QMetaObject.connectSlotsByName(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", u"About", None))
        self.aboutLargeTitle.setText(QCoreApplication.translate("About", u"NXBrew DL", None))
        self.aboutURL.setText(QCoreApplication.translate("About", u"<a href=\"https://github.com/bbtufty/nxbrew-dl\">https://github.com/bbtufty/nxbrew-dl</a>", None))
    # retranslateUi

