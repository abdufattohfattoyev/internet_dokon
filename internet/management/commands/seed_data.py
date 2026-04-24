from django.core.management.base import BaseCommand
from internet.models import Category, Product


DATA = [
    {
        "name": "Oziq-ovqat mahsulotlari",
        "products": [
            ("Guruch 'Dev zira' 5 kg", "Yuqori sifatli o'zbek guruchi, pishirganda mo'rtlanmaydi", 85000),
            ("Mosh 1 kg", "Toza, tozalangan mosh doni. Osh va sho'rvaga mos", 18000),
            ("Un 'Navbaxor' 5 kg", "Yuqori navli bug'doy uni, non va pishiriqlar uchun", 45000),
            ("Makaron 'Baraka' 500 g", "Durum bug'doydan tayyorlangan makaron mahsuloti", 8500),
            ("Osh tuzi 1 kg", "Yodlashtirilgan osh tuzi, oilaviy iste'mol uchun", 5000),
            ("Ziravorlar to'plami", "10 xil aralashma ziravorlar to'plami, 200 g", 22000),
        ],
    },
    {
        "name": "Ichimliklar",
        "products": [
            ("Coca-Cola 2 L", "Original Coca-Cola gazlangan ichimlik, 2 litr", 22000),
            ("Pepsi 1.5 L", "Pepsi gazlangan shirin ichimlik, 1.5 litr", 18000),
            ("Mineral suv 'Nurota' 1.5 L", "Tabiiy mineral suv, gazlangan, Nurota bulog'i", 8000),
            ("Lipton Qora choy 100 paket", "Lipton qora choy paketchalari, 100 ta", 35000),
            ("Granfuurt olcha sharbat 1 L", "Tabiiy meva sharbati, qo'shimcha rang va konservant yo'q", 15000),
            ("Red Bull 250 ml", "Energetik ichimlik, kofein va taurin bilan boyitilgan", 18000),
        ],
    },
    {
        "name": "Sut mahsulotlari",
        "products": [
            ("Sut 3.2% 1 L", "Pasterizatsiya qilingan sigir suti, 3.2% yog'lilik", 12000),
            ("Qatiq 500 g", "Tabiiy qatiq, probiotiklar bilan boyitilgan", 9000),
            ("Pishloq 'Rossiyskiy' 300 g", "Qattiq pishloq, quyuq sariq rang, 300 g", 45000),
            ("Sariyog' 200 g", "Tabiiy sigir sariyog'i, 82.5% yog'lilik", 28000),
            ("Qaymoq 20% 400 g", "Og'ir qaymoq, 20% yog'lilik, pishirishga mos", 16000),
            ("Tvorog 9% 250 g", "Siqdirilib tayyorlangan tvorog, 9% yog'lilik", 18000),
        ],
    },
    {
        "name": "Go'sht va baliq",
        "products": [
            ("Tovuq go'shti (file) 1 kg", "Muzlatilmagan tovuq filesi, 1 kg, halol", 48000),
            ("Mol go'shti 1 kg", "Yangi mol go'shti, a'lo navli, halol so'yilgan", 120000),
            ("Kolbasa 'Doktorskaya' 500 g", "Qaynatma kolbasa, yuqori sifatli, 500 g", 45000),
            ("Talapia baliq 1 kg", "Muzlatilgan talapia, 1 kg, toza tozalangan", 35000),
            ("Sardina konservasi 240 g", "Sardina baliq konservasi, zaytun moyi bilan", 18000),
            ("Tovuq qanoti 1 kg", "Yangi tovuq qanoti, grillga va sho'rvaga mos", 32000),
        ],
    },
    {
        "name": "Non va pishiriqlar",
        "products": [
            ("Bug'doy noni", "Yangi pishirilgan bug'doy noni, 350 g", 4500),
            ("Lavash yupqa non", "Yupqa lavash, soch non, 200 g", 6000),
            ("Keks shokoladli 350 g", "Shokolad qoplamali keks, 350 g", 22000),
            ("Pechene 'Jubilee' 200 g", "Klassik pechene, choy uchun, 200 g", 15000),
            ("Sushki 'Ring' 500 g", "Klassik sushki, yogsiz, 500 g", 18000),
            ("Tort 'Napoleon' 1 kg", "Klassik Napoleon torti, 8-10 kishilik", 85000),
        ],
    },
    {
        "name": "Shirinliklar",
        "products": [
            ("Shokolad 'Alpen Gold' sut 100 g", "Sut shokoladi, Alpen Gold, 100 g", 22000),
            ("Karamel 'Barberry' 500 g", "Assorted karamellar, 500 g, aralash lazzat", 20000),
            ("Marmelad aralash 400 g", "Mevali marmelad, 400 g, assorted", 18000),
            ("Zefir vanil 300 g", "Yumshoq vanil zefir, 300 g", 25000),
            ("Halva 'Toshkent' 500 g", "Klassik o'zbek halvasi, 500 g", 30000),
            ("Iris karamel 200 g", "Yumshoq iris karamel, 200 g", 16000),
        ],
    },
    {
        "name": "Meva va sabzavot",
        "products": [
            ("Olma 1 kg", "Yangi olma, Fuji navi, 1 kg, shirin-nordon", 12000),
            ("Banan 1 kg", "Ekvador banani, etilgan, 1 kg", 18000),
            ("Pomidor 1 kg", "Toza pomidor, yangi uzilgan, 1 kg", 8000),
            ("Bodring 1 kg", "Yangi bodring, mayin, 1 kg", 7000),
            ("Limon 1 kg", "Yangi limon, chayon lazzatida, 1 kg", 15000),
            ("Uzum 1 kg", "Shirin uzum, tayyor iste'molga, 1 kg", 22000),
        ],
    },
    {
        "name": "Uy kimyoviy tovarlari",
        "products": [
            ("Ariel kir yuvish kukuni 3 kg", "Avtomatik kir yuvish mashinasi uchun, 3 kg", 85000),
            ("Fairy idish yuvish 500 ml", "Fairy limon hidi bilan, 500 ml, tez ko'pikli", 22000),
            ("Domestos tualit tozalagichi 500 ml", "Kuchli dezinfeksion tualit tozalagichi, 500 ml", 25000),
            ("Mr. Proper universal 1 L", "Universal tozalagich, limon hidi, 1 L", 28000),
            ("Comfort matolarni yumshatgich 1 L", "Kir yumshatgich, bahor hidi, 1 L", 32000),
            ("Comet shkrablash kukuni 400 g", "Abraziv kukunli tozalagich, 400 g", 15000),
        ],
    },
    {
        "name": "Shaxsiy gigiena",
        "products": [
            ("Colgate tish pastasi 150 ml", "Mintali tish pastasi, karies va tosh oldini oladi", 18000),
            ("Head & Shoulders shampun 400 ml", "Kepak oldini oluvchi shampun, 400 ml", 55000),
            ("Dove sovun 100 g", "Moylovli sovun, teri qurishini oldini oladi, 100 g", 12000),
            ("Gillette Venus stanok", "Ayollar uchun 3 tigli stanok, 2 ta qo'shimcha", 85000),
            ("Kotex Promed 10 ta", "Gigienik prokladka, 10 ta, maxsus himoya", 22000),
            ("Nivea deo spray 150 ml", "48 soatlik antiperspirant, erkaklarcha hid, 150 ml", 42000),
        ],
    },
    {
        "name": "Bolalar mahsulotlari",
        "products": [
            ("Pampers 4 hajm 54 ta", "Bolalar quruq shimchalari, 4 hajm (9-14 kg), 54 ta", 165000),
            ("Huggies 3 hajm 44 ta", "Bolalar quruq shimchalari, 3 hajm (6-11 kg), 44 ta", 145000),
            ("Johnson's Baby lotion 200 ml", "Bolalar terisi uchun yumshatuvchi losyon, 200 ml", 45000),
            ("Heinz bolalar ovqati 200 g", "6 oydan bolalar uchun tayyor ovqat, 200 g", 32000),
            ("Bolalar tish pastasi 60 ml", "6 yoshgacha bolalar uchun tish pastasi, yutish mumkin", 18000),
            ("Bolalar shampuni 300 ml", "Ko'z yashiga moyil bolalar shampuni, 300 ml", 28000),
        ],
    },
]


class Command(BaseCommand):
    help = "10 ta kategoriya va 60 ta mahsulot qo'shadi"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Avval mavjud ma'lumotlarni o'chirib tashlaydi")

    def handle(self, *args, **options):
        if options["clear"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Barcha mahsulot va kategoriyalar o'chirildi"))

        created_cats = 0
        created_prods = 0

        for cat_data in DATA:
            cat, cat_created = Category.objects.get_or_create(name=cat_data["name"])
            if cat_created:
                created_cats += 1
                self.stdout.write(f"  + Kategoriya: {cat.name}")

            for name, desc, price in cat_data["products"]:
                _, prod_created = Product.objects.get_or_create(
                    name=name,
                    defaults={"category": cat, "description": desc, "price": price},
                )
                if prod_created:
                    created_prods += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nMuvaffaqiyatli: {created_cats} kategoriya, {created_prods} mahsulot qo'shildi"
            )
        )
