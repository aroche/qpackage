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

from PyQt4.QtCore import *
from PyQt4.QtXml import *
from qgis.core import *
from pyspatialite import dbapi2 as db
from osgeo import gdal
import os.path
import pdb

pyqtRemoveInputHook()


# generates proper name for database
def launderName(name):
    r = name.lower()
    r = r.replace("'", '_')
    r = r.replace("#", '_')
    r = r.replace("-", '_')
    return r


class QPackageProject:
    def __init__(self, projectFile):
        self.projectFile = projectFile
        
        self.processedLayers = []
        
        self.loadProject()
        self.createDB()
        
        
    def loadProject(self):
        f = QFile(self.projectFile)
        if not f.open(QIODevice.ReadOnly | QIODevice.Text):
            msg = "Cannot read file %s:\n%s." % (self.projectFile, f.errorString())
            #self.processError.emit(msg)
            print msg
            return False

        self.doc = QDomDocument()
        setOk, errorString, errorLine, errorColumn = self.doc.setContent(f, True)
        if not setOk:
            msg = "Parse error at line %d, column %d:\n%s" % (errorLine, errorColumn, errorString)
            # self.processError.emit(msg)
            print msg
            return False

        f.close()
        
        root = self.doc.documentElement()

        # ensure that relative path used
        e = root.firstChildElement("properties")
        e.firstChildElement("Paths").firstChild().firstChild().setNodeValue("false")

        # get layers section in project
        self.layerElement = root.firstChildElement("projectlayers")
        return True
    
    def saveProject(self):
        self.dbConnection.close()
        
        f = QFile(self.projectFile)
        if not f.open(QIODevice.WriteOnly | QIODevice.Text):
            msg = "Cannot write file %s:\n%s." % (self.projectFile, f.errorString())
            #self.processError.emit(msg)
            print msg
            return

        out = QTextStream(f)
        self.doc.save(out, 4)
        f.close()
        
    def createDB(self):
        (root, ext) = os.path.splitext(self.projectFile)
        self.slPath = root + '.sqlite'
        # TODO : better way to handle existing db because of time consuming process
        if QFile.exists(self.slPath):
            QFile.remove(self.slPath)
        self.dbConnection = db.connect(self.slPath)
        cur = self.dbConnection.cursor()
        cur.execute("SELECT initspatialmetadata(1)")
        self.dbConnection.commit()
        
             
    # adapted from QSpatialite plugin
    def copyGenericVectorLayer(self, layer):
        selected = False
        selected_ids=[]
        if selected==True :
            if layer.selectedFeatureCount()==0:
                print "No selected item in Qgis layer: %s)"%layer.name(),self.parent
                return False
            select_ids=layer.selectedFeaturesIds()

        tableName = launderName(layer.name())
       
        #Get data charset
        provider = layer.dataProvider()
        #charset=provider.encoding()
    
        #Get fields with corresponding types
        fields=[]
        fieldsNames=[]
        mapinfoDAte=[]
        for id,name in enumerate(provider.fields().toList()):
            fldName = unicode(name.name()).replace("'"," ").replace('"'," ")
            #Avoid two cols with same name:
            while fldName.upper() in fieldsNames:
                fldName='%s_2'%fldName
            fldType=name.type()
            fldTypeName=unicode(name.typeName()).upper()
            if fldTypeName=='DATE' and unicode(provider.storageType()).lower()==u'mapinfo file'and mapinfo==True: # Mapinfo DATE compatibility
                fldType='DATE'
                mapinfoDAte.append([id,fldName]) #stock id and name of DATE field for MAPINFO layers
            elif fldType in (QVariant.Char, QVariant.String): # field type is TEXT
                fldLength=name.length()
                fldType='TEXT(%s)'%fldLength  #Add field Length Information
            elif fldType in (QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong): # field type is INTEGER
                fldType='INTEGER'
            elif fldType == QVariant.Double: # field type is DOUBLE
                fldType='REAL'
            else: # field type is not recognized by SQLITE
                fldType=fldTypeName
            fields.append(""" "%s" %s """%(fldName,fldType))
            fieldsNames.append(fldName.upper())

        # is it a geometric table ?
        geometry=False
        if layer.hasGeometryType():
            #Get geometry type
            geom=['MULTIPOINT','MULTILINESTRING','MULTIPOLYGON','UnknownGeometry']
            geometry=geom[layer.geometryType()]
            srid=layer.crs().postgisSrid()

        #select attributes to import (remove Pkuid if already exists):
        allAttrs = provider.attributeIndexes()
        fldDesc = provider.fieldNameIndex("PKUID")
        if fldDesc != -1:
            print "Pkuid already exists and will be replaced!"
            del allAttrs[fldDesc] #remove pkuid Field
            del fields[fldDesc] #remove pkuid Field
        #provider.select(allAttrs)
        #request=QgsFeatureRequest()
        #request.setSubsetOfAttributes(allAttrs).setFlags(QgsFeatureRequest.SubsetOfAttributes)

        if geometry:
            fields.insert(0,"Geometry %s"%geometry)
        
        #Create new table in BD
        cur = self.dbConnection.cursor()
        fields=','.join(fields)
        if len(fields)>0:
            fields=', %s'%fields
        cur.execute("""CREATE TABLE "%s" ( PKUID INTEGER PRIMARY KEY AUTOINCREMENT %s )"""%(tableName, fields))
            
        #Recover Geometry Column:
        if geometry:
           cur.execute("""SELECT RecoverGeometryColumn("%s",'Geometry',%s,'%s',2)"""%(tableName,srid,geometry,))
        
        # Retrieve every feature
        for feat in layer.getFeatures():
            # selected features:
            if selected and feat.id()not in select_ids:
                continue 
        
            #PKUID and Geometry     
            values_auto=['NULL'] #PKUID value
            if geometry:
                geom = feat.geometry()
                #WKB=geom.asWkb()
                WKT=geom.exportToWkt()
                values_auto.append('CastToMulti(GeomFromText("%s",%s))'%(WKT,srid))
        
            # show all attributes and their values
            values_perso=[]
            for val in allAttrs: # All except PKUID
                # TODO force to unicode
                values_perso.append(feat[val])
            
            #Create line in DB table
            if len(fields)>0:
                cur.execute("""INSERT INTO "%s" VALUES (%s,%s)"""%(tableName,','.join([unicode(value).encode('utf-8') for value in values_auto]),','.join('?'*len(values_perso))),tuple([unicode(value) for value in values_perso]))
            else: #no attribute Datas
                cur.execute("""INSERT INTO "%s" VALUES (%s)"""%(table_name,','.join([unicode(value).encode('utf-8') for value in values_auto])))

        for date in mapinfoDAte: #mapinfo compatibility: convert date in SQLITE format (2010/02/11 -> 2010-02-11 ) or rollback if any error
            cur.execute("""UPDATE OR ROLLBACK "%s" set '%s'=replace( "%s", '/' , '-' )""" % (tableName, date[1], date[1]))
    
        # add spatial index
        if geometry:
            cur.execute("SELECT CreateSpatialIndex('%s', '%s')" % (tableName, 'Geometry'))
        
        #Commit DB connection:
        self.dbConnection.commit()
        
        # update project
        layerNode = self.findLayerInProject(layer.id())
        tmpNode = layerNode.firstChildElement("datasource")
        p = "dbname='%s' table='%s' (geometry) sql=" % (self.slPath, tableName)
        tmpNode.firstChild().setNodeValue(p)
        tmpNode = layerNode.firstChildElement("provider")
        #tmpNode.setAttribute("encoding", enc)
        tmpNode.firstChild().setNodeValue("spatialite")
        self.processedLayers.append(layer.id())
        return True
    
    def copyRasterLayer(self, layer):
        gdal.UseExceptions()
        srcPath = layer.source()
        try:
            src = gdal.Open(srcPath)
        except:
            print "GDAL error opening data source", srcPath
            return
        driver = gdal.GetDriverByName("RASTERLITE")
        tableName = launderName(layer.name())
        dstPath = "RASTERLITE:%s,table=%s" % (self.slPath, tableName)
        # NB : copy doesn't work with geographic SRS
        try:
            ds = driver.CreateCopy(dstPath, src, 0)
        except:
            print "GDAL error copying data into DB"
            return
        
        # update project
        layerNode = self.findLayerInProject(layer.id())
        tmpNode = layerNode.firstChildElement("datasource")
        tmpNode.firstChild().setNodeValue(dstPath)
        self.processedLayers.append(layer.id())
        return True
        
    # updates the project to set a new data source
    def changeLayerDataSource(self, layerId, newSource):
        layerNode = self.findLayerInProject(layerId)
        tmpNode = layerNode.firstChildElement("datasource")
        tmpNode.firstChild().setNodeValue(newSource)
        
        
    def findLayerInProject(self, layerId):
        child = self.layerElement.firstChildElement()
        while not child.isNull():
            nm = child.firstChildElement("id")
            if nm.text() == layerId:
                return child
            child = child.nextSiblingElement()
        return None
 
# TODO:
# better way to display warnings and errors
# check if a data source is used several times, in order not to copy it twice
    