def definition(varname,name='__main__'):
    ns=__import__(name or __name__)
    if not hasattr(ns,varname):
        try:
            return eval(varname)
        except NameError:
            return None #raise remote NameError
    return getattr(ns,varname)

def rimport(varname,name='__main__'):
    ns=__import__(name or __name__)
    rv = None
    if not hasattr(ns,varname):

        try:
            rv = eval(varname)
        except NameError:
            return 'µE|(NameError)'
    else:
        rv = getattr(ns,varname)
    RunTime.CPR[id(rv)]=rv
    return 'µM|%s'% id(rv)



def do(paths,argv,kw):
    objRoot = __import__('__main__')
    print('CALL:',paths,argv,kw)

    while len(paths):
        branch = paths.pop(0)
        if not len(paths): #leaf
            #print(" " * ( 8 - (len(paths)*2) ),"locate:",objRoot,branch,end=' : ')
            break
        if hasattr(objRoot,branch):
            objRoot = getattr(objRoot,branch)
        #else:
        #   raise remote
        #print(" " * ( 8 - (len(paths)*2) ),"locate:",objRoot,branch)
    rv = getattr(objRoot,branch)(*argv,**kw)
    #print("JSON:",  )
    return RunTime.to_json(rv)

#for use with atm websocket rpc
def do_raw(paths,argv,kw,silent=True):
    objRoot = __import__('__main__')
    if not silent:
        print('CALL:',paths,argv,kw)

    while len(paths):
        branch = paths.pop(0)
        if not len(paths):
            break
        if hasattr(objRoot,branch):
            objRoot = getattr(objRoot,branch)
    return getattr(objRoot,branch)(*argv,**kw)
