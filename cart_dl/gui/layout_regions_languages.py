# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout_regions_languages.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_FormRegionsLanguages(object):
    def setupUi(self, FormRegionsLanguages):
        if not FormRegionsLanguages.objectName():
            FormRegionsLanguages.setObjectName(u"FormRegionsLanguages")
        FormRegionsLanguages.resize(1044, 529)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentProperties))
        FormRegionsLanguages.setWindowIcon(icon)
        self.gridLayout = QGridLayout(FormRegionsLanguages)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayoutConfigRegionsLanguages = QGridLayout()
        self.gridLayoutConfigRegionsLanguages.setObjectName(u"gridLayoutConfigRegionsLanguages")
        self.horizontalLayoutConfigRegionsLanguages = QHBoxLayout()
        self.horizontalLayoutConfigRegionsLanguages.setObjectName(u"horizontalLayoutConfigRegionsLanguages")
        self.verticalLayoutConfigRegionsLanguagesRegions = QVBoxLayout()
        self.verticalLayoutConfigRegionsLanguagesRegions.setObjectName(u"verticalLayoutConfigRegionsLanguagesRegions")
        self.labelConfigRegionsLanguagesRegionsTitle = QLabel(FormRegionsLanguages)
        self.labelConfigRegionsLanguagesRegionsTitle.setObjectName(u"labelConfigRegionsLanguagesRegionsTitle")
        font = QFont()
        font.setBold(True)
        self.labelConfigRegionsLanguagesRegionsTitle.setFont(font)
        self.labelConfigRegionsLanguagesRegionsTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayoutConfigRegionsLanguagesRegions.addWidget(self.labelConfigRegionsLanguagesRegionsTitle)

        self.ConfigRegionsLanguagesRegionsTitleDivider = QFrame(FormRegionsLanguages)
        self.ConfigRegionsLanguagesRegionsTitleDivider.setObjectName(u"ConfigRegionsLanguagesRegionsTitleDivider")
        self.ConfigRegionsLanguagesRegionsTitleDivider.setFrameShadow(QFrame.Shadow.Plain)
        self.ConfigRegionsLanguagesRegionsTitleDivider.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayoutConfigRegionsLanguagesRegions.addWidget(self.ConfigRegionsLanguagesRegionsTitleDivider)

        self.labelConfigRegionsLanguagesRegionsDescription = QLabel(FormRegionsLanguages)
        self.labelConfigRegionsLanguagesRegionsDescription.setObjectName(u"labelConfigRegionsLanguagesRegionsDescription")
        self.labelConfigRegionsLanguagesRegionsDescription.setWordWrap(True)

        self.verticalLayoutConfigRegionsLanguagesRegions.addWidget(self.labelConfigRegionsLanguagesRegionsDescription)

        self.lineConfigRegionsLanguagesRegionsDescriptionDivider = QFrame(FormRegionsLanguages)
        self.lineConfigRegionsLanguagesRegionsDescriptionDivider.setObjectName(u"lineConfigRegionsLanguagesRegionsDescriptionDivider")
        self.lineConfigRegionsLanguagesRegionsDescriptionDivider.setFrameShadow(QFrame.Shadow.Plain)
        self.lineConfigRegionsLanguagesRegionsDescriptionDivider.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayoutConfigRegionsLanguagesRegions.addWidget(self.lineConfigRegionsLanguagesRegionsDescriptionDivider)

        self.listWidgetConfigRegionsLanguagesRegions = QListWidget(FormRegionsLanguages)
        self.listWidgetConfigRegionsLanguagesRegions.setObjectName(u"listWidgetConfigRegionsLanguagesRegions")
        self.listWidgetConfigRegionsLanguagesRegions.setFrameShape(QFrame.Shape.WinPanel)
        self.listWidgetConfigRegionsLanguagesRegions.setFrameShadow(QFrame.Shadow.Plain)
        self.listWidgetConfigRegionsLanguagesRegions.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self.verticalLayoutConfigRegionsLanguagesRegions.addWidget(self.listWidgetConfigRegionsLanguagesRegions)


        self.horizontalLayoutConfigRegionsLanguages.addLayout(self.verticalLayoutConfigRegionsLanguagesRegions)

        self.lineConfigRegionsLanguagesDivider = QFrame(FormRegionsLanguages)
        self.lineConfigRegionsLanguagesDivider.setObjectName(u"lineConfigRegionsLanguagesDivider")
        self.lineConfigRegionsLanguagesDivider.setFrameShadow(QFrame.Shadow.Plain)
        self.lineConfigRegionsLanguagesDivider.setFrameShape(QFrame.Shape.VLine)

        self.horizontalLayoutConfigRegionsLanguages.addWidget(self.lineConfigRegionsLanguagesDivider)

        self.verticalLayoutConfigRegionsLanguagesLanguages = QVBoxLayout()
        self.verticalLayoutConfigRegionsLanguagesLanguages.setObjectName(u"verticalLayoutConfigRegionsLanguagesLanguages")
        self.labelConfigRegionsLanguagesLanguagesTitle = QLabel(FormRegionsLanguages)
        self.labelConfigRegionsLanguagesLanguagesTitle.setObjectName(u"labelConfigRegionsLanguagesLanguagesTitle")
        self.labelConfigRegionsLanguagesLanguagesTitle.setFont(font)
        self.labelConfigRegionsLanguagesLanguagesTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayoutConfigRegionsLanguagesLanguages.addWidget(self.labelConfigRegionsLanguagesLanguagesTitle)

        self.lineConfigRegionsLanguagesLanguagesTitleDivider = QFrame(FormRegionsLanguages)
        self.lineConfigRegionsLanguagesLanguagesTitleDivider.setObjectName(u"lineConfigRegionsLanguagesLanguagesTitleDivider")
        self.lineConfigRegionsLanguagesLanguagesTitleDivider.setFrameShadow(QFrame.Shadow.Plain)
        self.lineConfigRegionsLanguagesLanguagesTitleDivider.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayoutConfigRegionsLanguagesLanguages.addWidget(self.lineConfigRegionsLanguagesLanguagesTitleDivider)

        self.labelConfigRegionsLanguagesLanguagesDescription = QLabel(FormRegionsLanguages)
        self.labelConfigRegionsLanguagesLanguagesDescription.setObjectName(u"labelConfigRegionsLanguagesLanguagesDescription")
        self.labelConfigRegionsLanguagesLanguagesDescription.setWordWrap(True)

        self.verticalLayoutConfigRegionsLanguagesLanguages.addWidget(self.labelConfigRegionsLanguagesLanguagesDescription)

        self.lineConfigRegionsLanguagesLanguagesDescriptionDivider = QFrame(FormRegionsLanguages)
        self.lineConfigRegionsLanguagesLanguagesDescriptionDivider.setObjectName(u"lineConfigRegionsLanguagesLanguagesDescriptionDivider")
        self.lineConfigRegionsLanguagesLanguagesDescriptionDivider.setFrameShadow(QFrame.Shadow.Plain)
        self.lineConfigRegionsLanguagesLanguagesDescriptionDivider.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayoutConfigRegionsLanguagesLanguages.addWidget(self.lineConfigRegionsLanguagesLanguagesDescriptionDivider)

        self.listWidgetConfigRegionsLanguagesLanguages = QListWidget(FormRegionsLanguages)
        self.listWidgetConfigRegionsLanguagesLanguages.setObjectName(u"listWidgetConfigRegionsLanguagesLanguages")
        self.listWidgetConfigRegionsLanguagesLanguages.setFrameShape(QFrame.Shape.WinPanel)
        self.listWidgetConfigRegionsLanguagesLanguages.setFrameShadow(QFrame.Shadow.Plain)
        self.listWidgetConfigRegionsLanguagesLanguages.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self.verticalLayoutConfigRegionsLanguagesLanguages.addWidget(self.listWidgetConfigRegionsLanguagesLanguages)


        self.horizontalLayoutConfigRegionsLanguages.addLayout(self.verticalLayoutConfigRegionsLanguagesLanguages)


        self.gridLayoutConfigRegionsLanguages.addLayout(self.horizontalLayoutConfigRegionsLanguages, 0, 0, 1, 1)


        self.gridLayout.addLayout(self.gridLayoutConfigRegionsLanguages, 0, 0, 1, 1)


        self.retranslateUi(FormRegionsLanguages)

        QMetaObject.connectSlotsByName(FormRegionsLanguages)
    # setupUi

    def retranslateUi(self, FormRegionsLanguages):
        FormRegionsLanguages.setWindowTitle(QCoreApplication.translate("FormRegionsLanguages", u"Region/Language Preferences", None))
        self.labelConfigRegionsLanguagesRegionsTitle.setText(QCoreApplication.translate("FormRegionsLanguages", u"Regions", None))
        self.labelConfigRegionsLanguagesRegionsDescription.setText(QCoreApplication.translate("FormRegionsLanguages", u"Order is important here! Higher in the list means more preferred. Drag boxes to rearrange. Check the box to include that platform, uncheck it to exclude", None))
        self.labelConfigRegionsLanguagesLanguagesTitle.setText(QCoreApplication.translate("FormRegionsLanguages", u"Languages", None))
        self.labelConfigRegionsLanguagesLanguagesDescription.setText(QCoreApplication.translate("FormRegionsLanguages", u"Order is important here! Higher in the list means more preferred. Drag boxes to rearrange. Check the box to include that language, uncheck it to exclude", None))
    # retranslateUi

