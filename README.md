# EMPG collector

Program prikuplja naučne radove iz jedne podoblasti (studija slučaja: Evropska grupa za matematičku psihologiju), odlučuje koji pripadaju oblasti i čuva ih u lokalnoj bazi kao vektore. Ideja i tok rada opisani su u [design.md](design.md).

## Pokretanje

Gemini ključ se upisuje u fajl `.env` (primer podešavanja nalazi se u `.env.example`):

```
GEMINI_API_KEY=ovde_ide_kljuc
```

Prikupljanje se pokreće komandom `run`, a broj označava najviše novih radova koji će se prikupiti:

```
run 25
```

Kada se `run` pokrene bez broja, program ispisuje kako se koristi. Početni skup (oblast, autori, radovi, ključne reči) nalazi se u `seed.yaml`.

## Kako radi

1. Opis oblasti iz `seed.yaml` pretvara se u niz brojeva (embedding).
2. Iz baze OpenAlex preuzimaju se radovi seed autora, seed radovi i rezultati pretrage po ključnim rečima.
3. Naslov i apstrakt svakog rada pretvaraju se u niz brojeva i porede sa opisom oblasti. Blizak rad se prihvata, daleki se odbacuje, a za srednje slučajeve Gemini odlučuje da li rad pripada oblasti.
4. Za prihvaćen rad Gemini izdvaja pojmove, a za autore i časopise koji se ponavljaju piše kratke opise.
5. Autori koji se pojave u tri prihvaćena rada postaju izvor novih radova, pa se oblast sama širi.

## Šta se čuva u bazi

Podaci se čuvaju na dva mesta u folderu `data/`.

**`data/chroma` je baza.** Sadrži četiri vrste zapisa istog oblika: **id, tekst, niz od 768 brojeva (vektor) i nekoliko podataka za prikaz.** Vektor je izračunat iz teksta, tako da tekstovi sličnog značenja imaju slične brojeve. Povezanost zapisa se ne čuva, nego se računa kao blizina vektora.

Rad (tekst su naslov i apstrakt):

```
id:      paper:W2045968318
tekst:   The Diffusion Decision Model: Theory and Data for Two-Choice Decision Tasks
         The diffusion decision model allows detailed explanations of behavior in ...
vektor:  [-0.013, 0.005, 0.005, -0.106, 0.014, ...]   (768 brojeva)
podaci:  godina 2007, časopis Neural Computation, autori "Roger Ratcliff; Gail McKoon",
         doi 10.1162/neco.2008.12-06-420, relevantnost 0.8276, pojmovi "diffusion decision model; drift rate; ..."
```

Pojam (tekst je definicija koju piše Gemini):

```
id:      concept:diffusion-decision-model
tekst:   diffusion decision model: A mathematical framework for modeling two-choice decision tasks ...
vektor:  [-0.005, -0.011, 0.001, -0.114, 0.011, ...]
podaci:  ime "diffusion decision model"
```

Autor (tekst je opis koji Gemini piše na osnovu njegovih radova):

```
id:      author:A5024018318
tekst:   Roger Ratcliff focuses on understanding cognitive processing in two-choice decision tasks ...
vektor:  [-0.029, 0.033, 0.016, -0.081, -0.025, ...]
podaci:  ime "Roger Ratcliff", broj radova 20
```

Časopis ima isti oblik kao autor (id `journal:S35223124`, tekst je opis onoga što objavljuje). Ime autora u podacima rada služi samo za prikaz, a veza „autor – rad" nigde nije zapisana.

**`data/state.json` je pomoćni fajl** koji program koristi između pokretanja. U njemu se pamte datum poslednjeg pokretanja, autori koji su već preuzeti i, za svakog autora i časopis, prihvaćeni radovi u kojima se pojavio. Po tom brojaču se odlučuje kada autor dobija opis i kada postaje izvor novih radova.

```
"authors": { "A5xxxxxxxxx": { "name": "Gail McKoon", "paper_ids": ["paper:W1", "paper:W2", "paper:W3"] } }
```

Brisanjem foldera `data/` prikupljanje počinje iz početka.
