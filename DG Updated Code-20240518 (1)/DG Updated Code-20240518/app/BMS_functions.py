from Imports import *
import Variables

def arange_float(start,stop,step):
    x=[]
    while start<=stop:
        x.append(start)
        start += step
    return x

def BMS_get_SOC(voltage,current):
    soc = float("NaN")
    lt=[]
    lt_vol = arange_float(1.74,2.135,0.005)

    raw = [0,0.012001983,0.016217532,0.020423869,0.023530445,0.027823983,0.030655778,0.034165985,0.038636997,0.048458534,
           0.056813724,0.087538554,0.1,0.121066997,0.134875006,0.152759777,0.176682412,0.218666555]
    
    lt_curr = list(map(lambda x: x * Variables.BB_Ahr_rating, raw))
    
    vol_y        = []
    curr_x       = []
    cell_voltage = []
    vol_soc      = []

    with open('abc.csv', 'r') as f:
        lt = [[float(num) for num in line.split(',')] for line in f if line.strip() != "" ]
    f.close()

    for i in range(len(voltage)):
        cell_voltage.append(voltage[i]/Variables.cell_in_series)
    
    for i in range(len(current)):
        col = 0
        if current[i]>0:
            for j in range(len(lt_curr)):
                if current[i]>lt_curr[j]:
                    col = col+1
            curr_x.append(len(lt_curr)-col-1)
            col = 0
            for j in range(len(lt_vol)):
                if cell_voltage[i]>lt_vol[j]:
                    col = col+1
            vol_y.append(col)

    vol_soc = []
    for i in range(len(curr_x)):
        x=len(lt_vol)-vol_y[i]
        y=curr_x[i]
        if(x>=79):
            x=79
        if(y>=18):
            y=18
        z=lt[y][x]
        vol_soc.append(z)
    if len(vol_soc)>0:
        soc = sum(vol_soc)/len(vol_soc)

    print(datetime.now(), 'CURR ->'   , ','.join(str(i) for i in current)     , '\n')
    print(datetime.now(), 'CURR_X ->' , ','.join(str(i) for i in curr_x)      , '\n')
    print(datetime.now(), 'VOL ->'    , ','.join(str(i) for i in cell_voltage), '\n')
    print(datetime.now(), 'VOL_Y ->'  , ','.join(str(i) for i in vol_y)       , '\n')
    print(datetime.now(), 'VOL_SOC ->', ','.join(str(i) for i in vol_soc)     , '\n')
    print(datetime.now(), 'Calculated SOC ->', soc, '\n')
    return soc

def get_AH_soc(charge_ahr, Discharge_ahr):
    dis_soc                = 0
    dis_ah_first           = 0
    dis_ah_last            = 0
    for i in range(len(Discharge_ahr)):
        if Discharge_ahr[i] != 0:
            dis_ah_first = Discharge_ahr[i]
            break
    for i in range(len(Discharge_ahr)):
        if Discharge_ahr[len(Discharge_ahr)-i-1] != 0:
            dis_ah_last = Discharge_ahr[len(Discharge_ahr)-i-1]
            break

    charge_ah_first = 0
    charge_ah_last  = 0
    for i in range(len(charge_ahr)):
        if charge_ahr[i] != 0:
            charge_ah_first = charge_ahr[i]
            break
    for i in range(len(charge_ahr)):
        if charge_ahr[len(charge_ahr)-i-1] != 0:
            charge_ah_last = charge_ahr[len(charge_ahr)-i-1]
            break

    temp_v = Variables.BB_Ahr_rating*Variables.SoH*Variables.discahrging_efficiency
    if temp_v != 0:
        dis_soc = (dis_ah_last - dis_ah_first)*100/temp_v
    temp_v = Variables.BB_Ahr_rating*Variables.SoH
    
    if temp_v != 0:
        charge_soc = (charge_ah_last - charge_ah_first)*Variables.charging_efficiency*100/temp_v
    final_soc_ah = abs(charge_soc) - abs(dis_soc)
    return final_soc_ah

def final_vol_soc(vol_soc,soc_queue,queue_size):
    global Deviation_percentage_avg
    out_soc = float("NaN")
    avg_soc = float("NaN")

    if queue_size>0:
        avg_soc = sum(soc_queue)/queue_size
    if avg_soc>0:
        x = vol_soc*100/avg_soc
        y = abs(100-x)
        print(datetime.now(), 'percentage off from avg soc->', y, '\n')
        Deviation_percentage_avg = y
        if y < 10:
            out_soc = avg_soc
    return out_soc

def final_soc(t,vol_soc,soc_ah,curr_soc):
    if t in [1,2,3,4,5] and vol_soc > 0:
        print(datetime.now(), 'Applying Correction at', t, '\n')
        curr_soc = vol_soc
        Variables.Correction_Time_hour        = t
        Variables.Correction_Time_hour_status = 1
    else:
        if t in [1,2,3,4,5]:
            print(datetime.now(), 'correction not applied, vol_soc  ->', vol_soc, '\n')
            Variables.Correction_Time_hour_status = 0
        curr_soc = curr_soc + soc_ah

    if curr_soc < 0:
        curr_soc = 0
    if curr_soc > 100:
        curr_soc = 100

    print(datetime.now(), 'updated SOC ->', curr_soc, '\n')
    return curr_soc

def calc_ah_soc_on_restart(c_n,c_o,d_n,d_o,curr_soc):
    discharge_const = Variables.BB_Ahr_rating*Variables.SoH*Variables.discahrging_efficiency
    charge_const = (Variables.BB_Ahr_rating*Variables.SoH)/Variables.charging_efficiency
    if discharge_const !=0 :
        dis_soc = (d_n - d_o)*100/discharge_const
    if charge_const != 0:
        charge_soc = (c_n - c_o)*100/charge_const
    dif_soc_ah = abs(charge_soc) - abs(dis_soc)
    curr_soc = curr_soc + dif_soc_ah
    return curr_soc

async def export_avg_to_file(Avg_type,Avg_value):
    try:
        if Avg_value != "":
            print(datetime.now(), '15 days average data recevied\n')
            with open('Forecasted_values', 'r') as f:
                lines = f.readlines()
                
            if Avg_type == "Solar_Avg":
                lines[0] = Avg_value + "\n"
                print(datetime.now(), 'Updating Solar Average Data.........\n')
            elif Avg_type == "Load_Avg":
                lines[1] = Avg_value + "\n"
                print(datetime.now(), 'Updating Load Average Data.........\n')
            with open('Forecasted_values', 'w') as f:
                f.writelines(lines)
            
            print(datetime.now(), '15 Days Average data Updated..!!\n')
            f.close()
        else:
            print(datetime.now(), 'No Average Data Recevied\n')
                
    except Exception as e:
         print(str(datetime.now()), 'Updating Average Error ', e, '\n')
         raise

async def export_Constant_to_file(Constant_type,Constant_value):
    try:
        if Constant_value != "":
            print(datetime.now(), 'New plant constants values recevied\n')
            with open('plant_constants', 'r') as f:
                lines = f.readlines()
        
            if Constant_type == "battery_capacity":
                lines[0] = Constant_type +","+Constant_value+"\n"
                print(datetime.now(), 'Updating battery_capacity Value.........\n')
            
            elif Constant_type == "BB_Ahr_rating":
                lines[1] = Constant_type +","+Constant_value+"\n"
                print(datetime.now(), 'Updating BB_Ahr_rating Value.........\n')
    
            elif Constant_type == "cell_in_series":
                lines[1] = Constant_type +","+Constant_value+"\n"
                print(datetime.now(), 'Updating cell_in_series Value.........\n')
        
            with open('plant_constants', 'w') as f:
                f.writelines(lines)
            
            print(datetime.now(), 'New plant constants values Updated..!!\n')
            f.close()
        else:
            print(datetime.now(), 'No New plant constants values Recevied\n')
                            
    except Exception as e:
         print(datetime.now(), 'Updating New plant constants values Error', e, '\n')
         raise
