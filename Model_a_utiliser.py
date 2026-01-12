from Class_Model1 import Algo
import csv
Nom_du_fichier = input("Nom du fichier de données (csv utf-8) : ")
resultat = []
capacity = float(input("Capacité de la batterie initiale en Wh : "))
finality = float(input("Dernière capacité à simuler en Wh :"))
efficiency = float(input("Rendement considéré entre 0 et 1  : "))
interval = float(input("Interval entre les capacités testées en Wh : "))
nom_du_fichier_de_resultat = input("Nom du fichier de resultat : ")
speed_charging_ratio = 2
while capacity <=finality+1:
    Object = Algo(Nom_du_fichier, capacity, efficiency, speed_charging_ratio)
    Object.read_csv()
    resultat.append(Object.run_algo())
    capacity+=interval

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
with open(f"{nom_du_fichier_de_resultat}_rdmt_{efficiency}.csv", "w",newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow(top_line)
    writer.writerows(resultat)

print("---------------------------------Simulation terminée--------------------------------------------")