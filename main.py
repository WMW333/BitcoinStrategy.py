import pandas as pd
import pandas_bokeh
import numpy as np
import matplotlib.pyplot as plt
import csv
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
init_notebook_mode(connected=True)
pandas_bokeh.output_notebook()
%matplotlib inline
pd.options.display.max_rows = 99999

def import_file(filename):
    dati = pd.read_csv(r'C:\Users\Arco\Desktop\BTCUSDT_Binance_futures_data_minute_1.csv', parse_dates = ["date"])
    dati.drop(0, inplace=True)
    dati["timestamp"] = pd.to_numeric(dati["unix"])
    dati.sort_values(by=["timestamp"], ascending = True, inplace=True)
    dati.drop(["unix"], axis = 1, inplace=True)
    dati.set_index("date", inplace = True)
    dati.drop(["tradecount::"], axis = 1, inplace=True)
    dati.drop(["timestamp"], axis = 1, inplace=True)
    dati.drop(["symbol"], axis = 1, inplace=True)
    return dati
FILENAME = "BTCUSDT_Binance_futures_data_minute_1.csv"
dati = import_file(FILENAME)

def avgprice(O,C,L,H):
    avg = ((O + C + L + H) / 4)
    return avg
dati["avg"] = avgprice(dati.open, dati.low, dati.close, dati.high)

dati["CloseOpen"] = round((dati.close - dati.open),2)
dati["Color"] = list(map(lambda x: "black" if x <= 0 else "white", dati.CloseOpen))
dati["higher"] = dati.high.rolling(15).max()
dati["lower"] = dati.low.rolling(15).min()
dati['Range'] = round(dati.high - dati.low, 2)
dati['Body'] = abs(dati.open - dati.close,)
dati['CO'] = round(dati.close - dati.open, 2)
dati['OL'] = round(dati.open - dati.low, 2)
dati['HO'] = round(dati.high - dati.open, 2)
dati['LC'] = round(dati.low - dati.close, 2)
dati['HC'] = round(dati.high - dati.close, 2)
dati['BodyPerc'] = (dati.close - dati.open) / dati.close * 100

#ATR
def atr():
    df = pd.concat([dati.Range, dati.HC, dati.LC] , axis = 1)
    TrueRange = np.max(df, axis = 1)
    atr = TrueRange.rolling(14).mean()
    return atr

dati["atr"] = atr()


#Thresholds Spikes,BTC Volums and ATR
SogliaSpikeUp = 0.20       #<----------------------------------------------------
SogliaSpikeDown = - 0.20    #<---------------------------------------------------- 
SogliaVolumi = 1900        #<----------------------------------------------------
SogliaATR = 110            #<----------------------------------------------------


#I'm looking for red candles with large lower spikes or green candles with large upper spikes
SpikeDownBlack = ((((dati.low - dati.close) / dati.close) * 100))
SpikeDownWhite = (((dati.low - dati.open) / dati.open) *100)
dati["spikeDown"] = np.where((dati.Color == "black"), SpikeDownBlack, SpikeDownWhite)

SpikeUpBlack = (((((dati.high - dati.open) / dati.open) * 100)))
SpikeUpWhite =spikeUp = (((((dati.high - dati.close) / dati.close) * 100)))
dati["spikeUp"] = np.where((dati.Color == "black"), SpikeUpBlack, SpikeUpWhite)
                     
#Entry conditions   
dati["SpikeUp_TF"] = np.where((dati.spikeUp.shift(1) > SogliaSpikeUp) & (dati.spikeDown.shift(1) > (-0.04)) & 
                              (dati.spikeUp.shift(1) < (0.59)), 1,0)
dati["SpikeDown_TF"] = np.where((dati.spikeDown.shift(1) <= SogliaSpikeDown) & (dati.spikeUp.shift(1) < 0.04) &
                                (dati.spikeDown.shift(1) > (-0.59)), 1,0)
                               

dati["Volume_TF"] = np.where((dati.VolumeBTC.shift(1) > SogliaVolumi), 1,0)


conditionlist = [
((dati["Volume_TF"] == 1) & (dati["SpikeUp_TF"] == 1) & (dati["BodyPerc"] <= 0.29) & (dati["BodyPerc"] >= -0.1) &
(dati["atr"] < SogliaATR)) , 
((dati["Volume_TF"] == 1) & (dati["SpikeDown_TF"] == 1) & (dati["BodyPerc"] >= -0.29) & (dati["BodyPerc"] <= 0.1) &
(dati["atr"] < SogliaATR)) , 
((dati["Volume_TF"] == 1) & (dati["SpikeDown_TF"] == 1) & (dati["SpikeUp_TF"] == 1))]

choicelist = [2, 1, 0] # 0 = / , 1 = long, 2 = Short
dati["Apri_Posizione"] = np.select(conditionlist, choicelist, default=0)



#Position size
money = 10000 #<----------------------------------------------------
fees = 0.0    #<----------------------------------------------------



dati["stocks"] = (money / dati.open).apply(lambda x: round(x,6)) #Quantity in BTC

dati["entry"] = np.where((dati.Apri_Posizione == 1) | (dati.Apri_Posizione == 2),
                         dati.open, 0)
                    
# "Apri Posizione" == "Open Position"
conditionexit = [
(dati["Apri_Posizione"] == 1), 
(dati["Apri_Posizione"] == 2), 
(dati["Apri_Posizione"] == 0)]  
choiceexit = [????????????] 
dati["exit"] = np.select(conditionexit, choiceexit, default=0)

                        

long = (dati.exit - dati.entry) * dati.stocks
gainLong = np.where((dati.Apri_Posizione == 1), long, 0)
gainshort = ((dati.entry - dati.exit) * dati.stocks)
gainShort = np.where((dati.Apri_Posizione == 2), (gainshort), 0)
Fees = np.where((dati.Apri_Posizione != 0), ((money * fees) / 100), 0)
dati["GainCumNet"] = (gainShort + gainLong) - Fees
dati["equity"] = dati.GainCumNet.cumsum()
dati.tail(300)
