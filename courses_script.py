# -*- coding: utf-8 -*-
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException

from src import Prof

def get_to_program_page():
    """ Cette fonction effectue toutes les tâches ennuyantes à l'ouverture du driver (connexion, refus de cookies...) """
    # Ouverture du driver
    driver.get('https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html')
    driver.implicitly_wait(5)

    # Pop-up cookies
    if driver.find_elements(By.ID, "tarteaucitronAlertBig"):
        driver.find_element(By.XPATH, "/html/body/div[4]/div[3]/button[2]").click()

    # Connexion
    connectUsername = driver.find_element(By.ID, "user")
    connectPassword = driver.find_element(By.ID, "pass")
    connectButton = driver.find_element(By.XPATH, "/html/body/section[3]/div/div/div/div/div/form/fieldset/input[3]")
    with open("id.txt", "r") as file:
        ids = file.read().split(" ")
        connectUsername.send_keys(ids[0])
        connectPassword.send_keys(ids[1])
    connectButton.click()

    # Test si la connexion a échoué
    try:
        driver.find_element(By.XPATH, "/html/body/section[3]/div/div/div/div/div/form/fieldset/input[3]")
        print("Vos identifiants sont incorrects, changez-les dans le fichier \"id.txt\"")
        driver.close()
        exit()
    except NoSuchElementException:
        driver.get('https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html')

if __name__ == "__main__":
    """
    Ce script permets à la fois de récupérer les profs de Polytech Annecy,
    mais aussi l'ensemble des UE (Unité d'Enseignement) et des modules
    On exporte toutes ces données dans le fichier data/profs.json à la fin du scrapping
    """
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)

    # On se rend sur la page principale
    get_to_program_page()

    # On lance le scrapping
    profs = Prof.all(driver)

    # Enregistrement des données dans un json
    with open("data/profs.json", "w", encoding='utf8') as profFile:
        json.dump([prof.to_json() for prof in profs.values()], profFile, indent=4)
        print("Terminé ! Fichier profs.json actualisé.")

    driver.close()