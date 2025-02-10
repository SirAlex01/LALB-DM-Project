linear_b_dict = {
    "\U00010000": "a", "\U00010001": "e", "\U00010002": "i", "\U00010003": "o", "\U00010004": "u",
    "\U00010005": "da", "\U00010006": "de", "\U00010007": "di", "\U00010008": "do", "\U00010009": "du",
    "\U0001000A": "ja", "\U0001000B": "je", "\U0001000D": "jo",
    "\U0001000F": "ka", "\U00010010": "ke", "\U00010011": "ki", "\U00010012": "ko", "\U00010013": "ku",
    "\U00010014": "ma", "\U00010015": "me", "\U00010016": "mi", "\U00010017": "mo", "\U00010018": "mu",
    "\U00010019": "na", "\U0001001A": "ne", "\U0001001B": "ni", "\U0001001C": "no", "\U0001001D": "nu",
    "\U0001001E": "pa", "\U0001001F": "pe", "\U00010020": "pi", "\U00010021": "po", "\U00010022": "pu",
    "\U00010023": "qa", "\U00010024": "qe", "\U00010025": "qi", "\U00010026": "qo",
    "\U00010028": "ra", "\U00010029": "re", "\U0001002A": "ri", "\U0001002B": "ro", "\U0001002C": "ru",
    "\U0001002D": "sa", "\U0001002E": "se", "\U0001002F": "si", "\U00010030": "so", "\U00010031": "su",
    "\U00010032": "ta", "\U00010033": "te", "\U00010034": "ti", "\U00010035": "to", "\U00010036": "tu",
    "\U00010037": "wa", "\U00010038": "we", "\U00010039": "wi", "\U0001003A": "wo",
    "\U0001003C": "za", "\U0001003D": "ze", "\U0001003F": "zo",
    "𐁅": "nwa", "𐁈": "rya", "𐁀":"ha", "𐁆":"phu","𐁊":"ryo", "𐁉":"rai", "𐁇": "pte", "𐁁":"ai", "𐁂": "au", "𐁋": "tya",
    "𐁄":"dwo"
}

import csv
def convert_file(file):
    with open(file, "r", encoding="utf-8") as csvfile:
        csvfile.readline()  # Skip header
        with open("converted_"+file, "w", encoding="utf-8", newline='') as csvfile2:
            reader = csv.reader(csvfile, delimiter="\t")
            writer = csv.writer(csvfile2)
            writer.writerow(["LB", "Greek"])
            for row in reader:
                myc = ""
                for c in row[0]:
                    myc += linear_b_dict[c] + "-"
                myc = myc[:-1]
                if row[1] != "_":
                    writer.writerow([myc, row[1]])

convert_file("linear_b-greek.cog")
convert_file("linear_b-greek.names.cog")