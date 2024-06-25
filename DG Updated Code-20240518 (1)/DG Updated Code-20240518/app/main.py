from Imports import *
from IOT_Message import *
import Variables
from IOT_functions import *
from BMS_functions import *
from Automation_functions import *

api1_downloaded = False   #Global variable to track api1 data downloaded
api2_downloaded  = False  #Global variable to track api2 data downloaded
# is_data_downloaded = False



async def load_BatAh():
    try:
        with open('data/id.txt','r') as idf:
            Variables.id = idf.readline()
            print(datetime.now(), ' IOT Id Loaded ',Variables.id+'\n')
        idf.close()

        with open('BatteryAhData.csv',newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if float(row['IOT']) == float(Variables.id):
                    print("True")
                    Variables.BB_Ahr_rating = float(row['Ah'])
                    
                    Variables.battery_capacity = float(row['Capacity'])
                    Variables.cell_in_series = float(row['CellInSeries'])
                    break
        print(datetime.now(), ' Battery Data Loaded \n')        
        csvfile.close()
    except:
        print("Unable to load Battery Data \n")

async def fetch_country_code():
    try:
        with open('data/country_code.txt','r') as f:
            Variables.country_code = f.readline().strip()
        f.close()
        print("Outside file read Country Code: ", Variables.country_code)
        if Variables.country_code=='IN':
            Variables.local_time = datetime.now()+timedelta(hours=5,minutes=30)
        elif Variables.country_code=='NG':
            Variables.local_time = datetime.now()+timedelta(hours=1,minutes=0)
    except:
        print("Unable to fetch country code \n")

async def fetch_forecast_values(line_number):
    global api1_downloaded
    global api2_downloaded
    if line_number==1:
      is_data_downloaded = api1_downloaded
    elif line_number==2:
      is_data_downloaded = api2_downloaded

    local_time = Variables.local_time.replace(second=0,microsecond=0)
    t1 = local_time.replace(hour=Variables.t1_hour, minute=Variables.t1_minute, second=0, microsecond=0)
    t1_upper_limit = t1+timedelta(minutes=Variables.range_of_time)
    t2= local_time.replace(hour=Variables.t2_hour, minute=Variables.t2_minute, second=0, microsecond=0)
    t2_upper_limit = t2+timedelta(minutes=Variables.range_of_time)
    print("Inside fetch_forecast_value")

    if ((local_time>=t1 and local_time<=t1_upper_limit) or (local_time>=t2 and local_time<=t2_upper_limit)) and is_data_downloaded==False:
        i=3
        for i in range(3):
            try:
                with open('data/id.txt','r') as idf:
                    Variables.id = idf.readline()
                idf.close()
                
                device_ID = 'Husk-IOT-'
                if Variables.country_code=='IN':
                    device_ID+='B'
                elif Variables.country_code=='NG':
                    device_ID+='N'

                zeroes = 5-len(str(int(Variables.id)))
                device_ID = device_ID + '0'*zeroes + str(int(Variables.id))
                print("Device_ID:", device_ID)

                if line_number==1:
                  api = Variables.forecast_api+'api/Solcast/GetPVForcastDetailsByConnectionId'
                  key = 'pv_power_rooftop'
                elif line_number==2:
                  api = Variables.forecast_api+'api/Solcast/GetLoadForcastDetailsByConnectionId'
                  key = 'totalPowerConsumed_KWh_Predicted'

                params = {
                    'contryCode': Variables.country_code,
                    'connectionDeviceId':device_ID,
                    'date': local_time
                }

                response = requests.get(api, params=params)
                print(response)
                data = response.json()
                print(response)
                if len(data)<23:
                    continue

                lst = []
                for item in data:
                    lst.append(str(item[key]))
                lst = ','.join(lst)

                with open('data/Forecasted_values', 'r') as f:
                    lines = f.readlines()

                with open('data/Forecasted_values', "w") as f:
                  if line_number==1:
                    f.writelines(lst+'\n'+lines[1])
                  elif line_number==2:
                    f.writelines(lines[0]+'\n'+lst)

                f.close()

                if line_number==1:
                  api1_downloaded=True
                elif line_number==2:
                  api2_downloaded=True

                break
            except:
                print("Unable to update Forcasted Values \n")
        #time.sleep(60*15)   # delay of 15 minutes

    elif (local_time<t1 and local_time>t1_upper_limit) and (local_time<t2 and local_time>t2_upper_limit):
        # If local time is out of range then set Variables.is_data_downloaded to False
        if line_number==1:
          api1_downloaded=False
        elif line_number==2:
          api2_downloaded=False

        
async def load_forcast_values():
    try:
        if not os.path.exists('data/Forecasted_values'):
            S_Avg = [0.000,0.000,0.000,0.000,0.000,0.000,0.013,0.696,2.738,5.622,8.765,11.589,
                     13.120,12.279,9.363,4.678,1.110,0.007,0.000,0.000,0.000,0.000,0.000,0.000]
            L_Avg = [0.898,0.849,0.828,0.818,1.651,4.921,7.490,8.544,5.702,6.192,11.326,11.501,
                     11.015,8.330,11.665,11.165,9.531,7.257,5.341,3.402,1.562,1.074,0.954,0.899]
            S_Avg = ",".join(map(str, S_Avg))
            L_Avg = ",".join(map(str, L_Avg))

            with open('data/Forecasted_values', 'w') as file:
                file.writelines(S_Avg + '\n' + L_Avg)
                print("Forcasted Values file Created.")
            file.close()

        else:
            with open('data/Forecasted_values', 'r') as f:
                lines = f.readlines()
            Variables.S_Avg += [ float(i) for i in lines[0].split(",") ]   #size = 1x24, Hourly Solar Average 15 Days
            Variables.L_Avg += [ float(i) for i in lines[1].split(",") ]   #size = 1x24, Hourly Load  Average 15 Days
            f.close()
    except:
        print("Unable to Load Forcasted Values \n")

async def plant_constants():
    try:
        if not os.path.exists('data/plant_constants'):
            dfaultConstants = ['DG_max,21', 'reserve_SOC_percentage,50','t_min_minutes_const,600',
                               'k,0.5','curr_soc,55','dg_power_min,8','LoadMin,4','LoadMax,15','NoDGMin,4',
                               'NoDGMax,8','SCalcutionTimeMin,18','SCalcutionTimeMax,8','MinBatteryV,235',
                               't1_hour,6','t1_minute,15','t2_hour,12','t2_minute,15','range_of_time,30',
                               'forecast_api,https://husk3pawrappers-dev.azurewebsites.net/']
            with open('data/plant_constants', 'w') as file:
                for item in dfaultConstants:
                    file.writelines(item+'\n') 
            print("PlantConstant Values file Created.")
            file.close()
            
        else:         
            with open('data/plant_constants', 'r') as pc:                       #Plant Constants
                lines = pc.readlines()
            print(lines)
            Variables.DG_max =              float(lines[0].split(",")[1])
            Variables.day_percentage =      float(lines[1].split(",")[1])
            Variables.t_min_minutes_const = float(lines[2].split(",")[1])
            Variables.k =                   float(lines[3].split(",")[1])
            Variables.curr_soc=             float(lines[4].split(",")[1])
            Variables.dg_power_min=         float(lines[5].split(",")[1])
            Variables.LoadMin=              float(lines[6].split(",")[1])
            Variables.LoadMax=              float(lines[7].split(",")[1])
            Variables.NoDGMin=              float(lines[8].split(",")[1])
            Variables.NoDGMax=              float(lines[9].split(",")[1])
            Variables.SCalcutionTimeMin=    float(lines[10].split(",")[1])
            Variables.SCalcutionTimeMax=    float(lines[11].split(",")[1])
            Variables.MinBatteryV=          float(lines[12].split(",")[1])
            Variables.t1_hour=              int(lines[13].split(",")[1])
            Variables.t1_minute=            int(lines[14].split(",")[1])
            Variables.t2_hour=              int(lines[15].split(",")[1])
            Variables.t2_minute=            int(lines[16].split(",")[1])
            Variables.range_of_time=        int(lines[17].split(",")[1])
            Variables.forecast_api=         lines[18].split(",")[1].strip()
            pc.close()
        
    except Exception as e:
         print('Unable to load Plants Constant', e, '\n')
         raise

async def main():
    module_client = IoTHubModuleClient.create_from_edge_environment()
    await module_client.connect()

    #Initializing the Constants
    Variables.init()
    await fetch_country_code()  
    await plant_constants()
    await load_BatAh()
    await fetch_forecast_values(1)    #passing line number as argument
    await fetch_forecast_values(2)
    await load_forcast_values()

    #Create reset_parameter.txt if not available
    if not os.path.exists('data/reset_parameter.txt'):
        with open('data/reset_parameter.txt', 'w') as file:
            print("Reset Parameter file Created.")
        file.close()
    
    num_avg_hr =        2
    count_soc_for_avg = num_avg_hr*6
    soc_queue =         [float("NaN")]*count_soc_for_avg
    soc_queue_i =       0                                                    # Current index for soc_queue
    Load_power =        []                                                   # Total Load power of all three phases R, Y and B
    reset_parameter =   []
    IS_RESTART =        True

    while True:
        try:
            print("Before asyncio.wait_for")
            await asyncio.wait_for(get_message(module_client), timeout=300)                 # Getting Data from IOT Devices for a period of 10 minutes
        except asyncio.TimeoutError:
            print(datetime.now(),' Timeout!\n')
        
        await fetch_forecast_values(1)
        await fetch_forecast_values(2)
        await load_forcast_values()
        print("After load_forecast_values")

        if(len(Variables.Load_powerR)>0 and len(Variables.Load_powerY)>0 and len(Variables.Load_powerB)>0):
            Load_power = [x + y + z for (x, y, z) in zip(Variables.Load_powerR, Variables.Load_powerY, Variables.Load_powerB)]
        
        try:
            if all([len(i)!=0 for i in [Variables.Voltage, Variables.Dg_power, Variables.DG_OF, Variables.ChargeAhr, Variables.DisChargeAhr, Load_power, Variables.Solar_power, Variables.Current]]):

                if max(Variables.ChargeAhr)-min(Variables.ChargeAhr)<=40 and max(Variables.DisChargeAhr)-min(Variables.DisChargeAhr)<=40:
                    
                    if IS_RESTART == True:
                        if (os.stat("data/reset_parameter.txt").st_size == 0):
                            print(datetime.now(), 'Starting program with initial conditions and SOC = 55\n')
                            Variables.IOT_restart_status = 0

                        else:
                            with open('data/reset_parameter.txt', 'r') as filehandle:
                                for line in filehandle:
                                    currentPlace = line[:-1]
                                    reset_parameter.append(currentPlace)
                            
                            if len(reset_parameter) > 0:
                                old_time, old_soc, charge_ah_old, discharge_ah_old = reset_parameter[0:4]
                                time_diff = Variables.local_time - datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S")
                                total_time_diff = divmod(time_diff.total_seconds(), 3600)
                                filehandle.close()
                                
                                if  total_time_diff[0] < 24:
                                    print(datetime.now(), 'Starting program with reference to old conditions\n')
                                    Variables.curr_soc = calc_ah_soc_on_restart(float(Variables.ChargeAhr[-1]),float(charge_ah_old),float(Variables.DisChargeAhr[-1]),float(discharge_ah_old),float(old_soc))
                                    Variables.IOT_restart_status = 1
                                
                                else:
                                    print(datetime.now(), 'No update done as the values are older than 24 Hours\n')
                                    Variables.curr_soc = 55
                                    Variables.IOT_restart_status = 2
                    
                    print(reset_parameter,IS_RESTART)
                    update_state(Variables.Dg_power[-1],Variables.DG_OF[-1])
                    print(datetime.now(), "DG Status ->"  , Variables.DG_running_status,'\n')
                    
                    vol_soc_out = BMS_get_SOC(Variables.Voltage,Variables.Current)
                    print(datetime.now(), "SOC Index ->"  , soc_queue_i, '\n')
                    
                    soc_queue[soc_queue_i]=vol_soc_out
                    soc_queue_i += 1
                    soc_queue_i %= count_soc_for_avg
                    print(datetime.now(), "SOC Index ->"  , soc_queue_i, '\n')
                    
                    vol_soc_out_final =final_vol_soc(vol_soc_out,soc_queue,count_soc_for_avg)
                    soc_ah=get_AH_soc(Variables.ChargeAhr,Variables.DisChargeAhr)
                    t = Variables.local_time.hour

                    print(datetime.now(), 'Soc queue ->', ','.join(str(i) for i in soc_queue), '\n')
                     
                    Variables.curr_soc=final_soc(t,vol_soc_out_final,soc_ah,Variables.curr_soc)
                    print(datetime.now(), "Final SOC->", Variables.curr_soc, '\n')
                    
                    SOC_live=Variables.curr_soc

                    print("\n","Total Solar Power = ",Variables.Solar_power[-1],"\n")
                    
                    Vbat = sum(Variables.Voltage[-5:])/len(Variables.Voltage[-5:])  #averaging 5 latest values
                    automation_output(Variables.Solar_power[-1],Load_power[-1],Variables.Dg_power[-1],SOC_live,Variables.DG_OF[-1],Vbat)
                    end_logic = timer()
                    await send_message_to_cloud(module_client,SOC_live)  
                    IS_RESTART = False
                    
                    reset_parameter.append(Variables.local_time.strftime("%Y-%m-%d %H:%M:%S"))
                    reset_parameter.append(Variables.curr_soc)
                    reset_parameter.append(Variables.ChargeAhr[-1])
                    reset_parameter.append(Variables.DisChargeAhr[-1])
                    
                    with open('data/reset_parameter.txt', 'r+') as filehandl:
                        filehandl.seek(0)
                        filehandl.truncate(0)
                        for listitem in reset_parameter:
                            filehandl.write('%s\n' % listitem)
                    filehandl.close()
                    reset_parameter.clear()
                else:
                    IS_RESTART = True
                    Variables.IOT_restart_status = -1
                    print(datetime.now(), 'Ahr out of range..Restarting the loop\n')
                                    
            Variables.Voltage.clear()
            Variables.Current.clear()
            Variables.ChargeAhr.clear()
            Variables.DisChargeAhr.clear()
            Variables.SourceTime.clear()
            dg_timer = timer()
            Variables.Solar_power.clear()
            Variables.Dg_power.clear()
            Variables.Load_powerR.clear()
            Variables.Load_powerY.clear()
            Variables.Load_powerB.clear()
        
        except Exception as e:
            print('Unexpected error', e,'\n')
            raise

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()