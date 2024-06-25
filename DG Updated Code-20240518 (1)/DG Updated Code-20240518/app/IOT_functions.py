from Imports import *
from IOT_Message import *
import Variables
from BMS_functions import *

async def get_message(module_client):
    global M1P,M2P,M3P;
    M1P=M2P=M3P=0
    loop = asyncio.get_event_loop()
    try:
        if not sys.version >= "3.5.3":
            raise Exception(
                "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version)
        print("IoT Hub Client for Python\n")
        while(True):
            try:
                input_message = await module_client.receive_message_on_input("input1")
                print(datetime.now(), ': Message received\n')
                message = input_message.data
                message_text = message.decode('utf-8')
                data = json.loads(message_text)
                decoded_team = IOTMessage(**json.loads(message))
                for Data in decoded_team.Content:
                    for Values in Data['Data']:
                        for Value in Values['Values']:
                            Variables.Solar_power.append(M1P+M2P+M3P)
                            if Value['DisplayName'] == 'ES-PB-DCV':
                                print(datetime.now(), 'Battery Voltage =', Value['Value'], '\n')
                                Variables.Voltage.append(float(Value['Value']))
                                Variables.SourceTime.append(Values['SourceTimestamp'])

                            elif Value['DisplayName'] == 'ES-PB-DCA':
                                print(datetime.now(), 'Current =', Value['Value'], '\n')
                                Variables.Current.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'PG-S-T':
                                print(datetime.now(), 'DisChargeAhr =', Value['Value'], '\n')
                                Variables.DisChargeAhr.append(float(Value['Value']))
                                
                            elif Value['DisplayName'] == 'PG-S-RH':
                                print(datetime.now(), 'ChargeAhr =', Value['Value'], '\n')
                                Variables.ChargeAhr.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'PG-DD-1P':
                                print(datetime.now(), 'Solar Power M1 =', Value['Value'], '\n')
                                M1P = float(Value['Value'])

                            elif Value['DisplayName'] == 'PG-DD-2P':
                                print(datetime.now(), 'Solar Power M2 =', Value['Value'], '\n')
                                M2P = float(Value['Value'])

                            elif Value['DisplayName'] == 'PG-DD-3P':
                                print(datetime.now(), 'Solar Power M3 =', Value['Value'], '\n')
                                M3P = float(Value['Value'])

                            elif Value['DisplayName'] == 'SG-BIO-P':
                                print(datetime.now(), 'DG Power =', Value['Value'], '\n')
                                Variables.Dg_power.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'SG-BIO-F':
                                print(datetime.now(), 'DG Output Frequency =', Value['Value'], '\n')
                                Variables.DG_OF.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'L-F1-RP':
                                print(datetime.now(), 'Load R power =', Value['Value'], '\n')
                                Variables.Load_powerR.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'L-F1-YP':
                                print(datetime.now(), 'Load Y power =', Value['Value'], '\n')
                                Variables.Load_powerY.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'L-F1-BP':
                                print(datetime.now(), 'Load B power =', Value['Value'], '\n')
                                Variables.Load_powerB.append(float(Value['Value']))

                            elif Value['DisplayName'] == 'Solar_Avg':
                                print(datetime.now(), 'Old Solar Average =', Variables.S_Avg, '\n')
                                Variables.S_Avg.clear()
                                Variables.S_Avg = [float(i) for i in Value['Value'].split(",")[:]]
                                print(datetime.now(), 'New Solar Average =', Variables.S_Avg, '\n')
                                await export_avg_to_file("Solar_Avg",Value['Value'])

                            elif Value['DisplayName'] == 'Load_Avg':
                                print(datetime.now(), 'Old Load Average =', Variables.L_Avg, '\n')
                                Variables.L_Avg.clear()
                                Variables.L_Avg = [float(i) for i in Value['Value'].split(",")[:]]
                                print(datetime.now(), 'New Load Average =', Variables.L_Avg, '\n')
                                await export_avg_to_file("Load_Avg",Value['Value'])

                            elif Value['DisplayName'] == 'cell_in_series':
                                print(datetime.now(), 'Old Cell in series value =', Variables.cell_in_series, '\n')
                                Variables.cell_in_series = None
                                Variables.cell_in_series = float(Value['Value'])
                                print(datetime.now(), 'New Cell in series value =', Variables.cell_in_series, '\n')
                                await export_Constant_to_file("cell_in_series",Value['Value'])

                            elif Value['DisplayName'] == 'BB_Ahr_rating':
                                print(datetime.now(), 'Old BB Ahr rating =', Variables.BB_Ahr_rating, '\n')
                                Variables.BB_Ahr_rating = None
                                Variables.BB_Ahr_rating = float(Value['Value'])
                                print(datetime.now(), 'New BB_Ahr_rating =', Variables.BB_Ahr_rating, '\n')
                                await export_Constant_to_file("BB_Ahr_rating",Value['Value'])

                            elif Value['DisplayName'] == 'battery_capacity':
                                print(datetime.now(), 'Old Battery capacity =', Variables.battery_capacity, '\n')
                                Variables.battery_capacity = None
                                Variables.battery_capacity = float(Value['Value'])
                                print(datetime.now(), 'New Battery capacity =', Variables.battery_capacity, '\n')
                                await export_Constant_to_file("battery_capacity",Value['Value'])
                                
                len_min = min(len(Variables.Voltage), len(Variables.Current))
                Variables.Voltage = Variables.Voltage[0:len_min]
                Variables.Current = Variables.Current[0:len_min]
                
            except Exception as e:
                print('Unexpected error', e, '\n')
                raise

    except Exception as e:
        print('Unexpected error', e, '\n')
        raise

async def send_message_to_cloud(module_client,soc):
    try:
        messagevalue                        = MessageValue(DisplayName = "ES-LI-SOC1", Address = "N.A." ,Value = soc)
        messagevalue_Dg_Status              = MessageValue(DisplayName = "ES-LI-SOC3", Address = "N.A." ,Value = Variables.DG_db_status)
        #messagevalue_Load_Status            = MessageValue(DisplayName = "ES-LI-SOC2", Address = "N.A." ,Value = str(int(Variables.load_connected)))
        messagevalue_Dg_timer               = MessageValue(DisplayName = "ES-PB-DIC" , Address = "N.A." ,Value = Variables.dg_timer_value)
        messagevalue_iot_restart            = MessageValue(DisplayName = "E-SC-OFF"  , Address = "N.A." ,Value = Variables.IOT_restart_status)
        messagevalue_sh_rate                = MessageValue(DisplayName = "ES-PB-BP"  , Address = "N.A." ,Value = Variables.Sh_rate)
        messagevalue_correction_hour        = MessageValue(DisplayName = "SA-LI-CVH" , Address = "N.A." ,Value = Variables.Correction_Time_hour)
        messagevalue_correction_hour_Status = MessageValue(DisplayName = "SA-LI-CVL" , Address = "N.A." ,Value = Variables.Correction_Time_hour_status)
        messagevalue_devitation_percent     = MessageValue(DisplayName = "ES-PB-ENC" , Address = "N.A." ,Value = Variables.Deviation_percentage_avg)
        
        data                        = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue])
        data_Dg_Status              = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_Dg_Status])
        #data_Load_Status            = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_Load_Status])
        data_Dg_timer               = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_Dg_timer])
        data_devitation_percent     = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_devitation_percent])
        data_sh_rate                = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_sh_rate])
        data_iot_restart            = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_iot_restart])
        data_correction_hour        = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_correction_hour])
        data_correction_hour_status = Data(CorrelationId = "ES-LI-SOC1", SourceTimestamp = str(datetime.now()), Values = [messagevalue_correction_hour_Status])
        
        content     = Content(HwID = "Statcon-RTU",Data = [data,data_Dg_Status,data_Dg_timer,data_devitation_percent,data_sh_rate,data_iot_restart,data_correction_hour,data_correction_hour_status])
        IOT_message = IOTMessage(PublishTimestamp = str(datetime.now()),Content = [content])
        output_data = json.dumps(IOT_message, default=lambda o: o.__dict__, indent=4)
        
        print(datetime.now(), 'Trying to send\n')
        await module_client.send_message_to_output(output_data, "output_al")
        print(datetime.now(), 'Message sent successfully\n')
        
    except Exception as e:
        print('Unexpected error', e)
        raise
