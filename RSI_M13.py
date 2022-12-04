import SmoresStockLib52e as ss
import calendar


datadir = './' 
ss.SetDB(datadir, 'newyahoo')

symbol = 'QQQ'
Y,O,H,L,C,V  = ss.read_newyahoo(symbol)
# print(Y)

RSI = ss.CalcRSI(C)
# print(RSI)

HOLDSTOCK = []
for i in range(len(RSI)):
    if i < 3:
        HOLDSTOCK.append(0)
        holdstock = 0
    else:
        rsi = RSI[i]
        mom13 = ((RSI[i]-RSI[i-1]) + (RSI[i]-RSI[i-3]))/2

        if rsi < 40: # check buy
            if mom13 > 1:
                if holdstock == 0:
                    holdstock = 1
            else:
                if holdstock == 1:
                    holdstock = 0
        
        elif rsi > 70: # check sell
            if mom13 < 1:
                if holdstock == 1:
                    holdstock = 0
                    
        # else:
            # if mom13 < 1:
                # if holdstock == 1:
                    # holdstock = 0
            
        HOLDSTOCK.append(holdstock)

cbuy,csell,accmprof = 0,0,0

for i in range(1,len(RSI)):
    if HOLDSTOCK[i]==1 and HOLDSTOCK[i-1]==0: # buy
        print('BUY  %d %.2f %.1f' % (Y[i],C[i],RSI[i]))
        cbuy = C[i]
    elif HOLDSTOCK[i]==0 and HOLDSTOCK[i-1]==1: # sell
        csell = C[i]
        profit = csell/cbuy - 1
        accmprof += profit
        print('SELL %d %.2f %.1f  profit=%.2f  accm. profit=%.2f' % (Y[i],C[i],RSI[i],profit,accmprof))
    else:
        print('     %d %.2f %.1f' % (Y[i],C[i],RSI[i]))
    
    # print('%d %.2f %.1f %d' % (Y[i],C[i],RSI[i],HOLDSTOCK[i]))
    


    


'''
inifile = '%s.ini' % (comp)
lastptr = -2

symbollist = open(inifile).read().split()

print('symbol date M136 M1 M3 M6 PrevM136 PrevM1 PrevM3 PrevM6')

for symbol in symbollist:
    try:
        Y,O,H,L,C,V  = ss.read_newyahoo(symbol)
        c0 = C[lastptr]
        c1 = C[lastptr-1]
        c3 = C[lastptr-3]
        c6 = C[lastptr-6]
        m1 = c0/c1
        m3 = c0/c3
        m6 = c0/c6
        m136 = (m1+m3+m6)/3

        pc0 = C[lastptr-1]
        pc1 = C[lastptr-2]
        pc3 = C[lastptr-4]
        pc6 = C[lastptr-7]
        pm1 = pc0/pc1
        pm3 = pc0/pc3
        pm6 = pc0/pc6
        pm136 = (pm1+pm3+pm6)/3


        print(symbol, Y[-1], m136, m1, m3, m6, pm136, pm1, pm3, pm6)
        #~ print(Y[-4],Y[-3],Y[-2],Y[-1])
        
                       
    except:
        #~ print('err: ', symbol)
        pass

        
'''
input()
