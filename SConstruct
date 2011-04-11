# -*- python -*-
#
# Setup our environment
#
import glob, os.path, re, os
import lsst.SConsUtils as scons

env = scons.makeEnv("pex_policy",
                    r"$HeadURL$",
                    [["boost", "boost/version.hpp", "boost_system:C++"],
                     ["boost", "boost/version.hpp", "boost_filesystem:C++"],
                     ["boost", "boost/regex.hpp", "boost_regex:C++"],
                     ["boost", "boost/system/config.hpp", "boost_system:C++"],
                     ["boost", "boost/serialization/serialization.hpp", "boost_serialization:C++"],
                     ["python", "Python.h"],
                     ["utils", "lsst/utils/Utils.h", "utils:C++"],
                     ["pex_exceptions", "lsst/pex/exceptions/Exception.h", "pex_exceptions:C++"],
                     ["daf_base", "lsst/daf/base/Citizen.h", "daf_base:C++"],
                    ])
env.libs["pex_policy"] += env.getlibs("boost utils daf_base pex_exceptions");
#
# Build/install things
#
for d in Split("lib tests python/lsst/pex/policy doc"):
    SConscript(os.path.join(d, "SConscript"))

env['IgnoreFiles'] = r"(~$|\.pyc$|^\.svn$|\.o$)"

Alias("install", [env.Install(env['prefix'], "python"),
                  env.Install(env['prefix'], "include"),
                  env.Install(env['prefix'], "lib"),
                  env.Install(env['prefix'], "tests"),
                  env.Install(env['prefix'], "examples"),
                  env.Install(env['prefix'], "bin"),
                  env.InstallAs(os.path.join(env['prefix'], "doc", "doxygen"),
                                os.path.join("doc", "htmlDir")),
                  env.InstallEups(env['prefix'] + "/ups", glob.glob("ups/*.table"))])

scons.CleanTree(r"*~ core *.so *.os *.o")

#
# Build TAGS files
#
files = scons.filesToTag()
if files:
    env.Command("TAGS", files, "etags -o $TARGET $SOURCES")

env.Declare()
env.Help("""
Pipeline Execution: Policy
""")

