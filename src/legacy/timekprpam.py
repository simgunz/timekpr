def isuserlocked(username):
    """Checks if user is in access.conf"""
    try:
        i = parseaccessconf().index(username)
    except ValueError:
        return False
    return True

def lockuser(username, accessfile='/etc/security/access.conf'):
    """Adds access.conf line of user to lock/disable user accounts from logging in.
    Returns:
      True (even if user is already locked)
      False

    """
    if isuserlocked(username):
        return True
    fn = open(accessfile, 'r')
    s = fn.read()
    fn.close()
    try:
        fn = open(accessfile, 'w')
    except IOError:
        return False
    m = re.sub('(## TIMEKPR END)', '-:' + username + ':ALL\n\\1', s)
    fn.write(m)
    fn.close()
    return True
    
def unlockuser(username,accessfile='/etc/security/access.conf'):
    """Removes access.conf line of user

    Returns:
      True  (even if user is not listed/locked)
      False (eveif no write permission)
    """
    if not isuserlocked(username):
        return True
    fn = open(accessfile, 'r')
    s = fn.read()
    fn.close()
    try:
        fn = open(accessfile, 'w')
    except IOError:
        return False
    m = re.compile('(## TIMEKPR START\n.*)-:' + username + ':ALL\n', re.S).sub('\\1', s)
    fn.write(m)
    fn.close()
    return True

def adduserlimits(username, bfrom, bto, timefile='/etc/security/time.conf'):
    """Adds a line with the username and their from and to time limits in time.conf

    Arguments:
      username
      bfrom: 7 elements list containing the from limit hours 
      bto: 7 elements list containing the to limit hours
    Returns:
      True or False (if no write permission)
    """
    getconfsection(timefile) #Check if timekpr section exists
    line = mktimeconfline(username, bfrom, bto) + "\n"
    fn = open(timefile, 'r')
    s = fn.read()
    fn.close()
    try:
        fn = open(timefile, 'w')
    except IOError:
        return False
    m = re.sub('(## TIMEKPR END)', line + '\\1', s)
    fn.write(m)
    return True


def removeuserlimits(username, timefile='/etc/security/time.conf'):
    """Removes a line with the username in time.conf

    Returns True or False (if no write permission)

    """
    getconfsection(timefile) # Check if timekpr section exists
    fn = open(timefile, 'r')
    s = fn.read()
    fn.close()
    try:
        fn = open(timefile, 'w')
    except IOError:
        return False
    m = re.compile('(## TIMEKPR START\n.*)\*;\*;' + username + ';[^\n]*\n', re.S).sub('\\1', s)
    fn.write(m)
    fn.close()
    return True


def isuserlimited(u, timefile='/etc/security/time.conf'):
    """Checks if user is in time.conf (if account has limited access hours)

    Argument: username
    Returns: True/False

    """
    s = getconfsection(timefile)
    #Check if Al0000-2400 present:
    x = re.compile('^\*;\*;' + u + ';Al0000-2400$', re.M).search(s)
    if x:
        return False
    m = re.compile('^\*;\*;([^;]+);', re.M).findall(s)
    try:
        i = m.index(u)
    except ValueError:
        return False
    return True


def isuserlimitednow(u, timefile='/etc/security/time.conf'):
    """Checks if username should be limited as defined in time.conf

    Argument: username
    If this is True and the user is logged in, they should be killed
    Returns: True or False (even if user is not in time.conf)

    """
    if not isuserlimited(u):
        return False
    s = getconfsection(timefile)
    m = re.compile('^\*;\*;' + u + ';(.*)$', re.M).findall(s)
    today = int(strftime("%w"))
    hournow = int(strftime("%H"))
    #If Al (All days):
    x = re.match('Al(\d\d)00-(\d\d)00', m[0])
    if x:
        low = int(x.group(1)) #lowest limit
        high= int(x.group(2)) #highest limit
        if low <= hournow < high:
            return False
    else:
        d = re.split(' \| ', m[0])[today]
        z = re.match('\w\w(\d\d)00-(\d\d)00', d)
        low = int(z.group(1))
        high = int(z.group(2))
        if low <= hournow < high:
            return False
    return True


def isuserlimitedtoday(u, timefile='/etc/security/time.conf'):
    #Argument: username
    #Checks if username has limitations for this day
    #Returns: True or False (even if user is not in time.conf)
    if not isuserlimited(u):
        return False
    s = getconfsection(timefile)
    m = re.compile('^\*;\*;' + u + ';(.*)$', re.M).findall(s)
    today = int(strftime("%w"))
    #If Al (All days):
    x = re.match('Al0000-2400', m[0])
    if x:
        return False
    else:
        day = { 0:"Su", 1:"Mo", 2:"Tu", 3:"We", 4:"Th", 5:"Fr", 6:"Sa" }
        g = re.compile(day[today] + '0000-2400').search(m[0])
        if g:
            return False
        return True


def strint(x):
    #makes '08' into '8' and '10' as '10'
    return str(int(x))

def converttconf(tfrom, tto, mode=0):
    """Removes the unnecessary 0 and multiplies from and to lists if necessary

    If mode = 0 (default), it converts tfrom = ['08','08','13','14','15','01','09'], 
    tto = ['22','14','19','20','21','23','25'] into ['8','8','13','14','15','1','9']
    and ['22','14','19','20','21','23','25'] respectively
    If mode = 1, it converts tfrom = '08', tto = '22' into ['8','8','8','8','8','8','8']
    and ['22','22','22','22','22','22','22'] respectively

    WARNING: Will NOT distinguish if tfrom is a list or string if mode is not properly defined!

    """
    if mode == 0:
        ffrom = list(map(strint, tfrom))
        fto = list(map(strint, tto))
    elif mode == 1:
        #Single values mode, need to multiply 7 times
        ffrom = [strint(tfrom)] * 7
        fto = [strint(tto)] * 7
    return ffrom, fto

def parsetimeconf(f='/etc/security/time.conf'):
    """Returns a list with usernames with from and to limits from the time.conf file

    Return example:
    [('niania', 'Al0000-2400'), ('wawa', 'Su0700-2200 | Mo0700-2200 | Tu0700-2200 | We0700-2200 | Th0700-2200 | Fr0700-2200 | Sa0900-2200')]

    """
    c = getconfsection(f)
    utlist = re.compile('^\*;\*;([^;]+);(.*)$', re.M).findall(c)
    return utlist

def parseutlist(utlist):
    """Parses the list from parsetimeconf()

    Example: ['niania', 'Al0000-2400']
    Returns a list (retlist):
        [0] = first item:
            [0] = username niania
            [1] = fromto:
                [0] = from ['0', '0', '0', '0', '0', '0', '0']
                [1] = to ['24', '24', '24', '24', '24', '24', '24']
    Example usage:
        parseutlist(utlist)[0][1][0]
        ['0', '0', '0', '0', '0', '0', '0']

    """
    retlist = []
    for u,t in utlist:
        #Check if Al is used
        checkAl = re.compile('^Al(\d{2})00-(\d{2})00$').search(t)
        if checkAl:
            final = converttconf(checkAl.group(1), checkAl.group(2), 1)
        else:
            pieces = re.split(' \| ', t) #Break time in 'pieces'
            if len(pieces) != 7:
                exit('Error: Unsupported format detected (should have 7 time items): "%s"' % t)
            if not re.search('^Su\d{2}00-\d{2}00$', pieces[0]):
                exit('Error: Unsupported format detected (Sunday should be first): "%s"' % t)
            #0=Sunday, su[0] is from, su[1] is to
            restr = '^%s(\d\d)00-(\d\d)00$'
            su = re.compile(restr % 'Su').findall(pieces[0])[0]
            mo = re.compile(restr % 'Mo').findall(pieces[1])[0]
            tu = re.compile(restr % 'Tu').findall(pieces[2])[0]
            we = re.compile(restr % 'We').findall(pieces[3])[0]
            th = re.compile(restr % 'Th').findall(pieces[4])[0]
            fr = re.compile(restr % 'Fr').findall(pieces[5])[0]
            sa = re.compile(restr % 'Sa').findall(pieces[6])[0]
            final = converttconf([su[0], mo[0], tu[0], we[0], th[0], fr[0], sa[0]], \
                                [su[1], mo[1],tu[1],we[1],th[1],fr[1],sa[1]])
        retlist.append([u, final])
        # Internal example - retlist.append appends like so:
        # user: [niania,(['0', '0', '0', '0', '0', '0', '0'], 
        #       ['24', '24', '24', '24', '24', '24', '24'])]
        # user: [wawa,(['7', '7', '7', '7', '7', '7', '9'], 
        #        ['22', '22', '22', '22', '22', '22', '22'])]
    
    return retlist
