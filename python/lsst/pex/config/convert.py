import lsst.pex.policy
import lsst.daf.base

def makePropertySet(config):
    def _helper(ps, prefix, dict_):
        for k,v in dict_.iteritems():
            name = prefix + "." + k if prefix is not None else k
            if isinstance(v, dict):
                _helper(ps, name, v)
            elif v is not None:
                ps.set(name, v)

    if config is not None:
        ps = lsst.daf.base.PropertySet()
        _helper(ps, None, config.toDict())
        return ps
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
