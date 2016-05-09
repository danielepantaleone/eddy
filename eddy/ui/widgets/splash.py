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


from time import time, sleep

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import QSplashScreen, QApplication

from eddy import APPNAME, COPYRIGHT, VERSION

from eddy.core.functions.misc import rangeF
from eddy.core.qt import Font


class Splash(QSplashScreen):
    """
    This class implements Eddy's splash screen.
    It can be used with the context manager, i.e:

    >>> import sys
    >>> from PyQt5.QtWidgets import QApplication
    >>> app = QApplication(sys.argv)
    >>> with Splash(':/images/eddy-splash', mtime=5):
    >>>     app.do_something_heavy()

    will draw a 5 seconds (at least) splash screen on the screen.
    The with statement body can be used to initialize the application and process heavy stuff.
    """
    def __init__(self, path, mtime=2):
        """
        Initialize Eddy's splash screen.
        :type path: str
        :type mtime: float
        """
        super().__init__(QPixmap(path), Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMask(self.pixmap().mask())
        self.setFixedSize(self.pixmap().width(), self.pixmap().height())
        self.mtime = time() + mtime

    #############################################
    #   INTERFACE
    #################################

    def sleep(self):
        """
        Wait for the splash screen to be drawn for at least 'mtime' seconds.
        """
        now = time()
        if now < self.mtime:
            for _ in rangeF(start=0, stop=self.mtime - now, step=0.1):
                # noinspection PyArgumentList
                QApplication.processEvents()
                sleep(0.1)

    #############################################
    #   CONTEXT MANAGER
    #################################

    def __enter__(self):
        """
        Draw the splash screen.
        """
        self.show()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Remove the splash screen from the screen.
        """
        self.sleep()
        self.close()

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        Executed when the splashscreen needs to be painted.
        :type paintEvent: QPaintEvent
        """
        super().paintEvent(paintEvent)
        painter = QPainter(self)
        painter.setFont(Font('Arial', 12, Font.Light))
        ## BOUNDING RECT (0, 194, 400, 86)
        painter.setPen(QPen(QColor(212, 212, 212), 1.0, Qt.SolidLine))
        painter.drawText(QRect(0, 202, 396, 14), Qt.AlignTop|Qt.AlignRight, '{0} v{1}'.format(APPNAME, VERSION))
        painter.drawText(QRect(0, 216, 396, 14), Qt.AlignTop|Qt.AlignRight, COPYRIGHT)
        painter.drawText(QRect(0, 230, 396, 14), Qt.AlignTop|Qt.AlignRight, 'Licensed under the GNU GPL v3')
        painter.drawText(QRect(0, 258, 396, 14), Qt.AlignTop|Qt.AlignRight, 'Starting up...')