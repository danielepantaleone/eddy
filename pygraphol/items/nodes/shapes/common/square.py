# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from pygraphol.items.nodes.shapes.common.base import AbstractNodeShape

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainterPath, QColor


class Square(AbstractNodeShape):
    """
    This class implements a square.
    """
    minW = 20
    minH = 20

    def __init__(self, width=minW, height=minH, brush=(252, 252, 252), **kwargs):
        """
        Initialize the square.
        :param width: the shape width (unused in current implementation).
        :param height: the shape height (unused in current implementation).
        :param brush: the brush to use as shape background
        """
        super().__init__(**kwargs)
        self.shapeBrush = QColor(*brush)
        self.rect = Square.createRect(self.minW, self.minH)

    ##################################################### GEOMETRY #####################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.rect

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.rect)
        return path

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.rect)
        return path

    ################################################ AUXILIARY METHODS #################################################

    @staticmethod
    def createRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect.height()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.rect.width()

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        raise NotImplementedError('method `labelPos` must be implemented in inherited class')

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        raise NotImplementedError('method `labelText` must be implemented in inherited class')

    def setLabelPos(self, pos):
        """
        Set the label position updating the 'moved' flag accordingly.
        :param pos: the node position.
        """
        raise NotImplementedError('method `setLabelPos` must be implemented in inherited class')

    def setLabelText(self, text):
        """
        Set the label text.
        :param text: the text value to set.
        """
        raise NotImplementedError('method `setLabelText` must be implemented in inherited class')

    def updateLabelPos(self):
        """
        Update the label text position.
        """
        raise NotImplementedError('method `updateLabelPos` must be implemented in inherited class')

    ################################################### ITEM DRAWING ###################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeBrushSelected if self.isSelected() else self.shapeBrush

        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawRect(self.rect)