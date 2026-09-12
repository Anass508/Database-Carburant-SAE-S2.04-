-- suppression si déja existance tables
DROP TABLE IF EXISTS rupture CASCADE;
DROP TABLE IF EXISTS prix CASCADE;
DROP TABLE IF EXISTS posseder CASCADE;
DROP TABLE IF EXISTS ouverture_horaire CASCADE;
DROP TABLE IF EXISTS service CASCADE;
DROP TABLE IF EXISTS carburant CASCADE;
DROP TABLE IF EXISTS station CASCADE;
DROP TABLE IF EXISTS departement CASCADE;
DROP TABLE IF EXISTS region CASCADE; -- suppression définitif de region

-- creation tables

-- departement
-- plus le nom_département pas de clé étrangère vers region
CREATE TABLE departement (
    code_departement VARCHAR(3) PRIMARY KEY
);

-- Table : station , plus l'attribut geom car compliqué de l'avoir, il est pas là, à la base on se basé sur csv
CREATE TABLE station (
    id_station INT PRIMARY KEY,
    pop CHAR(1),
    code_postal VARCHAR(10) NOT NULL,
    nom_ville VARCHAR(250),
    adresse VARCHAR(250),
    latitude NUMERIC,
    longitude NUMERIC,
    code_departement VARCHAR(3),     
    FOREIGN KEY (code_departement) REFERENCES departement(code_departement)
);

-- carburant, là il faut le insert initial pas dans le script
CREATE TABLE carburant (
    id_carburant INT PRIMARY KEY,
    nom_carburant VARCHAR(50) NOT NULL
);

-- service
CREATE TABLE service (
    id_service INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    service_propose VARCHAR(250) NOT NULL
);

-- ouverture_horaire
CREATE TABLE ouverture_horaire (
    jour VARCHAR(20) NOT NULL,
    id_station INT NOT NULL,
    heure_ouverture TIME,
    heure_fermeture TIME,
    automate BOOLEAN,
    PRIMARY KEY (jour, id_station),
    FOREIGN KEY (id_station) REFERENCES station(id_station)
);

--posseder
CREATE TABLE posseder (
    id_service INT NOT NULL,
    id_station INT NOT NULL,
    PRIMARY KEY (id_service, id_station),
    FOREIGN KEY (id_service) REFERENCES service(id_service),
    FOREIGN KEY (id_station) REFERENCES station(id_station)
);

-- prix
CREATE TABLE prix (
    id_carburant INT NOT NULL,
    id_station INT NOT NULL,
    date_prix_maj TIMESTAMP NOT NULL,
    prix_carburant NUMERIC(4,3) NOT NULL,
    PRIMARY KEY (id_carburant, id_station, date_prix_maj),
    FOREIGN KEY (id_carburant) REFERENCES carburant(id_carburant),
    FOREIGN KEY (id_station) REFERENCES station(id_station)
);

--rupture
CREATE TABLE rupture (
    id_carburant INT NOT NULL,
    id_station INT NOT NULL,
    debut_rupture TIMESTAMP NOT NULL,
    type_rupture VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_carburant, id_station, debut_rupture),
    FOREIGN KEY (id_carburant) REFERENCES carburant(id_carburant),
    FOREIGN KEY (id_station) REFERENCES station(id_station)
);

INSERT INTO carburant (id_carburant, nom_carburant) 
VALUES (1,'Gazole'), (2,'SP95'), (3,'E85'), (4,'GPLc'), (5,'E10'), (6,'SP98');