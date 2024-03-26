import time

holidays_const=[time.mktime((2000,1,1,0,0,0,0,1,-1)),time.mktime((2000,1,6,0,0,0,0,1,-1)),time.mktime((2000,5,1,0,0,0,0,1,-1)),time.mktime((2000,5,3,0,0,0,0,1,-1)),time.mktime((2000,8,15,0,0,0,0,1,-1)),time.mktime((2000,11,1,0,0,0,0,1,-1)),time.mktime((2000,11,11,0,0,0,0,1,-1)),time.mktime((2000,12,25,0,0,0,0,1,-1)),time.mktime((2000,12,26,0,0,0,0,1,-1))]


def now():
    #return string with current date and time, without .xxxxxx seconds
    now=time.localtime()
    return str(now.tm_year)+'-'+str(now.tm_mon)+'-'+str(now.tm_mday)+' '+str(now.tm_hour)+':'+str(now.tm_min)+':'+str(now.tm_sec)

def t_s(time_s):
    """convert int timestamp to str"""
    now=time.localtime(time_s)
    return str(now.tm_year)+'-'+str(now.tm_mon)+'-'+str(now.tm_mday)+' '+str(now.tm_hour)+':'+str(now.tm_min)+':'+str(now.tm_sec)
  
def press_sea_level(pressure,temp,height):
    #calculates the pressure at sea level
    #stopień baryczny
    h=8000*(1+0.004*temp)/pressure
    
    #ciśnienie na poziomie morza
    P=pressure+(height/h)
    
    #średnie ciśnienie
    Psr=(pressure+P)/2
    
    #średnia temperatura
    tpm=temp+(0.6*height)/100
    
    tsr=(temp+tpm)/2
    
    h=8000*(1+0.004*tsr)/Psr
    
    Pn=pressure+(height/h)
    
    return Pn

def _count_easter(year):
    """counts date of easter in year and returns the next day (Easter is always in Sunday, which is properly interpreted by Orno meter)
    Meeus/Jones/Butcher method"""

    a = year%19
    b = int(year/100)
    c = year%100
    d = int(b/4)
    e = b%4
    f = int((b+8)/25)
    g = int((b-f+1)/3)
    h = (19*a+b-d-g+15)%30
    i = int(c/4)
    k = c%4
    l = (32+2*e+2*i-h-k)%7
    m = int((a+11*h+22*l)/451)
    p = (h+l-7*m+114)%31
    day = p+1
    month = int((h+l-7*m+114)/31)
    
    delta=int(3600*24) #seconds in day
    #a im interested in the next day after easter
    return time.mktime((year,month,day,0,0,0,0,1,-1)) + delta

def _count_bc(year):
    """counts date of "Boże ciało" in year, 60 days after Easter (59 after the next day after easter)"""
    return _count_easter(year) + int(59*3600*24)  #59 days after

def is_holiday(day):
#check if date is a holiday in Poland
    date=time.localtime(day)
    for d in holidays_const:
        if (d.tm_mon==date.tm_mon) and (d.tm_wday==date.tm_wday):
            return True
        
    tmp_date=time.localtime(_count_easter(date.tm_year))
    if (date.tm_mon==tmp_date.tm_mon) and ((date.tm_mday==tmp_date.tm_mday)):
        return True
    
    tmp_date=time.localtime(_count_bc(date.tm_year))
    if (date.tm_mon==tmp_date.tm_mon) and ((date.tm_mday==tmp_date.tm_mday)):
        return True
    return False
