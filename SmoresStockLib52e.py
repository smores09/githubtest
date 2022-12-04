# version 5.2b : ATR bug fix
# version 5.2c : Volatility bug fix
# version 5.2d : stooqcsv reading error (some data doesn't have full data in a row, e.g. AMZN)
# version 5.2e : data conversion 'd','w','m' data to 'q','y'

import calendar
import os
import sys
import smtplib
import time
import zipfile
import requests


endl = '\n'


### DB Part ##########################################################################################

DataDir = './'  # end up with '/'
DataSource = None  # stooqcsv, stooqzip, yahoo, yohlc, yohlcv
DB = None
DBSYM = None
DBFILE = None


def SetDB(datadir, datasource=''):  
    global DataSource, DataDir, SimDir, DB, DBSYM    
    DataSource = datasource    
    DataDir = datadir
    if DataDir[-1]!='/': DataDir += '/'
    if DataSource=='stooqzip':
        prep_db_stooqzip()
        

def Read_YOHLC(symbol, ext='.csv'):
    global DataDir
    Y,O,H,L,C,V = [],[],[],[],[],[]
    path = DataDir
    if path[-1]!='/':
        path = path + '/'
    filename = path + symbol + ext
    buf = open(filename).read().split(endl)
    while buf[-1]=='': buf.pop(-1)
    for i in range(1,len(buf)):
        items = buf[i].split(',')
        y = int(items[0])
        o = float(items[1])
        h = float(items[2])
        l = float(items[3])
        c = float(items[4])
        Y.append(y)
        O.append(o)
        H.append(h)
        L.append(l)
        C.append(c)
        V.append(0)
    return Y,O,H,L,C,V    

def Read_YOHLCV(symbol, ext='.csv'):
    global DataDir
    Y,O,H,L,C,V = [],[],[],[],[],[]
    filename = DataDir + symbol + ext
    buf = open(filename).read().split(endl)
    while buf[-1]=='': buf.pop(-1)
    for i in range(1,len(buf)):
        items = buf[i].split(',')
        y = int(items[0])
        o = float(items[1])
        h = float(items[2])
        l = float(items[3])
        c = float(items[4])
        v = int(items[5])
        Y.append(y)
        O.append(o)
        H.append(h)
        L.append(l)
        C.append(c)
        V.append(v)
    return Y,O,H,L,C,V

def Read_NewYahoo(symbol):
    return read_newyahoo(symbol)
    
def Read_StooqCSV(symbol, dwm='m'):
    return read_stooqcsv(symbol, dwm)    
    
def Read_StooqZip(symbol, dwm='d'):
    Y,O,H,L,C,V = read_stockdata_stooqzip(symbol) # day chart
    if dwm!='d':
        Y,O,H,L,C,V = ConvertDayChartToWeekOrMonthChart(Y,O,H,L,C,V, dwm)        
    return Y,O,H,L,C,V


# ---- stooq csv --------------------------------------


def read_html(url):
    req = requests.get(url)
    html = requests.text
    return html

def save_webfile(url, filename):
    req = requests.get(url)
    with open(filename,'wb') as fp: fp.write(req.content)

def download_stooqdata(symbol, dwm='m'):    
    global DataDir
    url0 = 'https://stooq.com/q/d/l/?s=@@.us&i=' + dwm ## month chart historical data
    url = url0.replace('@@',symbol)
    filename = DataDir + symbol+ '_us_' + dwm + '.csv'
    try:
        save_webfile(url, filename)
        return True
    except:
        return False

def read_stooqcsv(symbol, dwm='m'):
    global DataDir
    filename = DataDir + symbol + '_us_' + dwm + '.csv'
    #~ buf = open(filename).read().replace('-','').replace(',',' ')
    #~ Y = list(map(int,buf[6::6]))
    #~ O = list(map(float,buf[7::6]))
    #~ H = list(map(float,buf[8::6]))
    #~ L = list(map(float,buf[9::6]))
    #~ C = list(map(float,buf[10::6]))
    #~ V = list(map(int,buf[11::6]))
    Y,O,H,L,C,V = [],[],[],[],[],[]
    buf = open(filename).read().replace('-','').replace(',',' ').split(endl)
    for i in range(1,len(buf)):
        s = buf[i]
        if s != '':
            items = buf[i].split()
            #~ print(items)
            y,o,h,l,c,v = 0,0,0,0,0,0
            try:
                y = int(items[0])
                o = float(items[1])
                h = float(items[2])
                l = float(items[3])
                c = float(items[4])
                v = int(items[5])
            except:
                continue
            Y.append(y)
            O.append(o)
            H.append(h)
            L.append(l)
            C.append(c)
            V.append(v)
    return Y,O,H,L,C,V

# ---- stooqzip (up to 2018.03) ---------------------------

def prep_db_stooqzip():
    global DataSource, DataDir, SimDir, DB, DBSYM, DBFILE    
    DB = zipfile.ZipFile(DataDir+'stooqzip')
    DBFILE = DB.namelist()
    DBSYM = []
    for s in DBFILE:
        DBSYM.append(s.split('/')[-1].split('.')[0].upper())

def read_stockdata_stooqzip(symbol):
    global DB, DBSYM, DBFILE
    symbol = symbol.upper()
    if symbol in DBSYM:
        p = DBSYM.index(symbol)
        filename = DBFILE[p]
        buf = DB.read(filename).decode('utf-8').replace(',',' ').replace('\r\n',' ').replace('-','').split()
        #buf = DB.read(filename).replace(',',' ').replace('\n',' ').replace('-','').split()
        Y=list(map(int,buf[7::7]))
        O=list(map(float,buf[8::7]))
        H=list(map(float,buf[9::7]))
        L=list(map(float,buf[10::7]))
        C=list(map(float,buf[11::7]))
        V=list(map(int,buf[12::7]))
        return Y,O,H,L,C,V
    else:
        return [],[],[],[],[],[]

# ---- new yahoo csv ---------------------------

def read_newyahoo(symbol):
    global DataDir
    filename = DataDir + symbol + '.csv'
    buf = open(filename).read().replace('-','').replace(',',' ').replace('Adj Close','AdjClose').split('\n')
    #~ buf = open(filename).read().split('\n')
    Y,O,H,L,C,V = [],[],[],[],[],[]   
    for i in range(1,len(buf)):        
        try:
            ss = buf[i].split()
            y = int(ss[0])
            o = float(ss[1])
            h = float(ss[2])
            l = float(ss[3])
            c = float(ss[5])
            v = int(ss[6])
            Y.append(y)
            O.append(o)
            H.append(h)
            L.append(l)
            C.append(c)
            V.append(v)
        except:
            pass
    return Y,O,H,L,C,V    

# ---- DB related ---------------------------

def ImportChartData(symbol, dwm='m'):    
    Y,O,H,L,C,V = [],[],[],[],[],[]
    if DataSource=='stooqzip':
        Y1,O1,H1,L1,C1,V1 = read_stockdata_stooqzip(symbol) # day chart
        if dwm!='d':
            Y,O,H,L,C,V = ConvertDayChartToWeekOrMonthChart(Y1,O1,H1,L1,C1,V1, dwm)    
        else:
            Y,O,H,L,C,V = Y1,O1,H1,L1,C1,V1
    if DataSource=='stooqcsv':
        Y,O,H,L,C,V = read_stooqcsv(symbol, dwm)
    if DataSource=='yahoo':
        Y,O,H,L,C,V = read_newyahoo(symbol)
    if DataSource=='yohlc':
        Y,O,H,L,C,V = Read_YOHLC(symbol)
    if DataSource=='yohlcv':
        Y,O,H,L,C,V = Read_YOHLCV(symbol)
    return Y,O,H,L,C,V


def ImportChartDataDWM(symbol, day_week_month):  # obsolete
    Y,O,H,L,C,V = ImportChartData(symbol, day_week_month)
    #~ Y1,O1,H1,L1,C1,V1 = ImportChartData(symbol)
    #~ Y,O,H,L,C,V = ConvertDayChartToWeekOrMonthChart(Y1,O1,H1,L1,C1,V1, day_week_month)    
    return Y,O,H,L,C,V

def ReadOneChart(symbol, dwm):
    Y,O,H,L,C,V = ImportChartDataDWM(symbol, dwm)
    ONECHART = {'Y':Y[:], 'O':O[:], 'H':H[:], 'L':L[:], 'C':C[:], 'V':V[:]}
    return ONECHART
    
def GetDataFromMultiCharts(CHARTS, symbol, ymd, itemname): 
    # charts is a dictionary of symbol:chart
    ret = None
    try:
        ONECHART = CHARTS[symbol]
        Y = ONECHART['Y']
        V = ONECHART[itemname]
        pos = Y.index(ymd)
        ret = V[pos]
    except:
        pass
    return ret

def GetDataFromMultiChartsYM(CHARTS, symbol, ym, itemname): 
    # charts is a dictionary of symbol:chart
    try:
        ONECHART = CHARTS[symbol]
        Y = ONECHART['Y']
        V = ONECHART[itemname]
        for i in range(len(Y)):
            y = int(Y[i]/100)
            if y==ym:
                return Y[i],V[i]
    except:
        pass
    return None,None

       
            
def YMDToDayOfWeek(YMD, mondaynum=0):
    # mondaynumber shift to cut one week differently
    DOW = []
    for ymd in YMD:
        ymdstr= "%d" % (ymd)
        y = int(ymdstr[0:4])
        m = int(ymdstr[4:6])
        d = int(ymdstr[6:8])
        dow = (calendar.weekday(y,m,d) + mondaynum) % 7  # mon-sun 0-6
        DOW.append(ymd)
    return DOW


def WeekStartEndPos(YMD):
    DOW = YMDToDayOfWeek(YMD)
    WeekStart = [0]
    WeekEnd = []
    for i in range(1,len(DOW)):
        dowprev = DOW[i-1]
        dowcurrent = DOW[i]
        if dowcurrent <= dowprev: # week changed
            WeekStart.append(i)
            WeekEnd.append(i-1)
    return WeekStart, WeekEnd
    
    
def FindStartEndPosYMDOld(YMD, startDateInt, endDateInt, dwm='d'):
    ## supposed that datelist is sorted from old to new date     
    if endDateInt==-1: endDateInt=99999999
    startpos,endpos = 0,0
    for i in range(len(YMD)-1,-1,-1):
        startpos = i
        if YMD[i] == startDateInt:
            break
        if YMD[i] < startDateInt:
            if dwm=='d':
                startpos = i+1
            else:
                startpos = i                
            break
    
    for i in range(len(YMD)):
        endpos = i
        if YMD[i] == endDateInt:
            break
        if YMD[i] > endDateInt:
            endpos = i - 1
            break

    return startpos, endpos


def FindStartEndPosYMD(YMD, startDateInt, endDateInt, dwm='d'):
    ## supposed that datelist is sorted from old to new date     
    if endDateInt==-1: endDateInt=99999999
    startpos,endpos = 0,0
    for i in range(len(YMD)):
        if YMD[i]>=startDateInt:
            startpos = i
            break
    for i in range(len(YMD)-1,-1,-1):
        if YMD[i]<=endDateInt:
            endpos = i
            break
    if endpos==0: 
        endpos = len(YMD)-1
    return startpos, endpos
    
    

def ConvertChartToQY(Y,O,H,L,C,V, QorY): # use only for m or d chart as input source
    if not(QorY=='q' or QorY=='y'):
        print('QorY must be either q or y')
        return [],[],[],[],[],[]
    
    Y1,O1,H1,L1,C1,V1 = [],[],[],[],[],[]
    Yt,Ot,Ht,Lt,Ct,Vt = [],[],[],[],[],[]    
    for i in range(len(Y)):
        y = Y[i]
        o = O[i]
        h = H[i]
        l = L[i]
        c = C[i]
        v = V[i]
        if i==0: # very first data
            Yt.append(y)
            Ot.append(o)
            Ht.append(h)
            Lt.append(l)
            Ct.append(c)
            Vt.append(v)
        else:
            if QorY=='q':
                mprev = int(Yt[0]/100) % 100
                mcurr = int(y/100) % 100
                qprev = int((mprev - 1) / 3)
                qcurr = int((mcurr - 1) / 3)
                if qprev!=qcurr: # new quarter, append previous lists to data lists, and restart
                    Y1.append(Yt)
                    O1.append(Ot)
                    H1.append(Ht)
                    L1.append(Lt)
                    C1.append(Ct)
                    V1.append(Vt)
                    Yt,Ot,Ht,Lt,Ct,Vt = [],[],[],[],[],[]   
                    Yt.append(y)
                    Ot.append(o)
                    Ht.append(h)
                    Lt.append(l)
                    Ct.append(c)
                    Vt.append(v)
            elif QorY=='y':
                yprev = int(Yt[0]/10000)
                ycurr = int(y/10000)
                if yprev!=ycurr: # new year, append previous lists to data lists, and restart
                    Y1.append(Yt)
                    O1.append(Ot)
                    H1.append(Ht)
                    L1.append(Lt)
                    C1.append(Ct)
                    V1.append(Vt)
                    Yt,Ot,Ht,Lt,Ct,Vt = [],[],[],[],[],[]   
                    Yt.append(y)
                    Ot.append(o)
                    Ht.append(h)
                    Lt.append(l)
                    Ct.append(c)
                    Vt.append(v)
                
    # add remaining data lists
    Y1.append(Yt)
    O1.append(Ot)
    H1.append(Ht)
    L1.append(Lt)
    C1.append(Ct)
    V1.append(Vt)

    # conversion 
    for i in range(len(Y1)):
        Y1[i] = Y1[i][0]
        O1[i] = O1[i][0]
        H1[i] = max(H1[i])
        L1[i] = min(L1[i])
        C1[i] = C1[i][-1]
        V1[i] = sum(V1[i])

    return Y1,O1,H1,L1,C1,V1
    
    
    
def ConvertDayChartToWeekOrMonthChart(Y,O,H,L,C,V, dwm):
    Y1,O1,H1,L1,C1,V1 =  [],[],[],[],[],[]

    if dwm == 'd':
        Y1 = Y[:]
        O1 = O[:]
        H1 = H[:]
        L1 = L[:]
        C1 = C[:]
        V1 = V[:]
        
    if dwm == 'w':

        DOW = []
        for i in range(len(Y)):
            ymdstr = str(Y[i])
            y = int(ymdstr[0:4])
            m = int(ymdstr[4:6])
            d = int(ymdstr[6:8])
            dow = calendar.weekday(y,m,d)
            DOW.append(dow)
                
        y,o,h,l,c,v = Y[0],O[0],H[0],L[0],C[0],V[0]        
        Y1.append(y)
        O1.append(o)        
        totalvol = v
        hh = h
        ll = l
        prevc = c

        for i in range(1,len(Y)):

            y,o,h,l,c,v = Y[i],O[i],H[i],L[i],C[i],V[i]

            if DOW[i]<DOW[i-1]: # week changed, append one week data and reset initial values
                H1.append(hh)
                L1.append(ll)
                C1.append(prevc)
                V1.append(totalvol)
                totalvol = v
                hh = h
                ll = l        
                prevc = c        
                Y1.append(y)
                O1.append(o)
            else:
                hh = max([hh,h])
                ll = min([ll,l])
                prevc = c
                totalvol += v
                if i==len(Y)-1: # the last week data was not appended
                    H1.append(hh)
                    L1.append(ll)
                    C1.append(prevc)
                    V1.append(totalvol)
                    
    if dwm == 'm':
        y,o,h,l,c,v = Y[0],O[0],H[0],L[0],C[0],V[0]
        Y1.append(y)
        O1.append(o)        
        totalvol = v        
        hh = h
        ll = l
        prevc = c
        prevmo = int(str(y)[4:6])
        
        for i in range(1,len(Y)):

            y,o,h,l,c,v = Y[i],O[i],H[i],L[i],C[i],V[i]
            mo = int(str(y)[4:6])

            if mo!=prevmo: # month changed, append one week data and reset initial values
                H1.append(hh)
                L1.append(ll)
                C1.append(prevc)
                V1.append(totalvol)
                totalvol = v
                hh = h
                ll = l        
                prevc = c   
                prevmo = mo     
                Y1.append(y)
                O1.append(o)          
            else:
                hh = max([hh,h])
                ll = min([ll,l])
                prevc = c
                totalvol += v
                if i==len(Y)-1: # the last week data was not appended
                    H1.append(hh)
                    L1.append(ll)
                    C1.append(prevc)
                    V1.append(totalvol)
                   
    return Y1,O1,H1,L1,C1,V1


def YtoYM(Y):
    YM = []
    for y in Y:
        ym = int(y/100)
        YM.append(ym)
    return YM
    
def MakeYMList(YYYYMM1,YYYYMM2):
    YM = []
    ym = YYYYMM1    
    y = int(ym/100)
    m = ym - y*100
    while ym<=YYYYMM2:
        YM.append(ym)
        m += 1
        if m==13:
            m = 1
            y += 1
        ym = y*100 + m
    return YM
    
    

    
### Indicator Math Part ####################################################################

def CalcAvg(vlist):
    avg = 0
    cnt = 0
    for v in vlist:
        if v!=None:
            avg += v
            cnt += 1
    if cnt > 0:
        return avg/cnt
    else:
        None

def CalcAvgMomentumList(C, MomList):
    maxperiod = max(MomList)
    AvgMomentum = [None] * len(C)
    for i in range(maxperiod,len(C)):
        momsum = 0
        for j in MomList:
            momsum += (C[i]/C[i-j])
        avgmom = momsum / len(MomList)
        AvgMomentum[i] = avgmom
    return AvgMomentum
    

def CalcM136List(C):
    AvgMomentum = [None] * len(C)
    for i in range(6,len(C)):
        avgmom = ( (C[i]/C[i-1])*4 + (C[i]/C[i-3])*3 + (C[i]/C[i-6])*3 ) /  10
        AvgMomentum[i] = avgmom
    return AvgMomentum


def CalcTrendScoreList(V,period):
    TS = [None] * len(V)
    for i in range(period,len(V)):
        tdirref = 1
        if V[i]-V[i-period]<0:
            tdirref = -1
        tdsum = 0
        for j in range(i-period,i):
            tdir = 1 
            if V[j+1]-V[j]<0:
                tdir = -1
            if tdir==tdirref:
                tdsum += 1
        tdsum = tdsum / period
        TS[i] = tdsum
    return TS

    

'''
def calc_trend_list(L):
    T = [0] * len(L)
    for i in range(2, len(L)):
        t = 0
        if (L[i]>=L[i-1] and L[i-1]>=L[i-2]) or (L[i]<L[i-1] and L[i-1]<L[i-2]):
            t = 1
        T[i] = t
    return T

def CalcTrendScoreList(vlist, period):
    T = calc_trend_list(vlist)
    TS = CalcSMA(T, period)
    return TS
        

def CalcTrendScoreV1(vlist, period):
    TS = [None] * len(vlist)
    for i in range(period+1, len(vlist)):
        ts = period
        for j in range(i-1,i-period-1,-1):
            if (vlist[j+1]>=vlist[j] and vlist[j]<vlist[j-1]) or (vlist[j+1]<vlist[j] and vlist[j]>=vlist[j-1]):
                ts -= 1
        TS[i] = ts/period                
    return TS

def CalcTrendScoreOld(vlist, period):
    TS = [None] * len(vlist)
    maxts = 0
    for i in range(1,period+1):
        maxts += i
    #~ print(maxts)
    for i in range(period, len(vlist)):
        ts = 0
        n = 0
        for j in range(i-period,i):
            n += 1
            d = 1
            if vlist[j+1]<vlist[j]:
                d = -1
            ts = ts + d * n
        TS[i] = ts/maxts                
    return TS
'''

def CalcSimpleNoise(vlist, startpos, endpos): # larger the noise, closer to zero the return value
    b = abs(vlist[endpos]-vlist[startpos])
    a = 0
    for i in range(startpos+1, endpos+1):
        a += abs(vlist[i]-vlist[i-1])
    noise = b / a
    return noise

def CalcSimpleNoiseList(vlist, period):
    N = [None] * len(vlist)
    for i in range(period,len(vlist)):
        noise = CalcSimpleNoise(vlist, i-period,i)
        N[i] = noise
    return N

def calcsum(vlist): 
    s=sum(vlist)
    return s
    
def calcavg(vlist):
    s = sum(vlist)
    return s*1.0/len(vlist)

    
def CalcStdev(vlist):
    avg = calcavg(vlist)
    sum = 0
    N = len(vlist)
    for i in range(N):
        sum = sum + (vlist[i]-avg)**2
    stdev = (sum/N)**0.5
    return stdev


def CalcSMMax(vlist, period):
    SMMax=[]
    for i in range(len(vlist)):
        p1 = i - period + 1
        p2 = i + 1
        if p1<0:
            SMMax.append(None)
        else:
            SMMax.append(max(vlist[p1:p2]))
    return SMMax
    

def CalcSMMin(vlist, period):
    SMMin=[]
    for i in range(len(vlist)):
        p1 = i - period + 1
        p2 = i + 1
        if p1<0:
            SMMin.append(None)
        else:
            SMMin.append(max(vlist[p1:p2]))
    return SMMin


def CalcSMA(vlist, period):
    SMA=[]
    for i in range(len(vlist)):
        p1 = i - period + 1
        p2 = i 
        if p1<0:
            SMA.append(None)
        else:
            sum = 0.0
            for j in range(p1,p2+1):
                if vlist[j]==None:
                    sum = None
                    break
                else:
                    sum = sum + vlist[j]
            if sum==None:
                SMA.append(None)
            else:
                SMA.append(sum/period)
    return SMA
    

def CalcEMA(vlist, period):
    SMA = CalcSMA(vlist, period)
    EMA=[]
    Multiplier = 2.0 / (period + 1)
    p = 0
    for i in range(len(SMA)):        
        if SMA[i]==None:
            EMA.append(None)
        else:
            EMA.append(SMA[i])
            p = i+1
            break            
    for i in range(
    p,len(vlist)):
        EMA.append((vlist[i]-EMA[i-1])*Multiplier+EMA[i-1])
    return EMA
                 

def CalcATR2(H, L, C, NumDays=14):
    HL=[]
    HCp=[]
    LCp=[]
    TR=[]
    ATR=[]
    for i in range(len(H)):
        HL.append(H[i]-L[i])
        if i<1:
            HCp.append(0)
            LCp.append(0)
        else:
            HCp.append(abs(H[i]-C[i-1]))
            LCp.append(abs(L[i]-C[i-1]))
        #~ print(HL[i],HCp[i],LCp[i])
        #~ print(H)
        #~ print(C)
        #~ print(HCp)
        #~ print(LCp)
        #~ input()
        TR.append(max([HL[i],HCp[i],LCp[i]]))
    # ------------------------------
    for i in range(len(H)):
        if i<NumDays-1:
            ATR.append(None)
        elif i==NumDays-1:
            ATR.append(CalcAvg(TR[0:NumDays]))
        else:
            ATR.append((ATR[i-1]*(NumDays-1)+TR[i])/NumDays)
    # ------------------------------
    return ATR, HL, HCp, LCp, TR


def CalcATR(H, L, C, NumDays=14):
    ATR, HL, HCp, LCp, TR = CalcATR2(H, L, C, NumDays)
    return ATR


def CalcATRperc(H, L, C, NumDays=14):
    ATR = CalcATR(H,L,C)
    ATRperc = ListDivide(ATR,C)
    return ATRperc

def CalcRSI(C, NumDays=14):
    Chg = [0.0]*len(C)
    Gain = [0.0]*len(C)
    Loss = [0.0]*len(C)
    #~ AvgGain = [0.0]*len(C)
    #~ AvgLoss = [0.0]*len(C)
    #~ RS = [0.0]*len(C)
    RSI = [0.0]*len(C)
    
    for i in range(1,len(C)):
        Chg[i] = C[i]-C[i-1]        
        if Chg[i]>0:
            Gain[i] = Chg[i]
        else:
            Loss[i] = -Chg[i]
        
    for i in range(NumDays,len(C)):
        if i==NumDays:
            avggain = sum(Gain[i-NumDays+1:i+1])/NumDays
            avgloss = sum(Loss[i-NumDays+1:i+1])/NumDays
        else:
            avggain = (avggain*(NumDays-1)+Gain[i])/NumDays
            avgloss = (avgloss*(NumDays-1)+Loss[i])/NumDays            
        if avgloss==0:
            RSI[i] = 100.0
        else:
            rs = avggain/avgloss
            RSI[i] = 100.0 - 100.0/(1.0+rs)
    
    return RSI
        
def CalcStoch(H, L, C, NumDays=14, KDays=3, DDays=3):
    HH = []
    LL = []
    K0 = []
    K = []
    D = []
    ## HH, LL, K0
    for i in range(len(C)):
        if i<NumDays-1:
            HH.append(None)
            LL.append(None)
            K0.append(None)
        else:
            hh = max(H[i-NumDays+1:i+1])
            ll = min(L[i-NumDays+1:i+1])            
            HH.append(hh)
            LL.append(ll)
            k = (C[i]-ll) / (hh-ll) * 100.0
            K0.append(k)
    ## K3,D3
    K = CalcSMA(K0, KDays)
    D = CalcSMA(K, DDays)    
    return K, D
    
    
def CalcStochRSI(C, NumDays=14, KDays=3, DDays=3):
    RSI = CalcRSI(C, NumDays)
    #RSI = C
    HH = []
    LL = []
    K0 = []
    D = []
    ## HH, LL, K0
    while True:
        if RSI[0]==None:
            HH.append(None)
            LL.append(None)
            K0.append(None)
            RSI.pop(0)
        else:
            break            
    for i in range(len(RSI)):
        if i<NumDays-1:
            HH.append(None)
            LL.append(None)
            K0.append(None)
        else:
            hh = max(RSI[i-NumDays+1:i+1])
            ll = min(RSI[i-NumDays+1:i+1])            
            HH.append(hh)
            LL.append(ll)
            k = 0
            if hh-ll!=0:
                k = (RSI[i]-ll) / (hh-ll) * 100.0
            K0.append(k)
    ## K3,D3
    K = CalcSMA(K0, KDays)
    D = CalcSMA(K, DDays)    
    return K, D

   
def CalcMACD(C, NumDay12=12, NumDay26=26, NumDaySig=9):
    EMA12 = CalcEMA(C, NumDay12)
    EMA26 = CalcEMA(C, NumDay26)
    ## calc MACD line
    MACDLine = []
    for i in range(len(C)):
        if EMA12[i]==None or EMA26[i]==None:
            MACDLine.append(None)
        else:
            MACDLine.append(EMA12[i]-EMA26[i])
    SigLine = CalcEMA(MACDLine, NumDaySig)
    ## calc MACD histogram
    MACDHist = []
    for i in range(len(C)):
        if MACDLine[i]==None or SigLine[i]==None:
            MACDHist.append(None)
        else:
            MACDHist.append(MACDLine[i]-SigLine[i])
    return MACDLine, SigLine, MACDHist
    
    
def CalcDerivative(V):
    dV = [None]
    for i in range(1, len(V)):
        if V[i]==None or V[i-1]==None:
            dV.append(None)
        else:
            delta = V[i]-V[i-1]
            dV.append(delta)
    return dV
    
def CalcChg(V,n=1):
    Chg = [None]*len(V)
    if n>0:
        for i in range(n,len(V)):
            if V[i]!=None and V[i-n]!=None:
                Chg[i] = V[i]-V[i-n]
    elif n<0:
        for i in range(len(V)-n):
            if V[i]!=None and V[i-n]!=None:
                Chg[i] = V[i-n]-V[i]
    return Chg

def CalcChgRatio(V,n=1,shift=0):
    ChgRatio = [None]*len(V)
    if n>0:
        for i in range(n,len(V)):
            if V[i]!=None and V[i-n]!=None:
                ChgRatio[i] = V[i]/V[i-n]+shift
    elif n<0:
        for i in range(len(V)-n):
            if V[i]!=None and V[i-n]!=None:
                ChgRatio[i] = V[i-n]/V[i]+shift  
    return ChgRatio

def CalcChgRatioOld(V):
    ChgRatio = [None]
    for i in range(1,len(V)):
        if V[i]==None or V[i-1]==None:
            ChgRatio.append(None)
        else:
            ChgRatio.append(V[i]/V[i-1])
    return ChgRatio
    
def CalcVelPerc(V):
    dV = [None]
    for i in range(1, len(V)):
        if V[i]==None or V[i-1]==None:
            dV.append(None)
        else:
            delta = V[i]-V[i-1]
            dV.append(delta/V[i])
    return dV

def CalcChgPerc(V):
    return CalcVelPerc(V)
    
def CalcAbs(V):
    r = FillList(len(V),None)
    for i in range(len(V)):
        if V[i]!=None:
            r[i] = abs(V[i])
    return r

def CalcTrendVolatility(V, pos, period):
    dV = CalcVelPerc(V)
    if pos-period+1<0 or dV[pos-period+1]==None:
        return 0,0
    trend = 0
    vola = 0
    for i in range(pos-period+1,pos+1):
        trend = trend + dV[i]
        vola = vola + abs(dV[i])
    trend = trend / period
    vola = trend / vola
    return trend, vol        
        
def CalcPCI(V, period):    
    PCI = FillList(len(V),None)
    step = period - 1
    nononepos = CheckNoNonePosMultiCol([V])
    for i in range(nononepos+step,len(V)):        
        slope = (V[i]-V[i-step])/step
        intercept = V[i-step]                
        sum_abs_del = 0
        sum_pos_del = 0
        for x in range(1,step):
            pos = i - step + x
            y = intercept + slope * x
            d = V[pos] - y
            sum_abs_del = sum_abs_del + abs(d)
            if d > 0:
                sum_pos_del = sum_pos_del + d
        pci = sum_pos_del / sum_abs_del * 100
        PCI[i] = pci
    return PCI

    
def CalcMomentum(V, period, convert_perc=False):
    M = FillList(len(V),None)
    for i in range(len(V)):
        p2 = i
        p1 = i - period
        if p1<0:
            continue
        v1 = V[p1]
        v2 = V[p2]
        if v1==None or v2==None:
            continue
        m = v2 - v1
        if convert_perc:
            m = m / v2
        M[i] = m
    return M

def MomentumScoreList(V, period):
    M = FillList(len(V),None)
    startpos = 0
    for i in range(len(V)):
        if V[i]!=None:
            startpos = i
            break
    startpos = startpos + period
    for i in range(startpos,len(V)):
        momscore = 0
        for j in range(i-period, i):            
            if V[j]<V[i]:
                momscore = momscore + 1
        M[i] = momscore
    return M        

def CalcBeta(Cref, Ctest, startpos, endpos):
    # Cref-ref, Ctest-test sample
    C1chgperc = CalcChgPerc(Cref)
    C2chgperc = CalcChgPerc(Ctest)
    avgC1chgperc = CalcAvg(C1chgperc[startpos:endpos+1])
    avgC2chgperc = CalcAvg(C2chgperc[startpos:endpos+1])
    stdevC1chgperc = CalcStdev(C1chgperc[startpos:endpos+1])
    stdevC2chgperc = CalcStdev(C2chgperc[startpos:endpos+1])
    Covar = []
    for i in range(startpos,endpos):        
        r = (C1chgperc[i]-avgC1chgperc) * (C2chgperc[i]-avgC2chgperc)
        Covar.append(r)
    avgCovar = CalcAvg(Covar)
    corrC1C2 = avgCovar / (stdevC1chgperc * stdevC2chgperc)
    beta = stdevC2chgperc * corrC1C2 / stdevC1chgperc
    return beta
    

def CalcBetaVariability(Cref, Ctest, startpos, endpos):
    # Cref-ref, Ctest-test sample
    Crefchgperc = CalcChgPerc(Cref)
    Ctestchgperc = CalcChgPerc(Ctest)
    avgCrefchgperc = CalcAvg(Crefchgperc[startpos:endpos+1])
    avgCtestchgperc = CalcAvg(Ctestchgperc[startpos:endpos+1])
    stdevCrefchgperc = CalcStdev(Crefchgperc[startpos:endpos+1])
    stdevCtestchgperc = CalcStdev(Ctestchgperc[startpos:endpos+1])
    Covar = []
    for i in range(startpos,endpos+1):
        r = (Crefchgperc[i]-avgCrefchgperc) * (Ctestchgperc[i]-avgCtestchgperc)
        Covar.append(r)
    avgCovar = CalcAvg(Covar)
    corrCrefCtest = avgCovar / (stdevCrefchgperc * stdevCtestchgperc)
    beta = stdevCtestchgperc * corrCrefCtest / stdevCrefchgperc
    return beta, stdevCtestchgperc
    

def CalcFractalEfficiency(C, testpos, period):
    abstotalchg = abs(C[testpos] - C[testpos-period])
    abschgsum = 0
    for i in range(1,period+1):
        abschgsum = abschgsum + abs(C[testpos-i+1]-C[testpos-i])        
    fractalefficiency = abstotalchg / abschgsum
    return fractalefficiency

    
def CalcMomentumScore(C, testpos, period, average=True, lossscore=0):
    momscore = 0
    if not average:
        if C[testpos]>=C[testpos-period]:
            momscore = 1
        else:
            momscore = lossscore
    else:
        for i in range(1,period+1):
            if C[testpos]>=C[testpos-i]:
                momscore += 1
            else:
                momscore += lossscore
    if momscore < 0:
        momscore = 0
    return momscore
    
def CalcMomentumScoreList(C, period, lossscore=0):
    MOSC = [None]*len(C)
    for i in range(period,len(C)):
         MOSC[i] = CalcMomentumScore(C, i, period, True, lossscore)
    return MOSC


def CalcDrawDown(C):
    DD = [0]
    for i in range(1,len(C)):
        dd = C[i]/max(C[0:i]) - 1
        DD.append(dd)
    return DD
    
def CalcMaxDrawDown(C):
    DD = CalcDrawDown(C)
    mdd = min(DD)
    return mdd
        
def ConvertToBinary(V, negative=0):
    B = FillList(len(V),None)
    for i in range(len(V)):
        v = V[i]
        if v!=None:
            if v>0:
                B[i] = 1
            else:
                B[i] = negative
    return B
    
#~ def CalcAverage(V, checkpos, numpts):
    #~ V1 = V[checkpos-numpts+1:checkpos+1]
    #~ return sum(V1)/numpts    

def AvgStdev(V):
    n = len(V)
    avg = sum(V)/n
    sumdevsq = 0
    for i in range(n):
        dev = V[i]-avg
        devsq = dev ** 2
        sumdevsq += devsq
    stdev = (sumdevsq / n) ** 0.5
    return avg,stdev
    
def CalcVolatilityList(C, period):
    n = len(C)
    VOLATILITY = [None] * n
    for i in range(period-1, n):
        if C[i-period+1] != None:
            avg,stdev = AvgStdev(C[i-period+1:i+1])
            VOLATILITY[i] = stdev
    return VOLATILITY   
    

    
def CalcNoise(O,H,L,C):
    N = [None]*len(C)
    for i in range(len(C)):
        o,h,l,c = O[i],H[i],L[i],C[i]
        if h-l==0:
            n = 1
        else:
            n = 1 - abs((c-o)/(h-l))
        N[i] = n
    return N
    
    
def CalcVariability(H,L,C):
    V = [None]*len(C)
    for i in range(len(C)):
        h,l,c = H[i],L[i],C[i]
        v = (h-l)/c
        V[i] = v
    return V
    

#~ def CalcStdevPerc(C, period):
    #~ MA = CalcSMA(C, period)
    #~ V = [None] * len(C)
    #~ for i in range(2*period-2,len(MA)):
        #~ sumdevsq = 0
        #~ for j in range(i-period+1,i+1):
            #~ dev = C[j]-MA[j]
            #~ devsq = dev**2
            #~ sumdevsq += devsq
            #~ #print(i,dev,devsq)
        #~ stdev = sumdevsq ** 0.5 / period
        #~ V[i] = stdev / MA[i]               
    #~ return V
    
    
#~ def CalcVolatilityPerc(C, period):
    #~ PF = [None]*len(C)
    #~ for i in range(1,len(C)):
        #~ PF[i] = C[i]/C[i-1]-1
    #~ MEAN = [None]*len(C)
    #~ for i in range(period,len(C)):
        #~ mean = sum(PF[i-period+1:i+1])/period
        #~ MEAN[i] = mean
    #~ V = [None]*len(C)
    #~ for i in range(2*period,len(C)):
        #~ sumdevsq = 0
        #~ for j in range(i-period+1,i+1):
            #~ dev = PF[j]-MEAN[j]
            #~ devsq = dev**2
            #~ sumdevsq += devsq
        #~ stdev = sumdevsq ** 0.5 / period
        #~ V[i] = stdev
    #~ return V
    
def ListMultiply(L1, L2):
    R = FillList(len(L1),None)
    for i in range(len(L1)):
        l1 = L1[i]
        l2 = L2[i]
        if l1==None or l2==None:
            continue
        else:
            R[i] = l1 * l2
    return R
    
        
def ListDivide(L1, L2):
    R = FillList(len(L1),None)
    for i in range(len(L1)):
        l1 = L1[i]
        l2 = L2[i]
        if l1==None or l2==None:
            continue
        else:
            R[i] = l1 / l2
    return R
    
    
def ConvertMultistepData(Y,O,H,L,C,V, nstep, start=0):
    Y1,O1,H1,L1,C1,V1 = [],[],[],[],[],[]
    for i in range(start,len(Y),nstep):
        p1=i+nstep
        if p1>len(Y):
            p1=len(Y)
        Y1.append(Y[i])
        O1.append(O[i])
        C1.append(C[p1-1])
        V1.append(sum(V[i:p1]))
        H1.append(max(H[i:p1]))
        L1.append(min(L[i:p1]))
    return Y1,O1,H1,L1,C1,V1

            
### Utility functions #########################################

def ReportErrorExit(msg):
    print(msg)
    input('')
    exit()


def ErrorLog(errmsg, logfilename='err.log', writemode='a'):
    f=open(logfilename,writemode)
    f.write(errmsg+'\n')
    f.close()
    

def InRange(v, v1, v2):
    if v>=v1 and v<=v2:
        return True
    else:
        return False
    
        
def CheckNoNonePosMultiCol(ListOfLists):
    pos = -1
    for L in ListOfLists:
        for i in range(len(L)):
            if L[i]!=None:
                if i > pos:
                    pos = i
                break
    return pos
    

def FindNoNonePosMultiCol(ListOfLists):
    return CheckNoNonePosMultiCol(ListOfLists)
    

    
def FillList(N, data):
    retlist = []
    for i in range(N):
        retlist.append(data)
    return retlist
    

def PrintFileCon(msg, fp=None, consolout=True):
    if consolout:
        print(msg)
    if fp!=None:
        fp.write(msg+'\n')


def Write(fp, msg, endl=''):
    msg2 = msg + endl
    if fp==0:
        sys.stdout.write(msg2)
    else:
        fp.write(msg2)
        

def WriteLn(fp, msg):
    Write(fp, msg, '\n')
     


def PrintFormattedList(vlist, format="%.2f", startnum=1):
    for i,v in enumerate(vlist):
        if v==None:
            msg = '%s %s' % (i+startnum, "None")
            print(msg) 
        else:
            msg = '%s %s' % (i+startnum, (format % (v)))
            print(msg)

def ReportPrint(filename, header, startpos, endpos, datalists, formatlist, separator=' ', NoneStr=' '): 
    fmt2 = '%.2f'
    f = open(filename, 'wt')
    f.write(header + '\n')
    for ir in range(startpos, endpos+1):
        outstr = ''
        for ic in range(len(datalists)):
            v = datalists[ic][ir]
            if v==None:
                outstr = outstr + NoneStr
            else:
                fmt = formatlist[ic]
                if fmt=='':
                    fmt = fmt2
                s = fmt % (v)
                outstr = outstr + s
            outstr = outstr + separator
        f.write(outstr + '\n')
    f.close()    


def FindMinPos(vlist, startpos, endpos):
    minv,minp = find_min_pos(vlist, startpos, endpos)
    return minv, minp
    
    
def FindMaxPos(vlist, startpos, endpos):
    maxv, maxp = find_max_pos(vlist, startpos, endpos)
    return maxv, maxp
    

def WaitEnter(msg):
    a = wait_enter(msg)
    return a
    
def Wait(sec):
    t1 = time.time()
    while time.time()-t1 < sec:
        pass  
            
def SendEmail(mygoogleid, mygooglepw, sendtoemail, msg):    
    try:
        server = smtplib.SMTP('smtp.gmail.com',587)
        server.ehlo()
        server.starttls()
        server.login(mygoogleid,mygooglepw)
        server.sendmail(mygoogleid, sendtoemail, msg)
        server.quit()
        print('successfully sent mail to'+sendtoemail)
    except:
        print('failed sending email')
    
def SendText(mygoogleid, mygooglepw, sendto_attphonenumber, msg):
    sendtoemail = sendto_attphonenumber + '@mms.att.net'
    SendEmail(mygoogleid, mygooglepw, sendtoemail, msg)
    
    
def CheckGXDX(L1,L2,pos):
    ret = 0
    if L1[pos-1]<=L2[pos-1] and L1[pos]>L2[pos]: # GC
        ret = 1
    if L1[pos-1]>L2[pos-1] and L1[pos]<=L2[pos]: # DC
        ret = -1
    return ret

def CheckPeak(L,pos,checkafter=True):
    ret = 0
    if checkafter:
        pos = pos - 1
    if L[pos-1]<L[pos] and L[pos]>L[pos+1]:  #  1 : /\
        ret = 1 
    if L[pos-1]>L[pos] and L[pos]<L[pos+1]:  # -1 : \/
        ret = -1
    if L[pos-1]<L[pos] and L[pos]<L[pos+1]:  #  2 : //         
        ret = 2 
    if L[pos-1]>L[pos] and L[pos]>L[pos+1]:  # -2 : \\        
        ret = -2 
    return ret
    
# -----------------------------------------------------------------------------

def find_min_pos_org(vlist, startpos, endpos):
    #~ endpos = min(endpos, len(vlist)-1)
    minv = vlist[startpos]
    minp = startpos
    for i in range(startpos+1,endpos+1):
        if vlist[i]<minv:
            minp = i
            minv = vlist[i]
    return minv, minp

def find_max_pos_org(vlist, startpos, endpos):
    #~ endpos = min(endpos, len(vlist)-1)
    maxv = vlist[startpos]
    maxp = startpos
    for i in range(startpos+1,endpos+1):
        if vlist[i]>maxv:
            maxp = i
            maxv = vlist[i]
    return maxv, maxp

def find_min_pos(vlist, startpos=0, endpos=-1):
    if endpos==-1:
        endpos = len(vlist) - 1
    minv = vlist[endpos]
    minp = endpos
    for i in range(endpos-1,-1,-1):
        v = vlist[i]
        if v==None:
            continue
        if vlist[i]<minv:
            minp = i
            minv = vlist[i]
    return minv, minp

def find_max_pos(vlist, startpos=0, endpos=-1):
    if endpos==-1:
        endpos = len(vlist) - 1
    maxv = vlist[endpos]
    maxp = endpos
    for i in range(endpos-1,-1,-1):
        v = vlist[i]
        if v==None:
            continue
        if vlist[i]>maxv:
            maxp = i
            maxv = vlist[i]
    return maxv, maxp

def linear_interpolate(x1,y1,x2,y2,x):
    a = 1.0*(y2-y1)/(x2-x1)
    b = y1-a*x1
    y = a*x + b
    return y
    
# window = x1,y1,x2,y2 : rectangular box, no matter bitmap or graph coordinates
def convert_coord(window1, window2, x,y):    
    bx1,by1,bx2,by2 = window1
    wx1,wy1,wx2,wy2 = window2
    wx = linear_interpolate(bx1,wx1,bx2,wx2, x)    
    wy = linear_interpolate(by1,wy2,by2,wy1, y)    
    return wx,wy


def copy_lists(LoL):  # LoL - list of lists
    A = []
    for l in LoL:
        A.append(list(l))
    return A    
    

def init_parameters(readoption='symbol,startdate,enddate,dwm,fromfile'):
    
    symbollist=[]
    startdate=0
    enddate=99999999
    dwm='m'
    fromfile=True

    if readoption.find('symbol')!=-1:
        df = input_def('symbol list, direct input or read from symbol list file (d/f) ?', 'd')
        if df=='d':
            s = input_def('input symbols separated by space character', '')
            symbollist = s.split()
        elif df=='f':
            filename = input_def('input symbol list file name', '')
            try:
                symbollist = open(filename).read().split(endl)
                while symbollist[-1]=='': symbollist.pop(-1)
                for i in range(len(symbollist)-1,-1,-1):
                    if symbollist[i][0:1]=='#':
                        symbollist.pop(i)
            except Exception  as inst:
                print('error: symbollist file reading')
                wait_enter()
                exit()
        else:
            print('must input d or f')
            wait_enter()
            exit()

    if readoption.find('startdate')!=-1:
        startdate = input_def('start date', 0)
        
    if readoption.find('enddate')!=-1:
        enddate = input_def('end date (<0, latest date will be chosen)', -1)
        if enddate<0:
            enddate = 99999999

    if readoption.find('dwm')!=-1:
        dwm = input_def('chart type - day or week or month (d/w/m)', 'm')
        
    if readoption.find('fromfile')!=-1:
        fromfile = (input_def('raw data from file or internet? (f/i)', 'f')=='f')

    print(endl)
   
    return symbollist, startdate, enddate, dwm, fromfile


def csv_format(fmt, datalist, separator=','):
    fmtlist = fmt.split(separator)
    if fmtlist[-1]=='':
        fmtlist.pop(-1)
    msg = ''
    for i, f in enumerate(fmtlist):
        dat = datalist[i]
        if dat == None:
            msg = msg + separator
        else:
            msg = msg + (f % (dat)) + separator
    return msg
    
    
def wait_enter(msg = 'press enter'):
    print(endl+endl)
    a = input(msg)


def input_def(msg = '', defval = ''):
    msg1 = '%s [%s] ' % (msg, defval)
    a = input(msg1)
    if a=='':
        return defval
    else:
        deftype = type(defval)
        return deftype(a)
            

def range2(start,end,step):
    ret = []
    if start<end:
        x = start
        while x<=end:
            ret.append(x)
            x += step
    else:
        x = start
        while x>=end:
            ret.append(x)
            x += step
    return ret
    

def print2(fp, *args):
    msg = ''
    for s in args:
        msg = msg + '%s ' % (s)
    msg = msg.strip()
    if fp!=None:
        fp.write(msg + endl)
    print(msg)
    

def print1(fp, *args):
    msg = ''
    for s in args:
        msg = msg + '%s ' % (s)
    msg = msg.strip()
    if fp==None or fp=='con':
        print(msg)
    else:
        fp.write(msg + endl)

    
def file_exist(path_filen):
    f = Path(path_file)
    if f.is_file():
        return True
    else:
        return False
        
        
        


if __name__ == '__main__':
    pass
