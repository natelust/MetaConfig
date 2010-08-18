import lsst.pex.policy as pp

def create_policy(d):
    '''
    lsst.pex.policy.Policy = create_policy(d)

    Creates an LSST Policy object, given a Python dictionary.

    The dictionary must map strings to:
    * int
    * float
    * string
    * bool,
    * dict (recursively)
    * pexPolicy.PolicyFile
    * pexPolicy.Policy
    * list or tuple of the above.
    '''
    p = pp.Policy()
    for k,v in d.items():
        if type(v) is dict:
            # recurse.
            p.set(k, create_policy(v))
            continue

        if type(v) is not str:
            # Note, we must check for dict and string before this,
            # because both those types are iterable.
            #   isiterable(v)  (via duck-typing)
            try:
                V = iter(v)
                for vv in V:
                    p.add(k, vv)
                continue
            except:
                pass

        # if we get here, it's scalar (presumably).  If not, swig will
        # probably complain violently when it tries to find the
        # right Policy::set() template.
        p.set(k,v)
    return p






if __name__ == '__main__':
    p = create_policy(dict(
        matchThreshold = 30,
        numBrightStars = 50,
        blindSolve = True,
        distanceForCatalogueMatchinArcsec = 5,
        cleaningParameter = 3,

        listtype = (3,4,5),
        slisttype = ['123', '456', '789'],
        emptylist = [], # this disappears.

        subpolicy = dict(
            smeg = 42.7,
            poo = 'yes',
            cack = False,
            ),

        pol2 = pp.PolicyFile('dne.paf'),
        subpol3 = pp.Policy(),

        ))

    print p.toString()
    
    try:
        p2 = create_policy("this won't work!")
        print p2.toString()
    except:
        print 'p2 failed'


    try:
        p3 = create_policy({"this won't work!": object()})
        print p3.toString()
    except:
        print 'p3 failed'


