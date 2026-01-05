class Timeslot:

    def __init__(self, date, consumption, production, price):
        self.date = date
        self.consumption = consumption
        self.production = production
        self.price = price
        self.allocated = False
        self.cost_prod = 0.01
        self.cost_batt = 0.02
        self.price_sell_to_grid = 0.1
        self.wh_from_PV_in_batt = 0

        self.for_later = False #chargement
        self.wh_buy_for_later = 0 #chargement
        self.buy_before = False #déchargement
        self.wh_buy_before = 0 #déchargement
        self.wh_sell_to_grid = 0
        self.wh_inject_to_battery = 0
        self.virtual_SOC = 0
        self.compute()


    def compute(self):
        if self.consumption > self.production:
            self.deficit = self.consumption - self.production
            self.surplus = 0
            self.autoconsumption = self.production

        else:
            self.deficit = 0
            self.surplus = self.production - self.consumption
            self.autoconsumption = self.consumption


        self.solde_before_buy = self.deficit - self.wh_from_PV_in_batt
        self.solde_to_buy = self.solde_before_buy - self.wh_buy_before
        if self.solde_to_buy < 0:
             self.solde_to_buy = 0
        self.import_price = self.deficit * self.price
        self.buying_price = self.solde_to_buy * self.price


    def reset(self):
        self.cost_prod = 0.01
        self.cost_batt = 0.02
        self.price_sell_to_grid = 0.1
        self.wh_from_PV_in_batt = 0
        self.buying_price = 0
        self.solde_to_buy = 0
        self.solde_before_buy = 0
        self.for_later = False  # chargement
        self.wh_buy_for_later = 0  # chargement
        self.buy_before = False  # déchargement
        self.wh_buy_before = 0  # déchargement
        self.wh_sell_to_grid = 0
        self.wh_inject_to_battery = 0
        self.Real_SOC = 0
        self.PV_SOC = 0
        self.grid_SOC = 0
        self.virtual_SOC =0
        self.compute()

    def dump_base(self):
        print(self.date,"déficit:", self.deficit, "surplus:",
              self.surplus,"import price",self.import_price)

    def dump_allocated(self):
        print(self.date,"Allocation SOC : ", self.allocated,
              "Achat pour plus tard : ", self.for_later,
              "Achat à l'avance : ", self.buy_before)

    def dump_conso(self):
        print(self.date, "deficit : ", self.deficit, "Real_SOC alloué : ", self.allocated,
              "Auto-conso : ", self.autoconsumption,
              "De la batterie : ", self.wh_from_PV_in_batt,
              "Wh acheté pour plus tard : ", self.wh_buy_for_later,
              "Wh acheté à l'avance : ", self.wh_buy_before,
              "Wh a acheté au Réseau : ", self.solde_to_buy,
              "SOC ", self.virtual_SOC, )

    def dump_battery(self):
        print(self.date, "Wh injectés : ", self.wh_inject_to_battery,
              "Wh achetés et stockes : ", self.wh_buy_for_later,
              "Wh produits et déchargés : ", self.wh_from_PV_in_batt,
              "Wh achetés et déchargés : ", self.wh_buy_before,
              "SOC ", self.virtual_SOC, )

    def dump_soldes(self):
        print(self.date, "avant pre buy : ", self.solde_before_buy,
              "après pré buy : ", self.solde_to_buy,
              "pré buy : ", self.wh_buy_before)

    def dump_date(self):
        print(self.date)

    def dump_SOC (self):
        print(self.date, "virtual SOC : ", self.virtual_SOC)