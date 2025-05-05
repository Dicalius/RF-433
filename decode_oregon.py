import sys

# Définition des seuils pour les signaux courts (S) et longs (L)
short_min = 200
short_max = 850
long_min = 850
long_max = 1400

def lire_fichier_raw(nom_fichier):
    """
    Lit les données brutes à partir d'un fichier texte.

    Args:
    nom_fichier (str): Le nom du fichier à lire.

    Returns:
    list: Une liste d'entiers représentant les durées des signaux.
    """
    try:
        with open(nom_fichier, 'r') as fichier:
            lignes = fichier.readlines()

        raw_data_ligne = None
        for ligne in lignes:
            if ligne.startswith("RAW_Data:"):
                raw_data_ligne = ligne.strip()
                break

        if raw_data_ligne:
            # Extract the data after "RAW_Data:" and split it into integers
            signals = list(map(int, raw_data_ligne.split(":")[1].split()))
            return signals
        else:
            print("Aucune ligne 'RAW_Data:' trouvée dans le fichier.")
            return []

    except FileNotFoundError:
        print(f"Erreur : Le fichier '{nom_fichier}' est introuvable.")
        return []
    except ValueError:
        print("Erreur : Données invalides dans le fichier. Assurez-vous qu'il contient une liste de nombres.")
        return []

# Fonction de classification des signaux en 'S' ou 'L'
def classify_signal(value):
    if short_min <= abs(value) <= short_max:
        return 'S'  # Short signal
    elif long_min <= abs(value) <= long_max:
        return 'L'  # Long signal
    else:
        return None  # Signal en dehors des seuils

# Fonction pour transformer les paires de 'S' en un seul 'S'
def transform_signal_chain(signal_chain):
    transformed = ""
    i = 0
    while i < len(signal_chain):
        if signal_chain[i] == 'S' and i + 1 < len(signal_chain) and signal_chain[i + 1] == 'S':
            transformed += 'S'
            i += 2
        else:
            transformed += signal_chain[i]
            i += 1
    return transformed

# Fonction pour reconstruire le bitstream à partir des symboles 'S' et 'L'
def reconstruire_bitstream(symboles):
    bitstream = [1]
    for symbole in symboles:
        if symbole == 'S':
            bitstream.append(bitstream[-1])
        elif symbole == 'L':
            bitstream.append(1 - bitstream[-1])
    return bitstream

# Fonction pour lire et inverser les nibbles
def lire_et_inverser_nibbles(bitstream):
    bitstream = bitstream[1:]
    nibbles = [bitstream[i:i+4] for i in range(0, len(bitstream), 4)]
    nibbles_inverses = [nibble[::-1] for nibble in nibbles]
    return nibbles, nibbles_inverses

# Fonction pour convertir en hexadécimal
def convertir_en_hexa(nibbles_inverses):
    hex_values = ['{:01X}'.format(int(''.join(map(str, nibble)), 2)) for nibble in nibbles_inverses]
    return ''.join(hex_values)

def parse_oregon_v3(raw_hex):
    # Supprimer les espaces ou les éventuels séparateurs
    raw_hex = raw_hex.strip().upper()

    # Étape 1 : détecter le préambule (suite de FF)
    i = 0
    while i < len(raw_hex) and raw_hex[i:i+2] == 'FF':
        i += 2
    preamble = raw_hex[:i]
    
    # Étape 2 : détecter le bit de synchronisation
    sync = raw_hex[i:i+1]
    i += 1

    # Étape 3 : extraire les 4 premiers nibbles après sync (i.e. 2 octets)
    sensor_code = raw_hex[i:i+4]

    # Dictionnaire des capteurs connus
    sensor_codes = {
        "5A5D": "BTHR918",
        "1D20": "THGR122NX / THGN123N",
        "F824": "THGR810 / THGN801",
        "EC40": "THN132N / THR238NF",
        "EA4C": "THWR288A",
        "D874": "UVN800",
        "1984": "WGR8003",
        "2A1D": "RGR918",
        "5D60": "BTHR968",
        "1A2D": "THGR228N",
        "F8B4": "THGR810",
        "EC70": "UVR128",
        "3A0D": "WGR918 / STR918",
        "2914": "PCR800",
        "2D10": "RGR968",
        "1A3D": "THGR918",
        "C844": "THWR800",
        "1994": "WGR800"
    }

    # Identifier le capteur si connu
    sensor_name = sensor_codes.get(sensor_code, "Inconnu")

    # Affichage
    print(f"Chaîne complète : {raw_hex}")
    print(f"Préambule       : {preamble}")
    print(f"Bit de synchro  : {sync}")
    print(f"Code capteur    : {sensor_code}")
    print(f"Nom capteur     : {sensor_name}")

    # Extraire température et humidité si capteur compatible
    if sensor_code in {"1D20", "F824", "F8B4"} and len(raw_hex) >= i + 13:
        # Extraire les nibbles
        nibbles = list(raw_hex[i:])

        try:
            temp_nibbles = nibbles[8:11]  # nibbles 8-11
            sign_nibble = nibbles[12]     # nibble 12
            hum_nibbles = nibbles[12:14]  # nibbles 12-13
            crc_nibbles = nibbles[15:17] # Extraire le CRC (nibbles 15 et 16)

            temp_str = ''.join(reversed(temp_nibbles))  # attention à l’ordre BCD inversé
            temperature = int(temp_str) / 10.0

            if sign_nibble.upper() == '8':
                temperature = -temperature

            humidity = int(''.join(reversed(hum_nibbles)))

            print(f"Température     : {temperature:.1f} °C")
            print(f"Humidité        : {humidity} %")

            if len(crc_nibbles) == 2:
                crc_hex = ''.join(crc_nibbles)
                print(f"CRC     : {crc_hex}")
            else:
                print("CRC non disponible (trame trop courte)")

        except (ValueError, IndexError):
            print("Erreur lors de l'extraction de la température/humidité.")

def afficher_symboles(symboles):
    print("\n--- Chaîne de symboles (S = court, L = long) ---")
    print(''.join(symboles))

# Fonction d'analyse principale
def analyse_symboles(symboles):
    bitstream_originale = reconstruire_bitstream(symboles)
    nibbles_originaux, nibbles_inverses = lire_et_inverser_nibbles(bitstream_originale)
    hexadecimal = convertir_en_hexa(nibbles_inverses)



    print("Comparaison des nibbles originaux et inversés :")
    print("Index | Nibble Original | Nibble Inversé")
    print("-----------------------------------------")
    for i in range(len(nibbles_originaux)):
        original_nibble = ''.join(map(str, nibbles_originaux[i]))
        reversed_nibble = ''.join(map(str, nibbles_inverses[i]))
        print(f"  {i:<4} | {original_nibble}          | {reversed_nibble}")
    
    print("\nChaîne en hexadécimal des nibbles inversés : ", hexadecimal)

    print("\n--- Analyse du capteur Oregon ---")
    parse_oregon_v3(hexadecimal)



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decode_oregon.py <nom_du_fichier>")
    else:
        nom_fichier = sys.argv[1]
        signals = lire_fichier_raw(nom_fichier)

        if signals:
            signal_chain = ''.join(classify_signal(signal) for signal in signals if classify_signal(signal) is not None)
            signal_chain_transformed = transform_signal_chain(signal_chain)
            afficher_symboles(signal_chain_transformed)
            analyse_symboles(signal_chain_transformed)



