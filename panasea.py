import sys
import time

def jalan_lirik():
    lirik = [
        ("terang selalu dirindukan gelap", 0.21),
        ("tenang selalu dirindukan resah", 0.19),
        ("begitu juga bila", 0.15),
        ("jauh engkau berada", 0.2),
        ("takkan ku berubah", 0.12),
        ("walau tak bersama", 0.1),
        ("kita tak pernah terpisah", 0.1),
        ("melintas ruang dan waktu", 0.13),
        ("selamanya........", 0.2),
    ]

    delay = [7.5, 8.3, 4.9, 7.8, 2.2, 2, 3.9, 3.4, 4, ]
    print("Memutar Panasea - rumahsakit")
    time.sleep(6.2)

    for i, (baris_lagu, delay_karakter) in enumerate(lirik):
        for karakter in baris_lagu:
            print(karakter, end='')
            sys.stdout.flush()
            time.sleep(delay_karakter)
        time.sleep(delay[i])
        print('')

    print("The End-")

jalan_lirik()