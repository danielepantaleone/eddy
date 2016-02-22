# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  #####################                          #####################  #
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


from abc import ABCMeta

from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel, Qt, QSize
from PyQt5.QtGui import QPainter, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QTreeView, QHeaderView, QTabWidget
from PyQt5.QtWidgets import QStyleOption, QStyle

from eddy.core.datatypes import Item
from eddy.core.functions import disconnect, connect


class Hierarchy(QTabWidget):
    """
    This class implements the diagram predicate node explorer.
    """
    def __init__(self, parent):
        """
        Initialize the Explorer.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.iconA = QIcon(':/icons/treeview-icon-attribute')
        self.iconC = QIcon(':/icons/treeview-icon-concept')
        self.iconR = QIcon(':/icons/treeview-icon-role')

        self.viewA = HierarchyView(Item.AttributeNode, self.iconA, self)
        self.viewC = HierarchyView(Item.ConceptNode, self.iconC, self)
        self.viewR = HierarchyView(Item.RoleNode, self.iconR, self)

        self.addTab(self.viewC, self.iconC, '')
        self.addTab(self.viewR, self.iconR, '')
        self.addTab(self.viewA, self.iconA, '')

        self.setCurrentWidget(self.viewC)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIconSize(QSize(18, 18))
        self.setMinimumWidth(216)
        self.setMinimumHeight(160)
        self.setTabsClosable(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    # @pyqtSlot('QModelIndex')
    # def itemCollapsed(self, index):
    #     """
    #     Executed when an item in the tree view is collapsed.
    #     :type index: QModelIndex
    #     """
    #     if self.mainview:
    #         if self.mainview in self.expanded:
    #             item = self.model.itemFromIndex(self.proxy.mapToSource(index))
    #             expanded = self.expanded[self.mainview]
    #             expanded.remove(item.text())
    #
    # @pyqtSlot('QModelIndex')
    # def itemExpanded(self, index):
    #     """
    #     Executed when an item in the tree view is expanded.
    #     :type index: QModelIndex
    #     """
    #     if self.mainview:
    #         item = self.model.itemFromIndex(self.proxy.mapToSource(index))
    #         if self.mainview not in self.expanded:
    #             self.expanded[self.mainview] = set()
    #         expanded = self.expanded[self.mainview]
    #         expanded.add(item.text())

    # @staticmethod
    # def childForNode(parent, node):
    #     """
    #     Search the item representing this node among parent children.
    #     :type parent: QStandardItem
    #     :type node: AbstractNode
    #     """
    #     key = ChildItem.key(node)
    #     for i in range(parent.rowCount()):
    #         child = parent.child(i)
    #         if child.text() == key:
    #             return child
    #     return None

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def browse(self, scene):
        """
        Set the widget to inspect the given scene.
        :type scene: DiagramScene
        """
        self.viewA.browse(scene)
        self.viewC.browse(scene)
        self.viewR.browse(scene)

    def reset(self):
        """
        Clear the widget from inspecting the current scene.
        """
        self.viewA.reset_()
        self.viewC.reset_()
        self.viewR.reset_()


class HierarchyView(QTreeView):
    """
    This class implements the explorer tree view.
    """
    def __init__(self, item, icon, parent=None):
        """
        Initialize the explorer view.
        :type item: Item
        :type icon: QIcon
        :type parent: QWidget
        """
        super().__init__(parent)

        self.scene = None

        self.item = item
        self.icon = icon
        self.root = None

        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)

        model = QStandardItemModel(self)
        proxy = QSortFilterProxyModel(self)
        proxy.setDynamicSortFilter(False)
        proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxy.setSortCaseSensitivity(Qt.CaseSensitive)
        proxy.setSourceModel(model)
        self.setModel(proxy)

    @pyqtSlot('QGraphicsItem')
    def add(self, x):
        """
        Executed when an item is added to the diagram index.
        :type x: AbstractItem
        """
        if x.node:

            ############################################################################################################
            #                                                                                                          #
            #   NODES                                                                                                  #
            #                                                                                                          #
            ############################################################################################################

            if x.item is self.item:

                # If we have no entry => create a new one in the ROOT.
                if not self.hasEntry(Entry.key(x.text())):
                    self.root.appendRow(Entry(self.icon, x.text()))
                    proxy = self.model()
                    proxy.sort(0, Qt.AscendingOrder)

        elif x.edge:

            ############################################################################################################
            #                                                                                                          #
            #   EDGES                                                                                                  #
            #                                                                                                          #
            ############################################################################################################

            if x.item is Item.InclusionEdge and x.source.item is self.item and x.target.item is self.item:

                proxy = self.model()
                model = proxy.sourceModel()

                key1 = Entry.key(x.source.text())
                key2 = Entry.key(x.target.text())

                # 1) Remove the "source" entry from being child of the ROOT item.
                self.root.removeChild(self.root.findChild(key1)) # TODO: MOVE CHILDREN

                # 2) Create a new entry for the "source" node and make it child of the "target" entry.
                for item in model.findItems(key2, Qt.MatchExactly|Qt.MatchRecursive):
                    entry = Entry(self.icon, x.source.text())
                    item.appendRow(entry)
                    proxy.sort(entry.column(), Qt.AscendingOrder)


    @pyqtSlot('QGraphicsItem')
    def remove(self, x):
        """
        Executed when an item is removed from the diagram index.
        :type x: AbstractItem
        """
        if x.node:
            pass

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def hasEntry(self, name):
        """
        Tells whether the given node has an entry representing it in the treeview.
        :type name: str
        :rtype: bool
        """
        proxy = self.model()
        model = proxy.sourceModel()
        return len(model.findItems(name, Qt.MatchExactly|Qt.MatchRecursive)) > 0

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def browse(self, scene):
        """
        Set the widget to inspect the given scene.
        :type scene: DiagramScene
        """
        self.reset_()

        if scene:
            connect(scene.index.sgnItemAdded, self.add)
            connect(scene.index.sgnItemRemoved, self.remove)
            self.scene = scene
            self.setup()

    def reset_(self):
        """
        Clear the widget from inspecting the current scene.
        """
        if self.scene:

            try:
                disconnect(self.scene.index.sgnItemAdded, self.add)
                disconnect(self.scene.index.sgnItemRemoved, self.remove)
            except RuntimeError:
                pass
            finally:
                self.scene = None

        proxy = self.model()
        model = proxy.sourceModel()
        model.clear()

    def setup(self):
        """
        Setup the treeview by creating a new root element.
        """
        self.root = Root(self.icon)
        proxy = self.model()
        model = proxy.sourceModel()
        model.appendRow(self.root)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the tree view.
        :type mouseEvent: QMouseEvent
        """
        self.clearSelection()
        # We call super after clearing the selection so that we click off an
        # item it will be deselected by clearSelection here above and the default
        # mousePressEvent will not emit the clicked signal that will select the item.
        super().mousePressEvent(mouseEvent)


########################################################################################################################
#                                                                                                                      #
#   TREEVIEW ITEMS IMPLEMENTATION                                                                                      #
#                                                                                                                      #
########################################################################################################################


class AbstractEntry(QStandardItem):
    """
    This class implements the base abstract entry of the treeview.
    """
    __metaclass__ = ABCMeta

    def __init__(self, icon, name):
        """
        Initialize the entry.
        :type icon: QIcon
        :type name: str
        """
        super().__init__(name)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        self.setIcon(icon)

    def children(self):
        """
        Returns a list of children for this entry.
        :rtype: list
        """
        return [self.child(i) for i in range(self.rowCount())]

    def findChild(self, name):
        """
        Returns the child of this entry that matches the given name.
        :type name: str
        :rtype: AbstractEntry
        """
        for item in self.children():
            if item.text() == name:
                return item
        return None

    def removeChild(self, item):
        """
        Remove the given child (and all the grand children attached).
        :type item: AbstractEntry
        """
        try:
            self.removeRow(self.children().index(item))
        except ValueError:
            pass


class Root(AbstractEntry):
    """
    This class implements the root element of each treeview section.
    """
    def __init__(self, icon):
        """
        Initialize the root element.
        :type icon: QIcon
        """
        super().__init__(icon, Root.key())

    @classmethod
    def key(cls):
        """
        Returns the key used to index the given node.
        :rtype: str
        """
        return 'TOP'


class Entry(AbstractEntry):
    """
    This class implements the single entry of a treeview section.
    """
    def __init__(self, icon, name):
        """
        Initialize the entry.
        :type icon: QIcon
        :type name: str
        """
        super().__init__(icon, Entry.key(name))

    @classmethod
    def key(cls, name):
        """
        Returns the key used to index the given node.
        :type name: str
        :rtype: str
        """
        return name.replace('\n', '')