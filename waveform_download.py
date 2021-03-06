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
import obspy
import shutil
from pathlib import Path
import re, os, shutil, glob
from events import parse_event

#User-specied
#Datos de el/los eventos que quieren estudiarse (ubicacion y parametros de seleccion de datos)
#end_time = datetime.datetime.now() 
#start_time = end_time-datetime.timedelta(hours=24) # Intervalo de busqueda desde 12 horas anteriores a la actual
#starttime = UTCDateTime(start_time.isoformat())
#print(start_time.isoformat())
#endtime = UTCDateTime(end_time.isoformat())
#mtime = datetime.datetime.strptime(item["time_tag"],'%Y-%m-%dT%H:%M:%SZ')t
#mindepth = 0
#maxdepth = 100
#minmagnitude=2
#maxmagnitude=7

#maxmagnitude=9
#latitude=15
#longitude=-90
#minradius=0
#maxradius=10
tmpfile="tmp.catalog"
catalog="catalog.dat"
stationfile = "STATIONS.sta"
#tmpstations = "STATIONS.xml"
out = open(catalog,"w")
print(1)
#client = Client("SCEDC") # Southern California
#request catalog
client = Client("IRIS")
with open(tmpfile,"r") as events:
        i=1
        for event in events:
            if(event != "\n"):
                #download template
                #client = Client("IRIS")
                year, month, day, hour, minutes, sec, msec, evla, evlo, evdp, evmag = parse_event(event)
                tb = UTCDateTime(year+"-"+month+"-"+day+"T"+hour+":"+minutes+":"+sec+"."+msec)-10
                te = UTCDateTime(year+"-"+month+"-"+day+"T"+hour+":"+minutes+":"+sec+"."+msec)+20
                out.write('{}{}{}{}{}{}.{} {} -{} {} {}\n'.format(year, month,day,hour,minutes,sec,msec,evla,evlo,evdp,evmag))
                templatedir = "./Template/" + year+month+day+hour+minutes+sec+ "-" + str(i) + "/"
                i+=1
                if not os.path.exists(templatedir):
                    os.makedirs(templatedir)
                with open(stationfile, "r") as f:
                        for station in f:
                            stlo, stla, net, sta, channels, elev = station.split()
                            stationdir = sta + '/'
                            if not os.path.exists(templatedir + stationdir):
                                os.makedirs(templatedir + stationdir)
                            chan0 = channels.split('.')
                            cont = 0
                            for chan1 in chan0:
                                print(sta,chan1)
                                #st = client.get_waveforms(network=net, station=sta, channel=chan1,starttime=tb,endtime=te, location='--')
                                try:
                                    st = client.get_waveforms(network=net, station=sta, channel=chan1,starttime=tb,endtime=te, location='--')
                                    # Se crea un objeto Stream() de obspy, que funciona como una lista de objetos Trace()
                                    # Un objeto Trace() es un objeto de obspy que contiene datos de una serie continua (como un sismograma)
                                    #st.detrend("demean")
                                    #st.detrend("linear")
                                    #st.filter('bandpass', freqmin=2, freqmax=8)
                                    st.detrend()
                                    st.taper(max_percentage=0.05)
                                    st.filter("highpass", freq=2.0, zerophase=True)
                                    #print(st[0].data)
                                    # El atributo data de un Trace() devuelve el arreglo de samples registrados (secuencia de valores numericos)
                                    print(templatedir + stationdir + chan1)
                                    st.write(filename=templatedir + stationdir + chan1,format="SAC")
                                    my_file = Path(templatedir + stationdir + chan1+'01')
                                    if my_file.is_file():
                                            # En caso de generarse muchos archivos por canal, cuyo comportamiento es desconocido
                                            print("Deleted incompatible format files")
                                            shutil.rmtree(templatedir+stationdir)
                                            break
                                    # SAC se trata de un formato binario usado por IRIS
                                    # Similar a un paquete de algun protocolo de red en el sentido de que contiene una cabecera y esta dividido en secciones para proporcionar los datos

                                    # La siguiente seccion se realiza para fijar estas variables en atributos del Trace() (en formato sac)
                                    # Estos datos no se guardan por si solos en los stats de los Trace(), asi que los guardamos nosostros; son datos de las estaciones en si, como stla, stlo, elev siendo la latitud, longitud y elevacion de la estacion tratada
                                    
                                    st1 = read(templatedir + stationdir + chan1)
                                    st1[0].stats.sac.stla=stla
                                    st1[0].stats.sac.stlo=stlo
                                    st1[0].stats.sac.stel=elev
                                    st1[0].stats.sac.evla=evla
                                    st1[0].stats.sac.evlo=evlo
                                    st1[0].stats.sac.evdp=evdp
                                    st1[0].stats.sac.mag=evmag				    
                                    st1[0].stats.sac.nzsec+=10
                                    st1[0].stats.sac.b=-10
                                    #if i==1:
                                    #        st1.spectrogram(show=True, log=True) 
                                    st1.write(filename=templatedir + stationdir + chan1,format="SAC")
                                    #st.plot()
                                except (obspy.clients.fdsn.header.FDSNNoDataException, obspy.clients.fdsn.header.FDSNException) as e:
                                    cont+=1
                                    if cont == len(chan0):
                                             shutil.rmtree(templatedir+stationdir)
                                    print("doesn't exist:",sta, chan1)

#os.remove(tmpfile)
