#!/usr/bin/env python
# -*- coding:Utf-8 -*-
#
# METEO TE CEFE
# Générer les graphiques
#
# Auteur : Cyril BERNARD, CEFE-CNRS, 06/2015 (cyril.bernard@cefe.cnrs.fr)
#

import datetime as dt
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.cm as cm

class GraphInstant():

	def __init__(self, data):
		self.data = data

	def genere_graph_heure_releve(self, fichierImage="date_heure_releve.png"):
		data = self.data
		dtReleve = data['Datetime']
		strDateHeureReleve = u"Conditions météorologiques observées le %s à %s" % (dtReleve.strftime('%d/%m/%Y'), dtReleve.strftime('%H:%M'))
		fig = plt.figure(figsize=(8, 0.5))
		fig.subplots_adjust(left=0.0625, right=0.95, top=0.9, bottom=0.1)
		ax = fig.add_subplot(111)
		ax.text(0, 0.5, strDateHeureReleve, horizontalalignment='left', verticalalignment='center', fontsize=14, color='#333333', transform=ax.transAxes)
		ax.set_axis_off()
		ax.set_xticks([])
		ax.set_yticks([])
		fig.savefig(fichierImage)

	def genere_graph_conditions_actuelles(self, fichierImage="cond_actuelles.png"):
		data = self.data
		# afficher les données : sous-graph 1
		strTemperature = u'Température :   indisponible' if data['TempOut'] is None else u'Température :   %.1f °C' % data['TempOut']
		strPressionAtmo = u'Pression atmosphérique :   indisponible' if data['Barometer'] is None else u'Pression atmosphérique :   %.1f hPa' % data['Barometer']
		strHumidite = u'Humidité :   indisponible' if data['HumOut'] is None else u'Humidité :   %d %%' % data['HumOut']
		strRadSol = u'Rayonnement solaire :   indisponible' if data['SolarRad'] is None else u'Rayonnement solaire :   %d W/m\xb2' % data['SolarRad']
		strUV = u'Index UV : indisponible' if data['UV'] is None else u'Indice UV :   %.1f' % data['UV']
		
		fig = plt.figure() #figsize=(4, 3)
		fig.subplots_adjust(left=0.125, right=0.9, top=0.8, bottom=0.15)
		ax = fig.add_subplot(111)
		ax.text(0, 0.95, strTemperature, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.text(0, 0.8, strPressionAtmo, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.text(0, 0.65, strHumidite, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.text(0, 0.4, strRadSol, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.text(0, 0.25, strUV, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.set_axis_off()
		ax.set_xticks([])
		ax.set_yticks([])
		fig.savefig(fichierImage)

	def genere_graph_vent(self, fichierImage="vent_actuel.png"):
		data = self.data
		# afficher les données : sous-graph 1
		strVitesse = u'Vitesse du vent* :   indisponible' if data['WindSpeed10Min'] is None else u'Vitesse du vent* :   %.1f km/h' % data['WindSpeed10Min'] 
		strDirection = u'Direction du vent :   indisponible' if data['WindDirStr'] is None else u'Direction du vent :   %s' % data['WindDirStr']
		#strVitesseMax = u'Vitesse maximale** :   indisponible' if data['DAY_HI_SPEED_WDID'] is None else u'Vitesse maximale** :   %.1f km/h' % dictVent['DAY_HI_SPEED_WDID']
		fig = plt.figure() #figsize=(4, 3)
		fig.subplots_adjust(left=0.125, right=0.9, top=0.8, bottom=0.15)
		ax = fig.add_subplot(111)
		ax.text(0, 0.95, strDirection, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		ax.text(0, 0.8, strVitesse, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		#ax.text(0, 0.65, strVitesseMax, ha='left', va='bottom', fontsize=12, color='#333333', transform=ax.transAxes)
		#ax.text(0, 0.15, u'*  moyenne des 10 minutes précédant le relevé', ha='left', va='bottom', fontsize=8, color='#333333', transform=ax.transAxes)
		#ax.text(0, 0.05, u'**  depuis le début de la journée', ha='left', va='bottom', fontsize=8, color='#333333', transform=ax.transAxes)
		ax.set_axis_off()
		ax.set_xticks([])
		ax.set_yticks([])
		fig.savefig(fichierImage)


		
class Graph24h():

	def __init__(self, recArrMeteo):
		# filtrer les donnees
		#arFiltre = (np.mod(recArrMeteo['packed_time'], 15)==0)
		#recArrMeteo15 = recArrMeteo[arFiltre]
		self.arWindDirSector = recArrMeteo['wind_direction']
		self.arWindSpeed = recArrMeteo['wind_speed']
		self.arTemps = recArrMeteo['heure']
		self.arTemperature = recArrMeteo['outside_temp'].astype(np.float)
		self.arBarometre = recArrMeteo['barometer'].astype(np.float)
		self.arSolarRad = recArrMeteo['solar_rad'].astype(np.float)

	def genere_graph_evolution_temperature(self, fichierImage="temppres_24h.png"):
		# calculer min et max temperature, arrondir à 5 dessous et dessus
		minTemperature, maxTemperature = np.nanmin(self.arTemperature), np.nanmax(self.arTemperature)
		minTemperature = (minTemperature // 5) * 5
		maxTemperature = (maxTemperature // 5 + 1) * 5
		# calculer min et max barometre, arrondir à 10 dessous et dessus
		minBarometre, maxBarometre = np.nanmin(self.arBarometre), np.nanmax(self.arBarometre)
		minBarometre = (minBarometre // 10) * 10
		maxBarometre = (maxBarometre // 10 + 1) * 10
		
		# formatage de l'heure
		ht1 = mdates.HourLocator(byhour=(0,4,8,12,16,20))
		ht2 = mdates.HourLocator(byhour=range(24), interval=1)
		hFmt = mdates.DateFormatter('%H:%M')
		# formatage barometre
		y2Fmt = mticker.FormatStrFormatter('%d')
		
		# afficher les données
		fig = plt.figure()
		fig.subplots_adjust(top=0.8, bottom=0.15)
		ax1 = fig.add_subplot(111)
		
		plt.xticks(rotation=90)
		lns1 = ax1.plot(self.arTemps, self.arTemperature, 'r', label=u'Température (°C)')
		ax1.xaxis.tick_bottom()
		plt.ylim([minTemperature, maxTemperature])
		
		ax2 = ax1.twinx()
		lns2 = ax2.plot(self.arTemps, self.arBarometre, '#4682b4', label=u'Pression (hPa)')
		plt.ylim([minBarometre, maxBarometre])
		
		ax1.xaxis.set_major_locator(ht1)
		ax1.xaxis.set_major_formatter(hFmt)
		ax1.xaxis.set_minor_locator(ht2)
		for tl in ax1.get_yticklabels():
			tl.set_color('r')
		# afficher les données : sous-graph 2
		ax2.yaxis.set_major_formatter(y2Fmt)
		for tl in ax2.get_yticklabels():
			tl.set_color('#4f94cd')
		# régler ticker et étiquette pour axes X et Y2
		lns = lns1+lns2
		labs = [l.get_label() for l in lns]
		fig.legend(lns, labs, bbox_to_anchor=(0.9, 0.98), loc=1, prop={'size':9}, borderaxespad=0.) #prop={'size':6}
		# autoformatage date (?)
		#fig.autofmt_xdate()
		#plt.figtext(0.125, 0.9, u'Température, pression', ha='left', va='bottom', fontsize=12)
		#plt.figtext(0.125, 0.825, u'Evolution 24 heures', ha='left', va='bottom', fontsize=12)
		plt.figtext(0.125, 0.925, u'Température, pression', ha='left', va='bottom', fontsize=12)
		plt.figtext(0.125, 0.85, u'(évolution sur 24h)', ha='left', va='bottom', fontsize=12)
		fig.savefig(fichierImage)

	def genere_graph_evolution_rayonnement(self, fichierImage="solaire_24h.png"):
		# calculer min et max temperature, arrondir à 5 dessous et dessus
		minSolarRad, maxSolarRad = np.nanmin(self.arSolarRad), np.nanmax(self.arSolarRad)
		minSolarRad = (minSolarRad // 100) * 100
		maxSolarRad = (maxSolarRad // 100 + 1) * 100
		
		# formatage de l'heure
		ht1 = mdates.HourLocator(byhour=(0,4,8,12,16,20))
		ht2 = mdates.HourLocator(byhour=range(24), interval=1)
		hFmt = mdates.DateFormatter('%H:%M')
		# formatage solaire
		y2Fmt = mticker.FormatStrFormatter('%d')
		
		# afficher les données
		fig = plt.figure()
		fig.subplots_adjust(top=0.8, bottom=0.15)
		ax1 = fig.add_subplot(111)
		
		plt.xticks(rotation=90)
		lns1 = ax1.plot(self.arTemps, self.arSolarRad, '#736F60', label=u'Rayon. (W/m\xb2)')
		ax1.xaxis.tick_bottom()
		plt.ylim([minSolarRad, maxSolarRad])
		
		ax1.xaxis.set_major_locator(ht1)
		ax1.xaxis.set_major_formatter(hFmt)
		ax1.xaxis.set_minor_locator(ht2)
		for tl in ax1.get_yticklabels():
			tl.set_color('#736F60')
		# régler ticker et étiquette pour axes X et Y2
		labs = [l.get_label() for l in lns1]
		fig.legend(lns1, labs, bbox_to_anchor=(0.9, 0.98), loc=1, prop={'size':9}, borderaxespad=0.) #prop={'size':6}
		# autoformatage date (?)
		#fig.autofmt_xdate()
		#plt.figtext(0.125, 0.9, u'Température, pression', ha='left', va='bottom', fontsize=12)
		#plt.figtext(0.125, 0.825, u'Evolution 24 heures', ha='left', va='bottom', fontsize=12)
		plt.figtext(0.125, 0.925, u'Rayonnement solaire', ha='left', va='bottom', fontsize=12)
		plt.figtext(0.125, 0.85, u'(évolution sur 24h)', ha='left', va='bottom', fontsize=12)
		fig.savefig(fichierImage)

	def genere_graph_vent24h(self, fichierImage="vent_24h.png"):
		# filtrer données : supprimer lignes où wind_direction est null (pas de vent)
		arWindDirSector = self.arWindDirSector
		arWindSpeed = self.arWindSpeed
		arFiltre = np.not_equal(arWindDirSector, None)
		iTailleTotale = arWindDirSector.size
		iTailleData = np.sum(arFiltre)
		iTailleNoData = iTailleTotale - iTailleData
		pNoData = (100. * iTailleNoData) / iTailleTotale
		arWindDirSector = arWindDirSector[arFiltre].astype(np.int8)
		arWindSpeed = arWindSpeed[arFiltre].astype(np.float32)

		# calculer les directions en radians suivant les 16 secteurs
		#(S0 = N > pi/2, S4=E > 0, S8=S > 3pi/2, S12=W > pi)
		sigma = np.array([4, 3, 2, 1, 0, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5])
		theta = sigma * (np.pi / 8) # E, ENE, NE, NNE, N, NNW, NW, WNW, W, WSW, SW, SSW, S, SSE, SE, ESE
		# calcule histogramme 2d
		# 16 secteurs, 5 classes de vent
		bins_direction = np.arange(17)
		bins_vitesse = np.array([0., 6., 12., 20., 38., 117.])
		H, xedges, yedges = np.histogram2d(arWindDirSector, arWindSpeed, bins= [bins_direction, bins_vitesse], normed=False)
		radii = (H * 100.) / iTailleTotale
		
		# génère graphique
		fig = plt.figure()
		fig.subplots_adjust(left = 0.075, top=0.75, right=0.725, bottom=0.1)
		ax1 = fig.add_subplot(111, polar=True)
		# étiquettes angles
		angle_grid = range(0,360,45)
		label = ['E','NE','N','NO','O','SO','S','SE']
		ax1.set_thetagrids(angle_grid, label, color='#999999')
		# étiquettes frequence
		angle_grid2 = sigma * 22.5
		dir_freq = np.sum(radii, axis=1)
		j = 0
		pref_dir = [1, 3, 15, 13, 11, 9, 7, 5, 0, 2, 4, 14, 12, 10, 8, 6]
		rotation_texte= [0., -22.5, -45., -67.5, -90., 67.5, 45., 22.5, 0., -22.5, -45., -67.5, 90., 67.5, 45., 22.5]
		for i in pref_dir:
			if (dir_freq[i] < 5.):
				j = i
				break
		maxFreq = int(np.max(dir_freq))
		freqs = np.arange(0, maxFreq, 5) + 5
		maxFreq = freqs[-1]
		freqs_labels = [("%d%%" %r) if (r%10==0) else "" for r in freqs]
		#freqs_labels = ["" if (r%10 == 0) else ("%d%%" %r) for r in freqs]
		#freqs_labels = [("%d%%" %r) for r in freqs]
		ax1.set_rgrids(freqs, labels=freqs_labels, angle=angle_grid2[j], size=8, color='#666666', rotation=rotation_texte[j])
		ax1.grid(color='#666666')
		# couleurs 5 classes
		cmap = cm.jet
		couleurs = [cmap(i) for i in np.linspace(0.0, 1.0, 5)]
		base_n = np.zeros(16)
		# labels légende
		legende_labels = [u"<= 5", u"6 - 11", u"12 - 19", u"20 - 37", u">= 38"]
		legende_patchs = []
		for i in range(5):
			radii_n = radii[:,i]
			bars_class_n = ax1.bar(theta, radii_n, width=(np.pi / 12), bottom=base_n, color=couleurs[i], linewidth=0, align='center', label=legende_labels[i])
			legende_patchs.append(mpatches.Rectangle((0, 0), 1, 1, fc=couleurs[i]))
			base_n = base_n + radii_n
		plt.ylim([0, maxFreq])
		fig.legend(legende_patchs, legende_labels, bbox_to_anchor=(0.9, 0.98), loc=1, title=u'Vitesse (km/h)', prop={'size':8}, borderaxespad=0.) #prop={'size':6}
		if (pNoData > 0.):
			plt.figtext(0.9, 0.1, u'Absence de vent : %d %%' % pNoData, color='#666666', ha='right', va='bottom', fontsize=8)
		plt.figtext(0.125, 0.925, u'Direction et vitesse des vents', ha='left', va='bottom', fontsize=12)
		plt.figtext(0.125, 0.85, u'(fréquence sur 24h)', ha='left', va='bottom', fontsize=12)
		fig.savefig(fichierImage)

class GraphCumul():

	def __init__(self, dictPrecipitations):
		self.data = dictPrecipitations

	def genere_graph_precipitations(self, fichierImage="precipitations.png"):
		pJour = self.data['cumulJour']
		pMois = self.data['cumulMois']
		pAn   = self.data['cumulAn']
		fig = plt.figure()
		fig.subplots_adjust(top=0.8)
		ind = 0.1
		# max arrondi à 50, avec marge de 200 à 250 au dessus du max
		maxY = (pAn // 50 + 5) * 50
		if maxY < 400: maxY=400
		posYlibelle = maxY - 25
		posYmesureJour = pJour + 25
		posYmesureMois = pMois + 25
		posYmesureAn = pAn + 25
		# JOUR
		ax1 = fig.add_subplot(131)
		ax1.bar([ind], [pJour], width=0.8, color='blue', linewidth=0)
		plt.xlim([0.0, 1.0])
		plt.ylim([0.0, maxY])
		ax1.set_xticks([])
		ax1.yaxis.tick_left()
		#ax1.text(0.5, posYlibelle, u'Jour', ha='center', va='top', fontsize=11)
		ax1.set_xlabel(u'Jour', labelpad=6, fontsize=11)
		ax1.text(0.5, posYmesureJour, '%.1f' % pJour, ha='center', va='bottom', fontsize=9)
		# MOIS
		ax2 = fig.add_subplot(132)
		ax2.bar([ind], [pMois], width=0.8, color='blue', linewidth=0)
		ax2.set_xticks([])
		ax2.set_yticks([])
		plt.xlim([0.0, 1.0])
		plt.ylim([0.0, maxY])
		#ax2.text(0.5, posYlibelle, u'Mois', ha='center', va='top', fontsize=11)
		ax2.set_xlabel(u'Mois', labelpad=6, fontsize=11)
		ax2.text(0.5, posYmesureMois, '%.1f' % pMois, ha='center', va='bottom', fontsize=9)
		# ANNEE
		ax3 = fig.add_subplot(133)
		ax3.bar([ind], [pAn], width=0.8, color='blue', linewidth=0)
		ax3.set_xticks([])
		ax3.set_yticks([])
		plt.xlim([0.0, 1.0])
		plt.ylim([0.0, maxY])
		#ax3.text(0.5, posYlibelle, u'Année', ha='center', va='top', fontsize=11)
		ax3.set_xlabel(u'Année', labelpad=6, fontsize=11)
		ax3.text(0.5, posYmesureAn, '%.1f' % pAn, ha='center', va='bottom', fontsize=9)
		plt.figtext(0.125, 0.925, u'Cumul précipitations (en mm)', ha='left', va='bottom', fontsize=12)
		
		fig.savefig(fichierImage)
			