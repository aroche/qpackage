# -*- coding: utf-8 -*-

#******************************************************************************
#
# QConsolidate
# ---------------------------------------------------------
# Consolidates all layers from current QGIS project into one directory and
# creates copy of current project using this consolidated layers.
#
# Copyright (C) 2012-2013 Alexander Bruy (alexander.bruy@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
#******************************************************************************


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

from qgis.core import *
from qgis.gui import *

from osgeo import gdal

import glob

ogrDatabase = ["PGeo",
               "SDE",
               "IDB",
               "INGRES",
               "MySQL",
               "MSSQLSpatial",
               "OCI",
               "ODBC",
               "OGDI",
               "PostgreSQL",
               "SQLite"   # file or db?
              ]

ogrDirectory = ["AVCBin",
                "GRASS",
                "UK. NTF",
                "TIGER"
               ]

ogrProtocol = ["DODS",
               "GeoJSON"   # file or protocol?
              ]

vectorProviders = ["gpx",
                   "osm",
                   "grass",
                   "memory",
                   "postgres",
                   "spatialite",
                   "sqlanywhere",
                   "delimitedtext"
                  ]


class ConsolidateThread(QThread):
    processError = pyqtSignal(str)
    rangeChanged = pyqtSignal(int)
    updateProgress = pyqtSignal()
    processFinished = pyqtSignal()
    processInterrupted = pyqtSignal()

    def __init__(self, iface, outputDir, projectFile):
        QThread.__init__(self, QThread.currentThread())
        self.mutex = QMutex()
        self.stopMe = 0

        self.iface = iface
        self.outputDir = outputDir
        self.layersDir = outputDir + "/layers"
        self.projectFile = projectFile

    def run(self):
        self.mutex.lock()
        self.stopMe = 0
        self.mutex.unlock()

        interrupted = False

        gdal.AllRegister()

        # read project
        doc = self.loadProject()
        root = doc.documentElement()

        # ensure that relative path used
        e = root.firstChildElement("properties")
        e.firstChildElement("Paths").firstChild().firstChild().setNodeValue("false")

        # get layers section in project
        e = root.firstChildElement("projectlayers")

        # process layers
        layers = self.iface.legendInterface().layers()
        self.rangeChanged.emit(len(layers))

        ogrSupported = ogrDatabase + ogrDirectory

        for layer in layers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                layerName = layer.name()
                layerSource = layer.source()
                pt = layer.providerType()
                if pt == "ogr":
                    storage = str(layer.storageType())
                    if storage in ogrSupported:
                        self.copyGenericVectorLayer(e, layer, layerName)
                    elif storage in ogrProtocol:
                        print "Storage type '%s' currently not supported" % storage
                    else:
                        self.copyFileLayer(e, layerSource, layerName)
                elif pt in vectorProviders:
                    self.copyGenericVectorLayer(e, layer, layerName)
                else:
                    print "Vector provider '%s' currently not supported" % pt
            elif layerType == QgsMapLayer.RasterLayer:
                pt = layer.providerType()
                if pt == "gdal":
                    self.copyRasterLayer(e, layer.source(), layer.name())
                else:
                    print "Raster provider '%s' currently not supported" % pt
            else:
                print "Layers with type '%s' currently not supported" % layerType

            self.updateProgress.emit()
            self.mutex.lock()
            s = self.stopMe
            self.mutex.unlock()
            if s == 1:
                interrupted = True
                break

        # save updated project
        self.saveProject(doc)

        if not interrupted:
            self.processFinished.emit()
        else:
            self.processInterrupted.emit()

    def stop(self):
        self.mutex.lock()
        self.stopMe = 1
        self.mutex.unlock()

        QThread.wait(self)

    def loadProject(self):
        f = QFile(self.projectFile)
        if not f.open(QIODevice.ReadOnly | QIODevice.Text):
            msg = self.tr("Cannot read file %s:\n%s.") % (self.projectFile, f.errorString())
            self.processError.emit(msg)
            return

        doc = QDomDocument()
        setOk, errorString, errorLine, errorColumn = doc.setContent(f, True)
        if not setOk:
            msg = self.tr("Parse error at line %d, column %d:\n%s") % (errorLine, errorColumn, errorString)
            self.processError.emit(msg)
            return

        f.close()
        return doc

    def saveProject(self, doc):
        f = QFile(self.projectFile)
        if not f.open(QIODevice.WriteOnly | QIODevice.Text):
            msg = self.tr("Cannot write file %s:\n%s.") % (self.projectFile, f.errorString())
            self.processError.emit(msg)
            return

        out = QTextStream(f)
        doc.save(out, 4)
        f.close()

    def copyFileLayer(self, layerElement, layerSource, layerName):
        # copy all files
        fi = QFileInfo(layerSource)
        mask = fi.path() + "/" + fi.baseName() + ".*"
        files = glob.glob(unicode(mask))
        fl = QFile()
        for f in files:
            fi.setFile(f)
            fl.setFileName(f)
            fl.copy(self.layersDir + "/" + fi.fileName())

        # update project
        layerNode = self.findLayerInProject(layerElement, layerName)
        sourceNode = layerNode.firstChildElement("datasource")
        p = "./layers/" + QFileInfo(sourceNode.text()).fileName()
        sourceNode.firstChild().setNodeValue(p)

    def copyGenericVectorLayer(self, layerElement, vLayer, layerName):
        crs = vLayer.crs()
        enc = vLayer.dataProvider().encoding()
        outFile = "%s/%s.shp" % (self.layersDir, layerName)
        error = QgsVectorFileWriter.writeAsVectorFormat(vLayer, outFile, enc, crs)
        if error != QgsVectorFileWriter.NoError:
            msg = self.tr("Cannot copy layer %s") % layerName
            self.processError.emit(msg)
            return

        # update project
        layerNode = self.findLayerInProject(layerElement, layerName)
        tmpNode = layerNode.firstChildElement("datasource")
        p = "./layers/%s.shp" % layerName
        tmpNode.firstChild().setNodeValue(p)
        tmpNode = layerNode.firstChildElement("provider")
        tmpNode.setAttribute("encoding", enc)
        tmpNode.firstChild().setNodeValue("ogr")

    def copyRasterLayer(self, layerElement, layerPath, layerName):
        outputFormat = "GTiff"
        creationOptions = ["COMPRESS=PACKBITS", "TILED=YES", "TFW=YES", "BIGTIFF=IF_NEEDED"]

        driver = gdal.GetDriverByName(outputFormat)
        if driver is None:
            print "Format driver %s not found." % outputFormat
            return

        metadata = driver.GetMetadata()
        if "DCAP_CREATE" not in metadata:
            print "Format driver %s does not support creation and piecewise writing" % outputFormat
            return

        # open source raster
        src = gdal.Open(unicode(layerPath))
        if src is None:
            print "Unable to open file", layerPath
            return

        # extract some metadata from source raster
        width = src.RasterXSize
        height = src.RasterYSize
        bands = src.RasterCount
        dataType = src.GetRasterBand(1).DataType
        crs = src.GetProjection()
        geoTransform = src.GetGeoTransform()

        # copy raster
        dstFilename = unicode("%s/%s.tif" % (self.layersDir, layerName))
        dst = driver.Create(dstFilename, width, height, bands, dataType, creationOptions)
        if dst is None:
            print "Creation failed"
            return

        dst.SetProjection(crs)
        dst.SetGeoTransform(geoTransform)

        # copy data from source file into output file
        for i in xrange(1, bands + 1):
            sBand = src.GetRasterBand(i)
            dBand = dst.GetRasterBand(i)

            data = sBand.ReadRaster(0, 0, width, height, width, height, dataType)
            dBand.WriteRaster(0, 0, width, height, data, width, height, dataType)

        src = None
        dst = None

        # update project
        layerNode = self.findLayerInProject(layerElement, layerName)
        tmpNode = layerNode.firstChildElement("datasource")
        p = "./layers/%s.tif" % layerName
        tmpNode.firstChild().setNodeValue(p)

    def findLayerInProject(self, layerElement, layerName):
        child = layerElement.firstChildElement()
        while not child.isNull():
            nm = child.firstChildElement("layername")
            if nm.text() == layerName:
                return child
            child = child.nextSiblingElement()
        return None
