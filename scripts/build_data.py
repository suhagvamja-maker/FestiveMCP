"""Builds data/benchmarks.json from the 'Festive Report 2026 Raw Data' sheet.

Values below were transcribed from the sheet on 2026-10-07. To refresh from a new
version of the sheet, use scripts/sync_from_xlsx.py instead (no hand-typing).
"""
import json, pathlib

CATS = [  # key, name, AOV, COD, Prepaid, PPCOD, EMI, CODRTO, PrepRTO, BlendRTO, CODReturn, CheckoutComp, CartAbandon, Rebuy, Charm, Charm%, Top10, T3orders, T3RTO, GMVd, Ordd, Rides
 ("fashion","Fashion & Apparel",1688,57.0,40.5,2.5,1.0,30.4,1.9,17.8,3.1,32.3,54.6,19,699,25.4,47.0,42.0,33.0,20.0,16.0,True),
 ("beauty","Beauty & Personal Care",831,49.1,48.5,2.4,0.7,32.6,2.1,16.5,1.9,33.4,51.6,25,999,14.7,38.0,44.0,34.8,8.0,11.0,True),
 ("home","Home & Living",1750,39.9,58.6,1.4,1.5,33.7,3.6,14.4,3.9,23.5,63.2,22,499,20.1,55.0,43.0,36.4,30.0,10.0,True),
 ("wellness","Wellness",1448,49.3,49.6,1.2,1.7,28.9,1.9,15.0,4.5,40.0,44.9,30,512,11.2,44.0,43.0,31.0,-12.0,-6.0,False),
 ("electronics","Electronics",1744,29.4,64.5,6.1,4.6,35.6,2.2,13.4,4.1,17.3,67.9,13,899,24.9,48.0,46.0,37.7,10.0,-13.0,True),
 ("food","Food & Beverages",999,46.4,52.1,1.5,0.3,22.0,1.9,11.1,0.6,39.4,51.7,29,608,4.2,39.0,44.0,23.1,-22.0,-20.0,False),
 ("toys","Toys, Games & Sports",1562,37.7,59.2,3.1,0.9,25.5,1.6,10.3,4.9,30.1,63.0,16,598,15.7,45.0,40.0,28.6,21.0,16.0,True),
 ("baby","Baby & Kids",1070,38.4,60.5,1.2,0.2,19.5,1.8,8.8,0.1,37.7,36.1,28,568,2.0,50.0,46.0,20.4,14.0,14.0,True),
 ("books","Books & Stationery",1123,38.3,59.7,2.0,0.1,25.3,1.6,10.8,1.3,28.1,56.0,11,599,9.6,41.0,45.0,27.8,44.0,28.0,True),
 ("pet","Pet Supplies",1199,45.7,52.2,2.1,0.0,31.0,2.6,17.6,6.3,44.0,39.4,27,540,7.3,55.0,33.0,32.9,91.0,19.0,True),
 ("hardware_auto","Hardware & Auto",1904,47.3,47.9,4.8,3.6,36.7,2.2,15.9,1.2,20.5,69.1,12,538,8.2,50.0,52.0,38.2,58.0,52.0,True),
 ("others","Others",1290,50.7,46.9,2.4,1.2,31.0,2.0,16.3,2.7,31.7,54.6,20,999,15.0,47.0,43.0,32.0,12.0,8.0,True),
]
FIELDS = ["aov_inr","cod_pct","prepaid_pct","ppcod_pct","emi_pct","cod_rto_pct","prepaid_rto_pct",
          "blended_rto_pct","cod_return_pct","checkout_completion_pct","cart_abandon_pct","rebuy_days",
          "charm_price_inr","charm_price_pct","top10_gmv_share_pct","tier3_orders_pct","tier3_rto_pct",
          "festive_gmv_lift_pct","festive_orders_lift_pct","rides_festive"]

BASKET = {  # (% of orders, COD RTO %) for 1 / 2 / 3-4 / 5+
 "fashion":[(64.5,31.4),(22.1,23.1),(11.1,18.7),(2.3,21.4)],
 "beauty":[(37.9,35.1),(29.3,38.4),(20.4,33.5),(12.3,27.5)],
 "home":[(60.7,36.5),(14.7,22.8),(8.9,22.0),(15.7,23.9)],
 "wellness":[(70.7,30.0),(19.5,32.4),(7.9,25.1),(1.8,19.7)],
 "electronics":[(79.5,34.8),(14.2,41.9),(3.8,19.0),(2.6,16.3)],
 "food":[(63.8,31.8),(16.6,23.6),(11.1,16.8),(8.5,15.4)],
 "toys":[(66.9,25.8),(20.3,21.0),(9.7,11.6),(3.1,8.8)],
 "baby":[(38.6,15.4),(13.6,29.7),(26.5,23.0),(21.3,16.1)],
 "books":[(68.5,29.7),(19.5,26.5),(8.4,22.6),(3.7,25.1)],
 "pet":[(83.1,31.9),(11.5,28.0),(4.0,17.9),(1.4,20.0)],
 "hardware_auto":[(80.9,40.8),(11.4,23.1),(5.3,20.0),(2.4,12.8)],
 "others":[(63.0,32.0),(21.0,30.0),(12.0,24.0),(4.0,28.0)],
}
SIZES = ["1 item","2 items","3-4 items","5+ items"]

SOLD = {
 "fashion":[("Bangles & anklets",11.4),("Pants",10.3),("Necklaces",8.1),("T-shirts",6.7),("Shirts",6.7)],
 "beauty":[("Serums",10.7),("Cleansers",10.7),("Perfumes",8.9),("Moisturisers",7.7),("Sunscreen",6.9)],
 "home":[("Cleaning",8.5),("Storage",8.1),("Kitchen tools",7.8),("Cookware",4.2),("Décor",4.0)],
 "wellness":[("Herbal supplements",15.0),("Protein",13.2),("Vitamins",4.5),("Orthopaedic supports",4.4)],
 "electronics":[("Phone covers",35.5),("Earphones",12.3),("Smartwatches",8.9),("Watches",4.0),("Laptop skins",3.5)],
 "food":[("Functional drinks",18.9),("Atta & grains",8.5),("Protein bars",7.7),("Namkeen",6.0),("Seasonings",4.2)],
 "toys":[("Educational toys",23.3),("Educational games",11.2),("Jigsaw puzzles",6.7),("Action figures",5.3)],
 "baby":[("Baby wipes",27.4),("Rash care",14.9),("Baby wash",11.1),("Diapers",8.9),("Baby soaps",8.2)],
 "books":[("Academic books",39.0),("Pens & pencils",16.3),("Sensory toys",7.9),("Planners",7.2),("Notebooks",4.2)],
 "pet":[("Dog food",27.6),("Skin & coat care",19.5),("Pet supplements",8.9),("Pet clothing",7.9),("Pet shampoo",5.3)],
 "hardware_auto":[("Car interior",28.6),("Bike parts",20.8),("Car care",6.6),("Car exterior",6.4),("Power tools",6.1)],
 "others":[],
}

TIMELINE = [
 ("Navratri","2025-09-22","Start of the season; the big sale week (BBD / GIF) kicks off here"),
 ("Dussehra","2025-10-02","End of the opening sale week"),
 ("Dhanteras","2025-10-18","Dhanteras → Diwali gifting peak begins"),
 ("Diwali","2025-10-21","Peak festival. The network's single biggest DAY is the sale week ~2-3 weeks earlier, not Diwali day itself"),
 ("Chhath","2025-10-28","Tail of the festive season"),
 ("Window end","2025-11-05","End of the benchmarked festive window"),
]

out = {
 "meta": {
  "title": "GoKwik Festive Checkout Benchmark",
  "window": {"start": "2025-09-22", "end": "2025-11-05", "label": "Festive 2025"},
  "source": "GoKwik network — category cuts across thousands of Indian D2C brands",
  "caveat": "Directional, for planning. Figures are analytics estimates; smaller categories are more directional.",
  "peaks_note": "Two demand peaks: (1) big sale week — Navratri / BBD-GIF; (2) Dhanteras → Diwali gifting. The sale-week spike, not Diwali day, is the biggest.",
  "payment_mix_note": "COD % + Prepaid % + PPCOD % = 100. EMI % is a subset of prepaid.",
 },
 "categories": [],
}
for row in CATS:
    key, name, vals = row[0], row[1], row[2:]
    c = {"key": key, "name": name, **dict(zip(FIELDS, vals))}
    b = BASKET[key]
    worst = max(range(4), key=lambda i: b[i][1])
    c["basket_risk"] = [{"basket_size": SIZES[i], "pct_of_orders": b[i][0], "cod_rto_pct": b[i][1], "riskiest": i == worst} for i in range(4)]
    c["top_products"] = [{"rank": i+1, "product": p, "pct_of_units": s} for i, (p, s) in enumerate(SOLD[key])]
    out["categories"].append(c)
out["festival_timeline"] = [{"event": e, "date": d, "what_it_marks": w} for e, d, w in TIMELINE]

p = pathlib.Path(__file__).resolve().parent.parent / "data" / "benchmarks.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("wrote", p, len(out["categories"]), "categories")
