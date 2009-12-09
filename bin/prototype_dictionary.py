import optparse
import sys
import os

from lsst.pex.policy import Policy, Dictionary, PAFWriter
from lsst.pex.exceptions import LsstCppException

usage = """usage: %prog [--help] <options> <policy>"""

desc = """
Extrapolate a Dictionary from a Policy in such a way that the Policy is a valid
instance of the Dictionary.  In practice, the Dictionary will probably be overly
strict, and you will want to loosen it up by hand.
"""

class PolicyValidator:
    def __init__(self):
        self.verbose = False

    def main(self, argv=None):
        self.parseArgs(argv)

        # 1. load policy
        policy = self.tryThis(Policy,
                              "Reading policy file \"" + self.policyFile + "\"",
                              self.policyFile)

        # resolve policy file references
        polLoadDir = self.options.loadPolicy
        polLoadDesc = polLoadDir
        if polLoadDir == None:
            if self.policyFile.find("/") >= 0:
                polLoadDir = self.policyFile.rpartition("/")[0]
                polLoadDesc = polLoadDir
            else:
                polLoadDir = ""
                polLoadDesc = "current directory; " \
                              "try -l DIR or --load-policy-references=DIR"
            if self.verbose:
                print "No policy load dir specified; defaulting to " + polLoadDesc
        message = "Resolving references in " + self.policyFile \
                  + ",\n    using " + polLoadDesc
        self.tryThis(policy.loadPolicyFiles, message, polLoadDir, True)

        # derive short name by trimming off path & suffix
        shortname = self.policyFile
        if shortname.endswith(".paf"):
            shortname = shortname.rpartition(".paf")[0]
        if shortname.find("/") >= 0:
            shortname = shortname.rpartition("/")[2]

        if self.verbose:
            print "Short name =", shortname

        # 2. create a dictionary from it
        dictionary = Policy()

        dictionary.set("target", shortname)
        self.generateDict(policy, dictionary)

        # TODO: remove commas from lists
        if self.verbose:
            print "Generating Dictionary for Policy " + self.policyFile + ":"
            print "---------------------------Policy---------------------------"
            print policy
            print "-------------------------Dictionary-------------------------"

        realDict = Dictionary(dictionary)
        try:
            realDict.validate(policy)
            print "#<?cfg paf dictionary ?>"
            writer = PAFWriter()
            writer.write(dictionary)
            print writer.toString()
            #print dictionary
        except LsstCppException, e:
            ve = e.args[0]
            print "Internal error: validation fails against extrapolated dictionary:"
            print ve.describe("  - ")

    def generateDict(self, policy, dictionary, prefix=""):
        definitions = Policy()
        dictionary.set("definitions", definitions)
        names = policy.names(True)
        for name in names:
            values = policy.getArray(name)
            defin = Policy()
            definitions.set(name, defin)
            defin.set("type", policy.getTypeName(name))
            defin.set("minOccurs", 1)
            defin.set("maxOccurs", len(values))
            type = policy.getValueType(name)

            if type == Policy.POLICY:
                newPrefix = prefix + "." + name
                subdict = Policy()
                defin.set("dictionary", subdict)
                if len(values) > 1:
                    print "# Warning: only using first value of", newPrefix
                self.generateDict(values[0], subdict, newPrefix)
            else:
                allowed = Policy()
                defin.set("allowed", allowed)
                orderable = type == Policy.INT or type == Policy.DOUBLE \
                            or type == Policy.STRING
                if orderable:
                    allowed.set("min", min(values))
                    allowed.set("max", max(values))
                for value in values:
                    defin.add("default", value)
                    allowed.add("value", value)

    def tryThis(self, callableObj, explain, *args, **kwargs):
        try:
            if self.verbose: print explain
            result = callableObj(*args, **kwargs)
            return result
        except LsstCppException, e:
            print "error", explain + ":"
            print e.args[0].what()
            sys.exit(2)

    def parseArgs(self, argv=None):
        # see http://docs.python.org/library/optparse.html
        self.parser = optparse.OptionParser(usage=usage, description=desc) # parasoft-suppress W0201
        self.parser.add_option("-p", "--policy", dest="policy", metavar="FILE",
                               help="the policy to validate")
        self.parser.add_option("-l", "--load-policy-references", dest="loadPolicy",
                               metavar="DIR",
                               help="Directory from which to load policy file "
                               "references (if not specified, load from "
                               "current directory).")
        self.parser.add_option("-v", "--verbose", dest="verbose",
                               action="store_const", const=True,
                               help="Print extra messages.")

        if argv is None:
            argv = sys.argv
        (self.options, args) = self.parser.parse_args(argv) # parasoft-suppress W0201
        # print "args =", args, len(args)
        # print "options =", self.options
        if (self.options.verbose != None):
            self.verbose = self.options.verbose
        
        self.policyFile = self.options.policy               # parasoft-suppress W0201
        del args[0] # script name
        if (self.policyFile == None):
            if len(args) < 1:
                self.parser.error("no policy specified")
            self.policyFile = args[0]
            del(args[0])

        if not os.path.exists(self.policyFile):
            self.parser.error("file not found: " + self.policyFile)

        if len(args) != 0:
            self.parser.error("too many arguments: " + str(args) + " were not parsed.")

if __name__ == "__main__":
    pv = PolicyValidator()
    pv.main()
    sys.exit(0)
