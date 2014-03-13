# -*- coding: utf-8 -*-
"""
/***************************************************************************
 qpackage
                                 A QGIS plugin
 Creates an export of the project and its data, for easy transfer. Like QConsolidate, but stores all the layers in a single spatialite database and allows custom selection of layers.
                              -------------------
        begin                : 2014-03-12
        copyright            : (C) 2014 by A. Roche
        email                : aroche@photoherbarium.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


class QPackageProject:
    def __init__(self, projectFile):
        self.projectFile = projectFile