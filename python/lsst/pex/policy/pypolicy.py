#import lsst.pex.policy as pp

def add_to_policy(p, d):
    '''
    add_to_policy(pexPolicy, dictionary)

    Adds the contents of the given dictionary to the given
    lsst.pex.policy.Policy object.

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

def create_policy(*args, **kwargs):
    '''
    lsst.pex.policy.Policy = create_policy(d)

    Creates an LSST Policy object, given a Python dictionary,
    or several dictionaries, or keyword arguments.

    The given dictionaries are added to the Policy in turn, followed
    by the keyword arguments.

    Eg,

    p1 = create_policy({'key':52})

    p2 = create_policy(dict(key=52), dict(anotherkey=75),
                       {'thirdkey':89}, yetanother=4)

    The dictionaries must map strings to:
    * int
    * float
    * string
    * bool,
    * dict (recursively)
    * pexPolicy.PolicyFile
    * pexPolicy.Policy
    * list or tuple of the above.
    '''
    import lsst.pex.policy as pp
    p = pp.Policy()
    for d in args:
        add_to_policy(p, d)
    add_to_policy(p, kwargs)
    return p



if __name__ == '__main__':
    import lsst.pex.policy as pp
    d = dict(
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
        )
    d.update({'subpol4.x':42})
    p = create_policy(d, {'extra.stuff':7}, morestuff=4)
    print p.toString()

    pb = create_policy(dict(key=52), dict(anotherkey=75),
                       {'thirdkey':89}, yetanother=4)
    print pb.toString()

    pc = create_policy(dict(key1=4, keyB='indeed', key9=[4,5,7]),
                       {'subpolicy.key': 17}, another_key=True)
    print pc.toString()

    pd = pp.Policy.frompython(d, test='yuh-huh')
    print pd.toString()
    pd.addpython({'more':'stuff'}, testing='')
    print pd.toString()

    pe = pp.Policy.frompython({'a':'b', 'c':'d', 'e':8}, nine=10)
    print pe.toString()
    pe.addpython(dict(more='better'), extra=6)
    print pe.toString()

    f=open('deprecated.paf', 'w')
    f.write('a:4')
    f.close()
    p = pp.Policy.frompython(ref=pp.PolicyFile('dne'),
                             ref2=pp.Policy.createPolicy('deprecated.paf'))
    print p.toString()
    
    try:
        p2 = create_policy("this won't work!")
        print p2.toString()
    except:
        print 'p2 failed (as expected)'


    try:
        p3 = create_policy({"this won't work!": object()})
        print p3.toString()
    except:
        print 'p3 failed'


