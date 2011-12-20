def get_users():
    users = list()
    rawusers = get_cmd_output('last')
    rawloggedusers = re.findall('(^.*)still logged in',rawusers,re.M)
    for i in rawloggedusers:
        users.append(re.split(' ',i)[0])
        users = set(users)
    return users 

def add_notified(u):
    # Adds username to notifiedusers list, so it does not re-notify them
    try:
        notifiedusers.index(u)
    except ValueError:
        notifiedusers.append(u)

def is_notified(u):
    # Checks if username is already in notifiedusers list
    try:
        notifiedusers.index(u)
    except ValueError:
        return False
    return True

def remove_notified(u):
    # Removes username from notifiedusers list, so it does not re-notify them
    try:
        notifiedusers.index(u)
    except ValueError:
        return
    notifiedusers.remove(u)