import optparse
import sys

from lsst.pex.policy import Policy, Dictionary
from lsst.pex.exceptions import LsstCppException

usage = """usage: %prog [--help] <options> [policy] [dictionary]"""

desc = """
Validate a policy file against a dictionary (policy schema).
"""

class PolicyValidator:
    def __init__(self):
        self.verbose = False

    def main(self, argv=None):
        self.parseArgs(argv)

        # 1. load policy
        policy = self.tryThis(Policy,
                              "reading policy file \"" + self.policyFile + "\"",
                              self.policyFile)

        # resolve policy file references
        polLoadDir = self.options.loadPolicy
        polLoadDesc = polLoadDir
        if polLoadDir == None:
            print " ### verbose?", self.verbose
            if self.verbose:
                print "No policy load dir specified; using current dir."
            polLoadDir = ""
            polLoadDesc = "current directory; " \
                          "try -l DIR or --load-policy-references=DIR"
        message = "resolving references in " + self.policyFile + ",\n    using " \
                  + polLoadDesc
        self.tryThis(policy.loadPolicyFiles, message, polLoadDir, True)

        # 2. load dictionary
        dictionary = self.tryThis(Dictionary,
                                  "reading dictionary file \"" + self.dictFile + "\"",
                                  self.dictFile)

        # resolve dictionary file references
        dictLoadDir = self.options.loadDict
        dictLoadDesc = dictLoadDir
        if (dictLoadDir == None):
            if self.verbose:
                print "No dictionary load dir specified; using policy load dir", \
                      polLoadDesc
            if polLoadDir != "":
                dictLoadDir = polLoadDir
                dictLoadDesc = polLoadDesc
            else:
                dictLoadDir = ""
                dictLoadDesc = "current directory; " \
                               "try -l DIR or --load-dictionary-references=DIR"
        message = "resolving references in " + self.dictFile + ",\n" \
                  "    using " + dictLoadDesc
        self.tryThis(dictionary.loadPolicyFiles, message, dictLoadDir, True)
    
        # 3. merge defaults into policy
        defaults = None
        defaultsFile = self.options.defaults
        if (defaultsFile != None):
            defaults = self.tryThis(Policy,
                                    "reading defaults from \"" + defaultsFile + "\"",
                                    defaultsFile)
        else: defaults = dictionary # if no defaults file specified, use dictionary
        self.tryThis(policy.mergeDefaults, "merging defaults into policy", defaults)

        # 4. validate
        self.tryThis(dictionary.validate,
                     "validating " + self.policyFile + "\n    against " + self.dictFile,
                     policy)

        if self.verbose:
            print
        print "Validation passed:"
        print "      policy: " + self.policyFile
        print "                  is a valid instance of"
        print "  dictionary: " + self.dictFile

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
        self.parser.add_option("-d", "--dictionary", dest="dictionary", metavar="FILE",
                               help="The dictionary to validate a policy against.")
        self.parser.add_option("-p", "--policy", dest="policy", metavar="FILE",
                               help="the policy to validate")
        self.parser.add_option("-l", "--load-policy-references", dest="loadPolicy",
                               metavar="DIR",
                               help="Directory from which to load policy file "
                               "references (if not specified, load from "
                               "current directory).")
        self.parser.add_option("-L", "--load-dictionary-references", dest="loadDict",
                               metavar="DIR",
                               help="Directory from which to load dictionary "
                               "file references (if not specified, load from "
                               "policy references dir).")
        self.parser.add_option("-D", "--load-defaults", dest="defaults", metavar="FILE",
                               help="Load defaults from FILE, which can be a policy "
                               "or dictionary.  If not specified, load defaults from "
                               "the dictionary being used for validation.")
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
        self.dictFile = self.options.dictionary             # parasoft-suppress W0201
        del args[0] # script name
        if (self.policyFile == None):
            if len(args) < 1:
                self.parser.error("no policy specified")
            self.policyFile = args[0]
            del(args[0])
        if (self.dictFile == None):
            if len(args) < 1:
                self.parser.error("no dictionary specified")
            self.dictFile = args[0]
            del(args[0])

        if len(args) != 0:
            self.parser.error("too many arguments: " + str(args) + " were not parsed.")

if __name__ == "__main__":
    pv = PolicyValidator()
    pv.main()
    sys.exit(0)
