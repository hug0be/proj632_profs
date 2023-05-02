from unidecode import unidecode
import re
from selenium.webdriver.common.by import By

class InvalidMailException(Exception): pass

class Prof:
    """ Cette classe représente un professeur. Elle contient toutes ses recherches ("papers") et les cours que le prof enseigne. """
    def __init__(self, nom:str, mail:str, cours:dict=None):
        self.nom = nom
        self.mail = mail
        self.cours = cours if not cours is None else {}
        self.papers = []

    def nb_cours(self):
        """ Retourne le nombre de modules enseignés """
        return sum(len(ue) for ue in self.cours.values())

    def nb_ue(self):
        """ Retourne le nombre d'UE enseigné """
        return len(self.cours)

    def add_cours(self, ueName:str, titreCours:str):
        """ Ajoute un module enseigné dans un UE """
        if not ueName in self.cours: self.cours[ueName] = []
        if not titreCours in self.cours[ueName]: self.cours[ueName].append(titreCours)

    def to_json(self):
        """ Convertit le prof en objet json """
        return {
            "nom": self.nom,
            "mail": self.mail,
            "cours": {
                ue: cours
                for ue, cours in self.cours.items()
            },
            "papers": self.papers
        }

    @staticmethod
    def from_json(jsonProf):
        """ Convertit un objet json en prof """
        return Prof(jsonProf["nom"], jsonProf["mail"], jsonProf["cours"])

    @staticmethod
    def format_name(name:str):
        """ Formate le nom donné (suppression des accents, majuscule)"""
        return unidecode(name.title())

    @staticmethod
    def format_last_name_exception(mail:str)->str:
        """ Tente d'extraire le nom de famille d'un mail qui n'a pas de symbole @ """
        if mail == "Pascal Francescato": return "francescato"
        if mail == "Guillaume.Ginolhacniv-smb.fr": return "ginolhac"
        if mail == "Michel Ondarts": return "ondarts"
        raise InvalidMailException(f"Le mail \"{mail}\" est invalide")

    @staticmethod
    def format_last_name(mail:str)->str:
        """ Tente d'extraire le nom de famille d'un mail  """
        at_symb_in_mail = "@" in mail
        if not at_symb_in_mail:
            return Prof.format_last_name_exception(mail)
        return unidecode(re.split("\.|\. | ", mail.lower().split("@")[0])[-1])

    @staticmethod
    def all(driver)->dict:
        """ Méthode principale qui scrap les profs et leurs cours. Elle renvoie un objet json"""
        profs = {}

        # Lecture des formations listées
        conteneurFormations = driver.find_element(By.CSS_SELECTOR, "#c3506 > div > div > form > ul > li.item1 > div")

        # (Utilisation d'un set pour éviter les duplicatas)
        formations = set(
            e.get_attribute('id')
            for e in conteneurFormations.find_elements(By.TAG_NAME, "input")
            if e.get_attribute('id') != ''
        )

        print("---------- RECUPERATION DES COURS --------")

        # Boucle principale, récupère toutes les données formation par formation
        for iFormation, formation in enumerate(formations):

            # Accès à la page d'accueil
            driver.get("https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html")
            driver.find_elements(By.ID, formation)[0].click()
            driver.find_element(By.CSS_SELECTOR, "#c3506 > div > div > form > div.filterButtons > button:nth-child(1)").click()

            # Lecture des modules listés
            modulesConteneur = driver.find_element(By.CLASS_NAME, "items")
            ueName = None

            # Boucle secondaire, récupère toutes les données modules par modules
            for line in modulesConteneur.find_elements(By.CLASS_NAME, "item"):

                # Accès à la page du module
                if "separateurUE" in line.get_attribute("class"): ueName = line.find_element(By.CLASS_NAME, "ue").text
                link = line.find_element(By.CSS_SELECTOR, "div.value > ul > li.intitule > a").get_attribute("href")
                driver.switch_to.new_window('course')
                driver.get(link)

                # Lecture des données du module
                titreCours = driver.find_element(By.CSS_SELECTOR, "#c853 > div > div.singleView.view > div.titleBar > div.titleLabel").text
                responsables = re.split(", | ; | - | Et | et |- | / |/|/ |; ", driver.find_element(By.CSS_SELECTOR,"#c853 > div > div.singleView.view > div.items > div:nth-child(3) > div:nth-child(1) > div.value").text)
                mails = re.split(", | ; | - | Et | et |,| / |/ ", driver.find_element(By.CSS_SELECTOR,"#c853 > div > div.singleView.view > div.items > div:nth-child(3) > div:nth-child(2) > div.value").text)

                # Gestion d'un cas d'erreur (nombre de mails différents du nombre de responsables)
                if len(mails) != len(responsables):
                    print(f"Le nombre de responsables {responsables} est différent du nombre de mails {mails}, lien: {link} ")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

                # Boucle tertiaire, récupère toutes les données prof par prof
                for nomProf, mailProf in zip(responsables, mails):
                    # Formatage du nom du prof
                    nomFullFormat = Prof.format_name(nomProf)

                    # Tentative de formatage du mail
                    try:
                        lastNameFormatted = Prof.format_last_name(mail=mailProf)
                    except InvalidMailException as e:
                        # Gestion de cas d'exceptions
                        if mailProf=="" and nomProf=="Adeline Berthier": lastNameFormatted = "berthier"
                        else:
                            print(f"{e}. Nom entier: \"{nomFullFormat}\", lien: {link}")
                            continue

                    # Teste si le prof existe déjà
                    if not lastNameFormatted in profs:
                        profs[lastNameFormatted] = Prof(nomFullFormat, mailProf.lower())

                    # Tentative de création du prof
                    prof = profs[lastNameFormatted]
                    prof.add_cours(ueName, titreCours)

                # Fin de la récupération prof par prof, retour à la liste des modules
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            # Fin de la récupération module par module, retour à la page d'accueil
            driver.get('https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html')
            print(f"\n{formation.upper()} terminé")

        # Fin de la récupération formation par formation, scrapping terminé
        print("---------- FIN DE SCRAPPING --------")
        return profs

    def __str__(self):
        return f"{self.nom}: {self.mail}, {self.nb_ue()} UE, {self.nb_cours()} cours"
