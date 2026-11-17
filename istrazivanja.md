# Slični radovi i sistemi

Kratak pregled postojećih sistema koji rade nešto slično. Svaka tvrdnja je proverena na navedenom izvoru.

## 1. Semantic Scholar: preporuke radova preko embeddinga

Semantic Scholar svakom radu računa embedding modelom SPECTER i koristi ga za preporuke. Za korisnika se kandidati traže pretragom najbližih vektora (FAISS) među oko milion radova objavljenih u poslednjih 60 dana, a indeks se osvežava svake noći. Kandidati se zatim rangiraju pomoću dva linearna SVM modela, jednog nad TF-IDF prikazom i jednog nad SPECTER embeddingom radova koje je korisnik ocenio.

Sličnost sa našim sistemom: blizina vektora određuje šta je povezano. Razlika: pokriva celu literaturu i prati jednog korisnika, a ne jednu oblast, i ne koristi LLM za obradu.

Izvor: Kinney i saradnici, *The Semantic Scholar Open Data Platform*, arXiv:2301.10140 (2023), odeljak 3.4. https://arxiv.org/abs/2301.10140

## 2. SPECTER: embedding naučnog rada iz naslova i apstrakta

SPECTER je model koji pravi embedding rada iz njegovog naslova i apstrakta. Polazi od modela SciBERT i dodatno se trenira na citatima, tako da radovi koji se citiraju dobiju bliske vektore.

Sličnost sa našim sistemom: i kod nas se rad predstavlja embeddingom naslova i apstrakta. Razlika: mi koristimo opšti model (Gemini), a ne model treniran na citatima.

Izvor: Cohan i saradnici, *SPECTER: Document-level Representation Learning using Citation-informed Transformers*, ACL 2020, arXiv:2004.07180. https://arxiv.org/abs/2004.07180

## 3. Mapa biomedicinskih istraživanja

Autori su apstrakte oko 21 milion radova na engleskom iz baze PubMed pretvorili u embeddinge modelom PubMedBERT i prikazali ih na jednoj dvodimenzionalnoj mapi (t-SNE), gde su srodne teme blizu jedna drugoj.

Sličnost sa našim sistemom: odgovara našoj mapi oblasti. Razlika: obuhvata ceo PubMed, ne prikuplja podatke samostalno i prikazuje samo radove, bez autora, pojmova i časopisa.

Izvor: González-Márquez, Schmidt, Schmidt, Berens, Kobak, *The landscape of biomedical research*, bioRxiv 2023, doi:10.1101/2023.04.10.536208; objavljena verzija doi:10.1016/j.patter.2024.100968. Kod: https://github.com/berenslab/pubmed-landscape

## 4. Connected Papers: graf sličnih radova

Za jedan polazni rad pravi graf srodnih radova. Sličnost se računa iz ko-citiranja (radovi koje drugi radovi citiraju zajedno) i bibliografskog uparivanja (radovi koji citiraju iste izvore). Podaci dolaze iz Semantic Scholar-a.

Sličnost sa našim sistemom: pokazuje srodne radove umesto strogih veza. Razlika: sličnost dolazi iz citata, a ne iz značenja teksta.

Izvor: vodič biblioteke Loyola Marymount University, https://libguides.lmu.edu/AIresearchtools/CP (zvanična stranica connectedpapers.com/about nije mogla da se pročita).
