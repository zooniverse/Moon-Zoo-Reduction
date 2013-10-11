from math import ceil

def timethis(expr, globalvars=None, localvars=None, repeat=5, number=1):
    t = timethisnow(expr, globalvars, localvars, repeat, number)
    newnumber = number
    while t < 0.1:
        newnumber *= 10
        t = timethisnow(expr, globalvars, localvars, repeat, newnumber)
    if newnumber != number:
        print 'Using number=%i to ensure minimum of 0.1 sec per repeat'%newnumber
    return t/newnumber


def timethisnow(expr, globalvars, localvars, repeat=5, number=1):
    import time, gc
    t = []
    for i in range(repeat):
        gc.disable()
        start = time.clock()
        for j in range(number):
            eval(expr, globalvars, localvars)
        t.append(time.clock()-start)
        gc.enable()
    return min(t)
