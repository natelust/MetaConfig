import lsst.pex.policy
import lsst.daf.base

def makePropertySet(config):
    def _helper(dict_):
        p = lsst.daf.base.PropertySet()
        for k,v in dict_.iteritems():
            if isinstance(v, dict):
                p.set(k, _helper(v))
            elif v is not None:
                p.set(k, v)
        return p
    if config:
        return _helper(config.toDict())
    else:
        return None

def makePolicy(config):
    def _helper(dict_):
        p = lsst.pex.policy.Policy()
        for k,v in dict_.iteritems():
            if isinstance(v, dict):
                p.set(k, _helper(v))
            elif isinstance(v, tuple):
                for vi in v:
                    p.add(k, vi)
            elif v is not None:
                p.set(k, v)
        return p
    if config:
        return _helper(config.toDict())
    else:
        return None
