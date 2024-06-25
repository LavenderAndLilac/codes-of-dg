from Imports import *
import Variables

def update_state(DG_power,frequency):
    if DG_power>0 or frequency>0:
        if Variables.DG_Timer == False:
            print(datetime.now(), 'DG started, Starting DG timer\n')
            start_timer()
        Variables.DG_running_status = True
        Variables.DG_Timer          = True
    else:
        if Variables.DG_Timer == True:
            print(datetime.now(), 'DG stopped, updating DG_running_status as false\n')
        Variables.DG_running_status = False
        Variables.DG_Timer          = False

def DG_stop(DG_Power,frequency):
    if DG_Power > 0 or frequency > 0:
        print(datetime.now(), 'DG_Timer', Variables.DG_Timer, '\n')
        
        if Variables.DG_Timer == True:
            Variables.dg_timer_value = read_DG_timer()
            print(datetime.now(), 'Dg_timer_value'     , Variables.dg_timer_value     , '\n')
            print(datetime.now(), 't_min_minutes_const', Variables.t_min_minutes_const, '\n')
            
            if Variables.dg_timer_value > Variables.t_min_minutes_const:
                Variables.DG_running_status = False
                os.system('echo "0" > /sys/class/gpio/gpio5/value')
                print('DG stopped as timer is greater than min_minutes')
                stop_timer()
                Variables.DG_db_status = 0

def DG_start(DG_Power,frequency):
    if (DG_Power <= 0 or frequency <= 0):
        Variables.DG_running_status = True
        os.system('echo "1" > /sys/class/gpio/gpio5/value')
        print(str(datetime.now()), 'DG Started.\n')
        start_timer()
        print(str(datetime.now()), 'DG_Timer after start', Variables.DG_Timer, '\n')
    return 0


def start_timer():
    Variables.dg_timer_start = timer()
    Variables.dg_timer_stop  = timer()
    Variables.dg_runtime     = Variables.dg_timer_value
    Variables.dg_timer_value = 0
    Variables.DG_Timer       = True

def stop_timer():
    Variables.dg_timer_start = timer()
    Variables.dg_timer_stop  = timer()
    Variables.dg_runtime     = Variables.dg_timer_value
    Variables.dg_timer_value = 0
    Variables.DG_Timer       = False

def read_DG_timer():
    Variables.dg_timer_stop = timer()
    return(Variables.dg_timer_stop-Variables.dg_timer_start)

def automation_output(Solar_value,Load_value,DG_Power,SOC_live,frequency,Voltage):
    gn = datetime.now()+timedelta(hours = 5,minutes = 30)
    n = gn.hour
    SOC_R = Variables.day_percentage
    print(datetime.now(),'SOC_Live -> ',SOC_live,' SOC_R -> ',SOC_R,'\n')
    if Solar_value > Load_value :
        print(datetime.now(), 'Battery should be charged using solar\n')
        print(datetime.now(), 'DG Stopping as Solar > Load\n')
        DG_stop(DG_Power,frequency)
        Variables.DG_db_status = 0
    elif (DG_Power <= Variables.dg_power_min and Variables.DG_running_status == True):
        print(datetime.now(), "DG Stopping as DG load less than "+ str(Variables.dg_power_min) + " kW"+'\n')
        DG_stop(DG_Power,frequency)
        Variables.DG_db_status = 0
    else:                                                                                  
        if(Voltage < Variables.MinBatteryV):
            DG_start(DG_Power,frequency)
        else:
            if (Load_value <= Variables.LoadMin):
                if (n <= Variables.NoDGMin or n>=Variables.NoDGMax):                 # AND changed to OR 
                    if(SOC_live < SOC_R-15):
                        DG_start(DG_Power,frequency)
                    else:
                        if (SOC_live > SOC_R-5):
                            DG_stop(DG_Power,frequency)
                else:
                    DG_stop(DG_Power,frequency)
            elif(Load_value > Variables.LoadMin and Load_value <= Variables.LoadMax):
                sh_t = 0 
                if(SOC_live >= SOC_R-10):
                    if(n>Variables.SCalcutionTimeMin or n<Variables.SCalcutionTimeMax):
                        print(datetime.now(), "SOC_live greater than SOC_R,calculating shortage\n")
                        Sh_avg = [Variables.S_Avg[i]-Variables.L_Avg[i] / 0.85 for i in range(len(Variables.S_Avg))]  #0.85 Hybrid inverter efficiency 
                        # Get 15 days hourly load, Sh_avg = S_Avg - L_Avg
                        sh_avg_v = 0                                                           
                        j=18 #shortage will be only calculated for night time.

                        while j != 8:
                            j = j%24
                            sh_avg_v = sh_avg_v + Sh_avg[j]
                            j=j+1

                        battery_buffer = (SOC_live-SOC_R)*Variables.battery_capacity/100  / 0.93      # Battery efficiency       
                        sh_t = (battery_buffer + sh_avg_v) / 0.9  # Rectifier + MPPT efficiency
                        print(datetime.now(),"Battery Buffer -> ",battery_buffer," sh_avg_v -> ",sh_avg_v,"\n")
                        sh_rate = 0
                        if Variables.DG_max != 0:
                            sh_rate = sh_t/Variables.DG_max
                        Variables.Sh_rate = sh_rate
                        print(datetime.now()," Sh_t=",sh_t," sh_rate=",sh_rate," k=",Variables.k,'\n')
                
                        if (sh_rate*(-1)< Variables.k):
                            print(datetime.now(), 'Shortage rate fullfilled stopping DG\n')
                            Variables.DG_db_status = 0
                            DG_stop(DG_Power,frequency)
                        else:
                            print(datetime.now(), 'Shortage is greater 30min, hence starting DG\n')
                            DG_start(DG_Power,frequency)
                            Variables.DG_db_status = 1
                    else:
                        DG_stop(DG_Power,frequency)
                else:
                    if(SOC_live < SOC_R-10):
                        DG_start(DG_Power,frequency)
            else:
                if(SOC_live < SOC_R):                       # if load > loadMax
                        DG_start(DG_Power,frequency)
                            

    return 0
