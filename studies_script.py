# -*- coding: utf-8 -*-
import json

from src import Prof
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

if __name__ == '__main__':
    """
    Ce script permets de récupérer toutes les recherches ("papers") faites par des profs
    Sur le site https://hal.science/
    On importe ces profs depuis le fichier data/profs.json
    (Si le fichier n'existe pas, il faut exécuter le script courses_script.py)
    """

    # Getting profs from json
    with open("data/profs.json", "r", encoding="utf8") as file:
        profsJson = json.load(file)

    profs = [Prof.from_json(profJson) for profJson in profsJson]

    # Opening web driver
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)

    # Scrapping papers for each prof
    for prof in profs[:4]:
        # Searching prof in search bar
        splittedFullName = prof.nom.split(" ")
        prenom, nom = splittedFullName[0], ' '.join(splittedFullName[1:])
        profLink = f"https://hal.science/search/index/?qa%5BauthFullName_t%5D%5B%5D={prenom}%20{nom}"
        driver.get(profLink)

        # Looking for results
        try:
            # Prof has no papers
            driver.find_element(By.CSS_SELECTOR, "body > main > section > section > div.section-shadow > div")
            print(f"{prof.nom}, no results\n")
            continue
        except NoSuchElementException:
            # Prof has some papers

            # Displaying stats for infos/debugging
            nbResults = int(driver.find_element(By.CSS_SELECTOR, "body > main > section > section.col-12.col-sm-9 > div.results-header > div:nth-child(1) > span").text.split(" ")[0])
            nbPages = nbResults // 30 + 1
            print(f"{prof.nom}. Total results: {nbResults}, {nbPages} pages, lien: {profLink}")

            # Scrapping papers on each page
            # We're already on page 1, so get() is called at end of loop
            for page in range(1,nbPages+1):
                resultsContainer = driver.find_elements(By.CSS_SELECTOR, "body > main > section > section.col-12.col-sm-9 > table > tbody > tr")

                # Displaying number of papers on this page
                print(f"Results on page {page}: {len(resultsContainer)}")
                for resultElement in resultsContainer:
                    paperName = resultElement.find_element(By.CSS_SELECTOR, "td.pl-4.pl-sm-0").text
                    prof.papers.append(paperName)

                # Next page
                driver.get(f"{profLink}&page={page+1}")

            # Displaying final results
            print(f"{prof.nom}, papers final count: {len(prof.papers)}\n")

    # Finished scrapping papers
    # Saving them in json
    with open('data/profs.json', 'w', encoding="utf8") as profFile:
        json.dump([prof.to_json() for prof in profs], profFile, indent=4)
        print("Finished ! File profs.json updated.")

