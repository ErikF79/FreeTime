# FreeTime - Changelog modernizzazione (Fase 1 + Fase 2)

## Fase 1 - Stack moderno (Python 3.12 / Flask 3.x)

Testato: home, giocatori, squadre, catalogo giochi, storico, classifica,
sessioni, trofei, export CSV/JSON, backup ZIP, partita completa a Tris e
a Forza 4 (vs PC, tutti i RuleSet).

Modifiche necessarie (una sola, il resto del codice era gia' compatibile):

- `app.py`, route `/backup`: il parametro `attachment_filename` di
  `send_file()` e' stato rinominato `download_name` nelle versioni
  moderne di Flask/Werkzeug. Aggiornato di conseguenza.
- `requirements.txt`: aggiornato a `Flask==3.1.3` / `Werkzeug==3.1.8`
  (versioni testate).

Nessuna modifica ai template, alla logica di gioco, al modello dati JSON.

## Fase 2 - PWA installabile e resiliente offline

L'app resta un'applicazione Flask locale (server-rendered, nessuna
dipendenza da internet: gira su `localhost` sullo stesso dispositivo che
la mostra). Le aggiunte la rendono installabile come un'app nativa:

Nuovi file:
- `static/manifest.json` - nome, icone, colori, modalita' standalone.
- `static/icons/icon-192.png`, `icon-512.png`, `icon-maskable-512.png`,
  `apple-touch-icon.png` - icone coerenti con il logo esistente.
- `static/service-worker.js` - cache degli asset statici (CSS/JS/icone)
  per caricamento istantaneo. Non intercetta mai richieste POST (le
  mosse di gioco vanno sempre dritte al server Flask).
- `static/offline.html` - pagina di attesa mostrata solo se il server
  Flask locale non risponde per un istante (es. riavvio), al posto
  della schermata di errore del browser.

File modificati:
- `templates/base.html` - aggiunti i tag `<link rel="manifest">`,
  meta theme-color, apple-touch-icon, e lo script di registrazione
  del service worker.
- `app.py` - nuova route `/service-worker.js` che serve lo script sulla
  root (necessario perche' lo "scope" di un service worker copre solo
  la cartella da cui viene servito: da `/static/` coprirebbe solo
  quella cartella, dalla root copre tutta l'app).

## Fase 3.1 - Pannello istruttore + Ruota della fortuna

Nuovo motore riutilizzabile (pensato per servire anche Taboo, Passaparola
e Sarabanda in futuro):

- `engine/content_engine.py` - gestisce una coda di contenuti inseriti
  dall'istruttore (`data/instructor_content.json`), taggati per
  `game_id`. Ogni gioco pesca il primo contenuto non ancora usato per il
  proprio `game_id` e lo marca come consumato.
- Route `/instructor` (GET/POST) - form riservato agli istruttori per
  inserire la prossima frase; valida lunghezza e caratteri ammessi
  (niente numeri o simboli, solo lettere/spazi/punteggiatura semplice).
  Mostra la coda attuale con possibilità di rimuovere una voce
  (`/instructor/<id>/delete`).

Nuovo gioco completo:

- `games/wheel.py` - motore della Ruota della fortuna: gira la ruota
  (valori 100-500 punti, con possibilità di "Perdi turno"), indovina
  lettera per lettera (punti = occorrenze x valore ruota), oppure
  indovina la frase intera per un bonus di 500 punti. Gestisce turni tra
  un numero libero di partecipanti (1-8), pensato per un solo
  dispositivo passato di mano in mano.
- `/new-match/wheel` - selezione partecipanti (nessun RuleSet o
  difficoltà PC, non serve per questo gioco).
- `/play/wheel/start`, `/play/wheel`, `/play/wheel/rematch` - ciclo di
  gioco completo, con salvataggio del risultato su `results.json`
  (stesso formato degli altri giochi: `winner_id`, `participant_ids`,
  `status`, più `scores`/`phrase`/`category` come metadati aggiuntivi),
  aggiornamento partite/vittorie giocatori, integrazione automatica con
  classifica e storico esistenti.

Corretto anche un piccolo bug preesistente in home: il "gioco preferito"
mostrava sempre "Tris" per qualsiasi gioco diverso da Forza 4 (ora usa i
nomi reali dal registro giochi, quindi funziona correttamente anche con
la Ruota della fortuna e i giochi futuri).

Testato a fondo: validazione frasi non valide, coda vuota, partita
completa fino a vittoria (sia per esaurimento lettere sia indovinando
la frase intera), bonus frase case-insensitive, rematch, cancellazione
contenuti dalla coda, e nessuna regressione sul resto dell'app (Tris,
Forza 4, backup/restore, tutte le pagine).

## Fase 3.2 - Catalogo giochi unificato + animazione Ruota

Riorganizzazione dell'interfaccia richiesta dopo il primo test pratico:

- **Pagina Giochi (`/games`) riscritta da zero**: prima mostrava solo i
  RuleSet di Tris sotto un titolo fisso "Tris", come se le modalità di
  gioco fossero giochi a sé. Ora è un vero catalogo con una card per
  ciascun gioco (Tris, Forza 4, Ruota della fortuna, e Memory mostrato
  come "In arrivo" per trasparenza sulla roadmap). I RuleSet restano
  visibili in una sezione separata più sotto, chiaramente etichettata
  come modalità di Tris/Forza 4 - non più confusi con un elenco giochi.
- **Rimossa la voce "Ruota" dalla barra laterale**: ora si accede alla
  Ruota della fortuna esclusivamente dal catalogo Giochi, come tutti
  gli altri giochi, invece di avere un trattamento speciale.
- **`/new-match` supporta la preselezione**: cliccando "Gioca" su Tris o
  Forza 4 dal catalogo, il gioco corretto è già selezionato nel form
  (prima era sempre Tris di default).
- Le modalità/RuleSet restano selezionabili solo dove ha senso: la
  Ruota della fortuna ha il proprio flusso di setup dedicato
  (`/new-match/wheel`) senza alcuna sezione RuleSet, dato che per quel
  gioco non si applica.

**Animazione "tabellone aeroportuale" per lo spin della Ruota**: il
valore della ruota resta deciso istantaneamente e in modo autentico
lato server (nessun trucco, il server sceglie il valore casuale prima
ancora che l'animazione parta), ma la rivelazione al giocatore viene
mostrata con un effetto a scheda che cambia testo sempre più lentamente
per circa 5 secondi, in stile tabellone voli, prima di fermarsi sul
valore vero. Implementata con un nuovo endpoint `/play/wheel/spin-ajax`
(JSON) più una piccola animazione JavaScript solo per l'effetto visivo:
se il JavaScript non fosse disponibile, il pulsante "Gira la ruota"
continua a funzionare normalmente (form HTML classico), mostrando il
risultato subito senza animazione.

## Fase 3.3 - Fix bug catalogo + Memory e Mastermind completi

**Bug corretto (introdotto nella Fase 3.2):** `BaseGame` usava lo stesso
campo `status` sia per "il gioco è pronto nel catalogo" (`ready`) sia
per "stato della partita in corso" (`active`/`won`/...). Tris, Forza 4
e Ruota, sovrascrivendo `status='active'` all'avvio della propria
logica di gioco, finivano per sembrare "in arrivo" nel catalogo. Ora
`BaseGame` usa un campo separato `catalog_status`, mai toccato dalla
logica di partita di ciascun gioco - la Ruota (e tutti i giochi futuri)
non avranno più questo problema.

**Nuovi giochi completi:**

- `games/memory.py` (sostituisce lo stub): 3 livelli di difficoltà (6/8/10
  coppie), turni tra 1-8 partecipanti, "trova una coppia e gioca ancora"
  come nel Memory tradizionale, storico partite e classifica integrati.
- `games/mastermind.py`: codice segreto di 3-4 pioli colorati generato
  casualmente, 3 livelli di difficoltà (colori/tentativi diversi),
  turni tra i partecipanti a ogni tentativo, feedback pioli
  esatti/spostati come nel gioco da tavolo originale, storico dei
  tentativi visibile in partita.

Entrambi accessibili solo dal catalogo Giochi (`/games`), con le
rispettive pagine di setup dedicate (`/new-match/memory`,
`/new-match/mastermind`) - nessuna voce extra in sidebar, coerente con
la richiesta di avere un unico catalogo.

**Prossimi passi (non ancora implementati):** Simon (richiede animazione
di sequenze da "guardare" prima di ripeterle) e Sarabanda (upload
audio) restano gli unici giochi discussi ma non ancora costruiti.


```bat
cd /d C:\percorso\FreeTime
python app.py
```

Poi, dal browser (Chrome/Edge) sul dispositivo:
- Aprire `http://127.0.0.1:5000/`
- Nel menu del browser cercare "Installa app" / "Aggiungi a schermata
  Home" - dopo l'installazione l'icona "F" comparira' come un'app vera,
  a schermo intero, senza barra degli indirizzi.

## Fase 3 (parziale) - Import/export backup per cambio dispositivo

Il download del backup ZIP esisteva gia' (`/backup`). Aggiunto il
ripristino:

- Nuova route `/restore` (POST, upload multipart) in `app.py`: accetta
  lo ZIP scaricato da `/backup`, valida che ogni file (`players.json`,
  `results.json`, `sessions.json`, `teams.json`) sia JSON valido e sia
  una lista, prima di toccare qualsiasi dato.
- Sicurezza: prima di sovrascrivere, i dati correnti vengono copiati in
  `data/pre_restore_backup_<timestamp>/` - se qualcosa va storto puoi
  sempre recuperarli manualmente da li'.
- Se lo ZIP e' invalido o corrotto, viene rifiutato con un messaggio di
  errore e i dati correnti NON vengono toccati.
- Nuovo form di upload nella pagina "Esportazioni" (`templates/exports.html`).

Nota sulla disabilitazione giocatori: la funzione era gia' presente e
funzionante nel progetto originale (pulsante Disabilita/Riattiva su
ogni giocatore, con filtro automatico nella scelta partecipanti per
nuova partita). Nessuna modifica necessaria - basta usarla dalla
pagina Giocatori per "nascondere" i profili di test.

## Fase 3.4 - Fix impaginazione Ruota/Memory + 4 nuovi giochi

**Fix richiesti dopo il test pratico:**
- Ruota della fortuna: le lettere ora sono raggruppate per parola
  (nuovo metodo `display_words()`), non vanno più a capo in mezzo a
  una parola. Verificato con "Chi fa da sè fa per tre".
- Memory: tessere ingrandite (da ~64px a ~96px).

**Pannello istruttore generalizzato:** ora supporta frasi per tre
giochi diversi (Ruota, Impiccato, Indovina mimando) tramite un menu a
tendina, più un secondo modulo per inserire domande a risposta
multipla per il Quizzone (domanda + 4 risposte + indicazione di quella
corretta).

**Quattro nuovi giochi completi:**

- `games/hangman.py` (Impiccato) - stesso motore "frase nascosta" della
  Ruota ma con contatore di errori (max 6) invece dei punti; game_id
  `impiccato`.
- `games/charades.py` (Indovina mimando) - il giocatore di turno vede a
  schermo il titolo/frase da mimare (film, canzone, frase libera) e
  segna "Indovinato!" o "Passa"; richiede almeno 2 partecipanti; punto
  a chi mima con successo; il turno di mimo ruota automaticamente;
  game_id `mimo`.
- `games/sequence.py` (Sequenza numeri) - gara a tempo tra 1-8
  giocatori: ciascuno tocca "Pronti? Via!" quando è pronto (il tempo
  parte da lì, non da quando gli viene passato il dispositivo), poi
  tocca i numeri in ordine crescente su una griglia rimescolata
  (9/16/25 numeri secondo la difficoltà). Il tempo è cronometrato lato
  server (timestamp, non manipolabile dal client); un piccolo
  cronometro JavaScript è puramente decorativo per il feedback visivo
  durante la partita. Classifica finale ordinata per tempo più basso.
  game_id `sequence`.
- `games/quiz.py` (Quizzone) - domande a risposta multipla inserite
  dagli istruttori, una alla volta, turni a rotazione tra i
  partecipanti a ogni domanda, punteggio cumulativo, il quiz finisce
  quando la coda di domande si esaurisce. game_id `quiz`.

Tutti e quattro accessibili solo dal catalogo Giochi, con pagina di
setup dedicata, integrazione automatica in storico/classifica/
statistiche giocatori come tutti gli altri giochi.

Testato a fondo: pannello istruttore multi-gioco, Impiccato (vittoria e
sconfitta), Indovina mimando (vincolo minimo 2 giocatori, esaurimento
coda), Sequenza numeri (gara completa tra 2 giocatori, gestione numero
sbagliato, tempi salvati correttamente), Quizzone (risposta corretta,
esaurimento domande, risposta mancante), e nessuna regressione sul
resto dell'app (9 giochi totali, backup, tutte le pagine).

## Fase 4 - Cruciverba + revisione architetturale del menu

**Cruciverba** (`games/crossword.py`): l'istruttore inserisce da 3 a 6
coppie indizio/risposta come un unico puzzle dal Pannello istruttore
(risposte solo lettere, validate). Non è una griglia con incroci veri
(richiederebbe un algoritmo di posizionamento complesso per un
beneficio pratico minimo in questo contesto), ma una lista numerata di
indizi: ogni parola si risolve lettera per lettera in autonomia,
turni a rotazione, "corretto = gioca ancora" coerente col resto
dell'app. game_id `crossword`.

**Revisione della sidebar:**
- Rimosso "＋ Gioca", che puntava solo al form di Tris/Forza 4 mentre
  "◆ Giochi" già copre tutti i 10 giochi con RuleSet mostrati solo
  dove applicabile. Un solo punto d'ingresso per "inizia una partita",
  invece di due che facevano la stessa cosa in modo incoerente.
- "Squadre" completata: esisteva già una pagina di sola lettura e un
  file dati (`teams.json`), ma senza alcuna interfaccia per creare
  davvero una squadra - fino ad ora un guscio vuoto. Aggiunto un form
  di creazione (nome + selezione giocatori) e la possibilità di
  rimuovere una squadra. Necessaria come base per i futuri mini-tornei
  a squadre nelle Sessioni.

Testato a fondo: catalogo con tutti e 10 i giochi, validazione
cruciverba (minimo 3 parole, solo lettere), partita cruciverba
completa, creazione/rimozione squadre con relative validazioni, sidebar
aggiornata, e nessuna regressione sul resto dell'app.

**Ancora da fare (discusso, non implementato):** trasformare le
Sessioni in mini-tornei a squadre veri (programma di giochi in
sequenza, punteggio aggregato per squadra) - cambiamento di modello
dati più corposo, da progettare insieme prima di costruirlo. Restano
sul tavolo anche Simon, Sarabanda e "disegna e indovina".

## Fase 5 - Sessioni come mini-tornei a squadre

Implementato secondo le due scelte confermate: squadre fisse per tutta
la sessione, programma di giochi deciso all'inizio.

**Decisione architetturale chiave**: invece di modificare tutte e 10 le
route di gioco per registrare i punti squadra, l'aggancio avviene in un
unico punto centrale già esistente, `attach_active_session()` - la
funzione che ogni risultato attraversa comunque per essere taggato con
la sessione attiva. Aggiunta lì la logica: se la sessione attiva è un
torneo, capisce a quale squadra appartiene il vincitore
(`team_of_player`) e le assegna un punto, oltre a segnare quel gioco
come completato nel programma (`record_tournament_result`). Questo
significa che **qualsiasi gioco, presente o futuro, alimenta
automaticamente i tornei senza bisogno di modifiche dedicate** -
zero duplicazione su 10 file diversi.

Novità:
- `/sessions` accetta ora anche la creazione di un torneo (nome,
  minimo 2 squadre tra quelle esistenti, minimo 2 giochi per il
  programma). Le squadre restano fisse per tutta la durata del torneo.
- La scheda di una sessione-torneo mostra la classifica a punti tra le
  squadre, quante partite del programma sono state giocate, e un
  pulsante "Prossimo: [gioco] →" che porta dritto al setup di quel
  gioco specifico.
- Le sessioni "libere" esistenti restano identiche a prima (stesso
  form, stessa classifica per singolo giocatore) - nessuna
  regressione, il nuovo sistema si aggiunge senza sostituire nulla.

Testato a fondo: validazioni creazione torneo (nome mancante, meno di
2 squadre, meno di 2 giochi), aggiornamento reale dei punti squadra
giocando una partita normale (Tris) con un giocatore appartenente a una
squadra, visualizzazione corretta di classifica e "prossimo gioco",
completamento del programma dopo aver giocato tutti i giochi previsti,
e nessuna regressione sulle sessioni libere esistenti né sul resto
dell'app (10 giochi, squadre, backup).

## Fase 6 - Cruciverba a incroci reali + responsive + contenuti d'esempio

**Cruciverba riscritto da zero** (`engine/crossword_builder.py` +
`games/crossword.py`): ora genera davvero uno schema con le parole che
si incrociano, come un cruciverba vero. Algoritmo: parte dalla parola
più lunga, poi per ognuna delle successive cerca la migliore
intersezione con le parole già piazzate (stessa lettera, direzione
perpendicolare, nessun conflitto con celle adiacenti); se non trova
incroci validi la piazza scollegata piuttosto che scartarla. Rivelare
una lettera in una parola rivela automaticamente la stessa cella nella
parola che la incrocia (dato che è la stessa cella condivisa) - proprio
come un cruciverba vero. Le risposte devono ora essere una singola
parola (niente spazi), requisito necessario per il posizionamento a
incroci.

**Fix responsive Tris e Forza 4**: le griglie erano dimensionate solo
in base alla larghezza dello schermo (vw); su telefoni con poca altezza
disponibile (specialmente con la barra del browser visibile) la
griglia poteva superare lo spazio verticale visibile, con la barra di
navigazione fissa in basso che copriva l'ultima riga. Le dimensioni
ora tengono conto anche dell'altezza disponibile (`dvh`, viewport
height dinamico, più affidabile di `vh` su mobile), sia su desktop sia
nella media query mobile; ridotti anche alcuni margini verticali per
lasciare più spazio reale al tabellone su schermi piccoli.

**Pacchetti di contenuti d'esempio**: tre file già pronti
(`examples/cultura_generale.json`, `musica.json`, `cinema.json`) con
domande e frasi verificate (inclusi fatti attuali: vincitore Sanremo
2026, Oscar 2026, NBA Finals 2026), caricabili con un pulsante dal
Pannello istruttore. Si aggiungono alla coda senza cancellare nulla,
quindi possono convivere con i contenuti reali degli istruttori e
essere ricaricati quante volte serve per avere sempre qualcosa pronto
da testare.

Testato a fondo: generazione schema con incroci verificati (anteprima
ASCII), rivelazione condivisa delle lettere agli incroci, validazione
risposte a singola parola, caricamento e conteggio corretto dei tre
pacchetti d'esempio, playthrough completo di quiz/ruota/mimo con i
contenuti caricati, e nessuna regressione sul resto dell'app.

## Fase 7 - Fix scroll/responsive, omino impiccato, sistema modalità completo

**Fix scroll durante il gioco (tutti i 10 giochi)**: ogni azione ora
reindirizza con un'ancora HTML (`#board-area`) invece di tornare
all'inizio pagina - il browser mostra insieme turno e tabellone,
niente più scroll manuale per ritrovare la scacchiera. Nessun
JavaScript necessario, solo redirect con `_anchor`.

**Impiccato**: aggiunto un disegno SVG dell'omino che si completa
progressivamente a ogni errore (testa, corpo, due braccia, due
gambe) - ora si percepisce subito quanto manca alla sconfitta.

**Sequenza numeri**: griglia ridisegnata come quadrato vincolato sia
in larghezza che in altezza (`dvh`), con colonne calcolate in base al
numero di caselle (3x3/4x4/5x5) - critico per un gioco a tempo dove
non ci si può permettere di scrollare.

**Sistema di modalità (Classico / Turno Conquistato / Distruttivo)**:
aggiunto un campo `mode` a Ruota, Memory, Mastermind, Impiccato,
Indovina mimando, Quizzone e Cruciverba (Sequenza numeri resta sempre
gara diretta, come richiesto). Regola generale: "Turno conquistato" fa
continuare lo stesso giocatore/squadra dopo un'azione riuscita,
"Classico" fa ruotare il turno comunque. Per la Ruota, "Distruttivo"
aggiunge un'azione alternativa: invece di indovinare una lettera, si
può scegliere un avversario e togliergli punti pari al valore appena
girato (mai sotto zero).

**Cruciverba - modalità Squadre** (nuova, terza modalità): ogni
partecipante selezionato rappresenta una squadra (anche un singolo
giocatore può rappresentarne una, nessuna logica separata necessaria).
Regole implementate esattamente come descritto:
- Ogni parola risolta vale 5 punti alla squadra.
- Si può tentare di indovinare la parola intera in qualsiasi momento;
  se sbagliata ma della lunghezza giusta, resta scritta nello schema
  (evidenziata in arancione) finché una squadra successiva non la
  corregge - correzione ammessa solo se non contraddice lettere già
  confermate agli incroci.
- Si può "comprare" una lettera che viene rivelata in tutto lo schema:
  gratis alla primissima mossa della partita, altrimenti costa 15
  punti (bloccato se la squadra non li ha).
- Vince la squadra con più punti quando lo schema è completo.

Testato a fondo ogni combinazione: Distruttivo (attacco reale con
sottrazione punti, auto-attacco bloccato), Memory/Impiccato Classico
(rotazione forzata anche con esito positivo), Mastermind/Mimo/Quiz
Turno Conquistato (turno mantenuto con esito positivo), Cruciverba
Squadre (primo turno gratuito, acquisto lettera con/senza punti
sufficienti, parola sbagliata che resta e viene poi corretta, conflitto
con lettere confermate agli incroci correttamente respinto, punteggi e
vincitore finali corretti). Nessuna regressione sul resto dell'app.

## Fase 8 - Homepage, contesto Ruota/Impiccato, bug click, Cruciverba vero

**Bug del click sui pulsanti di modalità risolto**: il radio input
nascosto (usato per gli stili "a card" di modalità/giocatori) non
copriva l'intera area cliccabile dell'etichetta - ora la copre per
intero (`inset:0`), quindi ogni click va sempre a segno al primo colpo.

**Contesto sempre presente in Ruota e Impiccato**: la categoria non è
più facoltativa nel Pannello istruttore - senza un indizio di contesto
il gioco perdeva di senso. Mostrata in modo più prominente sopra la
frase, non più solo come piccola etichetta.

**Ruota - spaziatura parole**: gap aumentato tra le parole e ogni
parola ha ora un leggero sfondo che la delimita visivamente, così
quando la frase va su più righe resta chiaro dove finisce una parola e
inizia la successiva.

**Impiccato - errori individuali per giocatore**: era un errore di
game design, non solo tecnico - un contatore di errori condiviso non
rispecchia il gioco reale, dove ogni giocatore rischia solo per sé.
Ora ogni partecipante ha il proprio contatore errori e il proprio
omino (SVG compatto, uno per giocatore, quello di turno evidenziato).
Un giocatore che arriva a 6 errori viene escluso dal turno (il gioco
salta automaticamente a chi può ancora giocare); se tutti vengono
eliminati la manche termina in sconfitta. Aggiunta anche una rete di
sicurezza: se tutte le lettere dell'alfabeto sono state tentate senza
che la parola sia stata trovata, la manche termina invece di restare
bloccata.

**Cruciverba, rifatto per davvero**:
- Il generatore ora garantisce che OGNI parola dello schema sia
  collegata ad almeno un'altra (nessuna parola isolata come in un vero
  cruciverba): prova a posizionare le parole rimanenti a ogni giro
  finché possibile, e chi non trova mai un incrocio valido viene
  escluso dallo schema con un avviso esplicito all'avvio della manche.
- Rimossa la vecchia doppia modalità Classico/Turno Conquistato (aveva
  poco senso per come è pensato un cruciverba): resta una sola
  modalità, quella economica a squadre già costruita in precedenza -
  parole intere (5 punti), lettera gratuita solo alla primissima mossa
  della partita, poi lettere a pagamento (15 punti).
- Aggiunta l'azione "Passa il turno", per non essere costretti a
  tentare quando non si ha idea della risposta.

**Homepage ridisegnata**: rimosso il riquadro "Nuova partita" che
proponeva solo Tris o Forza 4 (fuorviante ora che i giochi sono 10). Se
è attivo un torneo a squadre, la home lo mostra in evidenza con
classifica squadre e progresso del programma; altrimenti mostra un
invito a sfogliare l'intero catalogo. Statistiche aggiornate (giochi
disponibili, partite, sessioni) e una nuova card che invita a provare
un mini-torneo se non ce n'è uno attivo.

Testato a fondo: categoria obbligatoria, errori individuali (verificato
che un giocatore non influenzi il contatore di un altro), eliminazione
e salto turno corretto, rete di sicurezza su alfabeto esaurito,
generatore cruciverba con parole scartate per mancata connessione,
azione passa, homepage con e senza torneo attivo, nessuna regressione
sul resto dell'app.

## Fase 9 - Rifiniture su feedback pratico: tornei, Impiccato, Sequenza, contenuti estesi

**Bug più importante: configurazione partita nei tornei**. Prima,
cliccando "Prossimo: [gioco]" da un torneo attivo, si finiva comunque
sulla pagina di setup standard - scelta del gioco (già decisa),
modalità Coppia/Contro PC (senza senso in un torneo a squadre) e
selezione partecipanti (le squadre erano già definite). Ora, quando è
attivo un torneo, tutte le pagine di setup partita riconoscono il
contesto e mostrano solo le squadre in gara (lette automaticamente dal
torneo) e le regole di gioco genuinamente da scegliere (per Tris/Forza
4: Classico/Turno Conquistato/Distruttivo; per gli altri giochi: le
loro rispettive modalità). Fuori da un torneo attivo, tutto funziona
come prima.

**Impiccato - omini compatti**: con 2+ giocatori gli omini (grandi,
impilati verticalmente) spingevano il tabellone fuori dallo schermo.
Ora sono in una fascia orizzontale compatta sopra il tabellone (icona
piccola + nome + contatore), sempre tutti visibili insieme al resto
del gioco senza scroll.

**Sequenza numeri - quattro tipi di sequenza**, mantenendo le tre
difficoltà (9/16/25 caselle): Numeri crescenti (come prima), Lettere in
ordine alfabetico, Multipli crescenti (base casuale tra 2 e 5), Sfumature
di colore dal più chiaro al più scuro (tonalità casuale). Motore
riscritto per generalizzare "valore mostrato" e "posizione corretta"
invece di assumere sempre numeri.

**Quizzone e Cruciverba - contenuti estesi**: pulsante "+ Aggiungi
un'altra risposta/parola" nel Pannello istruttore per superare lo
standard (4 risposte per il Quizzone, 6 parole per il Cruciverba) fino
a un massimo di 8 risposte e 20 parole. I campi extra sono già presenti
nella pagina ma nascosti, si rivelano un click alla volta - nessuna
generazione dinamica di HTML lato client, solo mostra/nascondi, quindi
robusto anche su browser meno recenti.

Testato a fondo: setup partita semplificato in contesto torneo (Tris e
Ruota come casi rappresentativi, entrambi verificati end-to-end),
Impiccato compatto renderizzato senza errori, tutti e quattro i tipi di
Sequenza completati correttamente, Quiz con 6 risposte (mappatura
indice risposta corretta verificata anche con opzioni extra), Cruciverba
con 8 parole, nessuna regressione sul resto dell'app.

## Fase 10 - Uso dello spazio su schermi desktop grandi

Il contenitore di gioco (`.game-shell`) era fissato a 900px di
larghezza indipendentemente dalla dimensione dello schermo - su
monitor desktop ampi restava tantissimo spazio vuoto ai lati, come
mostrato dallo screenshot. Corretto:
- Il contenitore ora scala fino a un massimo più generoso (1200px, poi
  1320px oltre i 1400px di larghezza schermo) invece di restare fisso.
- Su schermi grandi (oltre 1400px), gli elementi di gioco stessi si
  ingrandiscono (tessere della Ruota/Impiccato, celle del Cruciverba,
  carte di Memory/Sequenza, pulsanti, testo dei punteggi) invece di
  lasciare lo spazio vuoto - il gioco "riempie" davvero lo schermo
  invece di limitarsi a centrarsi in una colonna stretta.

Verificato che il CSS resti valido e che le pagine di gioco continuino
a renderizzare correttamente.

## Fase 11 - Ottimizzazione spazio schermo grande / modalità proiezione

Lavoro sistematico di UX su tutta l'app, pensato esplicitamente per
l'uso reale previsto: proiettare lo schermo del PC durante un torneo,
con testo leggibile anche dagli spalti.

**Layout a due colonne nelle pagine di gioco**: prima, su schermi
larghi, il pannello punteggi stava sempre sotto il tabellone,
sprecando tutto lo spazio orizzontale e costringendo a scrollare anche
quando c'era abbondanza di spazio libero ai lati (esattamente il
problema mostrato negli screenshot). Ora, da 1000px di larghezza in
su, contenuto di gioco e pannello punteggi stanno affiancati (punteggi
a destra, "agganciati" durante lo scroll). Applicato a Ruota, Memory,
Mastermind, Impiccato, Indovina mimando, Sequenza numeri, Quizzone e
Cruciverba. Tris e Forza 4 restano a colonna singola (la loro
intestazione include già i punteggi, non serve una colonna separata),
ma le loro scacchiere ora possono crescere molto di più su schermi
grandi (non erano più vincolate a un limite fisso di ~570-850px).

**Vera "modalità proiezione"** (oltre 1900px di larghezza, tipico di
un proiettore o TV grande): titoli enormi (fino a 96px), testo dei
turni e dei punteggi molto più grande, tessere/celle/pulsanti
ingranditi in proporzione, card del catalogo giochi e delle squadre
disposte su più colonne. L'obiettivo è la leggibilità da lontano, non
solo il riempimento dello spazio.

**Altre pagine**: contenitore principale dell'app allargato (da 1500 a
1760px, fino a 2100px in modalità proiezione), pagine di configurazione
partita leggermente più ampie, griglia Squadre/Giocatori che passa da
3 a 4-5 colonne su schermi grandi invece di restare bloccata a 3.

Testato a fondo: tutti e 10 i giochi renderizzano correttamente con la
nuova struttura a due colonne (nessun errore di template), partite
complete giocate end-to-end su Tris, Forza 4 e Ruota per verificare che
il funzionamento non sia stato intaccato, CSS verificato sintatticamente
valido, nessuna regressione sul resto dell'app.

## Fase 12 - Mastermind a colori, fix pannello punteggi, transizioni fluide

**Mastermind**: la selezione dei colori era una tendina testuale
(Rosso/Verde/...), ora sono pallini colorati cliccabili - molto più
immediato da vedere e da usare, specialmente in proiezione.

**Bug del pannello punteggi risolto** (Ruota, Impiccato, Indovina
mimando, Memory, Quizzone, Cruciverba): il problema non era solo
estetico - il testo "· in turno" appeso al nome, unito a una colonna
centrale troppo stretta, causava un a-capo parola per parola invece
di un fluido ritorno a capo, e "pt" arrivava a spezzarsi dal numero.
Risolto alla radice: la colonna centrale ora tronca con puntini di
sospensione se il nome è troppo lungo per lo spazio disponibile
(invece di spezzarsi in un a-capo brutto), e il turno corrente non è
più segnalato con testo aggiuntivo ma con uno sfondo evidenziato
sull'intera riga - più leggibile, specialmente da lontano, e a prova
di nomi lunghi.

**Transizioni più fluide tra le pagine**: aggiunta la dichiarazione
CSS per le View Transitions del browser (supportata da Chrome/Edge),
che rende ogni cambio pagina un dissolvenza fluida invece di uno
sfarfallio secco - dovrebbe attenuare la sensazione di "refresh
adattivo" fastidioso segnalata su Sequenza numeri, Tris e Forza 4.
Aggiunto anche `touch-action:manipulation` e un feedback visivo
immediato (leggero effetto di pressione) su pulsanti e card di
selezione, per eliminare eventuali ritardi percepiti del browser nel
riconoscere il tocco/click, specialmente su dispositivi touch.

Testato a fondo: Mastermind con pallini colorati (rendering e invio
form corretti, partita completa fino a vittoria), pannello punteggi
senza più testo che si spezza male su Ruota/Impiccato/Memory/Quizzone,
CSS verificato bilanciato dopo le modifiche, nessuna regressione sul
resto dell'app.

**Nota sul refresh**: essendo l'app interamente server-side (ogni
mossa è un vero invio di form con ricaricamento pagina, non
un'applicazione JavaScript "a pagina singola"), un minimo di
ricaricamento a ogni mossa è strutturale. Le View Transitions
attenuano la sensazione fastidiosa; eliminarla del tutto richiederebbe
un cambiamento architetturale più profondo (aggiornare la pagina via
JavaScript invece di ricaricarla), da valutare se il fastidio dovesse
persistere in modo significativo.
