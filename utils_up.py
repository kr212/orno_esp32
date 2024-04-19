import time

#holidays_const=[time.mktime((2000,1,1,0,0,0,0,1)),time.mktime((2000,1,6,0,0,0,0,1)),time.mktime((2000,5,1,0,0,0,0,1)),time.mktime((2000,5,3,0,0,0,0,1)),time.mktime((2000,8,15,0,0,0,0,1)),time.mktime((2000,11,1,0,0,0,0,1)),time.mktime((2000,11,11,0,0,0,0,1)),time.mktime((2000,12,25,0,0,0,0,1)),time.mktime((2000,12,26,0,0,0,0,1))]
holidays_const=[(1,1),(1,6),(5,1),(5,3),(8,15),(11,1),(11,11),(12,25),(12,26)]

def now():
    """return string with current date and time, without .xxxxxx seconds"""
    now=time.localtime()
    #now=(year, month, mday, hour, minute, second, weekday, yearday)
    #return str(now[0])+'-'+str(now[1])+'-'+str(now[2])+' '+str(now[3])+':'+str(now[4])+':'+str(now[5])
    return f"{now[0]:04}-{now[1]:02}-{now[2]:02} {now[3]:02}:{now[4]:02}:{now[5]:02}"

def t_s(time_s):
    """convert int timestamp to str"""
    now=time.localtime(time_s)
    #return str(now[0])+'-'+str(now[1])+'-'+str(now[2])+' '+str(now[3])+':'+str(now[4])+':'+str(now[5])
    return f"{now[0]:04}-{now[1]:02}-{now[2]:02} {now[3]:02}:{now[4]:02}:{now[5]:02}"
  
def press_sea_level(pressure,temp,height):
    """calculates the pressure at sea level"""
    #stopień baryczny/baric degree
    h=8000*(1+0.004*temp)/pressure
    
    #ciśnienie na poziomie morza,pressure at sea level
    P=pressure+(height/h)
    
    #średnie ciśnienie/mean pressure
    Psr=(pressure+P)/2
    
    #średnia temperatura/mean temperature
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
    #i am interested in the next day after easter
    return time.mktime((year,month,day,0,0,0,0,1)) + delta

def _count_bc(year):
    """counts date of "Boże ciało" in year, 60 days after Easter (59 after the next day after easter)"""
    return _count_easter(year) + int(59*3600*24)  #59 days after

def is_holiday(day):
    """check if date is a holiday in Poland"""
    date=time.localtime(day)
    holidays=holidays_const
    #add easter date
    tmp_date=time.localtime(_count_easter(date[0]))
    holidays=holidays+[(tmp_date[1],tmp_date[2])]
    #add Boże ciało date
    tmp_date=time.localtime(_count_bc(date[0]))
    holidays=holidays+[(tmp_date[1],tmp_date[2])]

    #check all dates
    for d in holidays:
        if (d[0]==date[1]) and (d[1]==date[2]):
            return True
    return False

def stime():
    """returns present time in seconds since epoch"""
    return time.mktime(time.localtime())
