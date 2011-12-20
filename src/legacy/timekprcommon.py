def is_late(bto, allowfile):
    # Get current day index and hour of day
    index = int(strftime("%w"))
    hour = int(strftime("%H"))
    if (hour > bto[index]):
        if isfile(allowfile):
            if not from_today(allowfile):
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def is_past_time(limits, time):
    index = int(strftime("%w"))
    if (time > limits[index]):
        return True
    else:
        return False

def is_early(bfrom, allowfile):
    # Get current day index and hour of day
    index = int(strftime("%w"))
    hour = int(strftime("%H"))
    if (hour < bfrom[index]):
        if isfile(allowfile):
            if not from_today(allowfile):
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def is_restricted_user(username, limit):
    if not isuserlimited(username) and limit == 86400:
        return False
    else:
        return True 
