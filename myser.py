"""
Tested on:

Distributor ID:	Ubuntu
Description:	Ubuntu 18.04.5 LTS
Release:	18.04
Codename:	bionic
   
Python 3.6.9 (default, Jan 26 2021, 15:33:00) 
Type "copyright", "credits" or "license" for more information.

IPython 7.16.1 -- An enhanced Interactive Python.
"""

import serial
import serial.tools.list_ports
import io

#  ***************  Function definitions ******************
def two_compl(n,nbits):
    base=2**nbits
    if n<0: n=0
    if n>base-1:n=base-1
    if n<base/2: x=n
    else: x=n-base
    return x
    
def lista_porte():
    "returns a list with the port numbers and description"
    lp=[]
    ld=[]
    zz=serial.tools.list_ports.comports()
    for por,desc,garb in zz:
        lp=lp+[por]
        ld=ld+[desc]
    return lp,ld

def icpl(a):
    if a==1: return 0
    else: return 1
def ixor(a,b):
    if a==0: return b
    else: return icpl(b)

class gen_mcu(object):
   
    def __init__(self,dev,brate,tout=2):
            self.ser=serial.Serial(dev,brate,timeout=tout)
            self.echo=1
    def close(self):
        self.ser.close()
    def write(self,st):
        nl=self.ser.write(st)
        return nl
    def read(self,n):
        return self.ser.read(n)
    
    def readline(self,eol='\r'):
        c=""
        st=""
        while (c != eol):
            c=self.ser.read(1)
            if (c == ""):
                break
            st=st+c
        return st
    def send_cmd(self,cmd):
        self.write(cmd +"\r")
        if self.echo: self.readline()
    def ver(self):
        self.send_cmd("VER")
        s=self.readline()
        ifw=s.find("FW")
        icpu=s.find("CPU")
        fw=s[ifw+2:].split()[0]
        cpu=s[icpu+3:].split()[0]
        return fw,cpu


class msp430(object):   
    
    def __init__(self,dev,brate=9600,tout=2):
            self.ser=serial.Serial(dev,brate,timeout=tout)
            self.echo=1
            self.mcu_type="msp";
            self.fw="gen"
    def ver(self):
            self.send_cmd("VER")
            s=self.readline()
            ifw=s.find("FW")
            icpu=s.find("CPU")
            fw=s[ifw+2:].split()[0]
            cpu=s[icpu+3:].split()[0]
            self.mcu_type=cpu
            self.fw=fw
            return (fw,cpu)
        
    def write(self,st):
        nl=self.ser.write(st.encode()) # python 3 fixed
        return nl
    
    def read(self,n):
        return self.ser.read(n)
    
    def readline(self,eol='\r'):
        c=""
        st=""
        while (c != eol):
            c=self.ser.read(1)
            c = c.decode('utf-8') # python 3 fixed
            if (c == ""):
                break
            st=st+c
        return st
    
    def close(self):
        self.ser.close()
        
    def send_cmd(self,cmd):
        self.write(cmd +"\r")
        if self.echo: self.readline()

    def set_reg(self,reg_string,mask):
        self.send_cmd("SR "+reg_string + " %02X" % mask)
        self.readline()
    def res_reg(self,reg_string,mask):
        self.send_cmd("RR "+reg_string + " %02X" % mask)
        self.readline()
# Rember to set the corresponding bit in the DIR byte first by using
# set_reg functions

    def set_port(self,port,bit):
        self.send_cmd("S P%1dOUT %1d" % (port,bit))
        self.readline()
    def res_port(self,port,bit):
        self.send_cmd("R P%1dOUT %1d" % (port,bit))
        self.readline()	
    def i2c_write(self,adr,hex_string):
        self.send_cmd("I2CW %02X "% adr + hex_string)
        S=self.readline()
        return S
    def i2c_write_nostop(self,adr,hex_string):
        self.send_cmd("I2CWNS %02X "% adr + hex_string)
        S=self.readline()
        return S
    def i2c_read(self, adr, n_byte):
        self.send_cmd("I2CR " + ("%02X" % adr)+(" %02X" % n_byte))
        self.readline()
        s=self.readline()
        return s
    def spi_send_bytes(self,port,sck,cs,d_out,d_in,data,wt,mode):
        arg1="%1d%1d%1d%1d%1d%1d" % (port,sck,cs,d_out,d_in,mode)
        arg3="%04X" % wt # unit delay time. with wt=0x40 : fck=100 kHz
        self.send_cmd("SPIC "+arg1 + " " + data + " " + arg3)
        self.readline()
        s=self.readline()
        return s        
    def spi_send_bytes_noCS(self,port,sck,cs,d_out,d_in,data,wt,mode):
        arg1="%1d%1d%1d%1d%1d%1d" % (port,sck,cs,d_out,d_in,mode)
        arg3="%04X" % wt # unit delay time. with wt=0x40 : fck=100 kHz
        self.send_cmd("SPICNCS "+arg1 + " " + data + " " + arg3)
        self.readline()
        s=self.readline()
        return s           
 
    def read_mi(self,channel):
        self.send_cmd("ADCM %02X" % (channel))
        self.readline()
        s=self.readline()
        return two_compl(int(s[:-2],16),32)
    def read_v(self,channel):
        self.send_cmd("ADCM %02X" % (channel))
        self.readline()
        s=self.readline()
##        print s
        dato_i=two_compl(int(s[:-2],16),32)
        return float(dato_i)/2**23*1.2
    def micwrt(self,porta,sclk,wrt,dta,cmd_str):
        out_str="MICWRT %1d%1d%1d%1d %s" % (porta,sclk,wrt,dta,cmd_str)
##        print out_str
        self.send_cmd(out_str)
        s=self.readline()
        s=self.readline()
##        print "micwrt=",s
    def save_mic_string(self,XY,cmd):
        if XY=="X":
            st="STSX %s" % cmd
        elif XY=="Y":
            st="STSY %s" % cmd
        self.send_cmd(st)
        self.readline()
    def read_2_sens(self,porta,sclk,wrt,dta,rit):
        st="RD_SA %1d%1d%1d%1d %04X" % (porta,sclk,wrt,dta,rit)
        self.send_cmd(st)
        #self.readline()
        s=self.readline()
        #print s
        d=two_compl(int(s[:-2],16),32)
        dx=float(d)/2**23*1.2
        #self.readline()
        s=self.readline()
        #print s
        d=two_compl(int(s[:-2],16),32)
        dy=float(d)/2**23*1.2
        return dx, dy
          
class msp430_FR5949(msp430):
    def __init__(self,dev,brate=9600,tout=2):
        msp430.__init__(self,dev,brate,tout)
        self.Vref=2.5
    def read_v(self,ch):
        self.send_cmd("ADC")
        s=self.readline()
        risu=self.Vref*(int(s[0:4],16)-2**11)/2**11
        return risu
        
#  ************************ class definitions *************************
class ADuC8(object):

        def __init__(self,dev,brate=9600,tout=2,vfs=2.56,aincom=1.25,cpu="ADuC847"):
            self.ser=serial.Serial(dev,brate,timeout=tout)
            self.vfs=vfs
            self.aincom=aincom
            self.cpu=cpu
            self.set_bits()
            self.fw="ND"
            self.echo=True
            self.mcu_type="ADuC";
            self.fw="gen"
        def get_vmin(self):
            return self.aincom-self.vfs
        def get_vmax(self):
            return self.aincom+self.vfs
        
        def set_bits(self):
            if self.cpu=="ADuC847":
                self.n_bit=24
            elif self.cpu=="ADuC842":
                self.n_bit=12
                self.vfs=1.25
                self.aincom=1.25
            else:
                self.n_bit=24
            self.fs=2**(self.n_bit-1)          
    
        def unlock(self):
            """ Unlock the microcontroller. Necessary before any other command
            if the mcu was previously locked""" 
            self.write("%")
            return self.readline()
                
        def write(self,st):
            nl=self.ser.write(st)
            return nl
        def read(self,n):
            return self.ser.read(n)
        
        def readline(self,eol='\r'):
            c=""
            st=""
            while (c != eol):
                c=self.ser.read(1)
                if (c == ""):
                    break
                st=st+c
            return st
        
        def close(self):
            self.ser.close()
            
        def send_cmd(self,cmd):
            self.write(cmd +"\r")
            if self.echo: self.readline()
            
        def read_v(self,adc_n):
            self.send_cmd("ADC %01X" % adc_n)
            s=self.readline()
            if (adc_n<10):
                return float((int(s,16)-self.fs))/self.fs*self.vfs+self.aincom
            else:
                return float((int(s,16)-self.fs))/self.fs*self.vfs
            
        def write_v(self,dac_n,v_out):
            d_out=int(v_out/2.5*4095)
            if d_out<0 : d_out=0
            if d_out>4095 : d_out=4095
            self.send_cmd("DAC %01X %04X" % (dac_n,d_out))
            
        def set_port(self,porta,b):
            self.send_cmd("S %1d%1d" % (porta,b))
                        
        def res_port(self,porta,b):
            self.send_cmd("R %1d%1d" % (porta,b))
            
        def ver(self):
            self.send_cmd("VER")
            s=self.readline()
            ifw=s.find("FW")
            icpu=s.find("CPU")
            fw=s[ifw+2:].split()[0]
            cpu=s[icpu+3:].split()[0]
            self.mcu=cpu
            self.fw=fw
            return (fw,cpu)

        def auto_ver(self):
            self.fw=self.ver()[0]
            self.cpu=self.ver()[1]
            
        def exta(self,adr,stringa):
            lun=len(stringa)
            self.send_cmd("EXTA " + "%04X " % adr + "%04X" % lun)
            self.read(1)
            self.write(stringa)
            self.readline()
            
        def extb(self,adr,n):
            self.send_cmd("EXTB " + "%04X " % adr + "%04X" % n)
            self.readline()
            s=self.readline()
            return s[:-2]
        def spic(self,adr,n):
            self.send_cmd("SPIC " + "%04X " % adr + "%04X" % n)
        def spi_send_byte(self,port,sck,sync,din,d_byte):
            pref="%1X%1X%1X%1X" % (port,sck,sync,din)
            com_s=pref+("%02X" % d_byte)
            print(com_s)
            self.exta(0,com_s)
            self.spic(0,2)
##            self.send_cmd("SPIC " + "%04X " % adr + "%04X" % n)
        def spi_send_bytes(self,port,sck,sync,din,d_bytes):
            n_b=len(d_bytes)
            pref="%1X%1X%1X%1X" % (port,sck,sync,din)
            com_s=pref
            for i in range(n_b):
                com_s=com_s+("%02X" % d_bytes[i])
            # print com_s
            self.exta(0,com_s)
            self.spic(0,n_b*2)
            S=self.readline()
            return S
                  
        def micwrt_from_exta(self,adr,n):
            self.send_cmd("MICWRT " + "%04X " % adr + "%04X" % n)
        def micwrt(self,porta,sclk,wrt,dta,cmd_str):
            st1="%1d%1d%1d%1d" % (porta,sclk,wrt,dta)
            com_s=st1+cmd_str
            self.exta(0,com_s)
            self.micwrt_from_exta(0,len(cmd_str))
 
        
        def i2c_write(self,adr,hex_string):
            stringa="%02X" % adr + hex_string
            self.exta(0,stringa)
            nbytes=int(len(stringa)/2)-1
            self.send_cmd("I2CWB 0000 " + "%04X" % nbytes)
            self.readline()
            S=self.readline()
            return S
        def i2c_read_1(self,adr):
            self.send_cmd("I2CR " + "%02X" % adr)
            s=self.readline()
            return s[:-2]
        def i2c_read(self, adr, n_byte):
            self.send_cmd("I2CRB " + ("%02X" % adr)+(" %02X" % n_byte))
            s=self.readline()
            return s[2:]
        def i2c_write_nostop(self,adr,hex_string):
            stringa="%02X" % adr + hex_string
            self.exta(0,stringa)
            nbytes=int(len(stringa)/2)-1
            self.send_cmd("I2CWBN 0000 " + "%04X" % nbytes)
            self.readline()
            S=self.readline()
            return S

#
# Compatibility class to use SPI in the same way as with Bus Pyrate Board
#

class ADuC_Spi(object):
    def __init__(self,mcu,port,sck,sync,din):
        self.mcu=mcu
        self.port=port
        self.sck=sck
        self.sync=sync
        self.din=din
    def send_bytes(self,data_list):
        S=self.mcu.spi_send_bytes(self.port,self.sck,self.sync,self.din,data_list)
        S2=S[0:2]+" "+S[2:4]+" "+S[4:6]
        return S2
    def read_reg(self,dati):
        S=self.send_bytes(dati)      
        val=int(S[6:8],16)*256+int(S[3:5],16)
        return val
    def CS_Low(self):
        self.mcu.res_port(self.port,self.sync)
    def CS_High(self):
        self.mcu.set_port(self.port,self.sync)
    def close(self):
        self.mcu.close()
        
class MSP_Spi(object):
    def __init__(self,mcu,port,sck,sync,d_out,d_in,wt_time,mode):
        #  wt:unit delay time. with wt=0x40 : fck=100 kHz
        # sync is the cs signal. d_out: mosi, d_in: miso
        # mode=1 : ck 1->0 data propagate 0->1 data sampled
        # mode=0 : ck 0->1 data propagate 1->0 data sampled
        self.mcu=mcu
        self.port=port
        self.sck=sck
        self.sync=sync
        self.d_in=d_in
        self.d_out=d_out
        self.wt_time=wt_time
        self.mode=mode
    def sendbytes(self,data_list):
        com_s=""
        for i in range(len(data_list)):
            com_s=com_s+("%02X" % data_list[i])
        
        S=self.mcu.spi_send_bytes(self.port,self.sck,self.sync,self.d_out,self.d_in,com_s,self.wt_time,self.mode)
        S2=S[0:2]+" "+S[2:4]+" "+S[4:6]
        return S2
    def sendbytes2(self,data_list):
        com_s=""
        for i in range(len(data_list)):
            com_s=com_s+("%02X" % data_list[i])
        
        S=self.mcu.spi_send_bytes(self.port,self.sck,self.sync,self.d_out,self.d_in,com_s,self.wt_time,self.mode)
        #S2=S[0:2]+" "+S[2:4]+" "+S[4:6]
        return S
    def sendbytes_noCS(self,data_list):
        com_s=""
        for i in range(len(data_list)):
            com_s=com_s+("%02X" % data_list[i])
        
        S=self.mcu.spi_send_bytes_noCS(self.port,self.sck,self.sync,self.d_out,self.d_in,com_s,self.wt_time,self.mode)
        S2=S[0:2]+" "+S[2:4]+" "+S[4:6]
        return S2
    def sendbytes_noCS2(self,data_list):
        com_s=""
        for i in range(len(data_list)):
            com_s=com_s+("%02X" % data_list[i])
        
        S=self.mcu.spi_send_bytes_noCS(self.port,self.sck,self.sync,self.d_out,self.d_in,com_s,self.wt_time,self.mode)
        return S
    def all_hz(self):
        arg1="%1d%1d%1d%1d%1d" % (self.port,self.sck,self.sync,self.d_out,self.d_in)
        self.mcu.send_cmd("SPI_HZ "+arg1)
        self.mcu.readline()
        self.mcu.readline()
    def start(self):
        arg1="%1d%1d%1d%1d%1d" % (self.port,self.sck,self.sync,self.d_out,self.d_in)
        self.mcu.send_cmd("SPI_RD "+arg1)
        self.mcu.readline()   
        self.mcu.readline()
    def read_reg(self,dati):
        S=self.sendbytes(dati)      
        val=int(S[6:8],16)*256+int(S[3:5],16)
        return val
    def CS_Low(self):
        self.mcu.res_port(self.port,self.sync)
    def CS_High(self):
        self.mcu.set_port(self.port,self.sync)
    def close(self):
        self.mcu.close()
    def id_protocol(self):
        return ("SPI","pyrate")

class bit_field(object):
    def __init__(self,pos,N,invert=False,msb_first=True):
        self.N=N
        self.pos=pos
        self.invert=invert
        self.msb_first=msb_first
        self.value=0
    def assign(self,value):
        self.value=value % 2**self.N
        
class data_bits(object):
    def __init__(self,n):
        self.n=n
        self.bits=[0]*n
        self.keys=["NA"]*n
    def load_from_file(self,file_name):
        f=open(file_name,"r")
        i=0
        for line in f:
            ls=line.split()
            self.bits[i]=int(ls[0])
            if len(ls)==2: self.keys[i]=ls[1]
            i=i+1
        f.close()
    def stampa(self):
        for i in range(0,self.n):
            print(i,self.bits[i],"   ", self.keys[i])
    def prog_string(self):
        cod=0
        for i in range(0,self.n):
            cod=cod+self.bits[i]*2**(self.n-i-1)
            # print cod
        fom="%%0%dX" % ((self.n)/4)
        st=fom % cod
        return st
    def write(self,val,pos,nbits,invert,msb_first):
        if val>2**nbits-1: return 1
        if (pos+nbits)>self.n: return 1 
        else:
            fom="{:0%db}" % nbits
            stb=fom.format(val)
            stl=map(int,list(stb))
        if invert==1:
            stl=map(icpl,stl)
        if msb_first==1:
            for i in range(0,nbits):
                self.bits[pos+i]=stl[i]
        else:
            for i in range(0,nbits):
                self.bits[pos+i]=stl[-(i+1)]   
        return stl
    def get_value(self,pos,N,inv,msb_f):
        z=0
        for i in range(N):
            if msb_f==0:
                z=z+2**i*ixor(self.bits[i+pos],inv)
            else:
                z=z+2**i*ixor(self.bits[N-i-1+pos],inv)
        return z
    def get_value_field(self,BF):
        return self.get_value(BF.pos,BF.N,BF.invert,BF.msb_first)
    def write_from_field(self,BF):
        self.write(BF.value,BF.pos,BF.N,BF.invert,BF.msb_first)
    def salva(self,file_save):
        f=open(file_save,"w")
        for i in range(self.n):
            s="{0:<3d}  {1:12s}\n".format(self.bits[i],self.keys[i])
            f.write(s)
        f.close()
            
   
class mich_int(object):
    """ Define a generic mich_interface. Requires the previous instance of a
    microcontroller object (dv) and data_bits object """
    def __init__(self,dev,port=2,sck=2,wrt=3,data=4):
        self.dev=dev
        self.port=port
        self.sck=sck
        self.wrt=wrt
        self.data=data
        self.mem_adr=0
    def program(self,databit):
        st=databit.prog_string()
##        st1="%d%d%d%d" % (self.port,self.sck,self.wrt,self.data)
##        com_s=st1+st
        if self.dev!=None:
##            self.dev.exta(self.mem_adr,com_s)
##            self.dev.micwrt(self.mem_adr,(databit.n/4))
            self.dev.micwrt(self.port,self.sck,self.wrt,self.data,st)     
        
    def code_string(self,databit):
        st=databit.prog_string()
        st1="%d%d%d%d" % (self.port,self.sck,self.wrt,self.data)
        com_s=st1+st
        return com_s
    def code_ee_save(self,adr,databit):
        code=self.code_string(databit)
        n=len(code)
        for i in range(n/4):
            prs="STORE {0:04x} {1:4s}".format(adr,code[i*4:i*4+4])
            #print prs
            self.dev.send_cmd(prs)
            self.dev.readline()
            adr=adr+1
        if (n%4)!=0:
            i=i+1
            prs="STORE {0:04x} {1:<04s}".format(adr,code[i*4:i*4+4])
            #print prs
            self.dev.send_cmd(prs)
            self.dev.readline()
            
class mich_int_430(object):
    """ Define a generic mich_interface. Requires the previous instance of a
    microcontroller object (dv) and data_bits object """
    def __init__(self,dev,port=2,sck=2,wrt=3,data=4):
        self.dev=dev
        self.port=port
        self.sck=sck
        self.wrt=wrt
        self.data=data
        self.mem_adr=0
    def program(self,databit):
        st=databit.prog_string()
        self.dev.micwrt(self.port,self.sck,self.wrt,self.data,st)
    def code_string(self,databit):
        st=databit.prog_string()
        st1="%d%d%d%d" % (self.port,self.sck,self.wrt,self.data)
        com_s=st1+st
        return com_s
    def code_ee_save(self,adr,databit):
        return
   


class mic_conf(object):
    def __init__(self,nome_file,interface=None):
        self.field=dict()
        self.fields=[]
        self.interface=interface
        f=open(nome_file,"r")
        for line in f:
            if line[0]!="#":
                ls=line.split()
                self.fields.append(ls[0])
                self.field[ls[0]]=bit_field(int(ls[1]),int(ls[2]),int(ls[3]),int(ls[4]))
                self.field[ls[0]].assign(int(ls[5]))
            else: pass
        self.nbits=0
        for i in iter(self.field):
            self.nbits=self.nbits+self.field[i].N
        self.db=data_bits(self.nbits)
        for i in self.fields:
            self.db.write_from_field(self.field[i])
            N=self.field[i].N
            if N<=1:
                self.db.keys[self.field[i].pos]=i
            else:
                for j in range(N):                  
                    if self.field[i].msb_first==0:
                        self.db.keys[j+self.field[i].pos]=i+"_"+str(j)
                    else:
                        self.db.keys[j+self.field[i].pos]=i+"_"+str(N-j-1)
        f.close()
        
    def write_to_file(self,file_out):
        f=open(file_out,"w")
        for i in self.fields:
            ff=self.field[i]
            s="{0:12s}{1:4d}{2:4d}{3:3d}{4:3d}{5:8d}\n".format(i,ff.pos,ff.N,ff.invert,
            ff.msb_first,ff.value)
            f.write(s)
        f.close()
    def load_databits(self,nome_file):
        dbx=data_bits(self.nbits)
        dbx.load_from_file(nome_file)
        for i in self.fields:
            value=dbx.get_value_field(self.field[i])
            self.field[i].assign(value)
            self.db.write_from_field(self.field[i])              
    def stampa(self):
        for i in self.fields:
            print(i,self.field[i].pos,self.field[i].N,self.field[i].value)
    def set_value(self,campo,valore):
        self.field[campo].assign(valore)
        self.db.write_from_field(self.field[campo])
    def get_value(self,campo):
        return self.field[campo].value
    def write(self,interface=None):
        if (interface==None) and (self.interface!=None):
            self.interface.program(self.db)
        elif interface!=None:         
            interface.program(self.db)
        else:
            print("Interface not defined")
            raise RuntimeError
    def get_prog_string(self):
        return self.db.prog_string()
        
class mich_chip(data_bits):
    """ Define an interface for the Mich_chip triple flow sensor
    inherits from data_bits, which is initialized with a number of bits = 32
    Requires the previous instance of a microcontroller object (dv)
    Inherited methods pertinent the mich_chip user:
    load_from_file(filename)
    write(val,pos,nbits,invert,msb_first) """
    def __init__(self,dev,port=2,sck=2,wrt=3,data=4):
        data_bits.__init__(self,32)
        self.dev=dev
        self.port=port
        self.sck=sck
        self.wrt=wrt
        self.data=data
        self.mem_adr=0
    def program(self):
        st=self.prog_string()
        st1="%d%d%d%d" % (self.port,self.sck,self.wrt,self.data)
        com_s=st1+st
        self.dev.exta(self.mem_adr,com_s)
        self.dev.micwrt(self.mem_adr,(self.n/4))
    def heater(self,status):
        if status==0: self.bits[8]=1
        else : self.bits[8]=0
        self.program()
                    
class Meter(object):
        """ Implements a generic meter (V-meter, A-meter etc) using  one channel (chan) of an ADuC8
        device. Maps the range Mmax,Mmin into the target input range """
        def __init__(self,dev,chan,zero,gain):
            self.dev=dev
            self.zero=zero
            self.gain=gain
            self.chan=chan
        def read_m(self):
            v=self.dev.read_v(self.chan)
            return (v-self.zero)*self.gain

class AD5754(object):
        """ Object class for the AD5754 4 channel, 16 bit DAC """
        ranges={"+5":(0,0.0,5.0),"+10":(1,0,10.0),"+10.8":(2,0,10.8),"+-5":(3,-5.0,5.0),"+-10":(4,-10.0,10.0),"+-10.8":(5,-10.8,10.8)}
        def __init__(self,dev,port=2,sck=4,sync=3,din=2,lda=5):
            self.rngs=["+5","+5","+5","+5"]
            self.port=port
            self.sck=sck
            self.sync=sync
            self.din=din
            self.dev=dev;
            self.lda=lda
            self.mem_adr=0;
          
        def write_reg(self,reg,adr,data):
            """Writes the DAC registes according to the three fields:
            reg (register number: 0=DAC reg, 1=output range register, 2 = power, 3 = control reg)
            adr (DAC channnel, when applicable 0-3= channels A-D, 4=all channels)
            data (data field, meaning varies depending on register """
            com=data+adr*2**16+reg*2**19
            pref="%1X%1X%1X%1X" % (self.port,self.sck,self.sync,self.din)
            com_s=pref+("%06X" % com)
            self.dev.exta(self.mem_adr,com_s)
            self.dev.spic(self.mem_adr,6)
            print(com_s)
            
        def ldac(self):
            """ Triggers the DAC output update (ldac)"""
            self.dev.send_cmd("LDAC "+"%1X%1X" % (self.port,self.lda))
            
        def pon_all(self):
            """ Powers on all the DAC channels """
            self.write_reg(2,0,15)
            
        def set_range(self,chan,rng):
            """ Sets the range of the channel chan. Valid ranges (strings) are:
            "+5" "+10" "+10.8" "+-5" "+-10" "+-10.8" """
            self.rngs[chan]=rng
            cod=AD5754.ranges[rng][0]
            self.write_reg(1,chan,cod)

        def set_v(self,chan,v):
            """ Writes the voltage v into the DAC channel (chan) but
            does not trigger the DAC output update (ldac)"""
            rng=self.rngs[chan]
            vmin=AD5754.ranges[rng][1]
            vmax=AD5754.ranges[rng][2]
            cod=int((v-vmin)/(vmax-vmin)*2**16)
            if cod>=2**16 : cod=2**16-1
            if cod<0 : cod=0
            self.write_reg(0,chan,cod)
            
        def write_v(self,chan,v):
            """ Writes the voltage v into the DAC channel (chan) and
            triggers the DAC output update (ldac)"""
            self.set_v(chan,v)
            self.ldac()

class AD5933(object):
        """ Object class for the AD5933 impedance meter """
        def __init__(self,adr,dev,clk=16e6):
            self.adr=adr
            self.dev=dev
            self.clk=clk
        def write_reg(self,reg,val_str):
            self.dev.i2c_write(self.adr,"%02X" % reg + val_str)
        def read_reg(self,reg):
            self.dev.i2c_write(self.adr,"B0" +"%02X" % reg)
            val=self.dev.i2c_read_1(self.adr)
            return val
        def set_start_freq(self,freq):
            cod_str="%06X" % int(freq/self.clk*2**29)
            self.write_reg(0x82,cod_str[0:2])
            self.write_reg(0x83,cod_str[2:4])
            self.write_reg(0x84,cod_str[-2:])

        def set_incr_freq(self,freq):
            cod_str="%06X" % int(freq/self.clk*2**29)
            self.write_reg(0x85,cod_str[0:2])
            self.write_reg(0x86,cod_str[2:4])
            self.write_reg(0x87,cod_str[-2:])
        def set_steady_out(self,out_freq):
            self.set_start_freq(out_freq)
            self.stand_by()
            self.init_freq()
            
        def set_num_incr(self,num):
            if num>511 : num=511
            if num<0 : num=0
            cod_str="%04X" % num
            self.write_reg(0x88,cod_str[0:2])
            self.write_reg(0x89,cod_str[-2:])
            
        def write_ctrl_nibble(self,nib):
            buf=int(self.read_reg(0x80),16)
            buf=(buf & 0x0F) | (nib*16)
            self.write_reg(0x80,"%02X" % buf)
            
        def stand_by(self):
            self.write_ctrl_nibble(0x0B)
        def init_freq(self):
            self.write_ctrl_nibble(0x01)
        def start_freq_sweep(self):
            self.write_ctrl_nibble(0x02)
        def increment_freq(self):
            self.write_ctrl_nibble(0x03)
        def power_down(self):
            self.write_ctrl_nibble(0x0A)
        def check_val_meas(self):
            buf=int(self.read_reg(0x8F),16)
            val=False
            if (buf & 0x02)!=0 :val=True
            return val
        def check_end_meas(self):
            buf=int(self.read_reg(0x8F),16)
            val=False
            if (buf & 0x04)!=0 : val=True
            return val
        def get_real(self):
            val_H=int(self.read_reg(0x94),16)
            val_L=int(self.read_reg(0x95),16)
            return val_L+val_H*256
        def get_imag(self):
            val_H=int(self.read_reg(0x96),16)
            val_L=int(self.read_reg(0x97),16)
            return val_L+val_H*256
        def set_PGA_gain(self,rng):
            "gain: H-> x5 , L -> 1"
            ctr=int(self.read_reg(0x80),16)
            if rng=="H": ctr=ctr & 0xFE
            else: ctr=ctr | 0x01
            self.write_reg(0x80,"%02X" % ctr)
        def set_output_range(self,rng):
            "rng=1: 2V; rng=2: 1V rng=3: 400 mV, rng=4: 200 mV"
            ctr=int(self.read_reg(0x80),16) & 0xF9
            if rng==1: crt=ctr | 0x00
            elif rng==2: ctr=ctr | 0x06
            elif rng==3: ctr=ctr | 0x04
            else: ctr=ctr | 0x02
            self.write_reg(0x80,"%02X" % ctr)
        def set_cycles(self,nc,mult=1):
            if nc<0:nc=0
            if nc>511:nc=511
            if mult==2: nc=nc + 512
            elif nc==4: nc=nc +1536

            cod_str="%04X" % nc
            self.write_reg(0x8A,cod_str[0:2])
            self.write_reg(0x8B,cod_str[-2:])
            
##############################################################################
### 2021-05-10:
### ADDED functions for COM scanning also compatible with OS other than the 
### Microsoft's stuff
### adapted from: 
### https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
##############################################################################

import sys
import glob

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def list_available_serial_ports():
    print(serial_ports())
            
            



        
    
        
        
        
    
