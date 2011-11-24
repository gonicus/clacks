


class XMLDBInt(object):

    def openDatabase(self):
        """
        Opens an existing databse
        """
        raise Exception("Method not implemented: %s" % ("openDatabase",))

    def createDatabase(self, name):
        """
        Creates a new database collection.
        """
        raise Exception("Method not implemented: %s" % ("createDatabase",))

    def databaseExists(self, name):
        """
        Checks whethter a databse exists or not
        """
        raise Exception("Method not implemented: %s" % ("databaseExists",))

    def addDocument(self, name, contents):
        """
        Adds a new document to the database

        addDocuemnt('world.xml', '/universe', contents)
        xquery("collection('db/universe/world.xml')")
        """
        raise Exception("Method not implemented: %s" % ("addDocument",))

    def documentExists(self, name):
        """
        Checks whethter a document exists or not
        """
        raise Exception("Method not implemented: %s" % ("documentExists",))

    def getDocuments(self):
        """
        Returns a list of all documents attached to the given database.
        """
        raise Exception("Method not implemented: %s" % ("getDocuments",))

    def xquery(self, query):
        """
        Executes an xquery statement
        xquery("collection('db/universe/world.xml')")
        """
        raise Exception("Method not implemented: %s" % ("xquery",))

    def setNamespace(self, abbr, namespace):
        """
        Sets a namespace abbreviation
        """
        raise Exception("Method not implemented: %s" % ("setNamespace",))

    def dropDatabase(self, name):
        """
        Drops the given database
        """
        raise Exception("Method not implemented: %s" % ("dropDatabase",))

    def deleteDocument(self, name):
        """
        Removes the given document from the currently openened database
        """
        raise Exception("Method not implemented: %s" % ("deleteDocument",))



"""

init
    mgr = XmlManager(DBXML_ALLOW_EXTERNAL_ACCESS)
    qc = mgr.createQueryContext()
    qc.setNamespace("", "http://www.gonicus.de/Events")
    qc.setNamespace("gosa", "http://www.gonicus.de/Events")
    qc.setNamespace("xsi","http://www.w3.org/2001/XMLSchema-instance")

    uc = mgr.createUpdateContext()

createDatabase
    mgr.createContainer(containerName, DBXML_ALLOW_VALIDATION, XmlContainer.NodeContainer)

addDocument:
    cont.putDocument(name, string, uc)

query
    results = mgr.query("collection('%s')/Event/Inventory/DeviceID/string()" % (containerName,), qc)

"""



