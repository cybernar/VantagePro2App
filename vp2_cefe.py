#!/usr/bin/env python
# -*- coding:Utf-8 -*-
#
# METEO TE CEFE
# Script principal
#
# Auteur : Cyril BERNARD, CEFE-CNRS, 06/2015 (cyril.bernard@cefe.cnrs.fr)
#

import sys
import logging
import psycopg2
import datetime as dt
import ConfigParser as cg

from pyvantagepro import VantagePro2
from vp2_graph import GraphInstant, Graph24h, GraphCumul

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.cm as cm

def farenheit2celsius(temperature_f):
	if temperature_f is None:
		temperature_c = None
	else:
		temperature_c = (temperature_f - 32) * 5 / 9
	return temperature_c

def inHg2hPa(pression_inHg):
	if pression_inHg is None:
		pression_hPa = None
	else:
		pression_hPa = (1013.25 / 29.92) * pression_inHg
	return pression_hPa

def mph2kph(vitesse_mph):
	if vitesse_mph is None:
		vitesse_kph = None
	else:
		vitesse_kph = vitesse_mph * 1.609344
	return vitesse_kph

def click2mm(precipitation_in):
	if precipitation_in is None:
		precipitation_mm = None
	else:
		precipitation_mm = precipitation_in * 0.2
	return precipitation_mm

def rainfall_correction(rainfall, rain_rate_hi):
	# precipitations corrigees (paramètres en mm)
	if (rain_rate_hi < 25):
		rain_corrige = rainfall
	elif (rain_rate_hi >= 25 and rain_rate_hi < 50):
		rain_corrige = rainfall * 1.04
	else:
		rain_corrige = rainfall * 1.05
	return rain_corrige
	
def degToCompass(direction_deg):
	direction_compass = None
	if direction_deg is None:
		direction_compass = None
	elif direction_deg == 0:
		direction_compass = "---"
	else:
		val = int((direction_deg / 22.5) + .5)
		arr= ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSO","SO","OSO","O","ONO","NO","NNO"]
		direction_compass = arr[(val % 16)]
	return direction_compass

def dirToCompass(direction_code):
	if direction_code is None:
		return "---"
	else:
		arr= ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSO","SO","OSO","O","ONO","NO","NNO"]
		return arr[direction_code]


# PROGRAMME PRINCIPAL
if __name__ == "__main__":
	try:

		# Lecture Paramètres configuration
		conf = cg.ConfigParser()
		#conf.read("E:\\PyMeteo\\meteo_te.cfg")
		conf.read("D:\\Travail2\\meteo_te\\Python\\PyMeteo\\meteo_te.cfg")
		
		# connexion Weatherlink
		CONSOLE_IP_PORT = "tcp:%s:%s" % (conf.get("console_vp2","ip"), conf.get("console_vp2","port"))
		# chemin d'acces du fichier de log
		CHEMIN_ACCES_FICHIER_LOG = conf.get("fichiers_sortie","f_logs")
		# connexion BD PostgreSQL
		BD_CONNEXION = "host=%s dbname=%s user=%s password=%s" % (conf.get("pg_conn","host"), conf.get("pg_conn","dbname"), conf.get("pg_conn","user"), conf.get("pg_conn","password"))
		# repertoire stockage graphiques (pour site www)
		CHEMIN_ACCES_REPERTOIRE_WEB = conf.get("fichiers_sortie","d_images")
		# intervalle de telechargement des donnees (en minutes)
		INTERVALLE_TELECHARGEMENT = int(conf.get("autres","intervalle_telechargement"))
	
		logging.basicConfig(filename=CHEMIN_ACCES_FICHIER_LOG, level=logging.DEBUG, format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
		logging.debug("********** DEBUG PyVantagePro **********")

		# se connecter à la station via WeatherLinkIP
		device = VantagePro2.from_url(CONSOLE_IP_PORT)
		# charger les donnees actuelles
		data = device.get_current_data()
		dictConditionsMeteo = {}
		# heure station
		dtStation = data['Datetime']
		strDateHeureReleve = dtStation.strftime('%d/%m/%Y %H:%M')
		batteryStatus = data['BatteryVolts']
		logging.debug("Date/heure station : %s - Batterie : %.1f volts" , strDateHeureReleve, batteryStatus)
		# recueil données instantanées : température, baromètre, soleil, vent
		#dictConditionsMeteo = {}
		# filtrer les données
		data['TempOut'] = None if data['TempOut'] == 3276.7 else data['TempOut']
		data['Barometer'] = None if data['Barometer'] == 0 else data['Barometer']
		data['HumOut'] = None if data['HumOut'] == 255 else data['HumOut']
		data['SolarRad'] = None if data['SolarRad'] == 32767 else data['SolarRad']
		data['UV'] = None if data['UV'] == 255 else (data['UV'] / 10)
		data['WindSpeed10Min'] = None if data['WindSpeed10Min'] == 255 else data['WindSpeed10Min']
		data['WindDir'] = None if data['WindDir'] == 32767 else data['WindDir']
		# conversion unités
		data['TempOut'] = farenheit2celsius(data['TempOut'])
		data['Barometer'] = inHg2hPa(data['Barometer'])
		data['WindSpeed10Min'] = mph2kph(data['WindSpeed10Min'])
		data['WindDirStr'] = degToCompass(data['WindDir'])

		try:
			# MATPLOTLIB NOW : données instant
			logging.debug("Générer les graphs instant")
			gi = GraphInstant(data)
			# génération des graphiques : date et heure dernier relevé
			gi.genere_graph_heure_releve(CHEMIN_ACCES_REPERTOIRE_WEB + 'date_heure_releve.png')
			# génération des graphiques : température, baromètre, soleil
			gi.genere_graph_conditions_actuelles(CHEMIN_ACCES_REPERTOIRE_WEB + 'conditions_actuelles.png')
			# génération des graphiques : données vent
			gi.genere_graph_vent(CHEMIN_ACCES_REPERTOIRE_WEB + 'vent.png')
			# génération des graphiques : données pluie
			#genereGraph_precipitations(dictConditionsMeteo, CHEMIN_ACCES_REPERTOIRE_WEB + "precipitations.png")
		except Exception as e:
			logging.error("Erreur inattendue - %s", e)

		# BASE DE DONNEES
		# connexion pgsql
		connect_pg = psycopg2.connect(BD_CONNEXION)
		pg_curs = connect_pg.cursor()

		# lire heure dernier releve
		reqSQL = "SELECT max(_date + _time) AS dt_last FROM meteo.donnees_brutes_30min"
		pg_curs.execute(reqSQL)
		recDerniereMesure = pg_curs.fetchone()
		dtLastRec = recDerniereMesure[0]
		strDateHeureLast = dtLastRec.strftime('%d/%m/%Y %H:%M')
		logging.debug("Date/heure LastRec : %s" , strDateHeureLast)
		
		# si 30 min ou + entre le temps de la derniere mesure dans la BD, et le temps actuel de la station
		# alors télécharger les dernières données !
		deltaT = dt.timedelta(minutes=INTERVALLE_TELECHARGEMENT)		
		
		if (dtStation >= (dtLastRec + deltaT)):
			# on logge le statut batterie et la date
			reqSQL = "INSERT INTO meteo.log_records (_datetime, battery_status) "
			reqSQL = reqSQL + "VALUES (%s, %s) RETURNING logid;"
			valReqSQL = (dtStation, batteryStatus)
			logging.debug("SQL - %s", pg_curs.mogrify(reqSQL, valReqSQL))
			pg_curs.execute(reqSQL, valReqSQL)
			logid = pg_curs.fetchone()[0]
			logging.debug("logid = %s", logid)

			# on relève les derniers totaux precipitations
			reqSQL = "SELECT dt_last_rec, sum_rain_year, sum_rain_month, sum_rain_day FROM meteo.total_precipitations WHERE id_mesure = 0;"
			pg_curs.execute(reqSQL)
			recPrec = pg_curs.fetchone()
			dtLastPrec = recPrec[0]
			sumRainYear = recPrec[1]
			sumRainMonth = recPrec[2]
			sumRainDay = recPrec[3]

			# on télécharge à partir de la dernière donnée
			logging.debug("Téléchargement données")
			data = device.get_archives(start_date=dtLastRec, stop_date=dtStation)
			logging.debug("%d données téléchargées", len(data))
			
			reqSQL = "INSERT INTO meteo.donnees_brutes_30min "
			reqSQL = reqSQL + "(packed_time, _date, _time, _date_synthese, outside_temp, hi_outside_temp, low_outside_temp, "
			reqSQL = reqSQL + "rain, hi_rain_rate, rain_corrige, barometer, solar_rad, wind_samples, inside_temp, "
			reqSQL = reqSQL + "inside_hum, outside_hum, wind_speed, hi_wind_speed, hi_wind_direction, hi_wind_direction_str, wind_direction, "
			reqSQL = reqSQL + "wind_direction_str, uv, et, hi_solar_rad, hi_uv, forecast_rule, archive_period, logid) "
			reqSQL = reqSQL + "VALUES (%s, %s, %s, %s, %s, %s, %s, "
			reqSQL = reqSQL + "%s, %s, %s, %s, %s, %s, %s, "
			reqSQL = reqSQL + "%s, %s, %s, %s, %s, %s, %s, "
			reqSQL = reqSQL + "%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_mesure;"
			#reqMAJ1 = "UPDATE meteo.donnees_brutes_30min SET _date_synthese = (_date + _time - interval '1 minute')::date WHERE (id_mesure = %s)";
			
			# parcourir les archives téléchargées
			pg_modif = 0
			for dataRec in data:
				dtRec = dataRec['Datetime']
				dtSynthese = (dataRec['Datetime'] - deltaT)
				packedTime = dtRec.hour * 60 + dtRec.minute
				dtRec_date = dtRec.date() #strftime('%d/%m/%Y')
				dtRec_time = dtRec.time() #strftime('%H:%M')
				dtSynthese_date = dtSynthese.date() #strftime('%d/%m/%Y')
				
				# filtrer les données
				dataRec['WindHiDir'] = None if dataRec['WindHiDir'] == 255 else dataRec['WindHiDir']
				dataRec['WindAvgDir'] = None if dataRec['WindAvgDir'] == 255 else dataRec['WindAvgDir']
				dataRec['TempOut'] = None if dataRec['TempOut'] == 3276.7 else dataRec['TempOut']
				dataRec['TempOutHi'] = None if dataRec['TempOutHi'] == 3276.8 else dataRec['TempOutHi']
				dataRec['TempOutLow'] = None if dataRec['TempOutLow'] == 3276.7 else dataRec['TempOutLow']
				dataRec['Barometer'] = None if dataRec['Barometer'] == 0 else dataRec['Barometer']
				dataRec['SolarRad'] = None if dataRec['SolarRad'] == 32767 else dataRec['SolarRad']
				dataRec['TempIn'] = None if dataRec['TempIn'] == 3276.7 else dataRec['TempIn']
				dataRec['HumIn'] = None if dataRec['HumIn'] == 255 else dataRec['HumIn']
				dataRec['HumOut'] = None if dataRec['HumOut'] == 255 else dataRec['HumOut']
				dataRec['WindAvg'] = None if dataRec['WindAvg'] == 255 else dataRec['WindAvg']
				dataRec['WindHi'] = None if dataRec['WindHi'] == 0 else dataRec['WindHi']
				dataRec['WindHiDir'] = None if dataRec['WindHiDir'] == 255 else dataRec['WindHiDir']
				dataRec['WindAvgDir'] = None if dataRec['WindAvgDir'] == 255 else dataRec['WindAvgDir']
				dataRec['UV'] = None if dataRec['UV'] == 25.5 else dataRec['UV']
				dataRec['ETHour'] = None if dataRec['ETHour'] == 32.767 else dataRec['ETHour']
				dataRec['SolarRadHi'] = None if dataRec['SolarRadHi'] == 32767 else dataRec['SolarRadHi']
				dataRec['UVHi'] = None if dataRec['UVHi'] == 255 else dataRec['UVHi'] / 10
				dataRec['ForecastRuleNo'] = None if dataRec['ForecastRuleNo'] == 193 else dataRec['ForecastRuleNo']

				# conversion unites
				dataRec['TempOut'] = farenheit2celsius(dataRec['TempOut'])
				dataRec['TempOutHi'] = farenheit2celsius(dataRec['TempOutHi'])
				dataRec['TempOutLow'] = farenheit2celsius(dataRec['TempOutLow'])
				dataRec['Barometer'] = inHg2hPa(dataRec['Barometer'])
				dataRec['RainRate'] = click2mm(dataRec['RainRate'])
				dataRec['RainRateHi'] = click2mm(dataRec['RainRateHi'])
				dataRec['WindAvg'] = mph2kph(dataRec['WindAvg'])
				dataRec['WindHi'] = mph2kph(dataRec['WindHi'])	
				# precipitations corrigees
				rain_corrige = rainfall_correction(dataRec['RainRate'], dataRec['RainRateHi'])

				# direction du vent
				strWindAvgDir = dirToCompass(dataRec['WindAvgDir'])
				strWindHiDir = dirToCompass(dataRec['WindHiDir'])
				
				# EXECUTION INSERT INTO donnees_brutes dataRec[''], 
				valReqSQL = (packedTime, dtRec_date, dtRec_time, dtSynthese_date, dataRec['TempOut'], dataRec['TempOutHi'], dataRec['TempOutLow'], 
					dataRec['RainRate'], dataRec['RainRateHi'], rain_corrige, dataRec['Barometer'], dataRec['SolarRad'], dataRec['WindSamps'], dataRec['TempIn'], 
					dataRec['HumIn'], dataRec['HumOut'], dataRec['WindAvg'], dataRec['WindHi'], dataRec['WindHiDir'], strWindHiDir, dataRec['WindAvgDir'], 
					strWindAvgDir, dataRec['UV'], dataRec['ETHour'], dataRec['SolarRadHi'], dataRec['UVHi'], dataRec['ForecastRuleNo'], INTERVALLE_TELECHARGEMENT, logid)
				logging.debug("SQL - %s", pg_curs.mogrify(reqSQL, valReqSQL))
				pg_curs.execute(reqSQL, valReqSQL)
				#id_mesure = pg_curs.fetchone()[0]
				
				# MAJ TOTAUX PRECIPITATIONS
				dtLastPrec = dtRec
				sumRainYear += rain_corrige
				sumRainMonth += rain_corrige
				sumRainDay += rain_corrige
				
				# MAJ : date_synthese
				#valReqMAJ = (id_mesure,)
				#pg_curs.execute(reqMAJ1, valReqMAJ)
				pg_modif += 1
			
			# log nb de lignes ajoutées
			reqMAJLog = "UPDATE meteo.log_records SET nb_records = %s WHERE (logid = %s)";
			valReqMAJ = (len(data), logid)
			logging.debug("SQL - %s", pg_curs.mogrify(reqMAJLog, valReqMAJ))
			pg_curs.execute(reqMAJLog, valReqMAJ)
			# maj precipitations totales
			reqMAJPrec = "UPDATE meteo.total_precipitations "
			reqMAJPrec = reqMAJPrec + "SET (dt_last_rec, sum_rain_year, sum_rain_month, sum_rain_day) = " 
			reqMAJPrec = reqMAJPrec + "(%s, %s, %s, %s) "
			reqMAJPrec = reqMAJPrec + "WHERE id_mesure = 0;"
			valMAJPrec = (dtLastPrec, sumRainYear, sumRainMonth, sumRainDay)
			logging.debug("SQL - %s", pg_curs.mogrify(reqMAJPrec, valMAJPrec))
			pg_curs.execute(reqMAJPrec, valMAJPrec)
			# commit maj
			connect_pg.commit()
			logging.info("%d enregistrements ajoutés dans la table donnees_brutes", len(data))
			
			# SYNTHESE JOURNALIERE
			# si changement de jour
			# alors synthétiser les donnees journalieres à partir du dernier jour archivé
			# !! décaler de 30 min vers le jour précédent pour obtenir la date de synthèse !!
			dtStation = dtStation - deltaT
			dtLastRec = dtLastRec - deltaT
			if (dtStation.day != dtLastRec.day):
				# EXECUTION INSERT INTO donnees_journalieres2
				reqSQL = "INSERT INTO meteo.donnees_journalieres2 ("
				reqSQL = reqSQL + "_year, _month, _day, _date, max_outside_temp, min_outside_temp, avg_outside_temp, max_wind_speed, avg_wind_speed, "
				reqSQL = reqSQL + "sum_rain, sum_rain_corrige, min_barometer, max_barometer, avg_barometer, min_outside_hum, max_outside_hum, avg_outside_hum, "
				reqSQL = reqSQL + "max_solar_rad, avg_solar_rad, sum_et, archive_period, nb_mesures, automatic) "
				reqSQL = reqSQL + "SELECT "
				reqSQL = reqSQL + "extract(year from _date_synthese) as _year, extract(month from _date_synthese) as _month, extract(day from _date_synthese) as _day, _date_synthese, "
				reqSQL = reqSQL + "max(hi_outside_temp) as max_outside_temp, min(low_outside_temp) as min_outside_temp, avg(outside_temp)::real as avg_outside_temp, "
				reqSQL = reqSQL + "max(wind_speed) as max_wind_speed, avg(wind_speed)::real as avg_wind_speed, sum(rain) as sum_rain, sum(rain_corrige) as sum_rain_corrige, "
				reqSQL = reqSQL + "min(barometer) as min_barometer, max(barometer) as max_barometer, avg(barometer)::real as avg_barometer, "
				reqSQL = reqSQL + "min(outside_hum) as min_outside_hum, max(outside_hum) as max_outside_hum, avg(outside_hum)::real as avg_outside_hum, "
				reqSQL = reqSQL + "max(solar_rad) as max_solar_rad, avg(solar_rad)::real as avg_solar_rad, sum(et) as sum_et, "
				reqSQL = reqSQL + "avg(archive_period)::real as archive_period, count(id_mesure) as nb_mesures, TRUE as automatic "
				reqSQL = reqSQL + "FROM meteo.donnees_brutes_30min WHERE (_date_synthese >= %s AND _date_synthese < %s) "
				reqSQL = reqSQL + "GROUP BY _date_synthese "
				reqSQL = reqSQL + "ORDER BY _date_synthese ASC;"
				valReqSQL = (dtLastRec.date(), dtStation.date())
				logging.debug("SQL - %s", (pg_curs.mogrify(reqSQL, valReqSQL)))
				pg_curs.execute(reqSQL, valReqSQL)
				iNbEnreg = pg_curs.rowcount
				connect_pg.commit()
				logging.info("%d enregistrements ajoutés dans la table donnees_journalieres", iNbEnreg)

				# Recalculer les totaux précipitation : année, mois, jour
				if (true): #(dtStation.year != dtLastRec.year):
					reqMAJAn = "UPDATE meteo.total_precipitations "
					reqMAJAn = reqMAJAn + "SET sum_rain_year = ("
					reqMAJAn = reqMAJAn + "SELECT COALESCE(sum(rain_corrige),0) AS sum_rain_year "
					reqMAJAn = reqMAJAn + "FROM meteo.donnees_brutes_30min "
					reqMAJAn = reqMAJAn + "WHERE extract(year FROM _date_synthese)::smallint = %s);"
					valReqAn = (dtStation.year,)
					pg_curs.execute(reqMAJAn, valReqAn)
				if (true): #(dtStation.month != dtLastRec.month):
					reqMAJMois = "UPDATE meteo.total_precipitations "
					reqMAJMois = reqMAJMois + "SET sum_rain_month = ("
					reqMAJMois = reqMAJMois + "SELECT COALESCE(sum(rain_corrige),0) AS sum_rain_month "
					reqMAJMois = reqMAJMois + "FROM meteo.donnees_brutes_30min "
					reqMAJMois = reqMAJMois + "WHERE extract(year FROM _date_synthese)::smallint = %s AND extract(month FROM _date)::smallint = %s);"
					valReqMois = (dtStation.year, dtStation.month)
					pg_curs.execute(reqMAJMois, valReqMois)
				reqMAJJour = "UPDATE meteo.total_precipitations "
				reqMAJJour = reqMAJJour + "SET sum_rain_day = ("
				reqMAJJour = reqMAJJour + "SELECT COALESCE(sum(rain_corrige),0) AS sum_rain_day "
				reqMAJJour = reqMAJJour + "FROM meteo.donnees_brutes_30min "
				reqMAJJour = reqMAJJour + "WHERE _date_synthese = %s);"
				valReqJour = (dtStation.date(),)
				pg_curs.execute(reqMAJJour, valReqJour)
				connect_pg.commit()
				# on relève les derniers totaux precipitations
				reqSQL = "SELECT sum_rain_year, sum_rain_month, sum_rain_day FROM meteo.total_precipitations WHERE id_mesure = 0;"
				pg_curs.execute(reqSQL)
				recPrec = pg_curs.fetchone()
				sumRainYear, sumRainMonth, sumRainDay = recPrec

			try:
				# MATPLOTLIB GRAPHIQUE 24H
				logging.debug("Générer les graphs 24H")
				# requête SQL
				reqSQL = "SELECT id_mesure, packed_time, (_date + _time) AS heure, barometer, outside_temp, outside_hum, wind_speed, hi_wind_speed, wind_direction , wind_direction_str, solar_rad, uv "
				reqSQL = reqSQL + "FROM meteo.donnees_brutes_30min "
				reqSQL = reqSQL + "WHERE (_date + _time > %s - interval '1 day') "
				reqSQL = reqSQL + "ORDER BY (_date + _time);"
				valReqSQL = (dtStation,)
				logging.debug("SQL - %s", (pg_curs.mogrify(reqSQL, valReqSQL)))
				pg_curs.execute(reqSQL, valReqSQL)
				# récupérer toutes les lignes (liste de tuples)
				allRecs = pg_curs.fetchall()
				# créer un record array numpy
				recArrMeteo = np.rec.fromrecords(allRecs, names="id_mesure, packed_time, heure, barometer, outside_temp, outside_hum, wind_speed, hi_wind_speed, wind_direction , wind_direction_str, solar_rad, uv")
				logging.debug("Générer les graphs 24 h")
				g24 = Graph24h(recArrMeteo)
				# génération des graphiques : données température, pression
				g24.genere_graph_evolution_temperature(CHEMIN_ACCES_REPERTOIRE_WEB + 'evolution_24h.png')
				# génération des graphiques : données rayonnement
				g24.genere_graph_evolution_rayonnement(CHEMIN_ACCES_REPERTOIRE_WEB + 'evolution_solaire_24h.png')
				# génération des graphiques : données vent
				g24.genere_graph_vent24h(CHEMIN_ACCES_REPERTOIRE_WEB + 'vent_24h.png')

				# MATPLOTLIB GRAPHIQUE CUMUL PRECIPITATIONS YMD
				logging.debug("Générer les graphs Cumul")
				dictCumul = {'cumulJour': sumRainDay, 'cumulMois': sumRainMonth, 'cumulAn': sumRainYear}
				gcumul = GraphCumul({'cumulJour': sumRainDay, 'cumulMois': sumRainMonth, 'cumulAn': sumRainYear})
				gcumul.genere_graph_precipitations(CHEMIN_ACCES_REPERTOIRE_WEB + 'precipitations.png')
			except Exception as e:
				logging.error("Erreur inattendue - %s", e)
			
		# fermeture connexion pgsql
		pg_curs.close()
		connect_pg.close()

		
	except psycopg2.Error as epg:
		logging.error("Erreur PostgreSQL - Code %s - Message %s", epg.pgcode, epg.pgerror)
		sys.exit(1)

	except Exception as e:
		logging.error("Erreur inattendue - %s", e)
		sys.exit(1)

	sys.exit(0)