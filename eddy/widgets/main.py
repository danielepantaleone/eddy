# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import itertools
import os
import sys
import traceback
import webbrowser

from collections import OrderedDict

from PyQt5.QtCore import Qt, QSettings, QFile, QIODevice, QTextStream, QSizeF, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QPainter, QPageSize
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QMainWindow, QAction, QStatusBar, QMessageBox, QDialog, QStyle
from PyQt5.QtWidgets import QMenu, QToolButton, QUndoGroup
from PyQt5.QtXml import QDomDocument

from eddy import __version__ as version, __appname__ as appname, __organization__ as organization
from eddy.commands import *
from eddy.datatypes import *
from eddy.dialogs import *
from eddy.exceptions import ParseError
from eddy.functions import connect, disconnect, getPath, snapF
from eddy.functions import make_colored_icon, make_shaded_icon
from eddy.items import ItemType, __mapping__ as mapping
from eddy.items import *
from eddy.utils import Clipboard
from eddy.widgets.dock import *
from eddy.widgets.mdi import *
from eddy.widgets.scene import *
from eddy.widgets.view import *
from eddy.widgets.toolbar import *


class MainWindow(QMainWindow):
    """
    This class implements Eddy's main window.
    """
    MaxRecentDocuments = 5
    MinHeight = 600
    MinWidth = 1024

    documentLoaded = pyqtSignal('QGraphicsScene')
    documentSaved = pyqtSignal('QGraphicsScene')

    def __init__(self, parent=None):
        """
        Initialize the application main window.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.abortQuit = False
        self.clipboard = Clipboard()
        self.undogroup = QUndoGroup()
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, organization, appname)

        ################################################################################################################
        #                                                                                                              #
        #   CREATE MENUS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.menuFile = self.menuBar().addMenu("&File")
        self.menuEdit = self.menuBar().addMenu("&Edit")
        self.menuView = self.menuBar().addMenu("&View")
        self.menuHelp = self.menuBar().addMenu("&Help")

        ################################################################################################################
        #                                                                                                              #
        #   CREATE TOOLBARS                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        self.toolbar = self.addToolBar('Toolbar')

        ################################################################################################################
        #                                                                                                              #
        #   CREATE WIDGETS                                                                                             #
        #                                                                                                              #
        ################################################################################################################

        self.mdi = MdiArea()
        self.navigator = Navigator()
        self.overview = Overview()
        self.palette_ = Palette()
        self.zoomctrl = ZoomControl()

        ################################################################################################################
        #                                                                                                              #
        #   CREATE DOCK WIDGETS                                                                                        #
        #                                                                                                              #
        ################################################################################################################

        self.dockNavigator = DockWidget('Navigator', self.navigator, self)
        self.dockOverview = DockWidget('Overview', self.overview, self)
        self.dockPalette = DockWidget('Palette', self.palette_, self)

        ################################################################################################################
        #                                                                                                              #
        #   CREATE ICONS                                                                                               #
        #                                                                                                              #
        ################################################################################################################

        self.iconBringToFront = make_shaded_icon(':/icons/bring-to-front')
        self.iconClose = make_shaded_icon(':/icons/close')
        self.iconColorFill = make_shaded_icon(':/icons/color-fill')
        self.iconCopy = make_shaded_icon(':/icons/copy')
        self.iconCreate = make_shaded_icon(':/icons/create')
        self.iconCut = make_shaded_icon(':/icons/cut')
        self.iconDelete = make_shaded_icon(':/icons/delete')
        self.iconGrid = make_shaded_icon(':/icons/grid')
        self.iconLink = make_shaded_icon(':/icons/link')
        self.iconNew = make_shaded_icon(':/icons/new')
        self.iconOpen = make_shaded_icon(':/icons/open')
        self.iconPaste = make_shaded_icon(':/icons/paste')
        self.iconPalette = make_shaded_icon(':/icons/appearance')
        self.iconPreferences = make_shaded_icon(':/icons/preferences')
        self.iconPrint = make_shaded_icon(':/icons/print')
        self.iconQuit = make_shaded_icon(':/icons/quit')
        self.iconRedo = make_shaded_icon(':/icons/redo')
        self.iconRefresh = make_shaded_icon(':/icons/refresh')
        self.iconSave = make_shaded_icon(':/icons/save')
        self.iconSaveAs = make_shaded_icon(':/icons/save')
        self.iconSelectAll = make_shaded_icon(':/icons/select-all')
        self.iconSendToBack = make_shaded_icon(':/icons/send-to-back')
        self.iconStarFilled = make_shaded_icon(':/icons/star-filled')
        self.iconSwapHorizontal = make_shaded_icon(':/icons/swap-horizontal')
        self.iconSwapVertical = make_shaded_icon(':/icons/swap-vertical')
        self.iconUndo = make_shaded_icon(':/icons/undo')
        self.iconZoom = make_shaded_icon(':/icons/zoom')

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE ACTIONS                                                                                          #
        #                                                                                                              #
        ################################################################################################################
        
        self.actionUndo = self.undogroup.createUndoAction(self)
        self.actionUndo.setIcon(self.iconUndo)
        self.actionUndo.setShortcut(QKeySequence.Undo)

        self.actionRedo = self.undogroup.createRedoAction(self)
        self.actionRedo.setIcon(self.iconRedo)
        self.actionRedo.setShortcut(QKeySequence.Redo)
        
        self.actionNewDocument = QAction('New', self)
        self.actionNewDocument.setIcon(self.iconNew)
        self.actionNewDocument.setShortcut(QKeySequence.New)
        self.actionNewDocument.setStatusTip('Create a new diagram')
        connect(self.actionNewDocument.triggered, self.newDocument)

        self.actionOpenDocument = QAction('Open...', self)
        self.actionOpenDocument.setIcon(self.iconOpen)
        self.actionOpenDocument.setShortcut(QKeySequence.Open)
        self.actionOpenDocument.setStatusTip('Open a diagram')
        connect(self.actionOpenDocument.triggered, self.openDocument)

        self.actionsOpenRecentDocument = []
        for i in range(MainWindow.MaxRecentDocuments):
            action = QAction(self)
            action.setVisible(False)
            connect(action.triggered, self.openRecentDocument)
            self.actionsOpenRecentDocument.append(action)

        self.actionSaveDocument = QAction('Save', self)
        self.actionSaveDocument.setIcon(self.iconSave)
        self.actionSaveDocument.setShortcut(QKeySequence.Save)
        self.actionSaveDocument.setStatusTip('Save the current diagram')
        self.actionSaveDocument.setEnabled(False)
        connect(self.actionSaveDocument.triggered, self.saveDocument)

        self.actionSaveDocumentAs = QAction('Save As...', self)
        self.actionSaveDocumentAs.setIcon(self.iconSaveAs)
        self.actionSaveDocumentAs.setShortcut(QKeySequence.SaveAs)
        self.actionSaveDocumentAs.setStatusTip('Save the active diagram')
        self.actionSaveDocumentAs.setEnabled(False)
        connect(self.actionSaveDocumentAs.triggered, self.saveDocumentAs)

        self.actionImportDocument = QAction('Import...', self)
        self.actionImportDocument.setStatusTip('Import a document')
        connect(self.actionImportDocument.triggered, self.importDocument)

        self.actionExportDocument = QAction('Export...', self)
        self.actionExportDocument.setStatusTip('Export the active diagram')
        self.actionExportDocument.setEnabled(False)
        connect(self.actionExportDocument.triggered, self.exportDocument)

        self.actionPrintDocument = QAction('Print...', self)
        self.actionPrintDocument.setIcon(self.iconPrint)
        self.actionPrintDocument.setStatusTip('Print the active diagram')
        self.actionPrintDocument.setEnabled(False)
        connect(self.actionPrintDocument.triggered, self.printDocument)

        self.actionCloseActiveSubWindow = QAction('Close', self)
        self.actionCloseActiveSubWindow.setIcon(self.iconClose)
        self.actionCloseActiveSubWindow.setShortcut(QKeySequence.Close)
        self.actionCloseActiveSubWindow.setStatusTip('Close the active diagram')
        self.actionCloseActiveSubWindow.setEnabled(False)
        connect(self.actionCloseActiveSubWindow.triggered, self.closeActiveSubWindow)

        self.actionOpenPreferences = QAction('Preferences', self)
        self.actionOpenPreferences.setShortcut(QKeySequence.Preferences)
        self.actionOpenPreferences.setStatusTip('Open {0} preferences'.format(appname))
        connect(self.actionOpenPreferences.triggered, self.openPreferences)

        if not sys.platform.startswith('darwin'):
            self.actionOpenPreferences.setIcon(self.iconPreferences)

        self.actionQuit = QAction('Quit', self)
        self.actionQuit.setStatusTip('Quit {0}'.format(appname))
        self.actionQuit.setShortcut(QKeySequence.Quit)
        connect(self.actionQuit.triggered, self.close)

        if not sys.platform.startswith('darwin'):
            self.actionQuit.setIcon(self.iconQuit)

        self.actionSnapToGrid = QAction('Snap to grid', self)
        self.actionSnapToGrid.setIcon(self.iconGrid)
        self.actionSnapToGrid.setStatusTip('Snap diagram elements to the grid')
        self.actionSnapToGrid.setCheckable(True)
        self.actionSnapToGrid.setChecked(self.settings.value('scene/snap_to_grid', False, bool))
        connect(self.actionSnapToGrid.triggered, self.toggleSnapToGrid)

        self.actionAbout = QAction('About {0}'.format(appname), self)
        self.actionAbout.setShortcut(QKeySequence.HelpContents)
        connect(self.actionAbout.triggered, self.about)

        self.actionSapienzaWeb = QAction('DIAG - Sapienza university', self)
        self.actionSapienzaWeb.setIcon(self.iconLink)
        connect(self.actionSapienzaWeb.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/en'))

        self.actionGrapholWeb = QAction('Graphol homepage', self)
        self.actionGrapholWeb.setIcon(self.iconLink)
        connect(self.actionGrapholWeb.triggered, lambda: webbrowser.open('http://www.dis.uniroma1.it/~graphol/'))

        ## DIAGRAM SCENE
        self.actionOpenSceneProperties = QAction('Properties...', self)
        self.actionOpenSceneProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenSceneProperties.triggered, self.openSceneProperties)

        ## ITEM GENERIC ACTIONS
        self.actionCut = QAction('Cut', self)
        self.actionCut.setIcon(self.iconCut)
        self.actionCut.setShortcut(QKeySequence.Cut)
        self.actionCut.setStatusTip('Cut selected items')
        self.actionCut.setEnabled(False)
        connect(self.actionCut.triggered, self.itemCut)

        self.actionCopy = QAction('Copy', self)
        self.actionCopy.setIcon(self.iconCopy)
        self.actionCopy.setShortcut(QKeySequence.Copy)
        self.actionCopy.setStatusTip('Copy selected items')
        self.actionCopy.setEnabled(False)
        connect(self.actionCopy.triggered, self.itemCopy)

        self.actionPaste = QAction('Paste', self)
        self.actionPaste.setIcon(self.iconPaste)
        self.actionPaste.setShortcut(QKeySequence.Paste)
        self.actionPaste.setStatusTip('Paste items')
        self.actionPaste.setEnabled(False)
        connect(self.actionPaste.triggered, self.itemPaste)

        self.actionDelete = QAction('Delete', self)
        self.actionDelete.setIcon(self.iconDelete)
        self.actionDelete.setShortcut(QKeySequence.Delete)
        self.actionDelete.setStatusTip('Delete selected items')
        self.actionDelete.setEnabled(False)
        connect(self.actionDelete.triggered, self.itemDelete)

        self.actionBringToFront = QAction('Bring to Front', self)
        self.actionBringToFront.setIcon(self.iconBringToFront)
        self.actionBringToFront.setStatusTip('Bring selected items to front')
        self.actionBringToFront.setEnabled(False)
        connect(self.actionBringToFront.triggered, self.bringToFront)

        self.actionSendToBack = QAction('Send to Back', self)
        self.actionSendToBack.setIcon(self.iconSendToBack)
        self.actionSendToBack.setStatusTip('Send selected items to back')
        self.actionSendToBack.setEnabled(False)
        connect(self.actionSendToBack.triggered, self.sendToBack)

        self.actionSelectAll = QAction('Select All', self)
        self.actionSelectAll.setIcon(self.iconSelectAll)
        self.actionSelectAll.setShortcut(QKeySequence.SelectAll)
        self.actionSelectAll.setStatusTip('Select all items in the active diagram')
        self.actionSelectAll.setEnabled(False)
        connect(self.actionSelectAll.triggered, self.selectAll)

        ## NODE GENERIC ACTIONS
        self.actionOpenNodeProperties = QAction('Properties...', self)
        self.actionOpenNodeProperties.setIcon(self.iconPreferences)
        connect(self.actionOpenNodeProperties.triggered, self.openNodeProperties)

        style = self.style()
        size = style.pixelMetric(QStyle.PM_ToolBarIconSize)

        self.actionsChangeNodeBrush = []
        for color in Color:
            action = QAction(color.name, self)
            action.setIcon(make_colored_icon(size, size, color.value))
            action.setCheckable(False)
            action.setData(color)
            connect(action.triggered, self.changeNodeBrush)
            self.actionsChangeNodeBrush.append(action)

        self.actionResetLabelPosition = QAction('Reset label position', self)
        self.actionResetLabelPosition.setIcon(self.iconRefresh)
        connect(self.actionResetLabelPosition.triggered, self.resetLabelPosition)

        self.actionsNodeSetSpecial = []
        for special in SpecialType:
            action = QAction(special.value, self)
            action.setCheckable(True)
            action.setData(special)
            connect(action.triggered, self.setSpecialNode)
            self.actionsNodeSetSpecial.append(action)

        ## ROLE NODE
        self.actionComposeAsymmetricRole = QAction('Asymmetric Role', self)
        self.actionComposeIrreflexiveRole = QAction('Irreflexive Role', self)
        self.actionComposeReflexiveRole = QAction('Reflexive Role', self)
        self.actionComposeSymmetricRole = QAction('Symmetric Role', self)
        self.actionComposeTransitiveRole = QAction('Transitive Role', self)

        connect(self.actionComposeAsymmetricRole.triggered, self.composeAsymmetricRole)
        connect(self.actionComposeIrreflexiveRole.triggered, self.composeIrreflexiveRole)
        connect(self.actionComposeReflexiveRole.triggered, self.composeReflexiveRole)
        connect(self.actionComposeSymmetricRole.triggered, self.composeSymmetricRole)
        connect(self.actionComposeTransitiveRole.triggered, self.composeTransitiveRole)

        ## ROLE / ATTRIBUTE NODES
        self.actionComposeFunctional = QAction('Functional', self)
        self.actionComposeInverseFunctional = QAction('Inverse Functional', self)
        self.actionComposePropertyDomain = QAction('Property Domain', self)
        self.actionComposePropertyRange = QAction('Property Range', self)

        connect(self.actionComposeFunctional.triggered, self.composeFunctional)
        connect(self.actionComposeInverseFunctional.triggered, self.composeInverseFunctional)
        connect(self.actionComposePropertyDomain.triggered, self.composePropertyDomain)
        connect(self.actionComposePropertyRange.triggered, self.composePropertyRange)

        ## DOMAIN / RANGE RESTRICTION
        self.actionsRestrictionChange = []
        for restriction in RestrictionType:
            action = QAction(restriction.value, self)
            action.setCheckable(True)
            action.setData(restriction)
            connect(action.triggered, self.changeDomainRangeRestriction)
            self.actionsRestrictionChange.append(action)

        ## VALUE DOMAIN NODE
        self.actionsChangeValueDomainDatatype = []
        for datatype in XsdDatatype:
            action = QAction(datatype.value, self)
            action.setCheckable(True)
            action.setData(datatype)
            connect(action.triggered, self.changeValueDomainDatatype)
            self.actionsChangeValueDomainDatatype.append(action)

        ## HEXAGON BASED CONSTRUCTOR NODES
        data = OrderedDict()
        data[ComplementNode] = 'Complement'
        data[DisjointUnionNode] = 'Disjoint union'
        data[DatatypeRestrictionNode] = 'Datatype restriction'
        data[EnumerationNode] = 'Enumeration'
        data[IntersectionNode] = 'Intersection'
        data[RoleChainNode] = 'Role chain'
        data[RoleInverseNode] = 'Role inverse'
        data[UnionNode] = 'Union'

        self.actionsSwitchHexagonNode = []
        for k, v in data.items():
            action = QAction(v, self)
            action.setCheckable(True)
            action.setData(k)
            connect(action.triggered, self.switchHexagonNode)
            self.actionsSwitchHexagonNode.append(action)

        ## EDGES
        self.actionRemoveEdgeBreakpoint = QAction('Remove breakpoint', self)
        self.actionRemoveEdgeBreakpoint.setIcon(self.iconDelete)
        connect(self.actionRemoveEdgeBreakpoint.triggered, self.removeBreakpoint)

        self.actionSwapEdge = QAction('Swap', self)
        self.actionSwapEdge.setIcon(self.iconSwapHorizontal)
        self.actionSwapEdge.setShortcut('CTRL+ALT+S' if sys.platform.startswith('win32') else 'ALT+S')
        connect(self.actionSwapEdge.triggered, self.swapEdge)

        self.actionToggleEdgeComplete = QAction('Complete', self)
        self.actionToggleEdgeComplete.setShortcut('CTRL+ALT+C' if sys.platform.startswith('win32') else 'ALT+C')
        self.actionToggleEdgeComplete.setCheckable(True)
        connect(self.actionToggleEdgeComplete.triggered, self.toggleEdgeComplete)

        self.actionToggleEdgeFunctional = QAction('Functional', self)
        self.actionToggleEdgeFunctional.setShortcut('CTRL+ALT+F' if sys.platform.startswith('win32') else 'ALT+F')
        self.actionToggleEdgeFunctional.setCheckable(True)
        connect(self.actionToggleEdgeFunctional.triggered, self.toggleEdgeFunctional)

        self.addAction(self.actionSwapEdge)
        self.addAction(self.actionToggleEdgeComplete)
        self.addAction(self.actionToggleEdgeFunctional)
        
        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE MENUS                                                                                            #
        #                                                                                                              #
        ################################################################################################################

        self.menuFile.addAction(self.actionNewDocument)
        self.menuFile.addAction(self.actionOpenDocument)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSaveDocument)
        self.menuFile.addAction(self.actionSaveDocumentAs)
        self.menuFile.addAction(self.actionCloseActiveSubWindow)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImportDocument)
        self.menuFile.addAction(self.actionExportDocument)

        self.recentDocumentSeparator = self.menuFile.addSeparator()
        for i in range(MainWindow.MaxRecentDocuments):
            self.menuFile.addAction(self.actionsOpenRecentDocument[i])
        self.updateRecentDocuments()

        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionPrintDocument)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)

        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addAction(self.actionDelete)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionBringToFront)
        self.menuEdit.addAction(self.actionSendToBack)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionOpenPreferences)

        self.menuView.addAction(self.actionSnapToGrid)
        self.menuView.addSeparator()
        self.menuView.addAction(self.toolbar.toggleViewAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.dockNavigator.toggleViewAction())
        self.menuView.addAction(self.dockOverview.toggleViewAction())
        self.menuView.addAction(self.dockPalette.toggleViewAction())

        self.menuHelp.addAction(self.actionAbout)

        if not sys.platform.startswith('darwin'):
            self.menuHelp.addSeparator()

        self.menuHelp.addAction(self.actionSapienzaWeb)
        self.menuHelp.addAction(self.actionGrapholWeb)

        ## NODE GENERIC MENU
        self.menuChangeNodeBrush = QMenu('Select color')
        self.menuChangeNodeBrush.setIcon(self.iconColorFill)
        for action in self.actionsChangeNodeBrush:
            self.menuChangeNodeBrush.addAction(action)

        self.menuNodeSpecial = QMenu('Special type')
        self.menuNodeSpecial.setIcon(self.iconStarFilled)
        for action in self.actionsNodeSetSpecial:
            self.menuNodeSpecial.addAction(action)

        ## ROLE NODE
        self.menuRoleNodeCompose = QMenu('Compose')
        self.menuRoleNodeCompose.setIcon(self.iconCreate)
        self.menuRoleNodeCompose.addAction(self.actionComposeAsymmetricRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeIrreflexiveRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeReflexiveRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeSymmetricRole)
        self.menuRoleNodeCompose.addAction(self.actionComposeTransitiveRole)
        self.menuRoleNodeCompose.addSeparator()
        self.menuRoleNodeCompose.addAction(self.actionComposeFunctional)
        self.menuRoleNodeCompose.addAction(self.actionComposeInverseFunctional)
        self.menuRoleNodeCompose.addSeparator()
        self.menuRoleNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuRoleNodeCompose.addAction(self.actionComposePropertyRange)

        ## ATTRIBUTE NODE
        self.menuAttributeNodeCompose = QMenu('Compose')
        self.menuAttributeNodeCompose.setIcon(self.iconCreate)
        self.menuAttributeNodeCompose.addAction(self.actionComposeFunctional)
        self.menuAttributeNodeCompose.addSeparator()
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuAttributeNodeCompose.addSeparator()
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyDomain)
        self.menuAttributeNodeCompose.addAction(self.actionComposePropertyRange)

        ## VALUE DOMAIN NODE
        self.menuChangeValueDomainDatatype = QMenu('Select type')
        self.menuChangeValueDomainDatatype.setIcon(self.iconRefresh)
        for action in self.actionsChangeValueDomainDatatype:
            self.menuChangeValueDomainDatatype.addAction(action)

        ## DOMAIN / RANGE RESTRICTION NODES
        self.menuRestrictionChange = QMenu('Select restriction')
        self.menuRestrictionChange.setIcon(self.iconRefresh)
        for action in self.actionsRestrictionChange:
            self.menuRestrictionChange.addAction(action)

        ## HEXAGON BASED NODES
        self.menuHexagonNodeSwitch = QMenu('Switch to')
        self.menuHexagonNodeSwitch.setIcon(self.iconRefresh)
        for action in self.actionsSwitchHexagonNode:
            self.menuHexagonNodeSwitch.addAction(action)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE STATUS BAR                                                                                       #
        #                                                                                                              #
        ################################################################################################################

        statusbar = QStatusBar(self)
        statusbar.setSizeGripEnabled(False)
        self.setStatusBar(statusbar)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE TOOLBAR                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.actionNewDocument)
        self.toolbar.addAction(self.actionOpenDocument)
        self.toolbar.addAction(self.actionSaveDocument)
        self.toolbar.addAction(self.actionPrintDocument)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionUndo)
        self.toolbar.addAction(self.actionRedo)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionCut)
        self.toolbar.addAction(self.actionCopy)
        self.toolbar.addAction(self.actionPaste)
        self.toolbar.addAction(self.actionDelete)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionBringToFront)
        self.toolbar.addAction(self.actionSendToBack)

        self.changeNodeBrushButton = QToolButton()
        self.changeNodeBrushButton.setIcon(self.iconColorFill)
        self.changeNodeBrushButton.setMenu(self.menuChangeNodeBrush)
        self.changeNodeBrushButton.setPopupMode(QToolButton.InstantPopup)
        self.changeNodeBrushButton.setEnabled(False)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.changeNodeBrushButton)

        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSnapToGrid)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoomctrl)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE SIGNALS                                                                                          #
        #                                                                                                              #
        ################################################################################################################

        connect(self.documentLoaded, self.documentLoadedOrSaved)
        connect(self.documentSaved, self.documentLoadedOrSaved)
        connect(self.mdi.subWindowActivated, self.subWindowActivated)
        connect(self.palette_.buttonClicked[int], self.paletteButtonClicked)
        connect(self.undogroup.cleanChanged, self.undoGroupCleanChanged)

        ################################################################################################################
        #                                                                                                              #
        #   CONFIGURE MAIN WINDOW                                                                                      #
        #                                                                                                              #
        ################################################################################################################

        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockPalette)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockNavigator)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockOverview)
        self.setCentralWidget(self.mdi)
        self.setMinimumSize(MainWindow.MinWidth, MainWindow.MinHeight)
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle()

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def about(self):
        """
        Display the about dialog.
        """
        about = AboutDialog()
        about.exec_()

    @pyqtSlot()
    def bringToFront(self):
        """
        Bring the selected item to the top of the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            for selected in scene.selectedNodes():
                zValue = 0
                colliding = selected.collidingItems()
                for item in filter(lambda x: not x.isType(ItemType.LabelNode, ItemType.LabelEdge), colliding):
                    if item.zValue() >= zValue:
                        zValue = item.zValue() + 0.2
                if zValue != selected.zValue():
                    scene.undostack.push(CommandNodeSetZValue(scene=scene, node=selected, zValue=zValue))

    @pyqtSlot()
    def changeDomainRangeRestriction(self):
        """
        Change domain/range restriction types.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            node = next(filter(lambda x: x.isType(ItemType.DomainRestrictionNode,
                                                  ItemType.RangeRestrictionNode), scene.selectedNodes()), None)
            if node:
                restriction = action.data()
                if restriction == RestrictionType.cardinality:
                    form = CardinalityRestrictionForm()
                    if form.exec_() == CardinalityRestrictionForm.Accepted:
                        cardinality = dict(min=form.minCardinalityValue, max=form.maxCardinalityValue)
                        scene.undostack.push(CommandNodeSquareChangeRestriction(scene, node, restriction, cardinality))
                else:
                    scene.undostack.push(CommandNodeSquareChangeRestriction(scene, node, action.data()))

    @pyqtSlot()
    def changeNodeBrush(self):
        """
        Change the brush of selected nodes.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            selected = scene.selectedNodes()
            selected = [x for x in selected if x.isType(ItemType.AttributeNode, ItemType.ConceptNode,
                                                        ItemType.IndividualNode, ItemType.RoleNode,
                                                        ItemType.ValueDomainNode, ItemType.ValueRestrictionNode)]
            if selected:
                scene.undostack.push(CommandNodeChangeBrush(scene, selected, action.data()))

    @pyqtSlot()
    def changeValueDomainDatatype(self):
        """
        Change the datatype of the selected value-domain node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            node = next(filter(lambda x: x.isType(ItemType.ValueDomainNode), scene.selectedNodes()), None)
            if node:
                scene.undostack.push(CommandNodeValueDomainSelectDatatype(scene, node, action.data()))

    @pyqtSlot()
    def closeActiveSubWindow(self):
        """
        Close the currently active subwindow.
        """
        subwindow = self.mdi.activeSubWindow()
        if subwindow:
            subwindow.close()

    @pyqtSlot()
    def composeAsymmetricRole(self):
        """
        Compose an asymmetric role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isType(ItemType.RoleNode), scene.selectedNodes()), None)
            if node and not node.asymmetric:

                x1 = snapF(node.pos().x() + node.width() / 2 + 100, DiagramScene.GridSize, snap=True)
                y1 = snapF(node.pos().y() - node.height() / 2 - 40, DiagramScene.GridSize, snap=True)
                y2 = snapF(node.pos().y() - node.height() / 2 - 80, DiagramScene.GridSize, snap=True)

                inverse = RoleInverseNode(scene=scene)
                inverse.setPos(QPointF(x1, node.pos().y()))
                complement = ComplementNode(scene=scene)
                complement.setPos(QPointF(x1, y1))
                edge1 = InputEdge(scene=scene, source=node, target=inverse)
                edge2 = InputEdge(scene=scene, source=inverse, target=complement)
                edge3 = InclusionEdge(scene=scene, source=node, target=complement, breakpoints=[
                    QPointF(node.pos().x(), y2),
                    QPointF(x1, y2)
                ])

                kwargs = {
                    'name': 'compose asymmetric role',
                    'scene': scene,
                    'source': node,
                    'nodes': {inverse, complement},
                    'edges': {edge1, edge2, edge3},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeFunctional(self):
        """
        Makes the selected role/attribute node functional.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            args = ItemType.RoleNode, ItemType.AttributeNode
            node = next(filter(lambda x: x.isType(*args), scene.selectedNodes()), None)
            if node:

                size = DiagramScene.GridSize

                node1 = DomainRestrictionNode(scene=scene, restriction=RestrictionType.exists)
                edge1 = InputEdge(scene=scene, source=node, target=node1, functional=True)

                offsets = (
                    QPointF(snapF(+node.width() / 2 + 90, size), 0),
                    QPointF(snapF(-node.width() / 2 - 90, size), 0),
                    QPointF(0, snapF(-node.height() / 2 - 70, size)),
                    QPointF(0, snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(+node.height() / 2 + 70, size)),
                )

                pos = None
                num = sys.maxsize
                rad = QPointF(node1.width() / 2, node1.height() / 2)

                for o in offsets:
                    count = len(scene.items(QRectF(node.pos() + o - rad, node.pos() + o + rad)))
                    if count < num:
                        num = count
                        pos = node.pos() + o

                node1.setPos(pos)

                kwargs = {
                    'name': 'compose functional {0}'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': {node1},
                    'edges': {edge1},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeInverseFunctional(self):
        """
        Makes the selected role node inverse functional.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            args = ItemType.RoleNode, ItemType.AttributeNode
            node = next(filter(lambda x: x.isType(*args), scene.selectedNodes()), None)
            if node:

                size = DiagramScene.GridSize

                node1 = RangeRestrictionNode(scene=scene, restriction=RestrictionType.exists)
                edge1 = InputEdge(scene=scene, source=node, target=node1, functional=True)

                offsets = (
                    QPointF(snapF(+node.width() / 2 + 90, size), 0),
                    QPointF(snapF(-node.width() / 2 - 90, size), 0),
                    QPointF(0, snapF(-node.height() / 2 - 70, size)),
                    QPointF(0, snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(+node.height() / 2 + 70, size)),
                )

                pos = None
                num = sys.maxsize
                rad = QPointF(node1.width() / 2, node1.height() / 2)

                for o in offsets:
                    count = len(scene.items(QRectF(node.pos() + o - rad, node.pos() + o + rad)))
                    if count < num:
                        num = count
                        pos = node.pos() + o

                node1.setPos(pos)

                kwargs = {
                    'name': 'compose inverse functional {0}'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': {node1},
                    'edges': {edge1},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeIrreflexiveRole(self):
        """
        Compose an irreflexive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isType(ItemType.RoleNode), scene.selectedNodes()), None)
            if node and not node.irreflexive:

                x1 = snapF(node.pos().x() + node.width() / 2 + 40, DiagramScene.GridSize, snap=True)
                x2 = snapF(node.pos().x() + node.width() / 2 + 120, DiagramScene.GridSize, snap=True)
                x3 = snapF(node.pos().x() + node.width() / 2 + 250, DiagramScene.GridSize, snap=True)

                restriction = DomainRestrictionNode(scene=scene, restriction=RestrictionType.self)
                restriction.setPos(QPointF(x1, node.pos().y()))
                complement = ComplementNode(scene=scene)
                complement.setPos(QPointF(x2, node.pos().y()))
                concept = ConceptNode(scene=scene, special=SpecialType.TOP)
                concept.setPos(QPointF(x3, node.pos().y()))
                edge1 = InputEdge(scene=scene, source=node, target=restriction)
                edge2 = InputEdge(scene=scene, source=restriction, target=complement)
                edge3 = InclusionEdge(scene=scene, source=concept, target=complement)

                kwargs = {
                    'name': 'compose irreflexive role',
                    'scene': scene,
                    'source': node,
                    'nodes': {restriction, complement, concept},
                    'edges': {edge1, edge2, edge3},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composePropertyDomain(self):
        """
        Compose a property domain using the selected role/attribute node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            args = ItemType.RoleNode, ItemType.AttributeNode
            node = next(filter(lambda x: x.isType(*args), scene.selectedNodes()), None)
            if node:

                size = DiagramScene.GridSize

                node1 = DomainRestrictionNode(scene=scene, restriction=RestrictionType.exists)
                edge1 = InputEdge(scene=scene, source=node, target=node1)

                offsets = (
                    QPointF(snapF(+node.width() / 2 + 90, size), 0),
                    QPointF(snapF(-node.width() / 2 - 90, size), 0),
                    QPointF(0, snapF(-node.height() / 2 - 70, size)),
                    QPointF(0, snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(-node.height() / 2 - 70, size)),
                    QPointF(snapF(+node.width() / 2 + 90, size), snapF(+node.height() / 2 + 70, size)),
                    QPointF(snapF(-node.width() / 2 - 90, size), snapF(+node.height() / 2 + 70, size)),
                )

                pos = None
                num = sys.maxsize
                rad = QPointF(node1.width() / 2, node1.height() / 2)

                for o in offsets:
                    count = len(scene.items(QRectF(node.pos() + o - rad, node.pos() + o + rad)))
                    if count < num:
                        num = count
                        pos = node.pos() + o

                node1.setPos(pos)

                kwargs = {
                    'name': 'compose {0} property domain'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': {node1},
                    'edges': {edge1},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composePropertyRange(self):
        """
        Compose a property range using the selected role/attribute node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            args = ItemType.RoleNode, ItemType.AttributeNode
            node = next(filter(lambda x: x.isType(*args), scene.selectedNodes()), None)
            if node:

                size = DiagramScene.GridSize

                node1 = RangeRestrictionNode(scene=scene, restriction=RestrictionType.exists)
                edge1 = InputEdge(scene=scene, source=node, target=node1)

                if node.isType(ItemType.AttributeNode):
                    node2 = ValueDomainNode(scene=scene)
                    edge2 = InclusionEdge(scene=scene, source=node1, target=node2)
                else:
                    node2 = None
                    edge2 = None

                offsets = (
                    (
                        QPointF(snapF(+node.width() / 2 + 90, size), 0),
                        QPointF(snapF(-node.width() / 2 - 90, size), 0),
                        QPointF(0, snapF(-node.height() / 2 - 70, size)),
                        QPointF(0, snapF(+node.height() / 2 + 70, size)),
                        QPointF(snapF(+node.width() / 2 + 90, size), snapF(-node.height() / 2 - 70, size)),
                        QPointF(snapF(-node.width() / 2 - 90, size), snapF(-node.height() / 2 - 70, size)),
                        QPointF(snapF(+node.width() / 2 + 90, size), snapF(+node.height() / 2 + 70, size)),
                        QPointF(snapF(-node.width() / 2 - 90, size), snapF(+node.height() / 2 + 70, size)),
                    ),
                    (
                        QPointF(snapF(+node1.width() / 2 + 120, size), 0),
                        QPointF(snapF(-node1.width() / 2 - 120, size), 0),
                        QPointF(0, snapF(-node1.height() / 2 - 80, size)),
                        QPointF(0, snapF(+node1.height() / 2 + 80, size)),
                    )
                )

                pos1 = None
                pos2 = None
                num1 = sys.maxsize
                num2 = sys.maxsize
                rad1 = QPointF(node1.width() / 2, node1.height() / 2)
                rad2 = None if node.isType(ItemType.RoleNode) else QPointF(node2.width() / 2, node2.height() / 2)

                if node.isType(ItemType.RoleNode):

                    for o1, o2 in itertools.product(*offsets):
                        count1 = len(scene.items(QRectF(node.pos() + o1 - rad1, node.pos() + o1 + rad1)))
                        if count1 < num1:
                            num1 = count1
                            pos1 = node.pos() + o1

                elif node.isType(ItemType.AttributeNode):

                    for o1, o2 in itertools.product(*offsets):
                        count1 = len(scene.items(QRectF(node.pos() + o1 - rad1, node.pos() + o1 + rad1)))
                        count2 = len(scene.items(QRectF(node.pos() + o1 + o2 - rad2, node.pos() + o1 + o2 + rad2)))
                        if count1 + count2 < num1 + num2:
                            num1 = count1
                            num2 = count2
                            pos1 = node.pos() + o1
                            pos2 = node.pos() + o1 + o2

                node1.setPos(pos1)
                nodes = {node1}
                edges = {edge1}

                if node.isType(ItemType.AttributeNode):
                    node2.setPos(pos2)
                    nodes.add(node2)
                    edges.add(edge2)

                kwargs = {
                    'name': 'compose {0} property range'.format(node.name),
                    'scene': scene,
                    'source': node,
                    'nodes': nodes,
                    'edges': edges,
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeReflexiveRole(self):
        """
        Compose a reflexive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isType(ItemType.RoleNode), scene.selectedNodes()), None)
            if node and not node.reflexive:

                x1 = snapF(node.pos().x() + node.width() / 2 + 40, DiagramScene.GridSize, snap=True)
                x2 = snapF(node.pos().x() + node.width() / 2 + 250, DiagramScene.GridSize, snap=True)

                restriction = DomainRestrictionNode(scene=scene, restriction=RestrictionType.self)
                restriction.setPos(QPointF(x1, node.pos().y()))
                concept = ConceptNode(scene=scene, special=SpecialType.TOP)
                concept.setPos(QPointF(x2, node.pos().y()))
                edge1 = InputEdge(scene=scene, source=node, target=restriction)
                edge2 = InclusionEdge(scene=scene, source=concept, target=restriction)

                kwargs = {
                    'name': 'compose reflexive role',
                    'scene': scene,
                    'source': node,
                    'nodes': {restriction, concept},
                    'edges': {edge1, edge2},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeSymmetricRole(self):
        """
        Compose a symmetric role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isType(ItemType.RoleNode), scene.selectedNodes()), None)
            if node and not node.symmetric:

                x1 = snapF(node.pos().x() + node.width() / 2 + 100, DiagramScene.GridSize, snap=True)
                y1 = snapF(node.pos().y() - node.height() / 2 - 80, DiagramScene.GridSize, snap=True)

                inverse = RoleInverseNode(scene=scene)
                inverse.setPos(QPointF(x1, node.pos().y()))
                edge1 = InputEdge(scene=scene, source=node, target=inverse)
                edge2 = InclusionEdge(scene=scene, source=node, target=inverse, breakpoints=[
                    QPointF(node.pos().x(), y1),
                    QPointF(x1, y1)
                ])

                kwargs = {
                    'name': 'compose symmetric role',
                    'scene': scene,
                    'source': node,
                    'nodes': {inverse},
                    'edges': {edge1, edge2},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot()
    def composeTransitiveRole(self):
        """
        Compose a transitive role using the selected Role node.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: x.isType(ItemType.RoleNode), scene.selectedNodes()), None)
            if node and not node.transitive:

                # always snap the points to the grid, even if the feature is not enabled so we have items aligned
                x1 = snapF(node.pos().x() + node.width() / 2 + 90, DiagramScene.GridSize, snap=True)
                x2 = snapF(node.pos().x() + node.width() / 2 + 50, DiagramScene.GridSize, snap=True)
                x3 = snapF(node.pos().x() - node.width() / 2 - 20, DiagramScene.GridSize, snap=True)
                y1 = snapF(node.pos().y() - node.height() / 2 - 20, DiagramScene.GridSize, snap=True)
                y2 = snapF(node.pos().y() + node.height() / 2 + 20, DiagramScene.GridSize, snap=True)
                y3 = snapF(node.pos().y() - node.height() / 2 + 80, DiagramScene.GridSize, snap=True)

                chain = RoleChainNode(scene=scene)
                chain.setPos(QPointF(x1, node.pos().y()))

                edge1 = InputEdge(scene=scene, source=node, target=chain, breakpoints=[
                    QPointF(node.pos().x(), y1),
                    QPointF(x2, y1),
                ])

                edge2 = InputEdge(scene=scene, source=node, target=chain, breakpoints=[
                    QPointF(node.pos().x(), y2),
                    QPointF(x2, y2),
                ])

                edge3 = InclusionEdge(scene=scene, source=chain, target=node, breakpoints=[
                    QPointF(x1, y3),
                    QPointF(x3, y3),
                    QPointF(x3, node.pos().y()),
                ])

                kwargs = {
                    'name': 'compose transitive role',
                    'scene': scene,
                    'source': node,
                    'nodes': {chain},
                    'edges': {edge1, edge2, edge3},
                }

                scene.undostack.push(CommandComposeAxiom(**kwargs))

    @pyqtSlot('QGraphicsScene')
    def documentLoadedOrSaved(self, scene):
        """
        Executed when a document is loaded or saved from/to a Graphol file.
        :param scene: the diagram scene instance containing the document.
        """
        self.addRecentDocument(scene.document.filepath)
        self.setWindowTitle(scene.document.name)

    @pyqtSlot()
    def exportDocument(self):
        """
        Export the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            res = self.exportFilePath(name=scene.document.name)
            if res:
                filepath = res[0]
                filetype = FileType.forValue(res[1])
                if filetype is FileType.pdf:
                    self.exportSceneToPdfFile(scene, filepath)

    @pyqtSlot()
    def importDocument(self):
        """
        Import a document from a different file format.
        """
        pass

    @pyqtSlot()
    def itemCut(self):
        """
        Cut selected items from the active scene.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            scene.clipboardPasteOffsetX = 0
            scene.clipboardPasteOffsetY = 0

            self.clipboard.update(scene)
            self.refreshActionsState()

            selection = scene.selectedItems()
            if selection:
                selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
                scene.undostack.push(CommandItemsMultiRemove(scene=scene, collection=selection))

    @pyqtSlot()
    def itemCopy(self):
        """
        Make a copy of selected items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            scene.clipboardPasteOffsetX = Clipboard.PasteOffsetX
            scene.clipboardPasteOffsetY = Clipboard.PasteOffsetY
            self.clipboard.update(scene)
            self.refreshActionsState()

    @pyqtSlot()
    def itemPaste(self):
        """
        Paste previously copied items.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            if not self.clipboard.empty():
                # TODO: figure out how to send context menu position to the clipboard
                self.clipboard.paste(scene)

    @pyqtSlot()
    def itemDelete(self):
        """
        Delete the currently selected items from the diagram scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selection = scene.selectedItems()
            if selection:
                selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
                scene.undostack.push(CommandItemsMultiRemove(scene=scene, collection=selection))

    @pyqtSlot('QGraphicsItem', int)
    def itemInserted(self, item, modifiers):
        """
        Executed after an item insertion process ends.
        :param item: the inserted item.
        :param modifiers: keyboard modifiers held during item insertion.
        """
        if not modifiers & Qt.ControlModifier:
            self.palette_.button(item.itemtype).setChecked(False)
            scene = self.mdi.activeScene
            if scene:
                scene.setMode(DiagramMode.Idle)
                scene.command = None

    @pyqtSlot()
    def newDocument(self):
        """
        Create a new empty document and add it to the MDI Area.
        """
        size = self.settings.value('scene/size', 5000, int)
        scene = self.createScene(size, size)
        mainview = self.createView(scene)
        subwindow = self.createSubWindow(mainview)
        subwindow.showMaximized()
        self.mdi.setActiveSubWindow(subwindow)
        self.mdi.update()

    @pyqtSlot()
    def openDocument(self):
        """
        Open a document.
        """
        dialog = OpenFileDialog(getPath('~'))
        dialog.setNameFilters([FileType.graphol.value])
        if dialog.exec_():
            filepath = dialog.selectedFiles()[0]
            if not self.focusDocument(filepath):
                scene = self.createSceneFromGrapholFile(filepath)
                if scene:
                    mainview = self.createView(scene)
                    subwindow = self.createSubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdi.setActiveSubWindow(subwindow)
                    self.mdi.update()

    @pyqtSlot()
    def openNodeProperties(self):
        """
        Executed when node properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            collection = scene.selectedNodes()
            if collection:
                node = collection[0]
                prop = node.propertiesDialog()
                prop.exec_()

    @pyqtSlot()
    def openPreferences(self):
        """
        Open the preferences dialog.
        """
        preferences = PreferencesDialog(self.centralWidget())
        preferences.exec_()
        
    @pyqtSlot()
    def openRecentDocument(self):
        """
        Open the clicked recent document.
        """
        action = self.sender()
        if action:
            if not self.focusDocument(action.data()):
                scene = self.createSceneFromGrapholFile(action.data())
                if scene:
                    mainview = self.createView(scene)
                    subwindow = self.createSubWindow(mainview)
                    subwindow.showMaximized()
                    self.mdi.setActiveSubWindow(subwindow)
                    self.mdi.update()

    @pyqtSlot()
    def openSceneProperties(self):
        """
        Executed when scene properties needs to be displayed.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            prop = ScenePropertiesDialog(scene=scene)
            prop.exec_()

    @pyqtSlot(int)
    def paletteButtonClicked(self, button_id):
        """
        Executed whenever a Palette button is clicked.
        :param button_id: the button id.
        """
        scene = self.mdi.activeScene
        if not scene:
            self.palette_.clear()
        else:
            scene.clearSelection()
            button = self.palette_.button(button_id)
            self.palette_.clear(button)
            if not button.isChecked():
                scene.setMode(DiagramMode.Idle)
            else:
                if ItemType.ConceptNode <= button_id < ItemType.InclusionEdge:
                    scene.setMode(DiagramMode.NodeInsert, button.property('item'))
                elif ItemType.InclusionEdge <= button_id <= ItemType.InstanceOfEdge:
                    scene.setMode(DiagramMode.EdgeInsert, button.property('item'))

    @pyqtSlot()
    def printDocument(self):
        """
        Print the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            shape = scene.visibleRect(margin=20)
            if shape:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.NativeFormat)
                dialog = QPrintDialog(printer)
                if dialog.exec_() == QDialog.Accepted:
                    painter = QPainter()
                    if painter.begin(printer):
                        scene.render(painter, source=shape)

    @pyqtSlot()
    def refreshActionsState(self):
        """
        Update actions enabling/disabling them when needed.
        """
        a = b = c = d = e = f = False

        # we need to check if we have at least one subwindow because if the program
        # simply lose the focus, self.mdi.activeScene will return None even though we
        # do not need to disable actions because we will have scene in the background
        if self.mdi.subWindowList():

            scene = self.mdi.activeScene
            if scene:

                nodes = scene.selectedNodes()
                edges = scene.selectedEdges()

                a = True
                b = not self.undogroup.isClean()
                c = not self.clipboard.empty()
                d = len(edges) != 0
                e = len(nodes) != 0
                f = next(filter(lambda x: x.isType(ItemType.AttributeNode,
                                                   ItemType.ConceptNode,
                                                   ItemType.IndividualNode,
                                                   ItemType.RoleNode,
                                                   ItemType.ValueDomainNode,
                                                   ItemType.ValueRestrictionNode), nodes), None) is not None

        self.actionBringToFront.setEnabled(e)
        self.actionCloseActiveSubWindow.setEnabled(a)
        self.actionCut.setEnabled(e)
        self.actionCopy.setEnabled(e)
        self.actionDelete.setEnabled(e or d)
        self.actionExportDocument.setEnabled(a)
        self.actionPaste.setEnabled(c)
        self.actionPrintDocument.setEnabled(a)
        self.actionSaveDocument.setEnabled(b)
        self.actionSaveDocumentAs.setEnabled(a)
        self.actionSelectAll.setEnabled(a)
        self.actionSendToBack.setEnabled(e)
        self.changeNodeBrushButton.setEnabled(f)

    @pyqtSlot()
    def removeBreakpoint(self):
        """
        Remove the edge breakpoint specified in the action triggering this slot.
        """
        scene = self.mdi.activeScene
        if scene:
            action = self.sender()
            edge, breakpoint = action.data()
            if 0 <= breakpoint < len(edge.breakpoints):
                scene.undostack.push(CommandEdgeBreakpointDel(scene=scene, edge=edge, index=breakpoint))

    @pyqtSlot()
    def resetLabelPosition(self):
        """
        Reset selected node label to default position.
        """
        scene = self.mdi.activeScene
        if scene:

            scene.setMode(DiagramMode.Idle)
            node = next(filter(lambda x: hasattr(x, 'label'), scene.selectedNodes()), None)
            if node and node.label.movable:
                command = CommandNodeLabelMove(scene=scene, node=node, label=node.label)
                command.end(pos=node.label.defaultPos())
                scene.undostack.push(command)
                node.label.updatePos()

    @pyqtSlot()
    def saveDocument(self):
        """
        Save the currently open graphol document.
        """
        scene = self.mdi.activeScene
        if scene:
            filepath = scene.document.filepath or self.saveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
                if saved:
                    scene.document.filepath = filepath
                    scene.document.edited = os.path.getmtime(filepath)
                    scene.undostack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot()
    def saveDocumentAs(self):
        """
        Save the currently open graphol document (enforcing a new name).
        """
        scene = self.mdi.activeScene
        if scene:
            filepath = self.saveFilePath(name=scene.document.name)
            if filepath:
                saved = self.saveSceneToGrapholFile(scene, filepath)
                if saved:
                    scene.document.filepath = filepath
                    scene.document.edited = os.path.getmtime(filepath)
                    scene.undostack.setClean()
                    self.documentSaved.emit(scene)

    @pyqtSlot(DiagramMode)
    def sceneModeChanged(self, mode):
        """
        Executed when the scene operation mode changes.
        :param mode: the scene operation mode.
        """
        if mode not in (DiagramMode.NodeInsert, DiagramMode.EdgeInsert):
            self.palette_.clear()

    @pyqtSlot()
    def selectAll(self):
        """
        Select all the items in the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.clearSelection()
            scene.setMode(DiagramMode.Idle)
            for collection in (scene.nodes(), scene.edges()):
                for item in collection:
                    item.setSelected(True)

    @pyqtSlot()
    def sendToBack(self):
        """
        Send the selected item to the back of the scene.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            for selected in scene.selectedNodes():
                zValue = 0
                colliding = selected.collidingItems()
                for item in filter(lambda x: not x.isType(ItemType.LabelNode, ItemType.LabelEdge), colliding):
                    if item.zValue() <= zValue:
                        zValue = item.zValue() - 0.2
                if zValue != selected.zValue():
                    scene.undostack.push(CommandNodeSetZValue(scene=scene, node=selected, zValue=zValue))

    @pyqtSlot()
    def setSpecialNode(self):
        """
        Set the special type of the selected concept node.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            args = ItemType.ConceptNode, ItemType.RoleNode, ItemType.AttributeNode, ItemType.ValueDomainNode
            node = next(filter(lambda x: x.isType(*args), scene.selectedNodes()), None)
            if node:
                special = action.data() if node.special is not action.data() else None
                scene.undostack.push(CommandNodeSetSpecial(scene, node, special))

    @pyqtSlot('QMdiSubWindow')
    def subWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :param subwindow: the subwindow which got the focus (0 if there is no subwindow).
        """
        if subwindow:

            mainview = subwindow.widget()
            scene = mainview.scene()
            scene.undostack.setActive()

            self.navigator.setView(mainview)
            self.overview.setView(mainview)

            disconnect(self.zoomctrl.scaleChanged)
            disconnect(mainview.zoomChanged)

            self.zoomctrl.setEnabled(False)
            self.zoomctrl.setZoomLevel(self.zoomctrl.index(mainview.zoom))
            self.zoomctrl.setEnabled(True)

            connect(self.zoomctrl.scaleChanged, mainview.onScaleChanged)
            connect(mainview.zoomChanged, self.zoomctrl.onMainViewZoomChanged)

            self.setWindowTitle(scene.document.name)

        else:

            if not self.mdi.subWindowList():

                self.zoomctrl.reset()
                self.zoomctrl.setEnabled(False)
                self.navigator.clearView()
                self.overview.clearView()
                self.setWindowTitle()

        # refresh all actions state: this will already take care of the situation where
        # the main window just went out of focus, and so actions will stay enabled.
        self.refreshActionsState()

    @pyqtSlot('QMdiSubWindow')
    def subWindowCloseEventIgnored(self, subwindow):
        """
        Executed when the close event of an MDI subwindow is aborted.
        :param subwindow: the subwindow whose closeEvent has been interrupted.
        """
        self.abortQuit = True
        self.mdi.setActiveSubWindow(subwindow)

    @pyqtSlot()
    def swapEdge(self):
        """
        Swap the selected edges by inverting source/target points.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = scene.selectedEdges()
            if selected:
                scene.undostack.push(CommandEdgeSwap(scene=scene, edges=selected))

    @pyqtSlot()
    def switchHexagonNode(self):
        """
        Switch the selected hexagon based constructor node to a different type.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            action = self.sender()
            selected = scene.selectedNodes()
            node = next(filter(lambda x: ItemType.UnionNode <= x.itemtype <= ItemType.DisjointUnionNode, selected), None)
            if node:
                clazz = action.data()
                if not isinstance(node, clazz):
                    xnode = clazz(scene=scene)
                    xnode.setPos(node.pos())
                    scene.undostack.push(CommandNodeHexagonSwitchTo(scene=scene, node1=node, node2=xnode))

    @pyqtSlot()
    def toggleEdgeComplete(self):
        """
        Toggle the 'complete' attribute for all the selected Inclusion edges.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [item for item in scene.selectedEdges() if item.isType(ItemType.InclusionEdge)]
            if selected:
                func = sum(edge.complete for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.complete, 'to': func} for edge in selected}
                scene.undostack.push(CommandEdgeInclusionToggleComplete(scene=scene, data=data))

    @pyqtSlot()
    def toggleEdgeFunctional(self):
        """
        Toggle the 'functional' attribute for all the selected Input edges.
        """
        scene = self.mdi.activeScene
        if scene:
            scene.setMode(DiagramMode.Idle)
            selected = [item for item in scene.selectedEdges() if item.isType(ItemType.InputEdge)]
            if selected:
                func = sum(edge.functional for edge in selected) <= len(selected) / 2
                data = {edge: {'from': edge.functional, 'to': func} for edge in selected}
                scene.undostack.push(CommandEdgeInputToggleFunctional(scene=scene, data=data))

    @pyqtSlot()
    def toggleSnapToGrid(self):
        """
        Toggle snap to grid setting.
        """
        self.settings.setValue('scene/snap_to_grid', self.actionSnapToGrid.isChecked())
        scene = self.mdi.activeScene
        if scene:
            scene.update()

    @pyqtSlot(bool)
    def undoGroupCleanChanged(self, clean):
        """
        Executed when the clean state of the active undostack changes.
        :param clean: the clean state.
        """
        self.actionSaveDocument.setEnabled(not clean)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def closeEvent(self, closeEvent):
        """
        Executed when the main window is closed.
        :param closeEvent: the close event instance.
        """
        self.abortQuit = False
        for subwindow in self.mdi.subWindowList():
            mainview = subwindow.widget()
            scene = mainview.scene()
            if (scene.items() and not scene.document.filepath) or (not scene.undostack.isClean()):
                self.mdi.setActiveSubWindow(subwindow)
                subwindow.showMaximized()
            subwindow.close()
            if self.abortQuit:
                closeEvent.ignore()
                break

    def keyReleaseEvent(self, keyEvent):
        """
        Executed when a keyboard button is released from the scene.
        :param keyEvent: the keyboard event instance.
        """
        if keyEvent.key() == Qt.Key_Control:
            mainview = self.mdi.activeView
            if mainview:
                scene = mainview.scene()
                scene.setMode(DiagramMode.Idle)
        super().keyReleaseEvent(keyEvent)

    def showEvent(self, showEvent):
        """
        Executed when the window is shown.
        :param showEvent: the show event instance.
        """
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addRecentDocument(self, path):
        """
        Add the given document to the recent document list
        :param path: the path of the recent document.
        :return:
        """
        documents = self.settings.value('document/recent_documents', None, str)

        try:
            documents.remove(path)
        except ValueError:
            pass
        finally:
            documents.insert(0, path) # insert on top of the list
            documents = documents[:MainWindow.MaxRecentDocuments]

        self.settings.setValue('document/recent_documents', documents)
        self.updateRecentDocuments()

    def createScene(self, width, height):
        """
        Create and return an empty scene.
        :param width: the width of the scene rect.
        :param height: the height of the scene rect
        :return: the initialized diagram scene.
        :rtype: DiagramScene
        """
        scene = DiagramScene(self)
        scene.setSceneRect(QRectF(-width / 2, -height / 2, width, height))
        scene.setItemIndexMethod(DiagramScene.NoIndex)
        connect(scene.nodeInserted, self.itemInserted)
        connect(scene.edgeInserted, self.itemInserted)
        connect(scene.modeChanged, self.sceneModeChanged)
        connect(scene.selectionChanged, self.refreshActionsState)
        self.undogroup.addStack(scene.undostack)
        return scene

    def createSceneFromGrapholFile(self, filepath):
        """
        Create a new scene by loading the given Graphol file.
        :param filepath: the path of the file to be loaded.
        :rtype: DiagramScene
        """
        file = QFile(filepath)

        try:

            if not file.open(QIODevice.ReadOnly):
                raise IOError('file not found: {0}'.format(filepath))

            document = QDomDocument()
            if not document.setContent(file):
                raise ParseError('could not initialized DOM document')

            root = document.documentElement()

            # read graph initialization data
            graph = root.firstChildElement('graph')
            w = int(graph.attribute('width', self.settings.value('scene/size', '5000', str)))
            h = int(graph.attribute('height', self.settings.value('scene/size', '5000', str)))

            # create the scene
            scene = self.createScene(width=w, height=h)
            scene.document.filepath = filepath
            scene.document.edited = os.path.getmtime(filepath)

            # add the nodes
            nodes_from_graphol = graph.elementsByTagName('node')
            for i in range(nodes_from_graphol.count()):
                E = nodes_from_graphol.at(i).toElement()
                C = mapping[E.attribute('type')]
                node = C.fromGraphol(scene=scene, E=E)
                scene.addItem(node)
                scene.uniqueID.update(node.id)

            # add the edges
            edges_from_graphol = graph.elementsByTagName('edge')
            for i in range(edges_from_graphol.count()):
                E = edges_from_graphol.at(i).toElement()
                C = mapping[E.attribute('type')]
                edge = C.fromGraphol(scene=scene, E=E)
                scene.addItem(edge)
                scene.uniqueID.update(edge.id)

        except Exception as e:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/eddy'))
            box.setWindowTitle('Load FAILED')
            box.setText('Could not open Graphol document: {0}!'.format(filepath))
            # format the traceback so it prints nice
            most_recent_calls = traceback.format_tb(sys.exc_info()[2])
            most_recent_calls = [x.strip().replace('\n', '') for x in most_recent_calls]
            # set the traceback as detailed text so it won't occupy too much space in the dialog box
            box.setDetailedText('{0}: {1}\n\n{2}'.format(e.__class__.__name__, str(e), '\n'.join(most_recent_calls)))
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return None
        else:
            self.documentLoaded.emit(scene)
            return scene
        finally:
            file.close()

    def createSubWindow(self, mainview):
        """
        Create a MdiSubWindow displaying the given main view.
        :param mainview: the mainview to be rendered in the subwindow.
        :rtype: MdiSubWindow
        """
        subwindow = self.mdi.addSubWindow(MdiSubWindow(mainview))
        subwindow.updateTitle()
        scene = mainview.scene()
        connect(self.documentSaved, subwindow.documentSaved)
        connect(scene.undostack.cleanChanged, subwindow.undoStackCleanChanged)
        connect(subwindow.closeEventIgnored, self.subWindowCloseEventIgnored)
        return subwindow

    @staticmethod
    def createView(scene):
        """
        Create a new main view displaying the given scene.
        :param scene: the scene to be added in the view.
        :rtype: MainView
        """
        view = MainView(scene)
        view.setViewportUpdateMode(MainView.FullViewportUpdate)
        view.centerOn(0, 0)
        view.setDragMode(MainView.NoDrag)
        return view

    @staticmethod
    def exportFilePath(path=None, name=None):
        """
        Bring up the 'Export' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :return: a tuple with the filepath and the selected file filter.
        :rtype: tuple
        """
        dialog = SaveFileDialog(path)
        dialog.setWindowTitle('Export')
        dialog.setNameFilters([x.value for x in FileType if x is not FileType.graphol])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0], dialog.selectedNameFilter()
        return None

    @staticmethod
    def exportSceneToPdfFile(scene, filepath):
        """
        Export the given scene as PDF saving it in the given filepath.
        :param scene: the scene to be exported.
        :param filepath: the filepath where to export the scene.
        :return: True if the export has been performed, False otherwise.
        """
        shape = scene.visibleRect(margin=20)
        if shape:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filepath)
            printer.setPaperSize(QPrinter.Custom)
            printer.setPageSize(QPageSize(QSizeF(shape.width(), shape.height()), QPageSize.Point))

            painter = QPainter()
            if painter.begin(printer):
                scene.render(painter, source=shape)
                painter.end()
                return True

        return False

    def focusDocument(self, document):
        """
        Move the focus on the subwindow containing the given document.
        :param document: the document filepath.
        :return: True if the subwindow has been focused, False otherwise.
        :rtype: bool
        """
        if isinstance(document, DiagramScene):
            document = document.document.filepath
        elif isinstance(document, Document):
            document = document.filepath

        for subwindow in self.mdi.subWindowList():
            scene = subwindow.widget().scene()
            if scene.document.filepath and scene.document.filepath == document:
                self.mdi.setActiveSubWindow(subwindow)
                self.mdi.update()
                return True

        return False

    @staticmethod
    def saveFilePath(path=None, name=None):
        """
        Bring up the 'Save' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :rtype: str
        """
        dialog = SaveFileDialog(path)
        dialog.setNameFilters([FileType.graphol.value])
        dialog.selectFile(name or 'Untitled')
        if dialog.exec_():
            return dialog.selectedFiles()[0]
        return None

    @staticmethod
    def saveSceneToGrapholFile(scene, filepath):
        """
        Save the given scene to the corresponding given filepath.
        :param scene: the scene to be saved.
        :param filepath: the filepath where to save the scene.
        :return: True if the save has been performed, False otherwise.
        """
        # save the file in a hidden file inside the eddy home: if the save successfully
        # complete, move the file on the given filepath (in this way if an exception is raised
        # while exporting the scene, we won't lose previously saved data)
        tmpPath = getPath('@home/.{0}'.format(os.path.basename(os.path.normpath(filepath))))
        tmpFile = QFile(tmpPath)

        try:
            if not tmpFile.open(QIODevice.WriteOnly|QIODevice.Truncate|QIODevice.Text):
                raise IOError('could not create temporary file {0}'.format(tmpPath))
            stream = QTextStream(tmpFile)
            document = scene.toGraphol()
            document.save(stream, 2)
            tmpFile.close()
            if os.path.isfile(filepath):
                os.remove(filepath)
            os.rename(tmpPath, filepath)
        except Exception:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowIcon(QIcon(':/images/eddy'))
            box.setWindowTitle('Save FAILED')
            box.setText('Could not export diagram!')
            box.setDetailedText(traceback.format_exc())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return False
        else:
            return True
        finally:
            if tmpFile.isOpen():
                tmpFile.close()

    def setWindowTitle(self, p_str=None):
        """
        Set the main window title.
        :param p_str: the prefix for the window title
        """
        T = '{0} - {1} {2}'.format(p_str, appname, version) if p_str else '{0} {1}'.format(appname, version)
        super().setWindowTitle(T)

    def updateRecentDocuments(self):
        """
        Update the recent document action list.
        """
        documents = self.settings.value('document/recent_documents', None, str)
        numRecentDocuments = min(len(documents), MainWindow.MaxRecentDocuments)

        for i in range(numRecentDocuments):
            filename = '&{0} {1}'.format(i + 1, os.path.basename(os.path.normpath(documents[i])))
            self.actionsOpenRecentDocument[i].setText(filename)
            self.actionsOpenRecentDocument[i].setData(documents[i])
            self.actionsOpenRecentDocument[i].setVisible(True)

        # turn off actions that we don't need
        for i in range(numRecentDocuments, MainWindow.MaxRecentDocuments):
            self.actionsOpenRecentDocument[i].setVisible(False)

        # show the separator only if we got at least one recent document
        self.recentDocumentSeparator.setVisible(numRecentDocuments > 0)