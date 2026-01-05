

# Modèle de batterie pouvant se charger et se décharger
class Battery:

    # Crée une batterie d'une capacité de max_capacity_wh
    # efficiency est compris entre 0.01 (rendement = 1%) et 1 (rendement = 100%) pour éviter des divisions par 0
    # La batterie commence par être vide
    def __init__(self, max_capacity_wh, efficiency):
        self.max_capacity = max_capacity_wh
        if efficiency > 1:
            efficiency = 1
        if efficiency < 0.01:
            efficiency = 0.01
        self.efficiency = efficiency
        self.capacity_level = 0

    # Retourne le soc de la batterie en Wh
    def get_soc(self):
        return self.capacity_level

    #  Ordre de charge de batterie. La charge se fait sans perte (rendement = 100%)
    #  Essaie de charger la batterie de quantity_wh
    #  Retourne le nombre de wh effectivement chargés
    def charge(self, quantity_wh):
        acceptable = self.max_capacity - self.capacity_level
        accepted = self.__compute_accepted(acceptable, quantity_wh)
        self.capacity_level += accepted
        return accepted

    #  Ordre de décharge de batterie
    #  Essaie de décharger la batterie de quantity_wh
    #  La batterie se vide plus que quantity_wh en tenant compte du rendement
    #  Retourne le nombre de wh effectivement déchargés
    def discharge(self, quantity_wh):
        quantity_wh = quantity_wh / self.efficiency  # augmente les Wh en fonction du rendement
        acceptable = self.get_soc()
        accepted = self.__compute_accepted(acceptable, quantity_wh)
        self.capacity_level -= accepted
        return accepted * self.efficiency  # adapte avec le rendement

    # Interne : choix entre acceptable et quantity_wh
    def __compute_accepted(self, acceptable, quantity_wh):
        if acceptable > quantity_wh:
            accepted = quantity_wh
        else:
            accepted = acceptable
        return accepted
