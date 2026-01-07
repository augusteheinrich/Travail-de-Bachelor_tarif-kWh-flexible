import csv
import heapq


import matplotlib.pyplot as plt
from matplotlib.mlab import window_hanning
from matplotlib.pyplot import legend
from battery import Battery

from timeslot import Timeslot

class Algo :

    def __init__(self, fichier, capacity_max_batt, efficiency_batt, rapport):
        self.rapport = rapport
        self.fichier_to_read = fichier
        self.capacity_max_batt = capacity_max_batt
        self.efficiency_batt = efficiency_batt
        self.batt = Battery(self.capacity_max_batt, self.efficiency_batt)
        self.max_capacity_per_hour = self.batt.max_capacity/rapport
        self.time_period = 0
    def read_csv(self):
        self.time_period = []
        with open(self.fichier_to_read, "r", encoding="utf-8-sig") as Donnees:
            reader = csv.reader(Donnees, delimiter=';')
            header = next(reader)
            for row in reader:
                ts = Timeslot(str(row[0]), float(row[2]), float(row[1]), float(row[3]))
                self.time_period.append(ts)

        return self.time_period,print("OK", self.batt.get_soc())

    def run_algo(self):
        if not self.time_period:
            self.read_csv()
        print("Is running .... ")
        # identifier périodes de déficit et de surplus
        for ts in self.time_period:
            ts.reset()

        # identifier périodes de déficit et de surplus
        periode_de_deficit = []
        in_deficit = False
        last_index_def = 0

        periode_de_surplus = []  # un tableau de tableaux de timeslots
        in_surplus = False  # on dit qu'au début on considère qu'on est pas en déficit
        last_index_sur = 0
        for i in range(len(self.time_period)):
            if self.time_period[i].deficit > 0:
                if in_deficit == False:
                    in_deficit = True
                    last_index_def = i
                if i == len(self.time_period) - 1:
                    periode_de_deficit.append(self.time_period[last_index_def:i + 1])
                if in_surplus == True:
                    in_surplus = False
                    periode_de_surplus.append(self.time_period[last_index_sur:i])
            if self.time_period[i].surplus > 0:
                if in_deficit == True:
                    in_deficit = False
                    periode_de_deficit.append(self.time_period[last_index_def:i])
                if in_surplus == False:
                    in_surplus = True
                    last_index_sur = i
                if i == len(self.time_period) - 1:
                    periode_de_deficit.append(self.time_period[last_index_sur:i + 1])

        for ts in self.time_period:
            ts.compute()
        depassement_capacite = 0

        # -----------------------------------Commencer par un surplus_-------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------
        first_ts = self.time_period[0]
        print("on commence vraiment l'algo pour la batterie ", self.batt.max_capacity, " et un rendement de ", self.batt.efficiency)
        if first_ts.production > first_ts.consumption:
            # si on commence directement par un surplus
            print("surplus")
            for i in range(len(periode_de_surplus)):
                surplus = periode_de_surplus[i]
                deficit = periode_de_deficit[i]

                for ts in surplus:
                    remaining_in_batt = self.batt.max_capacity - self.batt.get_soc()
                    if ts.surplus < remaining_in_batt and ts.surplus < self.max_capacity_per_hour:
                        charged = self.batt.charge(ts.surplus)
                        ts.wh_inject_to_battery = charged
                    elif ts.surplus > remaining_in_batt and ts.surplus < self.max_capacity_per_hour:
                        charged = self.batt.charge(ts.surplus)
                        ts.wh_inject_to_battery = charged
                        ts.wh_sell_to_grid = ts.surplus - charged
                    elif ts.surplus > remaining_in_batt and ts.surplus > self.max_capacity_per_hour:
                        charged = self.batt.charge(self.max_capacity_per_hour)
                        ts.wh_inject_to_battery = charged
                        ts.wh_sell_to_grid = ts.surplus - charged

                discharged_tot = 0
                charged_tot = self.batt.get_soc()
                to_discharge = charged_tot

                # seulement l'allocation du PV dans la batterie
                k = 1
                while k <= len(deficit) and discharged_tot <= charged_tot:
                    # k-ième import_price le plus grand dans la période de déficit
                    ts_imp = heapq.nlargest(k, deficit, key=lambda x: x.import_price)[-1]
                    idx_imp = deficit.index(ts_imp)
                    k += 1
                    if ts_imp.allocated == False and ts_imp.deficit / self.batt.efficiency <= to_discharge:
                        ts_imp.allocated = True
                        to_discharge -= ts_imp.deficit / self.batt.efficiency
                        ts_imp.wh_from_PV_in_batt = ts_imp.deficit / self.batt.efficiency
                        discharged_tot += ts_imp.deficit / self.batt.efficiency

                # décharge réelle est allocation en même temps
                soc = self.batt.get_soc()
                soc_ctrl = self.batt.get_soc()

                for td in deficit:
                    index = deficit.index(td)
                    if td.allocated == False and td.buy_before == False and td.for_later == False:
                        new_def = deficit[index:]
                        k = 1
                        while k <= len(new_def):
                            ts_imp = heapq.nlargest(k, new_def, key=lambda x: x.import_price)[-1]
                            idx_imp = new_def.index(ts_imp)
                            # on ne peut acheter que STRICTEMENT avant le timeslot à couvrir
                            candidats_prix = new_def[:idx_imp]
                            k += 1
                            if len(candidats_prix) == 0:
                                continue
                            l = 1
                            while l <= len(candidats_prix):
                                ts_prix = heapq.nsmallest(l, candidats_prix, key=lambda x: x.price)[-1]
                                idx_prix_new = new_def.index(ts_prix)
                                need_internal = ts_imp.deficit / self.batt.efficiency  # Wh internes (niveau batterie)
                                if (idx_prix_new < idx_imp
                                        and ts_prix.price < ts_imp.price
                                        and ts_imp.allocated == False
                                        and ts_imp.buy_before == False
                                        and ts_prix.wh_buy_for_later + need_internal <= self.batt.max_capacity

                                        and ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour):
                                    # print("dans l'achat")
                                    # calculer le "vrai SOC" à mettre dans ts_prix
                                    batt_control = Battery(self.capacity_max_batt, self.efficiency_batt)
                                    batt_control.charge(soc_ctrl)
                                    # passer sur les déficits et recalculer le SOC au moment de ts_prix
                                    remaining_SOC = 0
                                    for soc_calc in deficit:
                                        # print(soc_calc.date)
                                        # print("SOC avant:", batt_control.get_soc())
                                        batt_control.discharge(soc_calc.wh_buy_before)
                                        batt_control.discharge(soc_calc.wh_from_PV_in_batt)
                                        if soc_calc.date == ts_prix.date:
                                            remaining_SOC = batt_control.get_soc()
                                        batt_control.charge(soc_calc.wh_buy_for_later)
                                        # print("SOC après", batt_control.get_soc())
                                    # print("SOC au moment de TS_prix", remaining_SOC)
                                    remaining_capacity = batt_control.max_capacity - remaining_SOC
                                    # print("Capacité restante", remaining_capacity, ts_prix.date)
                                    if ts_prix.wh_buy_for_later + need_internal < remaining_capacity:
                                        if ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour:
                                            ts_imp.buy_before = True
                                            ts_imp.wh_buy_before = need_internal
                                            ts_prix.for_later = True
                                            ts_prix.wh_buy_for_later += need_internal
                                        if ts_prix.wh_buy_for_later + need_internal > self.max_capacity_per_hour:
                                            depassement_capacite += 1
                                l += 1
                    # décharge et charge relle de la batterie
                    self.batt.discharge(td.wh_from_PV_in_batt)
                    self.batt.discharge(td.wh_buy_before)
                    a = self.batt.charge(td.wh_buy_for_later)
                    td.wh_buy_for_later = a  # à enlever si on veut identifer les problèmes
                    if a != td.wh_buy_for_later:
                        td.dump_date()
                        print("Chargé dans batterie:", a)
                        print("Aurait du être chargé", td.wh_buy_for_later)
                        exit(0)
        # -----------------------------------Commencer par un deficit-------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------
        else:
            deficit = periode_de_deficit[0]
            soc_ctrl = 0
            for td in deficit:
                index = deficit.index(td)
                if td.allocated == False and td.buy_before == False and td.for_later == False:
                    new_def = deficit[index:]
                    k = 1
                    while k <= len(new_def):
                        ts_imp = heapq.nlargest(k, new_def, key=lambda x: x.import_price)[-1]
                        idx_imp = new_def.index(ts_imp)
                        # on ne peut acheter que STRICTEMENT avant le timeslot à couvrir
                        candidats_prix = new_def[:idx_imp]
                        k += 1
                        if len(candidats_prix) == 0:
                            continue
                        l = 1
                        while l <= len(candidats_prix):
                            ts_prix = heapq.nsmallest(l, candidats_prix, key=lambda x: x.price)[-1]
                            idx_prix_new = new_def.index(ts_prix)
                            need_internal = ts_imp.deficit / self.batt.efficiency  # Wh internes (niveau batterie)
                            if (idx_prix_new < idx_imp
                                    and ts_prix.price < ts_imp.price
                                    and ts_imp.allocated == False
                                    and ts_imp.buy_before == False
                                    and ts_prix.wh_buy_for_later + need_internal <= self.batt.max_capacity

                                    and ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour):
                                # print("dans l'achat")
                                # calculer le "vrai SOC" à mettre dans ts_prix
                                batt_control = Battery(self.capacity_max_batt, self.efficiency_batt)
                                batt_control.charge(soc_ctrl)
                                # passer sur les déficits et recalculer le SOC au moment de ts_prix
                                remaining_SOC = 0
                                for soc_calc in deficit:
                                    # print(soc_calc.date)
                                    # print("SOC avant:", batt_control.get_soc())
                                    batt_control.discharge(soc_calc.wh_buy_before)
                                    batt_control.discharge(soc_calc.wh_from_PV_in_batt)
                                    if soc_calc.date == ts_prix.date:
                                        remaining_SOC = batt_control.get_soc()
                                    batt_control.charge(soc_calc.wh_buy_for_later)
                                    # print("SOC après", batt_control.get_soc())
                                # print("SOC au moment de TS_prix", remaining_SOC)
                                remaining_capacity = batt_control.max_capacity - remaining_SOC
                                # print("Capacité restante", remaining_capacity, ts_prix.date)
                                if ts_prix.wh_buy_for_later + need_internal < remaining_capacity:
                                    if ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour:
                                        ts_imp.buy_before = True
                                        ts_imp.wh_buy_before = need_internal
                                        ts_prix.for_later = True
                                        ts_prix.wh_buy_for_later += need_internal
                                    if ts_prix.wh_buy_for_later + need_internal > self.max_capacity_per_hour:
                                        depassement_capacite += 1
                            l += 1
                # décharge et charge relle de la batterie
                self.batt.discharge(td.wh_from_PV_in_batt)
                self.batt.discharge(td.wh_buy_before)
                a = self.batt.charge(td.wh_buy_for_later)
                td.wh_buy_for_later = a  # à enlever si on veut identifer les problèmes
                if a != td.wh_buy_for_later:
                    td.dump_date()
                    print("Chargé dans batterie:", a)
                    print("Aurait du être chargé", td.wh_buy_for_later)
                    exit(0)

            for i in range(len(periode_de_surplus)):
                surplus = periode_de_surplus[i]
                deficit = periode_de_deficit[i + 1]

                for ts in surplus:
                    remaining_in_batt = self.batt.max_capacity - self.batt.get_soc()
                    if ts.surplus < remaining_in_batt and ts.surplus < self.max_capacity_per_hour:
                        charged = self.batt.charge(ts.surplus)
                        ts.wh_inject_to_battery = charged
                    elif ts.surplus > remaining_in_batt and ts.surplus < self.max_capacity_per_hour:
                        charged = self.batt.charge(ts.surplus)
                        ts.wh_inject_to_battery = charged
                        ts.wh_sell_to_grid = ts.surplus - charged
                    elif ts.surplus > remaining_in_batt and ts.surplus > self.max_capacity_per_hour:
                        charged = self.batt.charge(self.max_capacity_per_hour)
                        ts.wh_inject_to_battery = charged
                        ts.wh_sell_to_grid = ts.surplus - charged

                discharged_tot = 0
                charged_tot = self.batt.get_soc()
                to_discharge = charged_tot

                # seulement l'allocation du PV dans la batterie
                k = 1
                while k <= len(deficit) and discharged_tot <= charged_tot:
                    # k-ième import_price le plus grand dans la période de déficit
                    ts_imp = heapq.nlargest(k, deficit, key=lambda x: x.import_price)[-1]
                    idx_imp = deficit.index(ts_imp)
                    k += 1
                    if ts_imp.allocated == False and ts_imp.deficit / self.batt.efficiency <= to_discharge:
                        ts_imp.allocated = True
                        to_discharge -= ts_imp.deficit / self.batt.efficiency
                        ts_imp.wh_from_PV_in_batt = ts_imp.deficit / self.batt.efficiency
                        discharged_tot += ts_imp.deficit / self.batt.efficiency

                # décharge réelle est allocation en même temps
                soc = self.batt.get_soc()
                soc_ctrl = self.batt.get_soc()

                for td in deficit:
                    index = deficit.index(td)
                    if td.allocated == False and td.buy_before == False and td.for_later == False:
                        new_def = deficit[index:]
                        k = 1
                        while k <= len(new_def):
                            ts_imp = heapq.nlargest(k, new_def, key=lambda x: x.import_price)[-1]
                            idx_imp = new_def.index(ts_imp)
                            # on ne peut acheter que STRICTEMENT avant le timeslot à couvrir
                            candidats_prix = new_def[:idx_imp]
                            k += 1
                            if len(candidats_prix) == 0:
                                continue
                            l = 1
                            while l <= len(candidats_prix):
                                ts_prix = heapq.nsmallest(l, candidats_prix, key=lambda x: x.price)[-1]
                                idx_prix_new = new_def.index(ts_prix)
                                need_internal = ts_imp.deficit / self.batt.efficiency  # Wh internes (niveau batterie)
                                if (idx_prix_new < idx_imp
                                        and ts_prix.price < ts_imp.price
                                        and ts_imp.allocated == False
                                        and ts_imp.buy_before == False
                                        and ts_prix.wh_buy_for_later + need_internal <= self.batt.max_capacity
                                        and ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour):
                                    # print("dans l'achat")
                                    # calculer le "vrai SOC" à mettre dans ts_prix
                                    batt_control = Battery(self.capacity_max_batt, self.efficiency_batt)
                                    batt_control.charge(soc_ctrl)
                                    # passer sur les déficits et recalculer le SOC au moment de ts_prix
                                    remaining_SOC = 0
                                    for soc_calc in deficit:
                                        # print(soc_calc.date)
                                        # print("SOC avant:", batt_control.get_soc())
                                        batt_control.discharge(soc_calc.wh_buy_before)
                                        batt_control.discharge(soc_calc.wh_from_PV_in_batt)
                                        if soc_calc.date == ts_prix.date:
                                            remaining_SOC = batt_control.get_soc()
                                        batt_control.charge(soc_calc.wh_buy_for_later)
                                        # print("SOC après", batt_control.get_soc())
                                    # print("SOC au moment de TS_prix", remaining_SOC)
                                    remaining_capacity = batt_control.max_capacity - remaining_SOC
                                    # print("Capacité restante", remaining_capacity, ts_prix.date)
                                    if ts_prix.wh_buy_for_later + need_internal < remaining_capacity:
                                        if ts_prix.wh_buy_for_later + need_internal < self.max_capacity_per_hour:
                                            ts_imp.buy_before = True
                                            ts_imp.wh_buy_before = need_internal
                                            ts_prix.for_later = True
                                            ts_prix.wh_buy_for_later += need_internal
                                        if ts_prix.wh_buy_for_later + need_internal > self.max_capacity_per_hour:
                                            depassement_capacite += 1
                                l += 1
                    # décharge et charge relle de la batterie
                    self.batt.discharge(td.wh_from_PV_in_batt)
                    self.batt.discharge(td.wh_buy_before)
                    a = self.batt.charge(td.wh_buy_for_later)
                    td.wh_buy_for_later = a  # à enlever si on veut identifer les problèmes
                    if a != td.wh_buy_for_later:
                        td.dump_date()
                        print("Chargé dans batterie:", a)
                        print("Aurait du être chargé", td.wh_buy_for_later)
                        exit(0)

        for ts in (self.time_period):
            ts.compute()

        # calcul de la répartition de la consommation et des coûts
        wh_autoconso_cap = []
        wh_prod_stock_cap = []
        wh_really_buy_for_later_cap = []
        wh_grid_direct_cap = []
        wh_vente_prod_cap = []
        wh_inject_to_battery_cap = []
        wh_wanted_buy_before_cap = []

        cout_autoconso_cap = []
        cout_prod_stock_cap = []
        cout_really_buy_before_cap = []  # on prend le coût total à l'achat et on ajoute le coût de stockage
        cout_grid_direct_cap = []
        gain_vente_prod_cap = []
        cout_wanted_buy_before = []
        conso_total = []
        prod_total = []
        prix_total =[]

        for ts in self.time_period:
            # auto-consommation
            cout_autoconso_cap.append((ts.autoconsumption * ts.cost_prod)/1000)
            wh_autoconso_cap.append(ts.autoconsumption)
            # produit et stocké
            cout_prod_stock_cap.append((ts.wh_from_PV_in_batt * (ts.cost_batt + ts.cost_prod))/1000)
            wh_prod_stock_cap.append(ts.wh_from_PV_in_batt)
            # kWh que l'on voulait acheter au grid
            wh_wanted_buy_before_cap.append(ts.wh_buy_before)
            cout_wanted_buy_before.append((ts.wh_buy_before*ts.price)/1000)
            # kWh vraiment achetés en avance
            cout_really_buy_before_cap.append(ts.wh_buy_for_later *(ts.cost_batt + (ts.price/100))/1000)
            wh_really_buy_for_later_cap.append(ts.wh_buy_for_later)
            # kWh achetés au réseau en direct
            cout_grid_direct_cap.append((ts.solde_to_buy/1000) * (ts.price/100))
            wh_grid_direct_cap.append(ts.solde_to_buy)
            # vente au réseau
            gain_vente_prod_cap.append((ts.wh_sell_to_grid * ts.price_sell_to_grid)/1000)
            wh_vente_prod_cap.append(ts.wh_sell_to_grid)
            # général
            conso_total.append(ts.consumption)
            prod_total.append(ts.production)
            prix_total.append(ts.price)
            wh_inject_to_battery_cap.append(ts.wh_inject_to_battery)

        somme_cout_autoconso = sum(cout_autoconso_cap)
        somme_kwh_autoconso = sum(wh_autoconso_cap) / 1000
        somme_cout_prod_stock = sum(cout_prod_stock_cap)
        somme_kwh_prod_stock = sum(wh_prod_stock_cap) / 1000
        somme_cout_really_buy_on_grid = sum(cout_really_buy_before_cap)
        somme_kwh_really_buy_on_grid = sum(wh_really_buy_for_later_cap) / 1000
        somme_cout_grid_direct = sum(cout_grid_direct_cap)
        somme_kwh_grid_direct = sum(wh_grid_direct_cap) / 1000
        somme_gain_vente_prod = sum(gain_vente_prod_cap)
        somme_kwh_vente_prod = sum(wh_vente_prod_cap) / 1000
        somme_wh_wanted_to_buy_before = sum(wh_wanted_buy_before_cap) / 1000
        somme_price = sum(prix_total)
        somme_conso = sum(conso_total) / 1000
        somme_production = sum(prod_total) / 1000
        somme_wh_inject_to_battery = sum(wh_inject_to_battery_cap) / 1000

        diff = 0
        average_price = 0
        if somme_wh_wanted_to_buy_before != somme_kwh_really_buy_on_grid :
            diff = somme_wh_wanted_to_buy_before -somme_kwh_really_buy_on_grid
            average_price = somme_price/len(self.time_period)

        cost_diff = diff*average_price
        print("L'autoconsommation de ", somme_kwh_autoconso, "kWh coûte ", somme_cout_autoconso, "CHF")
        print("La consommation de ", somme_kwh_prod_stock, "kWh produits et stockés coûte ", somme_cout_prod_stock,
              "CHF")
        print("on a vraiment acheté à l'avance et stocké ", somme_kwh_really_buy_on_grid, "kWh pour ",
              somme_cout_really_buy_on_grid, "CHF")
        print("La consommation en direct du grid de ", somme_kwh_grid_direct, "kWh coûte ", somme_cout_grid_direct,
              "CHF")
        print("La vente au réseau de ", somme_kwh_vente_prod, "kWh produits rapporte", somme_gain_vente_prod, "CHF")
        print(" on aurait aimé acheté à l'avance", somme_wh_wanted_to_buy_before)
        print("conso total fichier: ", somme_conso)
        print("conso total allouée : ",somme_kwh_autoconso + somme_kwh_prod_stock + somme_kwh_really_buy_on_grid + somme_kwh_grid_direct)
        print("prod total : ", somme_production)
        print("injection batt : ", somme_wh_inject_to_battery)
        print("La compensation de la différence de ", diff, "coûte, ", cost_diff)
        print(depassement_capacite)
        return (self.batt.max_capacity,self.batt.efficiency, self.max_capacity_per_hour,
                somme_kwh_autoconso,somme_cout_autoconso,
                somme_kwh_prod_stock,somme_cout_prod_stock,
                somme_kwh_really_buy_on_grid,somme_cout_really_buy_on_grid,
                somme_kwh_grid_direct,somme_cout_grid_direct,
                somme_kwh_vente_prod,somme_gain_vente_prod,
                somme_wh_wanted_to_buy_before,
                diff, cost_diff,
                depassement_capacite)