# Dizajn: platforma za praćenje naučne podoblasti

Studija slučaja: Projekat 8b

## 1. Cilj sistema

Predmet dizajna je platforma koja na jednom mestu predstavlja jednu naučnu podoblast: njene radove, autore, časopise i pojmove. Ručno će se zadavati samo mali početni skup podataka. Sav ostali sadržaj platforma će samostalno preuzimati sa interneta i povremeno ažurirati.

Karakteristika sistema jeste način povezivanja podataka. Platforma neće čuvati eksplicitne veze, kao što su autorstvo ili citiranost. Umesto toga, svaki rad, autor, pojam i časopis biće predstavljen nizom brojeva (embedding) koji opisuje njegovo značenje, tako da stavke slična značenja imaju slične brojeve. Povezanost dve stavke biće izračunavana po potrebi, kao mera njihove sličnosti. Pretraga, preporuke i otkrivanje veza oslanjaće se isključivo na tu meru.

## 2. Tok rada sistema

Tok će biti opisan redom, od početnog unosa do čuvanja podataka.

Početni skup. Ručno će se napisati kratak fajl koji sadrži opis oblasti (nekoliko rečenica o matematičkoj psihologiji), nekoliko poznatih autora, nekoliko poznatih radova i ključne reči, na primer „evidence accumulation". To je jedini sadržaj koji se unosi ručno.

Prikupljanje. Program će iz javne baze publikacija (OpenAlex) preuzimati početne radove, najcitiranije radove početnih autora i rezultate pretrage po ključnim rečima. Ključne reči koriste se isključivo za pretragu i ne čuvaju se. Za svaki rad preuzimaju se naslov, apstrakt, autori i časopis.

Pretvaranje u brojeve. Naslov i apstrakt svakog rada biće prosleđeni modelu za embedding, koji vraća odgovarajući niz brojeva. Isti postupak primeniće se i na opis oblasti iz početnog fajla.

Provera pripadnosti oblasti. Pretraga po ključnim rečima vraća i radove koji ne pripadaju oblasti, na primer rad o računarskom „memory modelu". Zbog toga će se brojevi svakog rada poređiti sa brojevima opisa oblasti. Rad čija je sličnost visoka biće prihvaćen, a rad čija je sličnost niska biće odbačen. Za radove sa srednjom sličnošću postavljaće se pitanje jezičkom modelu (Gemini): da li rad pripada matematičkoj psihologiji. Početni radovi ne prolaze ovu proveru.

Pojmovi, autori i časopisi. Za svaki prihvaćen rad Gemini će izdvojiti nekoliko ključnih pojmova i svaki opisati jednom rečenicom. Pojmovi istog naziva iz različitih radova biće objedinjeni u jedan pojam. Kada se autor pojavi u dva prihvaćena rada, Gemini će napisati kratak opis njegovog istraživanja, a za časopis koji se pojavi u tri prihvaćena rada biće napisan opis onoga što objavljuje. I ti opisi biće pretvoreni u nizove brojeva.

Čuvanje. Svi podaci biće smešteni u jednu bazu. Svaki zapis sadrži tekst, odgovarajući niz brojeva i nekoliko osnovnih podataka potrebnih za prikaz, kao što su godina, časopis i imena autora.

Samostalan rast. Autor koji se pojavi u tri ili više prihvaćenih radova smatraće se delom oblasti, pa će se pri sledećem pokretanju preuzimati i njegovi ostali radovi. Oblast će se tako širiti uz autore koji joj već pripadaju. Program će pamtiti vreme poslednjeg pokretanja i pri narednim pokretanjima tražiti samo novije radove, dok se radovi koji su već u bazi preskaču.

## 3. Sadržaj baze

Baza će sadržati četiri vrste zapisa istog oblika: tekst, niz brojeva i osnovne podatke.

- Rad: tekst čine naslov i apstrakt.
- Pojam: tekst je kratka definicija koju piše Gemini.
- Autor: tekst je opis istraživanja koji piše Gemini na osnovu autorovih radova.
- Časopis: tekst je opis tematike koji piše Gemini na osnovu radova objavljenih u časopisu.

Veze između zapisa neće biti čuvane. Ime autora biće navedeno među podacima rada isključivo radi prikaza.

## 4. Korišćenje

Rezultati će se pregledati preko lokalnog sajta koji ne zahteva prijavu.

Pretraga. Korisnik unosi pitanje ili temu. Program pretvara unos u niz brojeva i vraća najbliže radove, autore, pojmove i časopise. Radovi o diffusion modelu biće pronađeni čak i kada unos ne sadrži te reči.

Stranica jedne stavke. Za rad će biti prikazani apstrakt i osnovni podaci, a za autora, časopis i pojam njihov opis. Ispod će biti navedene najbliže stavke svake vrste. Te veze se izračunavaju u trenutku prikaza i nisu unapred sačuvane.

Mapa. Sve stavke prikazuju se kao tačke na jednoj slici, obojene prema vrsti. Stavke slična značenja nalaze se blizu jedna drugoj. Izbor tačke otvara stranicu odgovarajuće stavke.

Ažuriranja. Poseban prikaz navodi šta je program dodao i kada.

## 5. Ograničenja i provera rezultata

Program će moći samostalno da se ponavlja, na primer jednom nedeljno. Dva pokretanja se neće preklapati. Ako pokretanje ne uspe, zbog nedostupnog servisa ili istekle kvote, već sačuvani podaci ostaju netaknuti, a naredno pokretanje ponavlja pokušaj. Broj radova biće ograničen radi kontrole troškova. Besplatni nivo Gemini servisa ograničava embedding na oko sto tekstova u minuti, pa će prvo veće prikupljanje trajati nekoliko sati.

Poznati rizici su sledeći. Presuda jezičkog modela za radove sa srednjom sličnošću neće uvek biti dosledna. Radovi bez apstrakta procenjuju se samo na osnovu naslova. Baza publikacija ponekad pogrešno razdvaja ili spaja autore, pa će za početne autore biti moguće zadati tačan identifikator. 

Rezultat će se proveriti na više načina: da li sadržaj posle prvog prikupljanja odgovara oblasti, da li pretraga poznatih tema vraća relevantne radove, da li među prihvaćenim radovima ima malo onih koji ne pripadaju oblasti i da li naredna pokretanja dodaju nov sadržaj bez dupliranja.

Kao moguća proširenja ostaju prikaz neočekivanih veza (autori slični po temi koji nisu koautori) i podrška za više oblasti.
