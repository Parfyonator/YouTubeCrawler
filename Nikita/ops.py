from collections import OrderedDict
from collections import deque
import time
import random
import sys
import re 
from imp import reload

glob=3

def getsize(x):
    return sys.getsizeof(x)

#Function profiler. Sorting options: 0-by call number, 1-by function inner time, 2-by function cumulative time.
def profile(s,sort=1):
    import cProfile
    cProfile.run(s,sort=sort)

#Use @initializer wrapper. Checks for defaults existence. Why do we need to go in reverse direction? 
#How much slower it is than usual init? 
from functools import wraps
import inspect

def inize(fun):
    names, varargs, keywords, defaults = inspect.getargspec(fun)
    @wraps(fun)
    def wrapper(self, *args, **kargs):
        self.inited=False
        for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
            setattr(self, name, arg)
        
        if defaults:
            for i in range(len(defaults)):
                index = -(i + 1)
                if not hasattr(self, names[index]):
                    setattr(self, names[index], defaults[index])
        fun(self, *args, **kargs)
        self.inited=True
    return wrapper

#To avoid problems with default empty lists.
def denone(fun):
    def wrap(*args,**kws):
        largs=inspect.getargspec(fun)[0]
        if largs[-1] not in kws and len(args)<len(largs): kws[largs[-1]]=[]
        return fun(*args, **kws)
    return wrap

def lfy(f):
    def wrap(*a):
        return list(f(*a))
    return wrap


def fread(s):
    return open(s,'r').read()

def hardread(s):
     return open(s,'r',encoding="utf8").read()

def fwrite(f,s):
    return open(f,'w',encoding="utf8").write(s)

'''Operations'''

def lflat2(l):
    if ist(l[0], list): return [x for y in l for x in y]
    else: return l
    
def lflat(l):
    return lflat2(l)

def lflat(l):
    nl=[]
    for x in l:
        if (isiter(x)): 
            nl+=lflat(x) 
        else: 
            nl.append(x)
    return nl

def ist(o,t):
    return isinstance(o,t)

def antinone(l):
    if l==None: return []
    else: return l
    
def getl(f):
    return f().split()

def getint(f):
    return int(f())

def getints(s):
    return lm(int, s.split())

def stoints(s):
    return lm(int, s.split())

def enum(l):
    return enumerate(l)

def sign(x):
    if x>0: return 1
    if x<0: return -1
    return 0

global la
la={
    '^': lambda x,y:x**y,
    '**':lambda x,y:x**y,
    '+': lambda x,y:x+y,
    '-': lambda x,y:x-y,
    '*': lambda x,y:x*y,
    '/': lambda x,y:x/y,
    '//': lambda x,y:x//y,
    '%': lambda x,y:x%y,
    '1': lambda x,y:x,
    '2': lambda x,y:y,
    'get':lambda x,y:x[y],
    '>': lambda x,y:x>y,
    '=>':lambda x,y:x>=y,
    '<': lambda x,y:x<y,
    '<=': lambda x,y:x<=y,
    '!=': lambda x,y:x!=y,
    '==': lambda x,y:x==y,
    'in': lambda x,y:x in y,
    'nin': lambda x,y:x not in y,
    'and': lambda x,y:x and y,
    'or': lambda x,y:x or y,
    

}


#Shortcut-functions processor. Allow fixing of the second arg. 
def tof(f,a2=None):
    if ist(f,str): f=la[f]
    return f if a2==None else lambda x:f(x,a2)

def isiter(o):
    try:
        iterator = iter(o)
    except TypeError:
        return 0
    else:
        return 1

def isarray(o):
    if isiter(o) and not ist(o,str): return 1
    else: return 0    

def lm(f,*l):
    f=tof(f)
    return list(map(f,*l))

#Multifunction
def mf(f,*l):
    return lm(f,l)

def fitem(i=0):
    return lambda x:x[i]

fself=lambda x:x

def lf(l,f):
    return [x for x in l if f(x)]


def lzip(*l):
    return list(zip(*l))

#fzip('+', [1,2,3])=6. Problem: list doesn't change? You shouldn't copy it, choose indeces instead. 
#Note! It takes list of arguments, not tuple!
def fzip(f,l):
    f=tof(f)
    for i in range(1,len(l)):
        l[i]=f(l[i-1],l[i])
    return l[-1]
        
def allwith(s,l):
    return [x for x in l if s in x]

class Op:  
    def __init__ (self,l=None):
        self.l=l
    
    def __add__(self,s):
        return self.act('+',s)
    
    def __sub__(self,s):
        return self.act('-',s)
    
    def __mul__(self,s):
        return self.act('*',s)
    
    def __truediv__(self,s):
        return self.act('/',s)
    
    def __pow__(self,s):
        return self.act('**',s)
    
    def __lt__(self,s):
        return self.act('<',s)
        
    def __gt__(self,s):
        return self.act('>',s)
        
    def __le__(self,s):
        return self.act('<=',s)
        
    def __ge__(self,s):
        return self.act('>=',s)
    
    def __eq__(self,s):
        op='in' if isiter(s) else '=='
        return self.act(op,s)
        
    def __ne__(self,s):
        op='nin' if isiter(s) else '!='
        return self.act(op,s)

    def __getitem__(self,s):
        return self.act('get',s)

class oneof(Op): 
    def act(self,op,s):
        l=[tof(op)(x,s) for x in self.l]
        return fzip('or',l)

class allof(Op):   
    def act(self,op,s):
        l=[tof(op)(x,s) for x in self.l]
        return fzip('and',l)

#How deal with lif(l)[1][1]>2. What key is doing here? Add to l?       
class lif(Op):
    @inize
    def __init__(c,l,key=fself): pass
    
    #key acts on values before filtering. 
    def act(self,op,y):
        return lf(self.l, lambda x:tof(op)(self.key(x),y))   
    
#Super lambda. But what if there are several variables? No complex statements lik X**2+10? How combine lambdas? 
class X(Op):
    def act(c,op,y):
        return tof(op,y)

class Xf(Op):
    @inize
    def __init__(c,f=None):pass
    
    def __call__(c,*a,**kw):
        return c.f(*a,**kw)
    
    def act(c,op,y):
        if not c.f: return Xf(tof(op,y))
        else: return lambda x:tof(op)(c.f(x),y)

X=Xf()

#Eg lop(l)*3
class lop(Op):
    def act(self,op,y):
        f=tof(op)
        return [f(x,y) for x in self.l]

'''Dicts and lists'''    

#Transpose table.
def ltrans(l):
    return [[x[k] for x in l] for k in range(0,len(l[0]))]

class D(dict):
    def __init__(c,d):
        dict.__init__(c,d)
        for x in d:
            setattr(c,x,d[x])  
        
    def __setattr__(c,x,v):
        c.__dict__[x]=v
        c[x]=v
        
#New array with specific dimensions. 
def lnew(*n,fill=0):
    l=[]
    for i in range(n[0]):
        if len(n)>1: l.append(lnew(*n[1:],fill=fill))
        else: l.append(fill)
    return l

def lsort(l,rev=1,key=fself):
    return sorted(l,reverse=rev,key=key)
    
def firstFalse(l,cond):
    for x in l:
        if not cond(x): return x
    return None

#What about use of external variable, does it first looks in context of outer function? 
#If so, then why can't you use ext-variables in body? Cause it's compilator-level error. 
def firstTrue(l,cond):
    for x in l:
        if cond(x): return x
    return None

def fcount(f):
    t=0
    while 1:
        t+=1
        step=f()
        if not step: break
    return t

#Fast dict from list. Works for words list to, cause maintains unique keys.
#Problem with empty list, binded to function. 
def dnew(l, fill=0):
    d={}
    for x in l: d[x]=fill
    return d

def dlnew(l):
    d={}
    for x in l: d[x]=[]
    return d

def odnew(l=None, fill=0):
    d=OrderedDict()
    if not l: return d
    
    for x in l: d[x]=fill
    return d

def odlnew(l=None):
    d=OrderedDict()
    if not l: return d
    
    for x in l: d[x]=[]
    return d

def od(l):
    return OrderedDict(l)

def odit(d,i):
    return d[list(d)[i]]

#Enumerated keys. 
def ekeys(d):
    return enum(list(d))

def dfill(d,fill):
    for x in d: d[x]=fill
    return d

def dtol(d): 
    return list(d.items())

def dvals(d):
    return list(d.values())

#Dsort by key. 
def dksort(d,rev=1):
    l=sorted(dtol(d),reverse=rev)
    return OrderedDict(l)

def dvsort(d,rev=1):
    l=sorted(dtol(d),reverse=rev,key=lambda x:x[1])
    return OrderedDict(l)