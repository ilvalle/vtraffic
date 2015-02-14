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
    fileinputNOX = os.path.join(request.folder, 'dispersion/input_caline_NOx.txt')
    fileinputPM10 = os.path.join(request.folder, 'input_caline_PM10.txt')
    fileoutputNOX = os.path.join(request.folder, 'output_caline_NO2.asc') # output gia' convertito NOx (emissione) -> NO2 (immissione)
    fileoutputPM10 = os.path.join(request.folder, 'output_caline_PM10.asc')
    filelogNOX = os.path.join(request.folder, 'caline_NOx.log')
    filelogPM10 = os.path.join(request.folder, 'caline_PM10.log')
    fileCalineMask = os.path.join(request.folder, "caline_mask.txt")

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
    conn_string = "dbname='integreenintime'"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sqlwid = "SELECT station_id from intime.streetbasicdata order by station_id asc;"
    cursor.execute(sqlwid)
    arco_id = cursor.fetchall()
    sqlwnp_tot = "SELECT ST_NPoints(\"linegeometry\") from intime.streetbasicdata;"
    cursor.execute(sqlwnp_tot)
    nsegmenti = cursor.fetchall()
    nlink = reduce(lambda n,m:n+m,reduce(lambda n,m:n+m,nsegmenti))-len(arco_id)
    # ciclo sul numero di archi
    fwNOx.write(str(nlink) + '\n')
    fwPM10.write(str(nlink) + '\n')
    fwNOx.write('#Nome    tipo x1     y1      x2     y2       g/km/h h[m] l[m]' + '\n')
    fwPM10.write('#Nome    tipo x1     y1      x2     y2       g/km/h h[m] l[m]' + '\n')
    print "  * Numero archi: ",len(arco_id)
    for j in range (0, len(arco_id)):
    #	NOx
	    sql = "select * from intime.elaborationhistory where type_id=44 and period=3600 and station_id="+str(arco_id[j][0])+" order by timestamp desc limit 1;"
	    cursor.execute(sql)
	    liststr = cursor.fetchall()
	    if (len(liststr)==0):
		    em_nox=0
	    else:
		    em_nox=liststr[0][3]
    #	PM10
	    sql = "select * from intime.elaborationhistory where type_id=42 and period=3600 and station_id="+str(arco_id[j][0])+" order by timestamp desc limit 1;"
	    cursor.execute(sql)
	    liststr = cursor.fetchall()
	    if (len(liststr)==0):
		    em_pm10=0
	    else:
		    em_pm10=liststr[0][3]
	    sqlwx = "SELECT ST_X ( (ST_DumpPoints(\"linegeometry\")).geom ) as geom from intime.streetbasicdata where station_id="+str(arco_id[j][0])+";"
	    cursor.execute(sqlwx)
	    valueX = cursor.fetchall()
	    sqlwy = "SELECT ST_Y ( (ST_DumpPoints(\"linegeometry\")).geom ) as geom from intime.streetbasicdata where station_id="+str(arco_id[j][0])+";"
	    cursor.execute(sqlwy)
	    valueY = cursor.fetchall()
	    sqlwnp = "SELECT ST_NPoints(\"linegeometry\") from intime.streetbasicdata where station_id="+str(arco_id[j][0])+";"
	    cursor.execute(sqlwnp)
	    npoints = cursor.fetchall()
	    for i in range (0, npoints[0][0]-1):
    #		scrivo nei file per caline l'elenco dei segmenti (link) su cui verra' eseguito il calcolo
		    fwNOx.write("LINK"+ "%3.3i" %(arco_id[j][0])+"_%2.2i" %(i+1)+" AG "+"%12.3f" %(valueX[i][0])+" "+"%12.3f" %(valueY[i][0])+" "+"%12.3f" %(valueX[i+1][0])+" "+" "+"%12.3f" %(valueY[i+1][0])+" "+ "%10.2f" %(em_nox)+" 0.5 5.0"'\n')
		    fwPM10.write("LINK"+ "%3.3i" %(arco_id[j][0])+"_%2.2i" %(i+1)+" AG "+"%12.3f" %(valueX[i][0])+" "+"%12.3f" %(valueY[i][0])+" "+"%12.3f" %(valueX[i+1][0])+" "+" "+"%12.3f" %(valueY[i+1][0])+" "+ "%10.2f" %(em_pm10)+" 0.5 5.0"'\n')
    conn.commit()
    conn.close()

    print "  * Lettura dati meteo"
    # leggo dal DB meteo le informazioni che mi servono (velocita' e direzione del vento, radiazione globale, mese corrente)
    conn_string = "dbname='integreenintime'"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sqlwd = "select * from intime.measurementhistory where station_id=23 and type_id=6 order by timestamp desc limit 1;"
    sqlws = "select * from intime.measurementhistory where station_id=23 and type_id=2 order by timestamp desc limit 1;"
    sqlrg = "select * from intime.measurementhistory where station_id=23 and type_id=3 order by timestamp desc limit 1;"
    cursor.execute(sqlwd)
    value_dir = cursor.fetchall()[0][3]
    cursor.execute(sqlws)
    value_vel = cursor.fetchall()[0][3]
    cursor.execute(sqlrg)
    res = cursor.fetchall()
    value_rad = res[0][3]
    month = res[0][2].month
    conn.commit()
    conn.close()

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
    caline_file = os.path.join(request.folder, "caline_mod2")
    call([caline_file, fileinputNOX, fileoutputNOX, filelogNOX, "t"])
    print "Fine modello CALINE NOx\n"
    print "Run modello CALINE PM10..."
    call([caline_file, fileinputPM10, fileoutputPM10, filelogPM10, "t"])
    print "Fine modello CALINE PM10\n"
