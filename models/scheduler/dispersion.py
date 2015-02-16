#!/usr/bin/env python

# Ilaria Todeschini, Chiara Lora, Gianluca Antonacci - CISMA Srl
# Ultima revisione 2015-02-10

import psycopg2
import psycopg2.extras
from subprocess import call
import os

def pasquill(vel,rad,month):
    """
    Calcola la classe di stabilita atmosferica di Pasquill 
    sulla base delle formule di Briggs, che servono a caline come input
    per il calcolo della dispersione.
    """
    if (rad >0.):
        if (vel < 2.):
            if(rad > 540.) :
                pasquill = 1
            elif (rad <= 540. and rad > 270.) :
                pasquill = 2
            elif (rad <= 270. and rad > 140.) :
                pasquill = 3
            else:
                pasquill = 4
        elif(vel >= 2. and vel < 3.) :
                if (rad > 700.):
                    pasquill = 1
                elif(rad <= 700. and rad > 270.) :
                        pasquill = 2
                elif (rad <= 270. and rad > 140.) :
                        pasquill = 3
                else:
                        pasquill = 4
        elif (vel >= 3. and vel < 4.) :
                if (rad > 400.) :
                    pasquill = 2
                elif (rad <= 400. and rad > 140.) :
                    pasquill = 3
                else:
                    pasquill = 4
        elif (vel >= 4. and vel < 5.) :
                if (rad > 540.) :
                    pasquill = 2
                elif (rad <= 540. and rad > 270.) :
                    pasquill = 3
                else:
                    pasquill = 4
        elif (vel >= 5. and vel < 6.) :
                if (rad > 270.) :
                        pasquill = 3
                else:
                        pasquill = 4
        else:
                if (rad > 540.) :
                    pasquill = 3
                else:
                    pasquill = 4
    else:
        if (month >= 1 and month <= 3 or month >= 9 and month <= 12) :
            if (vel < 1.) :
                pasquill = 6
            elif (vel >= 1. and vel < 3.) :
                pasquill = 5
            else:
                pasquill = 4
        else:
            if (vel < 1.) :
                pasquill = 5
            elif (vel >= 1. and vel < 3.) :
                pasquill = 4
            else:
                pasquill = 4
    return pasquill

def mixheight(pasq):
    """
    Calcola la mixing height
    sulla base della classe di stabilita di Pasquill.
    """
    if (pasq ==1):
        mixheight = 3000.
    elif(pasq==2):
        mixheight = 1500.
    elif(pasq==3):
        mixheight = 800.
    elif(pasq==4):
        mixheight = 500.
    elif(pasq==5):
        mixheight = 300.
    else:
        mixheight = 200.
    return mixheight

# MAIN PROGRAM
def intime_dispersion_model():
    #apro il file di testo che sara l'input per caline per il calcolo degli NOx e PM10
    fileinputNOX_name = 'input_caline_NOx.txt'
    fileinputPM10_name = 'input_caline_PM10.txt'
    fileinputNOX = os.path.join(request.folder, 'dispersion/%s' % fileinputNOX_name)
    fileinputPM10 = os.path.join(request.folder, 'dispersion/%s' % fileinputPM10_name)
    fileoutputNOX = 'output_caline_NO2.asc' # output gia' convertito NOx (emissione) -> NO2 (immissione)
    fileoutputPM10 = 'output_caline_PM10.asc'
    filelogNOX = 'caline_NOx.log'
    filelogPM10 = 'caline_PM10.log'
    fileCalineMask = os.path.join(request.folder, 'dispersion/caline_mask.txt')

    fwNOx = open(fileinputNOX, "w")
    fwPM10 = open(fileinputPM10, "w")

    #scrivo nei due file di input per caline la prima parte che rimane fissa a ogni simulazione
    print "Inizio scrittura file input CALINE..."
    fwNOx.write('#Sito' + '\n')
    fwNOx.write('Bolzano' + '\n')
    fwNOx.write('#Inquinante' + '\n')
    fwNOx.write('NOx' + '\n')
    fwNOx.write('#microg/m3 -> 0; PPM -> 1' + '\n')
    fwNOx.write('0' + '\n')
    fwNOx.write('#Peso molecolare (serve solo se PPM)' + '\n')
    fwNOx.write('46' + '\n')
    fwNOx.write('#Tempo di media [s]; z0 [cm]' + '\n')
    fwNOx.write('60. 150.' + '\n')
    fwNOx.write('#velocita di caduta, velocita di deposizione [cm/s]' + '\n')
    fwNOx.write('1.9 0.' + '\n')
    fwNOx.write('#passo di griglia recettori: Est, Nord [m]' + '\n')
    fwNOx.write('50 50' + '\n')
    fwPM10.write('#Sito' + '\n')
    fwPM10.write('Bolzano' + '\n')
    fwPM10.write('#Inquinante' + '\n')
    fwPM10.write('PM10' + '\n')
    fwPM10.write('#microg/m3 -> 0; PPM -> 1' + '\n')
    fwPM10.write('0' + '\n')
    fwPM10.write('#Peso molecolare (serve solo se PPM)' + '\n')
    fwPM10.write('46' + '\n')
    fwPM10.write('#Tempo di media [s]; z0 [cm]' + '\n')
    fwPM10.write('60. 150.' + '\n')
    fwPM10.write('#velocita di caduta, velocita di deposizione [cm/s]' + '\n')
    fwPM10.write('1.9 0.' + '\n')
    fwPM10.write('#passo di griglia recettori: Est, Nord [m]' + '\n')
    fwPM10.write('50 50' + '\n')

    # Leggo il file della maschera da applicare nel calcolo della concentrazione in caline
    # EVENTUALMENTE SI PUO' LEGGERE LA MASCHERA DAL DB, MA SERVE AGGIUNGERE UNA TABELLA
    print "  * Lettura file maschera di calcolo"
    mask = open(fileCalineMask, "r")
    lines = mask.readlines()
    fwNOx.write('#N. segmenti maschera' + '\n')
    fwNOx.write(str(len(lines)) + '\n')
    fwNOx.write('#x/y segmenti maschera [m]' + '\n')
    fwPM10.write('#N. segmenti maschera' + '\n')
    fwPM10.write(str(len(lines)) + '\n')
    fwPM10.write('#x/y segmenti maschera [m]' + '\n')
    for i in lines:
        s = i.strip()
        fwNOx.write(s + '\n')
        fwPM10.write(s + '\n')
    mask.close()
    fwNOx.write('#Quota recettori sul terreno [m]' + '\n')
    fwNOx.write('1.5' + '\n')
    fwNOx.write('#N. link lineari' + '\n')
    fwPM10.write('#Quota recettori sul terreno [m]' + '\n')
    fwPM10.write('1.5' + '\n')
    fwPM10.write('#N. link lineari' + '\n')

    print "  * Lettura grafo stradale ed emissioni"
    # Lettura il grafo stradale e le relative emissioni calcolate con il modulo precedente
    # dove la query non restituisce risultato (dato traffico non presente?) poniamo emissione pari a zero
    archi = db_intime(db_intime.streetbasicdata).select(db_intime.streetbasicdata.station_id, 
                                                             orderby=db_intime.streetbasicdata.station_id)
   
    nsegmenti = db_intime(db_intime.streetbasicdata).select(db_intime.streetbasicdata.linegeometry.st_npoints())
    nsegmentiL = [r[db_intime.streetbasicdata.linegeometry.st_npoints()] for r in nsegmenti]

    nlink = reduce(lambda n,m:n+m, nsegmentiL)-len(archi)

    # ciclo sul numero di archi
    fwNOx.write(str(nlink) + '\n')
    fwPM10.write(str(nlink) + '\n')
    fwNOx.write('#Nome    tipo x1     y1      x2     y2       g/km/h h[m] l[m]' + '\n')
    fwPM10.write('#Nome    tipo x1     y1      x2     y2       g/km/h h[m] l[m]' + '\n')
    print "  * Numero archi: %s" % len(archi)
    eh = db_intime.elaborationhistory
    for j, arco in enumerate(archi):
        #    NOx
        em_nox = db_intime( (eh.type_id == 44) &
                            (eh.period == 3600) &
                            (eh.station_id == arco.station_id)).select(eh.timestamp, eh.value, limitby=(0,1), orderby=~eh.timestamp).first()

        em_nox = em_nox.value if em_nox else 0

        #    PM10
        em_pm10 = db_intime( (eh.type_id == 42) &
                            (eh.period == 3600) &
                            (eh.station_id == arco.station_id)).select(eh.timestamp, eh.value, limitby=(0,1), orderby=~eh.timestamp).first()

        em_pm10 = em_pm10.value if em_pm10 else 0                     
        
        # link geometry data
        st_x = db_intime.streetbasicdata.linegeometry.st_dumppoints().st_x()
        st_y = db_intime.streetbasicdata.linegeometry.st_dumppoints().st_y()
        st_npoints = db_intime.streetbasicdata.linegeometry.st_npoints()
        geo_data = db_intime( (db_intime.streetbasicdata.station_id == arco.station_id)).select(st_x, st_y, st_npoints)
        
        for i in range(0, len(geo_data) -1):
            link = geo_data[i]
            link_n = geo_data[i+1]
            # scrivo nei file per caline l'elenco dei segmenti (link) su cui verra' eseguito il calcolo
            fwNOx.write("LINK"+ "%3.3i" %(arco.station_id)+"_%2.2i" %(i+1)+" AG "+"%12.3f" %(link[st_x])+" "+"%12.3f" %(link[st_y])+" "+"%12.3f" %(link_n[st_x])+" "+" "+"%12.3f" %(link_n[st_y])+" "+ "%10.2f" %(em_nox)+" 0.5 5.0"'\n')
            fwPM10.write("LINK"+ "%3.3i" %(arco.station_id)+"_%2.2i" %(i+1)+" AG "+"%12.3f" %(link[st_x])+" "+"%12.3f" %(link[st_y])+" "+"%12.3f" %(link_n[st_x])+" "+" "+"%12.3f" %(link_n[st_y])+" "+ "%10.2f" %(em_pm10)+" 0.5 5.0"'\n')
        
    print "  * Lettura dati meteo"
    # leggo dal DB meteo le informazioni che mi servono (velocita' e direzione del vento, radiazione globale, mese corrente)
    mh = db_intime.measurementhistory
    wd = db_intime( (mh.type_id == 6) &
                    (mh.station_id == 23)).select(mh.value, limitby=(0,1), orderby=~mh.timestamp).first()
    value_dir = wd.value if wd else 0

    ws = db_intime( (mh.type_id == 2) &
                    (mh.station_id == 23)).select(mh.value, limitby=(0,1), orderby=~mh.timestamp).first()
    value_vel = ws.value if ws else 0

    rg = db_intime( (mh.type_id == 3) &
                    (mh.station_id == 23)).select(mh.timestamp.month(), mh.value, limitby=(0,1), orderby=~mh.timestamp).first()

    month = rg[mh.timestamp.month()] if rg else 1
    value_rad = rg[mh.value] if rg else 0

    print "  * Calcolo stabilita' atmosferica"
    # Calcolo la classe di stabilita di Pasquill sulla base di radiazione, velocita del vento e mese dell'anno; Calcolo l'altezza di mescolamento
    classe_pasq = pasquill(value_vel,value_rad,month)
    mixing_height = mixheight(classe_pasq)

    # Srivo nei file per caline la parte riguardante il meteo
    fwNOx.write('#N. sorgenti areali' + '\n')
    fwNOx.write('0' + '\n')
    fwNOx.write('#Nome    tipo x1     y1      x2     y2   veh/h    g/km/veh h[m] l[m]' + '\n')
    fwNOx.write('#N. scenari meteo' + '\n')
    fwNOx.write('1' + '\n')
    fwNOx.write('#v [m/s], dir [gradiN], stabilita [-], mixh [m], conc. fondo [microg/m3], frequenza [-]' + '\n')
    fwNOx.write("%6.2f" %(value_vel)+ "%6.1f" %(value_dir)+ ' '+"%1i" %(classe_pasq)+ "%8.1f" %(mixing_height)+' 0.0 1'+ '\n')
    fwPM10.write('#N. sorgenti areali' + '\n')
    fwPM10.write('0' + '\n')
    fwPM10.write('#Nome    tipo x1     y1      x2     y2   veh/h    g/km/veh h[m] l[m]' + '\n')
    fwPM10.write('#N. scenari meteo' + '\n')
    fwPM10.write('1' + '\n')
    fwPM10.write('#v [m/s], dir [gradiN], stabilita [-], mixh [m], conc. fondo [microg/m3], frequenza [-]' + '\n')
    fwPM10.write("%6.2f" %(value_vel)+ "%6.1f" %(value_dir)+ ' '+"%1i" %(classe_pasq)+ "%8.1f" %(mixing_height)+' 0.0 1'+ '\n')
    fwNOx.close()
    fwPM10.close()
    print "Fine scrittura file input CALINE\n"

    # eseguo CALINE
    # "t" -> verbose output, "f" -> non verbose
    print "Run modello CALINE NOx..."
    caline_file = os.path.join(request.folder, "dispersion/caline_mod2")
    
    call([caline_file, fileinputNOX, fileoutputNOX, filelogNOX, "f"])
    print "Fine modello CALINE NOx\n"
    print "Run modello CALINE PM10..."
    call([caline_file, fileinputPM10, fileoutputPM10, filelogPM10, "f"])
    print "Fine modello CALINE PM10\n"
    
    # gdal_translate -co "TILED=YES" -co "BLOCKXSIZE=512" -co "BLOCKYSIZE=512"
    # output_caline_NO2.asc output_caline_NO2.tiff

