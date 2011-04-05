import sys, unittest, re, os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def suite():
    tests = ['testParseString', 'testParseFile', 'testRunWorkflow']
    return unittest.TestSuite(map(XmlReaderTest, tests))

from WorkflowTest          import WorkflowTest
from SpiffWorkflow.Storage import XmlReader
from xml.parsers.expat     import ExpatError

class XmlReaderTest(WorkflowTest):
    def setUp(self):
        WorkflowTest.setUp(self)
        self.reader = XmlReader()


    def testParseString(self):
        self.assertRaises(ExpatError,
                          self.reader.parse_string,
                          '')
        self.reader.parse_string('<xml></xml>')


    def testParseFile(self):
        # File not found.
        self.assertRaises(IOError,
                          self.reader.parse_file,
                          'foo')

        # 0 byte sized file.
        file = os.path.join(os.path.dirname(__file__), 'xml', 'empty1.xml')
        self.assertRaises(ExpatError, self.reader.parse_file, file)

        # File containing only "<xml></xml>".
        file = os.path.join(os.path.dirname(__file__), 'xml', 'empty2.xml')
        self.reader.parse_file(file)

        # Read a complete workflow.
        file = os.path.join(os.path.dirname(__file__), 'xml', 'spiff', 'workflow1.xml')
        self.reader.parse_file(file)


    def testRunWorkflow(self):
        file = os.path.join(os.path.dirname(__file__), 'xml', 'spiff', 'workflow1.xml')
        workflow_list = self.reader.parse_file(file)
        for wf in workflow_list:
            self.runWorkflow(wf)


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity = 2).run(suite())
