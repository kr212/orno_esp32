def crc(table):
    #calculate crc value, return LSB and MSB
    value=0xFFFF

    for i in table:
        value^=i

        for k in range(8):
            if (value & 0x0001):
                value>>=1
                value^=0xA001
            else:
                value>>=1
    return (value & 0x0ff, (value & 0xff00)>>8 ) 
     
