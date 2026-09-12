import xml.etree.ElementTree as ET
import psycopg2

# Config
db_config = {
    "dbname": "sae_204_20260526",
    "user": "delahamz",
    "password": "delahamz",
    "host": "localhost",
    "port": "5432"
}

fichier_xml = "PrixCarburants_quotidien_20260526.xml"

def nettoyer_texte(texte):#on met le texte entre guillemets pour SQL et double les apostrophes pour éviter les bugs.
    if texte == None:
        return "NULL"
    else:
        texte_propre = texte.replace("'", "''")
        return f"'{texte_propre}'"

def lancer_importation():#tout le vrai script
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    print("Connexion réussie.")

    print("Chargement du fichier XML en mémoire...")
    arbre_xml = ET.parse(fichier_xml)
    racine = arbre_xml.getroot()
    
    compteur = 0

    for station_xml in racine.findall("pdv"):
        compteur += 1
        # recup attributs station
        id_station = station_xml.get("id")
        pop = station_xml.get("pop")
        cp = station_xml.get("cp")
        
        # on extrait le code_departement via le code postal
        if cp != None:
            code_departement = cp[0] + cp[1]
            #if code_departement =="97": 
            #    code_departement =cp[0]+cp[1]+cp[2]
            # après ça c'est au cas ou il sont là l'outre mer,
            #  mais ça montre qu'on a compris qu'il fallais recuperer les 3 premier chiffres du cp
            
        else:
            code_departement ="NULL"

        # coordonnees (pas de geom)
        latitude_brute = station_xml.get("latitude")
        longitude_brute = station_xml.get("longitude")
        
        if latitude_brute!=None and latitude_brute!="" and longitude_brute!=None and longitude_brute!="":
            latitude = str(float(latitude_brute) / 100000)
            longitude = str(float(longitude_brute) / 100000)
        else :
            latitude ="NULL"
            longitude ="NULL"

        # en textes valides (ville et adresse)
        balise_ville = station_xml.find("ville")
        if balise_ville != None:
            ville = nettoyer_texte(balise_ville.text)
        else:
            ville = "NULL"

        balise_adresse = station_xml.find("adresse")
        if balise_adresse != None:
            adresse = nettoyer_texte(balise_adresse.text)
        else:
            adresse = "NULL"

        # on nettoie
        pop_sql = nettoyer_texte(pop)
        cp_sql = nettoyer_texte(cp)
        dept_sql = nettoyer_texte(code_departement)

        # creation département ici, on exploite ce qu'on a fait en haut
        if code_departement != "NULL":
            # on vérifie si le département existe deja dans la table departement
            cursor.execute(f"SELECT code_departement FROM departement WHERE code_departement = {dept_sql};")
            # sinon on le crée
            if len(cursor.fetchall()) == 0:
                cursor.execute(f"INSERT INTO departement (code_departement) VALUES ({dept_sql});")

        #verifs et insertiuon dans station
        cursor.execute(f"SELECT id_station FROM station WHERE id_station = {id_station};")
        resultat_verif = cursor.fetchall()
        
        if len(resultat_verif) == 0:
            cursor.execute(f"""
                INSERT INTO station (id_station, pop, code_postal, nom_ville, adresse, latitude, longitude, code_departement)
                VALUES ({id_station}, {pop_sql}, {cp_sql}, {ville}, {adresse}, {latitude}, {longitude}, {dept_sql});""")
        else:
            cursor.execute(f"""
                UPDATE station 
                SET pop = {pop_sql}, code_postal = {cp_sql}, nom_ville = {ville}, 
                    adresse = {adresse}, latitude = {latitude}, longitude = {longitude}, code_departement = {dept_sql}
                WHERE id_station = {id_station};""")

        # maintenant c'est service
        balise_services = station_xml.find("services")
        if balise_services != None:
            for balise_service in balise_services.findall("service"):
                nom_service = balise_service.text
                if nom_service != None:
                    nom_service_sql = nettoyer_texte(nom_service)
                    cursor.execute(f"SELECT id_service FROM service WHERE service_propose = {nom_service_sql};")
                    resultat_service = cursor.fetchall()
                    
                    if len(resultat_service) == 0:
                        cursor.execute(f"INSERT INTO service (service_propose) VALUES ({nom_service_sql});")
                        cursor.execute(f"SELECT id_service FROM service WHERE service_propose = {nom_service_sql};")
                        nouveau_resultat = cursor.fetchall()
                        premiere_ligne = nouveau_resultat[0]
                        id_service_a_utiliser = premiere_ligne[0]
                    else:
                        premiere_ligne = resultat_service[0]
                        id_service_a_utiliser = premiere_ligne[0]
                    
                    cursor.execute(f"SELECT id_service FROM posseder WHERE id_service = {id_service_a_utiliser} AND id_station = {id_station};")
                    if len(cursor.fetchall()) == 0:
                        cursor.execute(f"INSERT INTO posseder (id_service, id_station) VALUES ({id_service_a_utiliser}, {id_station});")

        # les prix
        for balise_prix in station_xml.findall("prix"):
            id_carburant = balise_prix.get("id")
            valeur_prix = balise_prix.get("valeur")
            date_maj = balise_prix.get("maj")
            
            if date_maj != None:
                date_sql = nettoyer_texte(date_maj)
                
                cursor.execute(f"SELECT id_carburant FROM prix WHERE id_carburant = {id_carburant} AND id_station = {id_station} AND date_prix_maj = {date_sql};")
                if len(cursor.fetchall()) == 0:
                    cursor.execute(f"INSERT INTO prix (id_carburant, id_station, date_prix_maj, prix_carburant) VALUES ({id_carburant}, {id_station}, {date_sql}, {valeur_prix});")

        # rupture
        for balise_rupture in station_xml.findall("rupture"):
            id_carburant = balise_rupture.get("id")
            type_rupture = balise_rupture.get("type")
            date_debut = balise_rupture.get("debut")
            if type_rupture == None:
                type_rupture = "Inconnu"
            type_rupture_sql = nettoyer_texte(type_rupture)
            
            if date_debut != None:
                date_debut_sql = nettoyer_texte(date_debut)
                cursor.execute(f"SELECT id_carburant FROM rupture WHERE id_carburant = {id_carburant} AND id_station = {id_station} AND debut_rupture = {date_debut_sql};")
                if len(cursor.fetchall()) == 0:
                    cursor.execute(f"INSERT INTO rupture (id_carburant, id_station, debut_rupture, type_rupture) VALUES ({id_carburant}, {id_station}, {date_debut_sql}, {type_rupture_sql});")

        # ouverture horaire
        balise_horaires = station_xml.find("horaires")
        if balise_horaires != None:
            automate_texte = balise_horaires.get("automate-24-24")
            if automate_texte == "1" or automate_texte == "oui":
                automate_sql = "TRUE"
            else:
                automate_sql = "FALSE"
                
            for balise_jour in balise_horaires.findall("jour"):
                nom_jour = balise_jour.get("nom")
                ferme = balise_jour.get("ferme")
                
                heure_ouv = "NULL"
                heure_ferm = "NULL"
                
                if ferme != "1": # Si ce n'est pas fermé, on cherche les heures
                    balise_horaire = balise_jour.find("horaire")
                    if balise_horaire != None:
                        heure_ouv = balise_horaire.get("ouverture")
                        heure_ferm = balise_horaire.get("fermeture")
                        
                        # postgresql ne veut pas les '.' points pour les heures, on doit mettre les ':'
                        if heure_ouv != None:
                            heure_ouv = nettoyer_texte(heure_ouv.replace(".", ":"))
                        else:
                            heure_ouv = "NULL"
                            
                        if heure_ferm != None:
                            heure_ferm = nettoyer_texte(heure_ferm.replace(".", ":"))
                        else:
                            heure_ferm = "NULL"
                nom_jour_sql = nettoyer_texte(nom_jour)
                
                # Vérification
                cursor.execute(f"SELECT jour FROM ouverture_horaire WHERE jour = {nom_jour_sql} AND id_station = {id_station};")
                if len(cursor.fetchall()) == 0:
                    cursor.execute(f"""
                        INSERT INTO ouverture_horaire (jour, id_station, heure_ouverture, heure_fermeture, automate) 
                        VALUES ({nom_jour_sql}, {id_station}, {heure_ouv}, {heure_ferm}, {automate_sql});""")
                else:
                    cursor.execute(f"""
                        UPDATE ouverture_horaire 
                        SET heure_ouverture = {heure_ouv}, heure_fermeture = {heure_ferm}, automate = {automate_sql} 
                        WHERE jour = {nom_jour_sql} AND id_station = {id_station};""")

        # Sauvegarde toutes les 100 stations
        if compteur % 100 == 0:
            print(f"{compteur} stations traités.")
            conn.commit()
    conn.commit()
    cursor.close()
    conn.close()
    print("Importation terminée avec succès !")

# c'est parti pour le programme
lancer_importation()