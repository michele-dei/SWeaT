#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time, sys
from datetime import datetime, date
import myser

hello = """
------------------------------------------------------------------------------
PCB4EC: Printed-Circuit Board for Electro-Chemistry.
    Module with functions definitions for the use of PCB4EC in the context of 
    the SWeaT project (H2020-MSCA-IF-2019, GaID: 893544)

Authors: 
        Andrea Ria, PhD             |       andrea.ria@ing.unipi.it
        Michele Dei, PhD            |       michele.dei@iet.unipi.it
        Paolo Bruschi, Prof.        |       paolo.bruschi@unipi.it
        Department of Information Engineering - University of Pisa
        Via G. Caruso 16, Pisa, Italy    

Tested on (2021-05-10):
    Ubuntu 18.04.5 LTS (bionic)
    Python 3.6.9 (default, Jan 26 2021, 15:33:00) 
    IPython 7.16.1 -- An enhanced Interactive Python.
------------------------------------------------------------------------------
"""

class ads1115(object):
    
    sps_vals = (8.0, 16.0, 32.0, 64.0, 128.0, 250.0, 475.0, 860.0)

    """
    ADC CLASS:
        
        PGA:
        0: +-6.144 V     4 +-0.512 V
        1: +-4.096 V     5 +-0.256 V
        2: +-2.048 V     6 +- as 5
        3: +-1.024 V     7 +- as 5
        
        ch:
        0: AIN0-AIN1     4: AIN0
        1: AIN0-AIN3     5: AIN1
        2: AIN1-AIN3     6: AIN2
        3: AIN2-AIN3     7: AIN3
        
        sps:
        0: 8  sps     4:  128 sps
        1: 16 sps     5:  250 sps
        2: 32 sps     6:  475 sps
        3: 64 sps     7:  860 sps
    """    
    def __init__(self, mcu, adr):
        self.mcu = mcu
        self.adr = adr
        
    def read(self, ch, pga, sps=1):       
        str0 = "01"+"%01X" % (8+ch) + "%01X" % (pga*2+1) + "%01X" % (sps*2)+"3"
        # print str       
        if   pga==4 : fs = 0.512
        elif pga==3 : fs = 1.024
        elif pga==2 : fs = 2.048
        elif pga==1 : fs = 4.096
        elif pga==0 : fs = 6.144
        else        : fs = 0.256       
        self.mcu.i2c_write(self.adr, str0)       
        time.sleep(1.0/self.sps_vals[sps])
        cod = 0
        while (cod & 0x8000)==0:            
            self.mcu.i2c_write(self.adr, "01")
            cod = self.mcu.i2c_read(self.adr, 2)
            cod = int(cod, 16)
            #print cod                            
        self.mcu.i2c_write(self.adr, "00")
        cod = self.mcu.i2c_read(self.adr, 2) 
        # print cod       
        return myser.two_compl(int(cod,16),16)*fs/2**15

class session(object):
    
    """
        ADC MAPPING:
            * acd0 (0x48)
                4: temperature
                5: ref_buf (potentiometric RE, common)
                6: trim_buf (buffered trim_a: amperometric RE)
                7: tia_out
            * acd1 (0x49)
                4: ISE1
                5: ISE2
                6: ISE3
                7: ISE4
    """
    # adc_map tuple: adc0 or adc1, ch, pga
    adc_map = {'ISE1': (1, 4, 1),
               'ISE2': (1, 5, 1),
               'ISE3': (1, 6, 1),
               'ISE4': (1, 7, 1),
               'VTMP': (0, 4, 2),
               'VREP': (0, 5, 1),
               'VREA': (0, 6, 1),
               'TIAO': (0, 7, 1),
               }
    is_open = False
    acquisition = []
    
    def __init__(self, device_port=None, RIA_socket=0, RTIA_socket=0, 
                 verbose=True):
        if verbose:
            print(hello)
        
        # DETECT OS AND LISTS CONNECTED PORTS
        if sys.platform.startswith('win'):
            sys_detected = 'Windows'
        elif sys.platform.startswith('linux'):
            sys_detected = 'Linux'
        #elif sys.platform.startswith('cygwin'):
        #    sys_detected = 'Cygwin'
        #elif sys.platform.startswith('darwin'):
        #    sys_detected = 'MacOS'
        else:
            raise EnvironmentError('Unsupported OS platform')
        if verbose:
            print('Detected OS platform: '+sys_detected)
            print('Available serial ports detected:')
            myser.list_available_serial_ports()
        self.sys_detected = sys_detected
        
        # ASK USER FOR DEVICE PORT OR INHERIT FROM device_port PARAMETER
        port_correct = False
        if device_port is None:
            loop_at_user_input = True
        else:
            loop_at_user_input = False
            try:
                port = device_port
                mcu = myser.msp430(port, 115200, 5)
                spi = myser.MSP_Spi(mcu, 2, 0, 1, 2, 3, wt_time=0x80, mode=0)
                port_correct = True 
                if verbose:
                    print("Device connected on port: " + port)
            except:
                print("Device not detected.")

        while loop_at_user_input:
            try:
                if sys_detected=='Windows':
                    com = input("> Please, insert the number of PCB's COM or any char to quit: ")
                    try:
                        port = "COM" + str(int(com))
                        mcu = myser.msp430(port, 115200, 5)
                        spi = myser.MSP_Spi(mcu, 2, 0, 1, 2, 3, wt_time=0x80, mode=0)                        
                        port_correct = True
                    except ValueError: # char inserted
                        pass    
                    loop_at_user_input = False
                    break
                if sys_detected=='Linux':
                    com = input("> Please, insert the PCB tty name or type quit: ")
                    if com=='quit':
                        pass
                    else:
                        port = com
                        mcu = myser.msp430(com, 115200, 5)
                        spi = myser.MSP_Spi(mcu, 2, 0, 1, 2, 3, wt_time=0x80, mode=0)
                        # scl=pin 2.0, CS= pin 2.1, SDI (MOSI) =pin 2.2, SDO (MISO) = pin 2.3 
                        port_correct = True            
                    loop_at_user_input = False
                    break
            except:
                print("Device not detected.")        
        
        if port_correct:
            self.port = port
            self.mcu = mcu
            self.start = '\n'+str(date.today())+ ', ' + str(datetime.now().time())+'\n'
            if verbose:
                print('Session started: '+self.start)
            self.is_open = True
            self.adc0 = ads1115(mcu, 0x48) # see ADC mapping legend
            self.adc1 = ads1115(mcu, 0x49) # see ADC mapping legend
            self.pwr_slave_off()
            mcu.set_reg("P1DIR", (1<<0))
            spi.all_hz()
            time.sleep(1)
            self.pwr_slave_on()
            spi.start()
            self.physical_settings(RIA_socket, RTIA_socket, verbose=verbose)
        return
    
    def pwr_slave_on(self):
        if self.is_open:
            self.mcu.set_port(1,0)
    
    def pwr_slave_off(self):
        if self.is_open:
            self.mcu.res_port(1,0)
    
    def read(self, label=None):
        if not(self.is_open):
            return None
        if label in self.adc_map:
            ch, pga = self.adc_map[label][1], self.adc_map[label][2]
            if self.adc_map[label][0] == 1:
                r = self.adc1.read(ch, pga)
            else:
                r = self.adc0.read(ch, pga)
        else:
            print('read function supports the following identifiers:')
            print(self.adc_map.keys())
            r = None
        return r
        
    def date_tags(self):
        today = str(date.today())
        now = str(datetime.now().time())
        return today+'_'+now

    def append_to_file(self, file, data_list):
        f = open(file,'a+')
        for i, data in enumerate(data_list):
            sep = ', '
            if i == len(data_list)-1:
                sep = '\n'
            f.write(str(data)+sep)
        f.close()
        return

    def physical_settings(self, RIA_socket=0, RTIA_socket=0, verbose=True):
        msg0 = 'PCB4EC physical settings (please, check):\n'
        msg1 = ('(a) "IA RES" plugged with R={}\n'.format(RIA_socket), '(a) "IA RES" sockets unconnected\n')[RIA_socket==0]
        msg2 = ('(b) "IA RES" plugged with R={}\n'.format(RTIA_socket), '(b) "TIA RES" sockets unconnected\n')[RTIA_socket==0]
        self.RIA_socket = RIA_socket
        self.RTIA_socket = RTIA_socket
        self.RIA_smd = 1e5
        self.RTIA_smd = 1e7
        if RIA_socket==0:
            RIA = self.RIA_smd
        else:
            RIA = 1/( 1/self.RIA_socket + 1/self.RIA_smd )
        if RTIA_socket==0:
            RTIA = self.RTIA_smd
        else:
            RTIA = 1/( 1/self.RTIA_socket + 1/self.RTIA_smd )
        self.RIA = RIA
        self.RTIA = RTIA
        self.GAIN_IA = 1+self.RIA_smd/self.RIA
        if verbose:
            print(msg0+msg1+msg2)
        
    def convert_temperature(self, vtmp):
        vpt = vtmp/self.GAIN_IA
        return vpt/3.3*2.0/(0.00385)
    
    def convert_we_current(self, tiao):
        return tiao*self.RTIA
    
    def __call__(self, channels='ALL', nacquisitions=1, timestep=1.0, 
                    verbose=True, file=None):
        """
        Acquisition method
    
        Parameters
        ----------
        channels : str array or str, optional
            Channel identifiers:
                'ISE1', channel 1 ISE potential voltage
                'ISE2', channel 2 ISE potential voltage
                'ISE3', channel 3 ISE potential voltage
                'ISE4', channel 4 ISE potential voltage
                'VREP', reference electrode voltage (potentiometric side)
                'VTMP', temperature channel readout (voltage)
                'TEMP', temperature conversion (celsius degree)
                'VREA', reference electrode voltage (amperometric side)
                'TIAO', transimpedence amplfier output (voltage)
                'WEAC', working electrode current (ampere)
                'ALL',  all channels
            The default 'ALL'.
        nacquisitions : number, optional
            number of aquisitions. The default is 1.
        timestep : number, optional
            time step between consecutive acquisitions in seconds. 
            The default is 1.0.
        verbose : boolean, optional
            Function terminal output control. The default is True.
        file : NoneType, Boolean or string, optional
            Print to file control: if None or False no file output is produced. 
            If True an automatic name (.csv) is generated for the output file.
            If string, the filename name will assume the string value.
            The default is None.
    
        Returns
        -------
        dictionary
            Data structure.
    
        """
        if not(self.is_open):
            if verbose:
                print('Session is not open')
            return
        
        identifiers = list(self.adc_map.keys())
        identifiers.append('TEMP')
        identifiers.append('WEAC')
                
        # check valid channels
        valid_channels = []
        if channels == 'ALL':
            channels = identifiers
        if type(channels)==tuple:
            channels = list(channels)
        if type(channels)!=list:
            channels = [channels]
        for channel in channels:
            if channel in identifiers:
                valid_channels.append(channel)
            else:
                if verbose:
                    print('Aquisition: ' + channel + ' not valid')
        if ('TEMP' in valid_channels) and not('VTMP' in valid_channels):
            valid_channels.append('VTMP')
        if ('WEAC' in valid_channels) and not('TIAO' in valid_channels):
            valid_channels.append('TIAO')
        if verbose:
            print('Valid channels: '+str(valid_channels))
            
        # create data structure as dictionary        
        data = {valid_channels[i]: [] for i in range(len(valid_channels))}
        data['time_stamp'] = self.date_tags()
        data['RIA_socket'] = self.RIA_socket
        data['RTIA_socket'] = self.RIA_socket
        file_head = ['time_stamp', 'RIA_socket', 'RTIA_socket']        
        
        # write-to-file enabling
        write_to_file = False
        if not(file is None):
            if isinstance(file, bool):
                if file:
                    file = 'pcb4ec-acquisition-' + data['time_stamp'] + '.csv'
                    write_to_file = True
            elif isinstance(file, str):
                write_to_file = True
        if write_to_file:
            if verbose:
                print('Data will be written to: '+file)
            f = open(file,'w')
            f.write('PCB4EC acquisition: ')
            for h in file_head:
                f.write(h + ':' + str(data[h])+'; ')
            f.write('naquisitions: {}, timestep: {} sec'.format(nacquisitions, timestep))
            f.write('\n')
            f.write('CHANNELS: ')
            for i, ch in enumerate(valid_channels):
                sep = ', '
                if i == len(valid_channels)-1:
                    sep = '\n'
                f.write(ch + sep)
            f.close()
                    
        # start acquisition
        if verbose:
            print('Acquisition started: naquisitions={}, timestep={} sec'.format(nacquisitions, timestep))
        for n in range(nacquisitions):
            if verbose:
                print('Acquisition {}/{}: '.format(n+1, nacquisitions))
            for ch in valid_channels:
                if ch in self.adc_map:
                    data[ch].append(self.read(ch))
            for ch in valid_channels:
                if ch=='TEMP':
                    vtmp = data['VTMP'][-1]
                    temp = self.convert_temperature(vtmp)
                    data['TEMP'].append(temp)
                if ch=='WEAC':
                    tiao = data['TIAO'][-1]
                    weac = self.convert_we_current(tiao)
                    data['WEAC'].append(weac)
            if verbose:
                for ch in valid_channels:
                    print( ch + ': ' + str(data[ch][-1]))
            if write_to_file:
                last_data = []
                for ch in valid_channels:
                    last_data.append(data[ch][-1])
                self.append_to_file(file, last_data)
            time.sleep(timestep)

        # acquisition ended
        self.acquisition.append(data)
        if verbose:
            print('Acquisition finished.')       
        return data
    


# # # close eventual orphan serial connections
#if "mcu" in dir():
#    if mcu.ser.isOpen():
#        mcu.close()
    
# ########################################33 BODY   
# print(hello)

# # DETECT OS AND LISTS CONNECTED PORTS
# if sys.platform.startswith('win'):
#     sys_detected = 'Windows'
# elif sys.platform.startswith('linux'):
#     sys_detected = 'Linux'
# #elif sys.platform.startswith('cygwin'):
# #    sys_detected = 'Cygwin'
# #elif sys.platform.startswith('darwin'):
# #    sys_detected = 'MacOS'
# else:
#     raise EnvironmentError('Unsupported OS platform')
# print('Detected OS platform: '+sys_detected)
# print('Available serial ports detected:')
# myser.list_available_serial_ports()

# # ASK USER FOR DEVICE PORT
# loop_at_user_input = True
# port_correct = False
# while loop_at_user_input:
#     try:
#         if sys_detected=='Windows':
#             com = input("> Please, insert the number of PCB's COM or any char to quit: ")
#             try:
#                 ncom = int(com)
#                 mcu = myser.msp430("COM"+str(ncom), 115200, 5)
#                 spi = myser.MSP_Spi(mcu, 2, 0, 1, 2, 3, wt_time=0x80, mode=0)
#                 port_correct = True
#             except ValueError: # char inserted
#                 pass    
#             loop_at_user_input = False
#             break
#         if sys_detected=='Linux':
#             com = input("> Please, insert the PCB tty name or type quit: ")
#             if com=='quit':
#                 pass
#             else:
#                 mcu = myser.msp430(com, 115200, 5)
#                 spi = myser.MSP_Spi(mcu, 2, 0, 1, 2, 3, wt_time=0x80, mode=0)
#                 port_correct = True            
#             loop_at_user_input = False
#             break
#     except:
#         print("Device not detected.")        
# # scl=pin 2.0, CS= pin 2.1, SDI (MOSI) =pin 2.2, SDO (MISO) = pin 2.3 
# if port_correct:
#     #adc0 = ads1115_class.ads1115(mcu, 0x48)
#     #adc1 = ads1115_class.ads1115(mcu, 0x49)
#     adc0 = ads1115(mcu, 0x48)
#     adc1 = ads1115(mcu, 0x49)
#     """
#     ADC MAPPING:
#         * acd0 (0x48)
#             4: temperature
#             5: ref_buf (potentiometric RE, common)
#             6: trim_buf (buffered trim_a: amperometric RE)
#             7: tia_out
#         * acd1 (0x49)
#             4: ISE1
#             5: ISE2
#             6: ISE3
#             7: ISE4
#     """
#     pwr_slave_off(mcu)
#     mcu.set_reg("P1DIR", (1<<0))
#     spi.all_hz()
#     time.sleep(1)
#     pwr_slave_on(mcu)
#     spi.start()

    
########################################################
######################  B O D Y   ######################
########################################################

