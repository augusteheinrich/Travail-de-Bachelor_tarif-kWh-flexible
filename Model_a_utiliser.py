from Class_Model1 import Algo
import csv

resultat = []
capacity = 5500
efficiency = 1
division_cap = 2
while capacity <=5501:
    c = Algo("Donnees_2024.csv", capacity, efficiency, division_cap)
    d = c.read_csv()
    resultat.append(c.run_algo())
    capacity+=5000

top_line = ["Capacité batterie [kWh]","Rendement [-]","Charge maximale par heure [kWh]",
            "Autoconsommation [kWh]","Cout autoconsommation [CHF]",
            "Production PV stockee [kWh]","Cout PV stockee [CHF]",
            "Achats differes reels au grid [kWh]","Cout achats differes [CHF]",
            "Consommation directe au grid [kWh]", "Cout consommation directe [CHF]",
            "Production vendue [kWh]","Gain de la vente [CHF]",
            "Achats differes voulus au grid [kWh]",
            "Difference achats differes voulus et reels [kWh]", "Cout de la difference [CHF]",
            "Depassement de capacite"]

print(resultat)
with open(f"resultats_Veyras_5500_rdmt({efficiency}).csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")  # ou "," si tu préfères
    writer.writerow(top_line)
    writer.writerows(resultat)