# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from eddy.core.datatypes.graphol import Item
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import cutR
from eddy.core.items.factory import ItemFactory
from eddy.core.items.nodes.common.meta import MetaFactory
from eddy.core.items.nodes.common.meta import PredicateMetaData
from eddy.core.syntax.owl import OWL2RLValidator
from eddy.core.utils.guid import GUID


K_DIAGRAM = 'diagrams'
K_EDGE = 'edges'
K_ITEM = 'items'
K_META = 'meta'
K_NODE = 'nodes'
K_PREDICATE = 'predicates'
K_TYPE = 'types'


# noinspection PyTypeChecker
class Project(QObject):
    """
    This class implements a graphol project.
    """
    sgnDiagramAdded = pyqtSignal('QGraphicsScene')
    sgnDiagramRemoved = pyqtSignal('QGraphicsScene')
    sgnItemAdded = pyqtSignal('QGraphicsItem')
    sgnItemRemoved = pyqtSignal('QGraphicsItem')
    sgnMetaAdded = pyqtSignal(Item, str)
    sgnMetaRemoved = pyqtSignal(Item, str)

    def __init__(self, path, prefix, iri, parent=None):
        """
        Initialize the graphol project.
        :type path: str
        :type prefix: str
        :type iri: str
        :type parent: QObject
        """
        super().__init__(parent)

        self.index = {
            K_DIAGRAM: {},
            K_EDGE: {},
            K_ITEM: {},
            K_NODE: {},
            K_PREDICATE: {},
            K_TYPE: {},
        }

        self.path = path
        self.prefix = prefix
        self.iri = iri

        self.guid = GUID(self)
        self.itemFactory = ItemFactory(self)
        self.metaFactory = MetaFactory(self)
        self.validator = OWL2RLValidator(self)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def name(self):
        """
        Returns the name of the project.
        :rtype: str
        """
        return os.path.basename(cutR(self.path, os.path.sep, os.path.altsep))

    #############################################
    #   INTERFACE
    #################################

    def addDiagram(self, diagram):
        """
        Add a diagram to the project index, together with all its items.
        :type diagram: Diagram
        """
        if diagram.id not in self.index[K_DIAGRAM]:
            self.index[K_DIAGRAM][diagram.id] = diagram
            self.sgnDiagramAdded.emit(diagram)
            for item in diagram.items():
                if item.isNode() or item.isEdge():
                    self.doAddItem(diagram, item)

    def addMeta(self, item, name, metadata):
        """
        Create metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        :type metadata: PredicateMetaData
        """
        self.index[K_PREDICATE][item][name][K_META] = metadata
        self.sgnMetaAdded.emit(item, name)

    def count(self, item=None, predicate=None, diagram=None):
        """
        Perform item/predicate count.
        If no diagram is supplied the counting is done on the whole project.
        :type item: Item
        :type predicate: Item
        :type diagram: Diagram
        :rtype: int
        """
        try:

            if item and predicate:
                raise ValueError('either "item" or "predicate" must be None')

            if item:
                sub = self.index[K_TYPE]
                if not diagram:
                    return len(set.union(*(sub[i][item] for i in sub)))
                return len(sub[diagram.id][item])

            if predicate:
                sub = self.index[K_PREDICATE]
                if not diagram:
                    return len(sub[predicate])
                return len({i for i in sub[predicate] if diagram.id in sub[predicate][i][K_NODE]})

            if not diagram:
                return len(set.union(*(set(self.index[K_ITEM][i].values()) for i in self.index[K_ITEM])))
            return len(set(self.index[K_ITEM][diagram.id].values()))

        except KeyError:
            return 0

    def diagram(self, did):
        """
        Returns the diagram matching the given id or None if no diagram is found.
        :type did: str
        :rtype: AbstractItem
        """
        try:
            return self.index[K_DIAGRAM][did]
        except KeyError:
            return None

    def diagrams(self):
        """
        Returns a collection with all the diagrams in this project.
        :rtype: set
        """
        return set(self.index[K_DIAGRAM].values())

    def edge(self, diagram, eid):
        """
        Returns the edge matching the given id or None if no edge is found.
        :type diagram: Diagram
        :type eid: str
        :rtype: AbstractEdge
        """
        try:
            return self.index[K_EDGE][diagram.id][eid]
        except KeyError:
            return None

    def edges(self, diagram=None):
        """
        Returns a collection with all the edges in the given diagram.
        If no diagram is supplied a collection with all the edges in the project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self.index[K_EDGE][i].values()) for i in self.index[K_EDGE]))
            return set(self.index[K_EDGE][diagram.id].values())
        except (KeyError, TypeError):
            return set()

    def item(self, diagram, iid):
        """
        Returns the item matching the given id or None if no item is found.
        :type diagram: Diagram
        :type iid: str
        :rtype: AbstractItem
        """
        try:
            return self.index[K_ITEM][diagram.id][iid]
        except KeyError:
            return None

    def items(self, diagram=None):
        """
        Returns a collection with all the items in the given diagram.
        If no diagram is supplied a collection with all the items in the project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self.index[K_ITEM][i].values()) for i in self.index[K_ITEM]))
            return set(self.index[K_ITEM][diagram.id].values())
        except (KeyError, TypeError):
            return set()

    def meta(self, item, name):
        """
        Returns predicate metadata.
        :type item: Item
        :type name: str
        :rtype: PredicateMetaData
        """
        try:
            return self.index[K_PREDICATE][item][name][K_META]
        except KeyError:
            return self.metaFactory.create(item, name)

    def metas(self):
        """
        Returns a collection of pairs 'item', 'name' for all the predicates with metadata.
        :rtype: list
        """
        return [(k1, k2) for k1 in self.index[K_PREDICATE] \
                            for k2 in self.index[K_PREDICATE][k1] \
                                if K_META in self.index[K_PREDICATE][k1][k2]]

    def node(self, diagram, nid):
        """
        Returns the node matching the given id or None if no node is found.
        :type diagram: Diagram
        :type nid: str
        :rtype: AbstractNode
        """
        try:
            return self.index[K_EDGE][diagram.id][nid]
        except KeyError:
            return None

    def nodes(self, diagram=None):
        """
        Returns a collection with all the nodes in the given diagram.
        If no diagram is supplied a collection with all the nodes in the project will be returned.
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set.union(*(set(self.index[K_NODE][i].values()) for i in self.index[K_NODE]))
            return set(self.index[K_NODE][diagram.id].values())
        except (KeyError, TypeError):
            return set()

    def predicates(self, item, name, diagram=None):
        """
        Returns a collection of predicate nodes belonging to the given diagram and that match
        the given item type and predicate name. If no diagram is supplied the lookup is
        performed across all the diagrams belonging to this project.
        :type item: Item
        :type name: str
        :type diagram: Diagram
        :rtype: set
        """
        try:
            if not diagram:
                return set(self.index[K_PREDICATE][item][name][K_NODE].values())
            return self.index[K_PREDICATE][item][name][K_NODE][diagram.id]
        except KeyError:
            return set()

    def removeDiagram(self, diagram):
        """
        Remove the given diagram from the project index, together with all its items.
        :type diagram: Diagram
        """
        if diagram.id in self.index[K_DIAGRAM]:
            for item in self.items(diagram):
                self.doRemoveItem(diagram, item)
            del self.index[K_DIAGRAM][diagram.id]
            self.sgnDiagramRemoved.emit(diagram)

    def removeMeta(self, item, name):
        """
        Remove metadata for the given predicate type/name combination.
        :type item: Item
        :type name: str
        """
        if item in self.index[K_PREDICATE]:
            if name in self.index[K_PREDICATE][item]:
                if K_META in self.index[K_PREDICATE][item][name]:
                    del self.index[K_PREDICATE][item][name][K_META]
                    self.sgnMetaRemoved.emit(item, name)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddItem(self, diagram, item):
        """
        Executed whenever an item is added to a diagram belonging to this project.
        This slot will add the given element to the project index.
        :type diagram: Diagram
        :type item: AbstractItem
        """
        # ITEM
        i = item.type()
        if diagram.id not in self.index[K_ITEM]:
            self.index[K_ITEM][diagram.id] = dict()
        if item.id not in self.index[K_ITEM][diagram.id]:
            self.index[K_ITEM][diagram.id][item.id] = item
            # TYPE
            if diagram.id not in self.index[K_TYPE]:
                self.index[K_TYPE][diagram.id] = dict()
            if i not in self.index[K_TYPE][diagram.id]:
                self.index[K_TYPE][diagram.id][i] = set()
            self.index[K_TYPE][diagram.id][i] |= {item}
            # NODE
            if item.isNode():
                if diagram.id not in self.index[K_NODE]:
                    self.index[K_NODE][diagram.id] = dict()
                self.index[K_NODE][diagram.id][item.id] = item
                # PREDICATE
                if item.isPredicate():
                    j = item.text()
                    if i not in self.index[K_PREDICATE]:
                        self.index[K_PREDICATE][i] = dict()
                    if j not in self.index[K_PREDICATE][i]:
                        self.index[K_PREDICATE][i][j] = {K_NODE: dict()}
                    if diagram.id not in self.index[K_PREDICATE][i][j][K_NODE]:
                        self.index[K_PREDICATE][i][j][K_NODE][diagram.id] = set()
                    self.index[K_PREDICATE][i][j][K_NODE][diagram.id] |= {item}
            # EDGE
            if item.isEdge():
                if diagram.id not in self.index[K_EDGE]:
                    self.index[K_EDGE][diagram.id] = dict()
                self.index[K_EDGE][diagram.id][item.id] = item
            # SIGNAL
            self.sgnItemAdded.emit(item)

    @pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveItem(self, diagram, item):
        """
        Executed whenever an item is removed from a diagram belonging to this project.
        This slot will remove the given element from the project index.
        :type diagram: Diagram
        :type item: AbstractItem
        """
        # ITEM
        i = item.type()
        if diagram.id in self.index[K_ITEM]:
            if item.id in self.index[K_ITEM][diagram.id]:
                del self.index[K_ITEM][diagram.id][item.id]
                if not self.index[K_ITEM][diagram.id]:
                    del self.index[K_ITEM][diagram.id]
            # TYPE
            if diagram.id in self.index[K_TYPE]:
                if i in self.index[K_TYPE][diagram.id]:
                    self.index[K_TYPE][diagram.id][i] -= {item}
                    if not self.index[K_TYPE][diagram.id][i]:
                        del self.index[K_TYPE][diagram.id][i]
                        if not self.index[K_TYPE][diagram.id]:
                            del self.index[K_TYPE][diagram.id]
            # NODE
            if item.isNode():
                if diagram.id in self.index[K_NODE]:
                    if item.id in self.index[K_NODE][diagram.id]:
                        del self.index[K_NODE][diagram.id][item.id]
                        if not self.index[K_NODE][diagram.id]:
                            del self.index[K_NODE][diagram.id]
                # PREDICATE
                if item.isPredicate():
                    j = item.text()
                    if i in self.index[K_PREDICATE]:
                        if j in self.index[K_PREDICATE][i]:
                            if diagram.id in self.index[K_PREDICATE][i][j][K_NODE]:
                                self.index[K_PREDICATE][i][j][K_NODE][diagram.id] -= {item}
                                if not self.index[K_PREDICATE][i][j][K_NODE][diagram.id]:
                                    del self.index[K_PREDICATE][i][j][K_NODE][diagram.id]
                                    if not self.index[K_PREDICATE][i][j][K_NODE]:
                                        del self.index[K_PREDICATE][i][j]
                                        if not self.index[K_PREDICATE][i]:
                                            del self.index[K_PREDICATE][i]
            # EDGE
            if item.isEdge():
                if diagram.id in self.index[K_EDGE]:
                    if item.id in self.index[K_EDGE][diagram.id]:
                        del self.index[K_EDGE][diagram.id][item.id]
                        if not self.index[K_EDGE][diagram.id]:
                            del self.index[K_EDGE][diagram.id]
            # SIGNAL
            self.sgnItemRemoved.emit(item)