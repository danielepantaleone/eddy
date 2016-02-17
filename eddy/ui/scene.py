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


import sys

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack

from eddy.core.commands import CommandEdgeAdd, CommandNodeAdd, CommandNodeMove
from eddy.core.datatypes import DiagramMode, File, Item
from eddy.core.functions import snapF, snap
from eddy.core.items.edges import InputEdge
from eddy.core.items.nodes import RangeRestrictionNode, DomainRestrictionNode
from eddy.core.items.factory import ItemFactory
from eddy.core.items.index import ItemIndex
from eddy.core.items.nodes.common.meta import PredicateMetaIndex
from eddy.core.syntax import OWL2RLValidator
from eddy.core.utils import Clipboard, GUID


class DiagramScene(QGraphicsScene):
    """
    This class implements the main Diagram Scene.
    """
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000
    RecentNum = 5

    itemAdded = pyqtSignal('QGraphicsItem', int)
    modeChanged = pyqtSignal(DiagramMode)
    updated = pyqtSignal()

    ####################################################################################################################
    #                                                                                                                  #
    #   DIAGRAM SCENE IMPLEMENTATION                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the diagram scene.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
        self.document = File(parent=self)
        self.guid = GUID(self)
        self.factory = ItemFactory(self)
        self.index = ItemIndex(self)
        self.meta = PredicateMetaIndex(self)
        self.undostack = QUndoStack(self)
        self.undostack.setUndoLimit(50)
        self.validator = OWL2RLValidator(self)
        self.mainwindow = mainwindow
        self.pasteOffsetX = Clipboard.PasteOffsetX
        self.pasteOffsetY = Clipboard.PasteOffsetY
        self.mode = DiagramMode.Idle
        self.modeParam = Item.Undefined
        self.mouseOverNode = None
        self.mousePressEdge = None
        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = {}

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def dragEnterEvent(self, dragEvent):
        """
        Executed when a dragged element enters the scene area.
        :type dragEvent: QGraphicsSceneDragDropEvent
        """
        super().dragEnterEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dragMoveEvent(self, dragEvent):
        """
        Executed when an element is dragged over the scene.
        :type dragEvent: QGraphicsSceneDragDropEvent
        """
        super().dragMoveEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dropEvent(self, dropEvent):
        """
        Executed when a dragged element is dropped on the scene.
        :type dropEvent: QGraphicsSceneDragDropEvent
        """
        super().dropEvent(dropEvent)
        if dropEvent.mimeData().hasFormat('text/plain'):
            item = Item.forValue(dropEvent.mimeData().text())
            node = self.factory.create(item=item, scene=self)
            node.setPos(snap(dropEvent.scenePos(), DiagramScene.GridSize, self.mainwindow.snapToGrid))
            self.undostack.push(CommandNodeAdd(scene=self, node=node))
            self.itemAdded.emit(node, dropEvent.modifiers())
            dropEvent.setDropAction(Qt.CopyAction)
            dropEvent.accept()
        else:
            dropEvent.ignore()

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.NodeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         NODE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # create a new node and place it under the mouse position
                item = Item.forValue(self.modeParam)
                node = self.factory.create(item=item, scene=self)
                node.setPos(snap(mouseEvent.scenePos(), DiagramScene.GridSize, self.mainwindow.snapToGrid))

                # no need to switch back the operation mode here: the signal handlers already does that and takes
                # care of the keyboard modifiers being held (if CTRL is being held the operation mode doesn't change)
                self.undostack.push(CommandNodeAdd(scene=self, node=node))
                self.itemAdded.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # see if we are pressing the mouse on a node and if so set the edge add command
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)
                if node:

                    item = Item.forValue(self.modeParam)
                    edge = self.factory.create(item=item, scene=self, source=node)
                    edge.updateEdge(target=mouseEvent.scenePos())
                    self.mousePressEdge = edge
                    self.addItem(edge)

                super().mousePressEvent(mouseEvent)

            else:

                # see if this event needs to be handled in graphics items before we prepare data for a different
                # operational mode: a graphics item may bypass the actions being performed here below by
                # switching the operational mode to something different than DiagramMode.Idle.
                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    # see if we have some nodes selected in the scene: this is needed because itemOnTopOf
                    # will discard labels, so if we have a node whose label is overlapping the node shape,
                    # clicking on the label will make itemOnTopOf return the node item instead of the label.
                    selected = self.selectedNodes()

                    if selected:

                        # we have some nodes selected in the scene so we probably are going to do a
                        # move operation, prepare data for mouse move event => select a node that will act
                        # as mouse grabber to compute delta movements for each componenet in the selection
                        self.mousePressNode = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)

                        if self.mousePressNode:

                            self.mousePressNodePos = self.mousePressNode.pos()
                            self.mousePressPos = mouseEvent.scenePos()

                            # initialize data
                            self.mousePressData = {
                                'nodes': {
                                    node: {
                                        'anchors': {k: v for k, v in node.anchors.items()},
                                        'pos': node.pos(),
                                    } for node in selected},
                                'edges': {}
                            }

                            # figure out if the nodes we are moving are sharing edges: if so, move the edge
                            # together with the nodes (which actually means moving the edge breakpoints)
                            for node in self.mousePressData['nodes']:
                                for edge in node.edges:
                                    if edge not in self.mousePressData['edges']:
                                        if edge.other(node).isSelected():
                                            self.mousePressData['edges'][edge] = edge.breakpoints[:]

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.mousePressEdge:

                    edge = self.mousePressEdge
                    mousePos = mouseEvent.scenePos()
                    currentNode = self.itemOnTopOf(mousePos, edges=False, skip={edge.source})
                    previousNode = self.mouseOverNode
                    statusBar = self.mainwindow.statusBar()

                    edge.updateEdge(target=mousePos)

                    if previousNode:
                        previousNode.updateBrush(selected=False)

                    if currentNode:
                        res = self.validator.result(edge.source, edge, currentNode)
                        currentNode.updateBrush(selected=False, valid=res.valid)
                        statusBar.showMessage(res.message)
                        self.mouseOverNode = currentNode
                    else:
                        statusBar.clearMessage()
                        self.mouseOverNode = None
                        self.validator.clear()

            else:

                # If we are still idle we are probably going to start a node(s) move: if that's
                # the case change the operational mode before actually computing delta movements.
                if self.mode is DiagramMode.Idle:
                    if self.mousePressNode:
                        self.setMode(DiagramMode.NodeMove)

                if self.mode is DiagramMode.NodeMove:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    point = self.mousePressNodePos + mouseEvent.scenePos() - self.mousePressPos
                    point = snap(point, DiagramScene.GridSize, self.mainwindow.snapToGrid)
                    delta = point - self.mousePressNodePos
                    edges = set()

                    # Update all the breakpoints positions.
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # Move all the selected nodes.
                    for node, data in self.mousePressData['nodes'].items():
                        edges |= set(node.edges)
                        node.setPos(data['pos'] + delta)
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)

                    # Update edges.
                    for edge in edges:
                        edge.updateEdge()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.button() == Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.mousePressEdge:

                    edge = self.mousePressEdge
                    edge.source.updateBrush(selected=False)
                    mousePos = mouseEvent.scenePos()
                    mouseModifiers = mouseEvent.modifiers()
                    currentNode = self.itemOnTopOf(mousePos, edges=False, skip={edge.source})
                    insertEdge = False

                    if currentNode:
                        currentNode.updateBrush(selected=False)
                        if self.validator.valid(edge.source, edge, currentNode):
                            edge.target = currentNode
                            insertEdge = True

                    if insertEdge:
                        self.undostack.push(CommandEdgeAdd(scene=self, edge=edge))
                        self.updated.emit()
                    else:
                        edge.source.removeEdge(edge)
                        self.removeItem(edge)

                    self.mouseOverNode = None
                    self.mousePressEdge = None
                    self.clearSelection()
                    self.validator.clear()
                    statusBar = self.mainwindow.statusBar()
                    statusBar.clearMessage()

                    # Always emit this signal even if the edge has not been inserted since this will clear
                    # also the palette switching back the operation mode to DiagramMode.Idle in case the CTRL
                    # keyboard modifier is not being held (in which case the palette button will stay selected).
                    self.itemAdded.emit(edge, mouseModifiers)

            elif self.mode is DiagramMode.NodeMove:

                ########################################################################################################
                #                                                                                                      #
                #                                         ITEM MOVEMENT                                                #
                #                                                                                                      #
                ########################################################################################################

                commandData = {
                    'undo': self.mousePressData,
                    'redo': {
                        'nodes': {
                            node: {
                                'anchors': {k: v for k, v in node.anchors.items()},
                                'pos': node.pos(),
                            } for node in self.mousePressData['nodes']},
                        'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                    }
                }

                self.undostack.push(CommandNodeMove(scene=self, data=commandData))
                self.setMode(DiagramMode.Idle)


        elif mouseEvent.button() == Qt.RightButton:

            if self.mode is not DiagramMode.SceneDrag:

                ########################################################################################################
                #                                                                                                      #
                #                                     CUSTOM CONTEXT MENU                                              #
                #                                                                                                      #
                ########################################################################################################

                item = self.itemOnTopOf(mouseEvent.scenePos())
                if item:
                    self.clearSelection()
                    item.setSelected(True)

                self.mousePressPos = mouseEvent.scenePos()
                menu = self.mainwindow.menuFactory.create(self.mainwindow, self, item, mouseEvent.scenePos())
                menu.exec_(mouseEvent.screenPos())


        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None

    ####################################################################################################################
    #                                                                                                                  #
    #   AXIOMS COMPOSITION                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def propertyAxiomComposition(self, source, restriction):
        """
        Returns a collection of items to be added to the given source node to compose a property axiom.
        :type source: AbstractNode
        :type restriction: class
        :rtype: set
        """
        node = restriction(scene=self)
        edge = InputEdge(scene=self, source=source, target=node)

        size = DiagramScene.GridSize

        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node.width() / 2, node.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node.setPos(pos)

        return {node, edge}

    def propertyDomainAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property domain.
        :type source: AbstractNode
        :rtype: set
        """
        return self.propertyAxiomComposition(source, DomainRestrictionNode)

    def propertyRangeAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property range.
        :type source: AbstractNode
        :rtype: set
        """
        return self.propertyAxiomComposition(source, RangeRestrictionNode)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def clear(self):
        """
        Clear the diagram by removing all the elements.
        """
        self.index.clear()
        self.undostack.clear()
        super().clear()

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addItem(self, item):
        """
        Add an item to the diagram scene.
        :type item: AbstractItem
        """
        super().addItem(item)
        self.index.add(item)

    def edge(self, eid):
        """
        Returns the edge matching the given edge id.
        :type eid: str
        """
        return self.index.edgeForId(eid)

    def edges(self):
        """
        Returns a view on all the edges of the diagram.
        :rtype: view
        """
        return self.index.edges()

    def itemOnTopOf(self, point, nodes=True, edges=True, skip=None):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :type skip: iterable
        :rtype: Item
        """
        skip = skip or {}
        data = [x for x in self.items(point) if (nodes and x.node or edges and x.edge) and x not in skip]
        if data:
            return max(data, key=lambda x: x.zValue())
        return None

    def node(self, nid):
        """
        Returns the node matching the given node id.
        :type nid: str
        """
        return self.index.nodeForId(nid)

    def nodes(self):
        """
        Returns a view on all the nodes in the diagram.
        :rtype: view
        """
        return self.index.nodes()

    def removeItem(self, item):
        """
        Remove an item from the Diagram scene.
        :type item: AbstractItem
        """
        super().removeItem(item)
        self.index.remove(item)

    def selectedEdges(self):
        """
        Returns the edges selected in the scene.
        :rtype: list
        """
        return [x for x in super(DiagramScene, self).selectedItems() if x.edge]

    def selectedItems(self):
        """
        Returns the items selected in the scene (will filter out labels since we don't need them).
        :rtype: list
        """
        return [x for x in super(DiagramScene, self).selectedItems() if x.node or x.edge]

    def selectedNodes(self):
        """
        Returns the nodes selected in the scene.
        :rtype: list
        """
        return [x for x in super(DiagramScene, self).selectedItems() if x.node]

    def setMode(self, mode, param=None):
        """
        Set the operation mode.
        :type mode: DiagramMode
        :type param: int
        """
        if self.mode != mode or self.modeParam != param:
            self.mode = mode
            self.modeParam = param
            self.modeChanged.emit(mode)

    def visibleRect(self, margin=0):
        """
        Returns a rectangle matching the area of visible items.
        :type margin: float
        :rtype: QRectF
        """
        bound = self.itemsBoundingRect()
        topLeft = QPointF(bound.left() - margin, bound.top() - margin)
        bottomRight = QPointF(bound.right() + margin, bound.bottom() + margin)
        return QRectF(topLeft, bottomRight)