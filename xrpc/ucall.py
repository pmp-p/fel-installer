



class RObject:

    def __init__(self,sender,**kw):
        self.__rpcob_send = sender
        self.__rpcob_rpcid = kw.pop('rpcid')
        self.__rpcob_repr  = kw.pop('repr')

    #fixme update RT
    def __repr__(self):
        return '&%s' % self.__rpcob_repr

    def __getattr__(self, attr):
        return _Remote(self.__rpcob_send, "*%s.%s" %( self.__rpcob_rpcid, attr) )

class _Remote:
    # bind a method to an RPC server and supports nesting
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
        self.__isobj = False

    def __getattr__(self, name):
        callpath = "%s.%s" % (self.__name, name)
        if self.__isobj:
            print('  getattr',callpath)

        return _Remote(self.__send, callpath)

    def __call__(self, *argv, **kw):
        if self.__isobj:
            print("  Obj_call",self.__name)
        else:
            if not self.__name.endswith('.__str__'):
                #print("  path_call",self.__name)
                pass
            else:
                rv=self.__send(self.__name, (argv,kw,)) #, wait_for_response=True )
                if not isinstance(rv,(str,unicode)):
                    return repr(rv)

        rv=self.__send(self.__name, (argv,kw,) )  #, wait_for_response=True )
        #got a list
        if self.__name.endswith('.__iter__'):
            return iter(rv)

        if isinstance(rv,str):
            #maybe got remote obj
            if rv.startswith('µO|'):
                self.__isobj = True
                rv,tips = rv[3:].split('|',1)
                print('<REF[%s]>'%rv)
                return RObject(self.__send, rpcid=rv, repr=tips )
            print('ReturnValue=',rv)


#        if isinstance(rv,dict) and 'rpcid' in rv:
#            self.__isobj = True
#            return RObject(self.__send, **rv)
        return rv


class CProxy:
    def __init__(self,requester):
        self.__rpc_req = requester

    def __repr__(self):
        return ( "<CProxy %s>" % (self.__handler) )

    __str__ = __repr__

    def __nonzero__(self):
        return True

    def __getattr__(self, attr):
        return _Remote(self.__rpc_req, attr)


