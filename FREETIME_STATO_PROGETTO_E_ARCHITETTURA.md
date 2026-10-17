# FreeTime
## Stato del progetto, architettura, decisioni e logiche applicative

**Documento di presa in carico tecnica e funzionale**  
**Stato documentato:** fino alla release installata **v0.9b**, con **v0.9c definita ma non ancora consolidata in un pacchetto completo**  
**Ambiente di riferimento:** Python 3.7.3, Anaconda3-2019, Flask 1.1.1, esecuzione locale Windows

---

# 1. Scopo del documento

Questo documento ricostruisce la visione complessiva del progetto FreeTime, partendo dalle scelte architetturali di basso livello fino alle logiche funzionali e di gestione dell’applicativo.

Gli obiettivi sono:

- consentire a uno sviluppatore di prendere in carico il progetto;
- chiarire le responsabilità dei moduli;
- documentare le decisioni già validate;
- distinguere la baseline stabile dalle evoluzioni ancora pianificate;
- evitare regressioni nelle funzionalità multi-gioco;
- preservare la compatibilità con l’ambiente aziendale;
- definire i vincoli da rispettare quando verranno aggiunti nuovi giochi.

Il documento è basato sulle decisioni e sui test descritti durante lo sviluppo iterativo del progetto.

---

# 2. Visione del prodotto

FreeTime è nato come piattaforma locale per giochi semplici, ma si è evoluto verso uno strumento per:

- attività ricreative;
- sfide tra giocatori;
- team building;
- workshop;
- attività formative;
- sessioni multi-partita;
- raccolta di risultati e classifiche.

La visione consolidata è:

```text
FreeTime
├── Piattaforma multi-gioco
├── Profili giocatore persistenti
├── Sessioni ed eventi
├── Classifiche e statistiche
├── RuleSet riutilizzabili
├── Modalità team building
├── Storico unificato
└── Catalogo giochi espandibile
```

Il valore futuro dell’applicativo deve derivare principalmente dal catalogo e dalla qualità dei giochi, non dall’aggiunta continua di nuove funzioni gestionali al core.

---

# 3. Vincoli ambientali non negoziabili

## 3.1 Stack tecnologico

Il progetto deve essere compatibile con:

```text
Python 3.7.3
Anaconda3-2019
Flask 1.1.1
Windows
Browser Edge e Chrome
```

## 3.2 Vincoli di sviluppo

- Non utilizzare sintassi introdotte dopo Python 3.7.
- Non introdurre dipendenze non strettamente necessarie.
- Evitare framework JavaScript complessi.
- Preferire Flask, HTML, CSS e JavaScript compatibile.
- Mantenere l’applicazione eseguibile localmente.
- Conservare i dati in file JSON locali fino a una decisione architetturale esplicita diversa.
- Consegnare file completi o pacchetti ZIP, non patch parziali da copiare manualmente.
- Non sovrascrivere i file dati durante gli aggiornamenti.

## 3.3 Compatibilità browser

È stato rilevato che Edge può mantenere in cache CSS precedenti. È stata quindi adottata la strategia di cache busting:

```html
style.css?v=<versione>
app.js?v=<versione>
```

Dopo un aggiornamento è comunque consigliato:

```text
CTRL+SHIFT+R
```

---

# 4. Evoluzione delle release

## v0.1 - Persistenza iniziale

Introduzione della struttura Flask e dei primi dati persistenti.

## v0.2 - Game Engine iniziale

Introduzione del concetto di gioco registrato e della base comune per i giochi.

## v0.3 - Team e Match Engine

Introduzione di:

- giocatori;
- squadre;
- modalità di partita;
- configurazione del match.

## v0.4 - Primo tentativo di wizard

Tentativo di configurazione in pagina singola con JavaScript. Il risultato si è dimostrato fragile in alcuni browser e nell’ambiente aziendale.

## v0.5 - Flusso multipagina stabile

La configurazione è stata spostata su pagine Flask distinte:

```text
Modalità
→ Partecipanti
→ Gioco
→ Riepilogo
```

Questa scelta è diventata un principio architetturale: il flusso applicativo principale non deve dipendere da JavaScript per funzionare.

## v0.6 / v0.6a - UX e hotfix Team

Introduzione dell’identità grafica moderna, con ispirazione entertainment, card, navigazione laterale e adattamento tablet.

La v0.6a ha corretto il nesting Jinja del template di selezione partecipanti.

## v0.7 - Tris Classico e GameRuleSet

Primo gameplay reale:

- Tris Classico;
- Coppia;
- Contro il PC;
- vittoria;
- pareggio;
- rivincita;
- storico;
- statistiche.

## v0.7a - Tris Turno conquistato

Introduzione del `TurnEngine` e dell’assegnazione manuale del turno.

## v0.7b - Tris Distruttivo

Introduzione della rimozione del simbolo avversario, con massimo due cancellazioni per giocatore.

## v0.8 - Forza 4 Classico

Introduzione del secondo gioco con griglia 6 × 7, gravità e vittorie multidirezionali.

## v0.8a / Fix1 - Forza 4 Turno conquistato

Introduzione del turno manuale per Forza 4. Il Fix1 ha ripristinato la Home multi-gioco e lo storico unificato dopo una regressione del pacchetto iniziale.

## v0.8b - Forza 4 Distruttivo

Introduzione della rimozione di pedine avversarie con ricompattamento verticale della colonna.

## v0.9 - Sessioni, classifiche e profili

Introduzione di:

- sessioni evento;
- classifica generale;
- punteggi;
- profilo giocatore;
- storico filtrabile;
- dashboard analitica.

## v0.9b - Gestione ciclo di vita giocatori, trofei ed export

Aggiornamento applicato tramite installer. Funzioni definite:

- abilitazione/disabilitazione giocatori;
- controllo duplicati anche sui profili disabilitati;
- esclusione dei disabilitati dalle nuove partite;
- conservazione dello storico;
- trofei base;
- esportazione CSV/JSON;
- backup ZIP.

## v0.9c - Freeze Candidate

La release è stata definita funzionalmente, ma non è ancora stata consolidata in un pacchetto completo verificato sul sorgente installato.

Scope previsto:

- chiusura sessioni;
- podio finale;
- classifica congelata;
- ricerca globale;
- dashboard finale;
- documento di architecture freeze.

---

# 5. Architettura logica

```text
Browser
  │
  ▼
Flask Routes / Controller
  │
  ├── Player Management
  ├── Match Configuration
  ├── Game Routes
  ├── Session Management
  ├── History / Ranking
  └── Export / Backup
  │
  ▼
Domain Engines
  ├── GameMode
  ├── GameRuleSet
  ├── TurnEngine
  ├── TicTacToeGame
  ├── Connect4Game
  ├── Achievement Engine
  ├── Ranking / Analytics
  └── Player Lifecycle
  │
  ▼
JSON Persistence
  ├── players.json
  ├── teams.json
  ├── results.json
  ├── sessions.json
  └── altri file futuri
```

---

# 6. Struttura prevista delle directory

```text
FreeTime/
├── app.py
├── requirements.txt
├── engine/
│   ├── __init__.py
│   ├── game_modes.py
│   ├── match_engine.py          # presente nelle fasi precedenti
│   ├── team_engine.py           # presente nelle fasi precedenti
│   └── turn_engine.py
├── games/
│   ├── __init__.py
│   ├── base_game.py
│   ├── game_registry.py
│   ├── game_ruleset.py
│   ├── tictactoe.py
│   └── connect4.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── players.html
│   ├── teams.html
│   ├── new_match.html
│   ├── tictactoe_play.html
│   ├── connect4_play.html
│   ├── history.html
│   ├── leaderboard.html
│   ├── player_profile.html
│   ├── sessions.html
│   ├── achievements.html
│   └── exports.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── data/
│   ├── players.json
│   ├── teams.json
│   ├── results.json
│   └── sessions.json
├── player_lifecycle.py
├── achievement_engine.py
├── export_engine.py
└── test_*.py
```

Nota: la struttura effettiva installata deve essere verificata contro la directory corrente, perché alcune release sono state applicate come aggiornamenti incrementali.

---

# 7. Principi architetturali consolidati

## 7.1 Separazione logica/UI

Le regole del gioco devono restare in Python.

La UI deve occuparsi di:

- rappresentazione;
- feedback visivo;
- invio dell’azione utente;
- animazioni decorative.

La UI non deve essere la fonte autorevole dello stato.

## 7.2 Flussi server-rendered

Le operazioni principali devono funzionare tramite normali richieste Flask.

JavaScript può migliorare l’esperienza, ma non deve essere necessario per:

- avanzare nella configurazione;
- assegnare una mossa;
- salvare una partita;
- navigare nell’applicazione.

## 7.3 Identificativi persistenti

Giocatori, sessioni e risultati devono usare ID stabili.

Lo storico deve referenziare gli ID, non affidarsi esclusivamente ai nomi.

## 7.4 Aggiornamenti non distruttivi

I pacchetti di rilascio non devono contenere i JSON operativi.

Prima di ogni aggiornamento deve essere eseguito il backup di:

```text
C:\Python\FreeTime\data
```

## 7.5 Piattaforma multi-gioco

Nessuna release dedicata a un nuovo gioco deve sostituire:

- Home;
- storico globale;
- catalogo;
- navigazione;
- giochi precedenti.

Ogni gioco deve essere aggiunto al registro e integrato nel core esistente.

---

# 8. Modello giocatore

## 8.1 Struttura

```json
{
  "id": "identificativo_univoco",
  "name": "Nome giocatore",
  "games": 0,
  "wins": 0,
  "enabled": true
}
```

## 8.2 Ciclo di vita

Un giocatore non deve essere eliminato fisicamente.

Stati:

```text
enabled = true
enabled = false
```

### Giocatore attivo

Visibile in:

- nuova partita;
- selezione partecipanti;
- eventuale creazione squadre;
- profili;
- storico;
- classifiche.

### Giocatore disabilitato

Non visibile nelle nuove selezioni, ma preservato in:

- storico;
- statistiche;
- sessioni passate;
- classifiche storiche;
- trofei;
- profilo.

## 8.3 Controllo duplicati

Il confronto dei nomi usa una forma normalizzata:

```python
' '.join(name.strip().lower().split())
```

Sono quindi equivalenti:

```text
Mario Rossi
mario rossi
MARIO ROSSI
Mario   Rossi
```

Il controllo deve includere sia i giocatori attivi sia quelli disabilitati.

Se il giocatore esiste ma è disabilitato, l’utente deve usare la funzione di riattivazione, non creare un nuovo ID.

## 8.4 Migrazione

I profili precedenti senza campo `enabled` devono essere migrati a:

```json
"enabled": true
```

---

# 9. Modello squadra

La squadra raggruppa ID giocatore.

Esempio:

```json
{
  "id": "team_id",
  "name": "Fulmini",
  "player_ids": ["player_1", "player_2"],
  "score": 0
}
```

Decisione funzionale validata:

- lo stesso giocatore può appartenere a più squadre;
- l’applicazione non impone appartenenza esclusiva;
- le squadre vengono mantenute come entità persistenti.

Il gameplay corrente di Tris e Forza 4 è focalizzato principalmente su Coppia e Contro il PC. La piena orchestrazione dei roster di squadra non è stata completata come gameplay multi-turnazione.

---

# 10. Modalità di partita

Modalità definite:

```python
VS_PC = "vs_pc"
DUEL = "duel"
TOURNAMENT = "tournament"
TEAM = "team"
```

Uso consolidato nei gameplay implementati:

- `duel`: due giocatori locali;
- `vs_pc`: un giocatore e computer, dove supportato;
- `tournament`: configurazione concettuale, non ancora motore torneo completo;
- `team`: configurazione concettuale, non ancora orchestrazione completa per tutti i giochi.

---

# 11. GameRuleSet

## 11.1 Scopo

`GameRuleSet` separa il gioco dalle varianti di regola.

RuleSet definiti:

```python
CLASSIC = "classic"
EARNED_TURN = "earned_turn"
DESTRUCTIVE = "destructive"
```

## 11.2 Classico

- alternanza automatica;
- una mossa per giocatore;
- regole standard del gioco.

## 11.3 Turno conquistato

- nessuna alternanza automatica;
- un gestore assegna manualmente la possibilità di giocare;
- il gestore clicca sul nome del giocatore;
- il giocatore esegue una sola mossa;
- il turno viene consumato;
- il tabellone torna bloccato;
- lo stesso giocatore può ottenere più turni consecutivi.

Questa modalità è stata pensata per team building, quiz, prove, attività formative e sfide esterne al tabellone.

## 11.4 Distruttivo

Nel proprio turno il giocatore può:

1. inserire il proprio simbolo/pedina;
2. rimuovere un elemento dell’avversario.

Vincolo consolidato:

```text
Massimo 2 cancellazioni per giocatore
```

La terza rimozione deve essere rifiutata.

---

# 12. TurnEngine

## 12.1 Responsabilità

Il TurnEngine gestisce il diritto temporaneo di effettuare una mossa.

Operazioni concettuali:

```python
award_turn(symbol)
can_play(symbol)
consume_turn()
to_dict()
from_dict()
```

## 12.2 Stato

```json
{
  "assigned_symbol": "X",
  "assignment_count": 3
}
```

## 12.3 Regola fondamentale

Il turno conquistato è un’autorizzazione monouso.

```text
Assegnazione
→ una mossa
→ consumo
→ blocco
```

---

# 13. Tris

## 13.1 Modello

Griglia lineare di nove celle:

```python
board = ["", "", "", "", "", "", "", "", ""]
```

Mappatura:

```text
0 | 1 | 2
3 | 4 | 5
6 | 7 | 8
```

## 13.2 Combinazioni vincenti

```python
[
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]
```

## 13.3 RuleSet supportati

### Classico

Alternanza X/O.

### Turno conquistato

Assegnazione manuale del simbolo autorizzato.

### Distruttivo

Il giocatore può inserire oppure rimuovere un simbolo avversario, entro il limite di due rimozioni.

## 13.4 Stati

```text
active
won
draw
```

## 13.5 Persistenza della partita

Lo stato temporaneo viene mantenuto nella sessione Flask.

Il risultato viene scritto su file soltanto alla conclusione.

---

# 14. Forza 4

## 14.1 Modello

Griglia standard:

```text
6 righe × 7 colonne
```

Riga 0 in alto, riga 5 in basso.

## 14.2 Inserimento

L’utente seleziona una colonna.

Il motore cerca la prima riga libera dal basso e vi inserisce la pedina.

## 14.3 Vittoria

Ricerca di quattro pedine consecutive in direzione:

- orizzontale;
- verticale;
- diagonale crescente;
- diagonale decrescente.

Il motore conserva le coordinate delle quattro pedine vincenti per evidenziarle nella UI.

## 14.4 RuleSet supportati

### Classico

Alternanza e gravità standard.

### Turno conquistato

Assegnazione manuale, una pedina per autorizzazione.

### Distruttivo

Il giocatore può inserire oppure rimuovere una pedina avversaria.

Dopo una rimozione:

1. la colonna viene ricompattata verso il basso;
2. vengono controllate nuovamente le vittorie;
3. se la caduta crea una combinazione vincente, vince il proprietario delle quattro pedine risultanti;
4. il turno prosegue secondo le regole previste.

Limite: due rimozioni per giocatore.

---

# 15. Avversario PC

Modalità inizialmente implementate:

## Facile

Scelta casuale tra le mosse disponibili.

## Media

Priorità:

1. completare una propria vittoria immediata;
2. bloccare una vittoria immediata dell’utente;
3. scegliere una mossa disponibile.

Le strategie più complesse non sono state rese requisito del core.

---

# 16. Risultati e storico

## 16.1 Schema risultato

Esempio concettuale:

```json
{
  "id": "result_id",
  "game_id": "tictactoe",
  "ruleset_id": "classic",
  "mode": "duel",
  "participant_ids": ["player_1", "player_2"],
  "winner_id": "player_1",
  "winner_symbol": "X",
  "status": "won",
  "moves": 7,
  "completed_at": "data-ora",
  "session_id": "event_session_id"
}
```

`session_id` può essere assente o nullo nelle partite non associate a una sessione.

## 16.2 Storico unificato

Lo storico deve leggere un unico `results.json` e non deve essere limitato a un singolo gioco.

Filtri introdotti:

- gioco;
- RuleSet;
- giocatore;
- sessione.

## 16.3 Regola anti-duplicazione

Il risultato deve essere salvato una sola volta, anche in caso di refresh della pagina conclusiva.

---

# 17. Classifiche e punteggi

Punteggio definito:

```text
Vittoria: 3 punti
Pareggio: 1 punto
Sconfitta: 0 punti
```

Ordinamento:

1. punti decrescenti;
2. vittorie decrescenti;
3. nome giocatore.

Le classifiche possono essere:

- globali;
- calcolate sui risultati di una sessione.

---

# 18. Profilo giocatore

Il profilo v0.9 comprende:

- punti complessivi;
- partite;
- vittorie;
- pareggi;
- percentuale di successo;
- gioco più utilizzato;
- RuleSet più utilizzato;
- ultime partite;
- esito delle ultime partite.

I profili disabilitati restano consultabili.

---

# 19. Sessioni di gioco

## 19.1 Scopo

Raggruppare più partite in un unico evento, ad esempio:

```text
Team Building Settembre
```

## 19.2 Struttura v0.9

```json
{
  "id": "session_id",
  "name": "Team Building Settembre",
  "created_at": "data-ora",
  "status": "active"
}
```

## 19.3 Associazione automatica

Se una sessione è attiva, ogni nuovo risultato riceve il relativo `session_id`.

## 19.4 Funzioni definite per v0.9c

Da completare nel pacchetto Freeze Candidate:

```json
{
  "status": "closed",
  "closed_at": "data-ora",
  "final_ranking": [],
  "podium": []
}
```

Una sessione chiusa:

- non deve accettare nuove partite;
- deve mantenere lo storico;
- deve conservare uno snapshot della classifica;
- deve conservare il podio finale.

---

# 20. Trofei

Trofei base definiti nella v0.9b:

- Primo successo: prima vittoria;
- Primi dieci: dieci partite;
- Veterano: cinquanta partite;
- Maestro del Tris: dieci vittorie a Tris;
- Campione Forza 4: dieci vittorie a Forza 4.

Il motore calcola i trofei a partire dallo storico.

La persistenza separata degli achievement non è ancora il requisito dominante; il calcolo può essere derivato dai risultati.

---

# 21. Esportazioni e backup

## 21.1 Esportazioni previste

Formati:

```text
CSV
JSON
```

Dataset:

- giocatori;
- risultati;
- classifica;
- sessioni.

## 21.2 Backup ZIP

Contenuto previsto:

```text
players.json
results.json
sessions.json
teams.json
```

## 21.3 Nota di compatibilità Flask

La modalità di invio dei file deve essere verificata con Flask 1.1.1 e l’ambiente Python 3.7.3. Evitare parametri introdotti in versioni Flask successive.

---

# 22. UX e identità visiva

## 22.1 Direzione

Ispirazione dichiarata:

- Xbox Dashboard;
- Netflix;
- Steam Big Picture;
- Apple TV.

## 22.2 Principi

- card grandi;
- alta leggibilità;
- azioni principali evidenti;
- navigazione touch-friendly;
- nessuna dipendenza dall’hover;
- layout responsive;
- colori scuri e accenti viola/ciano;
- catalogo visuale;
- profili rappresentati come card;
- tabelloni utilizzabili con mouse, touch e penna.

## 22.3 Navigazione

Voci introdotte progressivamente:

- Home;
- Nuova partita;
- Giochi;
- Giocatori;
- Squadre;
- Storico;
- Classifica;
- Sessioni;
- Trofei;
- Esportazioni.

## 22.4 Principio di non regressione

Ogni nuovo gioco deve lasciare intatte le funzioni di piattaforma e i giochi precedenti.

---

# 23. Errori e lezioni apprese

## 23.1 Wizard JavaScript fragile

Problema:

- step visualizzati contemporaneamente;
- pulsanti Continua non funzionanti;
- rendering incoerente.

Decisione:

- flusso multipagina Flask;
- JavaScript solo per feedback visivo.

## 23.2 Cache Edge

Problema:

- HTML nuovo, CSS apparentemente vecchio.

Soluzione:

- refresh forzato;
- versionamento degli asset.

## 23.3 Errore Jinja Team

Problema:

- ciclo `for` non chiuso prima di `else/endif`.

Lezione:

- compilare tutti i template Jinja durante la build;
- non limitarsi ai test Python.

## 23.4 Regressione multi-gioco v0.8a

Problema:

- pacchetto troppo focalizzato su Forza 4;
- perdita della Home completa;
- storico non più unificato.

Lezione:

- ogni release deve derivare dalla baseline multi-gioco più recente;
- aggiungere, non sostituire;
- eseguire test di regressione su Home, catalogo e storico.

## 23.5 Installer v0.9b e SameFileError

Problema:

```text
SameFileError
```

Causa:

- pacchetto estratto direttamente nella directory target;
- sorgente e destinazione coincidevano.

Procedura corretta:

- estrarre l’update in una cartella temporanea;
- eseguire l’installer da quella cartella.

Miglioramento raccomandato per installer futuri:

```python
if os.path.abspath(src) != os.path.abspath(dst):
    shutil.copy2(src, dst)
```

---

# 24. Strategia di test

## 24.1 Test motori

File introdotti nel percorso:

```text
test_rulesets.py
test_tictactoe.py
test_turn_engine.py
test_earned_turn.py
test_destructive.py
test_connect4.py
test_connect4_earned_turn.py
test_connect4_destructive.py
test_v09_analytics.py
test_v09b.py
```

## 24.2 Test template

Tutti i template devono essere compilati con Jinja prima del rilascio.

## 24.3 Test ZIP

Ogni archivio deve essere sottoposto a verifica di integrità.

## 24.4 Test di regressione obbligatori

Prima di dichiarare una release valida:

### Piattaforma

- Home;
- navigazione;
- giocatori;
- sessioni;
- classifica;
- storico;
- profili;
- export;
- backup.

### Tris

- Classico;
- Turno conquistato;
- Distruttivo.

### Forza 4

- Classico;
- Turno conquistato;
- Distruttivo.

### Browser

- Chrome;
- Edge;
- viewport tablet.

---

# 25. Procedura di aggiornamento

Procedura standard:

1. Arrestare l’applicazione con `CTRL+C`.
2. Copiare integralmente la cartella `data`.
3. Estrarre il pacchetto completo nella cartella applicativa oppure eseguire l’installer dalla cartella temporanea prevista.
4. Non sostituire i JSON operativi con file vuoti.
5. Avviare:

```bat
cd /d C:\Python\FreeTime
python app.py
```

6. Aggiornare il browser con:

```text
CTRL+SHIFT+R
```

7. Eseguire i test automatici e funzionali della release.

---

# 26. Freeze architetturale proposto

La v0.9c deve diventare la candidata al congelamento della piattaforma.

Dopo la validazione:

```text
Tag: FREE_TIME_GOLDEN_BASELINE
Versione: 0.9c
Stato: Core congelato
```

Modifiche consentite dopo il freeze:

- hotfix;
- bug;
- sicurezza;
- compatibilità;
- adattamenti minimi necessari a integrare nuovi giochi.

Modifiche da evitare:

- riscrittura della Home;
- sostituzione dello storico;
- cambiamenti incompatibili ai modelli JSON;
- duplicazione dei motori;
- logiche di gioco dentro i template;
- dipendenza obbligatoria da JavaScript;
- cancellazione fisica dei giocatori.

---

# 27. Contratto per i nuovi giochi

Ogni nuovo gioco deve:

1. derivare o rispettare il contratto di `BaseGame`;
2. avere un `game_id` stabile;
3. dichiarare nome, descrizione, categoria e icona;
4. essere registrato nel Game Registry;
5. esportare e ripristinare lo stato;
6. gestire `active`, `won`, `draw` dove applicabile;
7. produrre un risultato compatibile con `results.json`;
8. integrarsi con profili, classifiche e sessioni;
9. dichiarare i RuleSet supportati;
10. avere test automatici dedicati;
11. avere un template di gameplay dedicato;
12. preservare Home, storico e giochi preesistenti.

Esempio di metadati:

```python
{
    "game_id": "memory",
    "name": "Memory",
    "description": "Trova tutte le coppie.",
    "category": "Memoria",
    "icon": "MEM",
    "status": "ready"
}
```

---

# 28. Stato delle decisioni

## Decisioni consolidate

- Python 3.7.3 / Anaconda3-2019.
- Flask 1.1.1.
- Persistenza JSON.
- UI server-rendered.
- Multi-gioco.
- Storico unico.
- ID persistenti.
- Giocatori disabilitabili, non eliminabili.
- Duplicati controllati anche tra disabilitati.
- Tre RuleSet: Classico, Turno conquistato, Distruttivo.
- Due cancellazioni per giocatore nei RuleSet Distruttivi.
- Sessioni e punteggi.
- Classifica: 3/1/0.
- Trofei ed export.

## Decisioni ancora da consolidare

- implementazione completa v0.9c;
- podio e ranking congelato;
- ricerca globale;
- eventuale import/restore del backup;
- roadmap ordinata dei giochi futuri;
- grado di supporto di ogni RuleSet per ciascun nuovo gioco;
- politica definitiva per torneo e team nel gameplay multi-incontro.

---

# 29. Rischi residui

## Rischio 1 - Aggiornamenti incrementali

Alcune funzionalità sono state applicate tramite update. La directory installata è la fonte autorevole e deve essere acquisita prima di costruire la Golden Baseline completa.

## Rischio 2 - Modello JSON senza schema formale

Il modello è flessibile ma privo di validazione formale. Le migrazioni devono essere esplicite e backward-compatible.

## Rischio 3 - Sessione Flask client-side

Gli stati di Tris e Forza 4 sono piccoli e adatti. Giochi futuri con stati grandi potrebbero richiedere persistenza temporanea diversa.

## Rischio 4 - Crescita di app.py

Le route sono aumentate. Prima o durante la fase post-freeze può diventare opportuno separare blueprint o servizi, ma un refactoring deve essere eseguito solo con una suite di regressione affidabile.

## Rischio 5 - Export Flask 1.1.1

I parametri di invio file devono rimanere compatibili con Flask 1.1.1.

---

# 30. Informazioni necessarie per la presa in carico

Prima del prossimo rilascio completo, acquisire:

```text
C:\Python\FreeTime
```

come archivio sorgente corrente.

Controllare in particolare:

- `app.py` installato;
- file Python aggiunti dalla v0.9b;
- template effettivi;
- CSS effettivo;
- struttura dei JSON reali;
- backup automatici creati dagli installer;
- output dei test.

Il sorgente installato corrente deve diventare il punto di partenza per:

```text
FreeTime v0.9c Golden Baseline
```

---

# 31. Prossimi passi consigliati

## Passo 1 - Consolidamento sorgente

Creare uno ZIP completo della directory installata, esclusi soltanto eventuali cache e file temporanei.

## Passo 2 - v0.9c

Implementare e testare:

- chiusura sessioni;
- snapshot classifica;
- podio;
- ricerca globale;
- dashboard freeze;
- versione runtime visibile.

## Passo 3 - Golden Baseline

Eseguire tutti i test e produrre:

```text
FreeTime_v0.9c.zip
ARCHITECTURE_FREEZE.md
CHANGELOG.md
TEST_REPORT.md
```

## Passo 4 - Roadmap giochi

Ricostruire l’elenco dei giochi inizialmente approvati e ordinarli in base a:

- valore per team building;
- esperienza utente;
- complessità;
- riuso dei RuleSet;
- varietà del catalogo;
- dipendenze tecniche.

---

# 32. Sintesi esecutiva

FreeTime dispone oggi di:

- piattaforma Flask locale;
- UI moderna e responsive;
- Tris completo con tre RuleSet;
- Forza 4 completo con tre RuleSet;
- profili e ciclo di vita dei giocatori;
- storico unificato;
- classifiche;
- sessioni;
- profili analitici;
- trofei;
- esportazioni;
- backup.

Il progetto ha superato la fase di prototipo di singolo gioco. La priorità immediata è consolidare il sorgente installato e completare la v0.9c come Golden Baseline. Dopo il freeze, lo sviluppo deve spostarsi principalmente sul catalogo giochi, mantenendo invariati i contratti del core.

---

# 33. Nota di accuratezza

Il documento descrive le decisioni, i comportamenti e le release definiti e testati nel percorso di sviluppo. Poiché alcune versioni sono state distribuite tramite aggiornamenti incrementali, la struttura installata corrente deve essere verificata prima di considerare questo documento una fotografia file-per-file definitiva del repository.
