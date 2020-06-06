#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 16:23:58 2019

@original author: mliu
"""

from obspy.clients.fdsn import Client
from obspy import UTCDateTime, read
import os
import datetime
import copy
from bs4 import BeautifulSoup as Soup

#User-specied
#Datos de el/los eventos que quieren estudiarse (ubicacion y parametros de seleccion de datos)
end_time = datetime.datetime.now() 
start_time = end_time-datetime.timedelta(hours=24) # Intervalo de busqueda desde 12 horas anteriores a la actual
starttime = UTCDateTime(start_time.isoformat())
print(start_time.isoformat())
endtime = UTCDateTime(end_time.isoformat())
#mtime = datetime.datetime.strptime(item["time_tag"],'%Y-%m-%dT%H:%M:%SZ')t
mindepth = 0
maxdepth = 100
minmagnitude=2
maxmagnitude=9
latitude=15
longitude=-90
minradius=0
maxradius=20
tmpfile="tmp.catalog"
catalog="catalog.dat"
stationfile = "STATIONS.sta"
out = open(catalog,"w")

client = Client("SCEDC")
#request catalog

cat = client.get_events(catalog="SCEDC",starttime=starttime,endtime=endtime,mindepth=mindepth,maxdepth=maxdepth,minmagnitude=minmagnitude,maxmagnitude=maxmagnitude,latitude=latitude,longitude=longitude,minradius=minradius,maxradius=maxradius,orderby="mag")
cat.write(tmpfile,format="CNV")

i=0
with open(tmpfile,"r") as events:
        for event in events:
            if(event != "\n"):
                i+=1
                client = Client("SCEDC")
                event = event.strip("\n")
                ymd, hm, s, lat, lon , dep, mag, jk = event.split() # Datos del evento (sismo)
                year="20"+ymd[:2]
                month=ymd[2:4]
                day=ymd[4:6]
                hour=hm[:2]
                minutes=hm[2:4]
                sec,msec=s.split(".")
                if (len(sec)<2):
                    sec="0"+sec
                evla=lat[:7] # Latitud
                evlo=lon[:8] # Longitud
                evdp=dep # Profundidad [km]
                evmag=mag # Magnitud sismica en escala Richter
                out.write('{}{}{}{}{}{}.{} {} -{} {} {}\n'.format(year, month,day,hour,minutes,sec,msec,evla,evlo,evdp,evmag))
                #download template
                client = Client("IRIS")
                tb = UTCDateTime(year+"-"+month+"-"+day+"T"+hour+":"+minutes+":"+sec+"."+msec)-10
                te = UTCDateTime(year+"-"+month+"-"+day+"T"+hour+":"+minutes+":"+sec+"."+msec)+50
                templatedir = "./Template/" + year+month+day+hour+minutes+sec+"."+msec + "-" + str(i) + "/"
                if not os.path.exists(templatedir):
                    os.makedirs(templatedir)
                with open(stationfile, "r") as f:
                        for station in f:
                            stlo, stla, net, sta, channels, elev = station.split()
                            chan0 = channels.split('.')
                            for chan1 in chan0:
                                print(sta,chan1)
                                try:
                                    st = client.get_waveforms(network=net, station=sta, channel=chan1,starttime=tb,endtime=te, location = '--')
                                    # Se crea un objeto Stream() de obspy, que funciona como una lista de objetos Trace()
                                    # Un objeto Trace() es un objeto de obspy que contiene datos de una serie continua (como un sismograma)
                                    st.detrend("demean")
                                    st.detrend("linear")
                                    st.filter('bandpass', freqmin=2, freqmax=8)
                                    #print(st[0].data)
                                    # El atributo data de un Trace() devuelve el arreglo de samples registrados (secuencia de valores numericos)
                                    st.write(filename=templatedir + net + '.' + sta + '.' + chan1,format="SAC")
                                    # SAC se trata de un formato binario usado por IRIS
                                    # Similar a un paquete de algun protocolo de red en el sentido de que contiene una cabecera y esta dividido en secciones para proporcionar los datos

                                    # La siguiente seccion se realiza para fijar estas variables en atributos del Trace() (en formato sac)
                                    # Estos datos no se guardan por si solos en los stats de los Trace(), asi que los guardamos nosostros; son datos de las estaciones en si, como stla, stlo, elev siendo la latitud, longitud y elevacion de la estacion tratada
                                    st1 = read(templatedir+ net + '.' + sta + '.' + chan1)
                                    st1[0].stats.sac.stla=stla
                                    st1[0].stats.sac.stlo=stlo
                                    st1[0].stats.sac.stel=elev
                                    st1[0].stats.sac.evla=evla
                                    st1[0].stats.sac.evlo="-"+evlo
                                    st1[0].stats.sac.evdp=evdp
                                    st1[0].stats.sac.mag=evmag				    
                                    st1[0].stats.sac.nzsec+=10
                                    st1[0].stats.sac.b=-10
                                    st1.write(filename=templatedir + net + '.' + sta + '.' + chan1,format="SAC")
                                    #st.plot()
                                except:
                                    print("doesn't exist:",sta, chan1)
os.remove(tmpfile)
