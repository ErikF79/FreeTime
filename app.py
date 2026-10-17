# -*- coding: utf-8 -*-
import json, os, random, uuid, webbrowser, tempfile, zipfile, io, shutil
from datetime import datetime
from threading import Timer
from flask import Flask, flash, redirect, render_template, request, session, url_for, Response, send_file, jsonify
from engine.game_modes import GameMode
from games.game_registry import get_game_info
from games.game_ruleset import GameRuleSet
from games.tictactoe import TicTacToeGame
from games.connect4 import Connect4Game
from games.wheel import WheelGame
from games.memory import MemoryGame
from games.mastermind import MastermindGame,DIFFICULTIES as MASTERMIND_DIFFICULTIES,COLOR_NAMES as MASTERMIND_COLOR_NAMES
from games.hangman import HangmanGame
from games.charades import CharadesGame
from games.sequence import SequenceGame,SEQUENCE_TYPES
from games.quiz import QuizGame
from games.crossword import CrosswordGame
from player_lifecycle import migrate_players,find_by_name,enabled_players,toggle_player
from achievement_engine import unlocked_for
from export_engine import csv_bytes,json_bytes,backup_zip
from engine.content_engine import load_content,add_content,pending_for,next_pending,mark_used,delete_content

BASE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(BASE,'data')
PLAYERS=os.path.join(DATA,'players.json'); TEAMS=os.path.join(DATA,'teams.json'); RESULTS=os.path.join(DATA,'results.json'); SESSIONS=os.path.join(DATA,'sessions.json')
CONTENT=os.path.join(DATA,'instructor_content.json')
app=Flask(__name__); app.secret_key=os.environ.get('FREETIME_SECRET_KEY','freetime-v07-local-key')

def ensure_data():
    if not os.path.isdir(DATA): os.makedirs(DATA)
    for p in (PLAYERS,TEAMS,RESULTS,SESSIONS,CONTENT):
        if not os.path.isfile(p):
            with open(p,'w',encoding='utf-8') as f: json.dump([],f,indent=4)
def load(p):
    ensure_data()
    try:
        with open(p,'r',encoding='utf-8') as f:
            d=json.load(f); return d if isinstance(d,list) else []
    except (ValueError,OSError): return []
def save(p,d):
    t=p+'.tmp'
    with open(t,'w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=4)
    os.replace(t,p)
def pmap(): return {x['id']:x['name'] for x in load(PLAYERS)}

def result_points(result,player_id):
    participants=result.get('participant_ids',[])
    if player_id not in participants: return 0
    if result.get('status')=='draw': return 1
    return 3 if result.get('winner_id')==player_id else 0

def leaderboard_data(results=None):
    results=results if results is not None else load(RESULTS)
    board=[]
    for player in load(PLAYERS):
        played=[r for r in results if player['id'] in r.get('participant_ids',[])]
        wins=len([r for r in played if r.get('winner_id')==player['id']])
        draws=len([r for r in played if r.get('status')=='draw'])
        points=sum(result_points(r,player['id']) for r in played)
        board.append({'id':player['id'],'name':player['name'],'games':len(played),'wins':wins,'draws':draws,'points':points})
    return sorted(board,key=lambda x:(-x['points'],-x['wins'],x['name'].lower()))

def active_session_id():
    return session.get('active_event_session_id')

def team_of_player(session_obj,player_id):
    if not player_id: return None
    teams_data=load(TEAMS)
    for tid in session_obj.get('team_ids',[]):
        team=next((t for t in teams_data if t.get('id')==tid),None)
        if team and player_id in team.get('player_ids',[]):
            return tid
    return None

def record_tournament_result(session_id,result):
    sessions_data=load(SESSIONS)
    changed=False
    for s in sessions_data:
        if s.get('id')==session_id and s.get('mode')=='tournament':
            winner_id=result.get('winner_id')
            if winner_id:
                tid=team_of_player(s,winner_id)
                if tid:
                    s.setdefault('team_points',{})
                    s['team_points'][tid]=s['team_points'].get(tid,0)+1
            s.setdefault('completed_games',[]).append(result.get('game_id'))
            changed=True
            break
    if changed: save(SESSIONS,sessions_data)

def attach_active_session(result):
    sid=active_session_id()
    result['session_id']=sid
    if sid: record_tournament_result(sid,result)
    return result

def start_url_for_game(game_id):
    mapping={
        'tictactoe':lambda:url_for('new_match',game='tictactoe'),
        'connect4':lambda:url_for('new_match',game='connect4'),
        'wheel':lambda:url_for('new_match_wheel'),
        'memory':lambda:url_for('new_match_memory'),
        'mastermind':lambda:url_for('new_match_mastermind'),
        'impiccato':lambda:url_for('new_match_impiccato'),
        'mimo':lambda:url_for('new_match_mimo'),
        'sequence':lambda:url_for('new_match_sequence'),
        'quiz':lambda:url_for('new_match_quiz'),
        'crossword':lambda:url_for('new_match_crossword'),
    }
    fn=mapping.get(game_id)
    return fn() if fn else url_for('games')

@app.route('/')
def home():
    all_results=load(RESULTS); board=leaderboard_data(all_results); sessions_data=load(SESSIONS)
    game_counts={}
    ruleset_counts={}
    for result in all_results:
        game_counts[result.get('game_id','unknown')]=game_counts.get(result.get('game_id','unknown'),0)+1
        ruleset_counts[result.get('ruleset_id','unknown')]=ruleset_counts.get(result.get('ruleset_id','unknown'),0)+1
    favorite_game_id=max(game_counts,key=game_counts.get) if game_counts else None
    favorite_ruleset=max(ruleset_counts,key=ruleset_counts.get) if ruleset_counts else None
    game_info=get_game_info()
    game_names={g['game_id']:g['name'] for g in game_info}
    favorite_game=game_names.get(favorite_game_id) if favorite_game_id else None
    ready_games=[g for g in game_info if g['status']=='ready']
    active_id=active_session_id()
    active_tournament=None
    for s in sessions_data:
        if s.get('id')==active_id and s.get('mode')=='tournament':
            team_names={t['id']:t['name'] for t in load(TEAMS)}
            standings=sorted(s.get('team_points',{}).items(),key=lambda x:-x[1])
            completed=s.get('completed_games',[])
            active_tournament={'name':s['name'],'standings':[(team_names.get(tid,'?'),pts) for tid,pts in standings],
                                'played':len(completed),'total':len(s.get('program',[]))}
            break
    return render_template('index.html',players=len(load(PLAYERS)),teams=len(load(TEAMS)),results=len(all_results),games=game_info,games_available=len(ready_games),leaderboard=board[:5],favorite_game=favorite_game,favorite_ruleset=favorite_ruleset,last_result=(all_results[-1] if all_results else None),active_session_id=active_id,sessions=sessions_data,active_tournament=active_tournament,names=pmap())
@app.route('/players',methods=['GET','POST'])
def players():
    items=load(PLAYERS);migrate_players(items);save(PLAYERS,items)
    if request.method=='POST':
        name=request.form.get('name','').strip();existing=find_by_name(items,name)
        if not name:flash('Inserisci un nome.','error')
        elif existing and existing.get('enabled',True):flash('Giocatore già presente e attivo.','error')
        elif existing:flash('Giocatore già presente ma disabilitato. Usa Riattiva.','error')
        else:items.append({'id':uuid.uuid4().hex,'name':name,'wins':0,'games':0,'enabled':True});save(PLAYERS,items);flash('Giocatore creato.','success')
        return redirect(url_for('players'))
    status=request.args.get('status','enabled');shown=items if status=='all' else [p for p in items if p.get('enabled',True)==(status!='disabled')]
    return render_template('players.html',players=shown,status=status)
@app.route('/players/<player_id>/toggle',methods=['POST'])
def toggle_player_status(player_id):
    items=load(PLAYERS);player=toggle_player(items,player_id)
    if player:save(PLAYERS,items);flash('Stato giocatore aggiornato.','success')
    return redirect(url_for('players',status='all'))

@app.route('/teams',methods=['GET','POST'])
def teams():
    if request.method=='POST':
        name=request.form.get('name','').strip()
        ids=request.form.getlist('player_ids')
        if not name: flash('Inserisci un nome per la squadra.','error')
        elif not ids: flash('Seleziona almeno un giocatore per la squadra.','error')
        else:
            teams_data=load(TEAMS)
            teams_data.append({'id':uuid.uuid4().hex,'name':name,'player_ids':ids})
            save(TEAMS,teams_data)
            flash('Squadra creata.','success')
        return redirect(url_for('teams'))
    return render_template('teams.html',teams=load(TEAMS),names=pmap(),players=enabled_players(load(PLAYERS)))

@app.route('/teams/<team_id>/delete',methods=['POST'])
def delete_team(team_id):
    teams_data=load(TEAMS)
    filtered=[t for t in teams_data if t.get('id')!=team_id]
    if len(filtered)==len(teams_data): flash('Squadra non trovata.','error')
    else: save(TEAMS,filtered); flash('Squadra rimossa.','success')
    return redirect(url_for('teams'))
@app.route('/games')
def games(): return render_template('games.html',games=get_game_info(),rulesets=GameRuleSet.catalog())
def active_tournament():
    sid=active_session_id()
    if not sid: return None
    for s in load(SESSIONS):
        if s.get('id')==sid and s.get('mode')=='tournament': return s
    return None

def tournament_teams_info(tournament):
    if not tournament: return []
    teams_data=load(TEAMS); tmap={t['id']:t for t in teams_data}
    return [tmap[tid] for tid in tournament.get('team_ids',[]) if tid in tmap]

@app.route('/new-match',methods=['GET','POST'])
def new_match():
    people=enabled_players(load(PLAYERS))
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ruleset_id=request.form.get('ruleset_id',GameRuleSet.CLASSIC)
        game_id=request.form.get('game_id','tictactoe')
        difficulty=request.form.get('difficulty','easy')
        if t_teams:
            ids=[t['id'] for t in t_teams]; mode=GameMode.DUEL
            valid=len(ids)==2
            if not valid: flash('Tris e Forza 4 supportano tornei solo tra esattamente due squadre.','error')
        else:
            mode=request.form.get('mode',''); ids=request.form.getlist('player_ids')
            valid=(mode==GameMode.DUEL and len(ids)==2) or (mode==GameMode.VS_PC and len(ids)==1)
            if not valid: flash('Seleziona i partecipanti richiesti dalla modalità.','error')
        if valid and ruleset_id in (GameRuleSet.EARNED_TURN,GameRuleSet.DESTRUCTIVE) and mode!=GameMode.DUEL:
            valid=False; flash('Il RuleSet selezionato richiede la modalità Coppia.','error')
        if valid:
            session['setup']={'mode':mode,'player_ids':ids,'difficulty':difficulty,'ruleset_id':ruleset_id,'game_id':game_id}
            return redirect(url_for('connect4_start' if game_id=='connect4' else 'tictactoe_start'))
    return render_template('new_match.html',players=people,preselect=request.args.get('game','tictactoe'),tournament_teams=t_teams)

def pc_move(game,difficulty):
    moves=game.available_moves()
    if not moves:return
    choice=random.choice(moves)
    if difficulty=='medium':
        for symbol in ('O','X'):
            for cell in moves:
                game.board[cell]=symbol
                if game.check_winner(symbol): choice=cell; game.board[cell]=''; return game.make_move(choice)
                game.board[cell]=''
    game.make_move(choice)

@app.route('/play/tictactoe/start')
def tictactoe_start():
    setup=session.get('setup')
    if not setup:return redirect(url_for('new_match'))
    game=TicTacToeGame(setup.get('ruleset_id',GameRuleSet.CLASSIC)); session['active_game']=game.export_state(); session['result_saved']=False
    return redirect(url_for('tictactoe_play',_anchor='board-area'))
@app.route('/play/tictactoe/award/<symbol>',methods=['POST'])
def award_tictactoe_turn(symbol):
    setup=session.get('setup'); state=session.get('active_game')
    if not setup or not state: return redirect(url_for('new_match'))
    game=TicTacToeGame.from_state(state)
    ok,msg=game.award_turn(symbol.upper())
    if not ok: flash(msg,'error')
    session['active_game']=game.export_state()
    return redirect(url_for('tictactoe_play',_anchor='board-area'))

@app.route('/play/tictactoe',methods=['GET','POST'])
def tictactoe_play():
    setup=session.get('setup'); state=session.get('active_game')
    if not setup or not state:return redirect(url_for('new_match'))
    game=TicTacToeGame.from_state(state); names=pmap(); ids=setup['player_ids']
    player_x=names.get(ids[0],'Giocatore X'); player_o='Computer' if setup['mode']==GameMode.VS_PC else names.get(ids[1],'Giocatore O')
    if request.method=='POST' and game.status=='active':
        try: cell=int(request.form.get('cell','-1'))
        except ValueError: cell=-1
        action=request.args.get('action',request.form.get('action','place'))
        if action=='remove': ok,msg=game.remove_opponent(cell)
        else: ok,msg=game.make_move(cell)
        if not ok: flash(msg,'error')
        elif setup['mode']==GameMode.VS_PC and game.status=='active' and game.current_symbol=='O': pc_move(game,setup.get('difficulty','easy'))
        session['active_game']=game.export_state()
        if game.status!='active' and not session.get('result_saved'):
            winner_id=None
            if game.status=='won': winner_id=ids[0] if game.winner=='X' else (None if setup['mode']==GameMode.VS_PC else ids[1])
            results=load(RESULTS); results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'tictactoe','ruleset_id':game.ruleset.ruleset_id,
                'mode':setup['mode'],'participant_ids':ids,'winner_id':winner_id,'winner_symbol':game.winner,
                'status':game.status,'moves':game.moves,'completed_at':datetime.now().isoformat(timespec='seconds')})); save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in ids: p['games']=p.get('games',0)+1
                if winner_id and p['id']==winner_id:p['wins']=p.get('wins',0)+1
            save(PLAYERS,players); session['result_saved']=True
        return redirect(url_for('tictactoe_play',_anchor='board-area'))
    return render_template('tictactoe_play.html',game=game,player_x=player_x,player_o=player_o,mode=setup['mode'])
@app.route('/play/tictactoe/rematch',methods=['POST'])
def rematch(): return redirect(url_for('tictactoe_start'))

def connect4_pc_move(game,difficulty):
    columns=game.available_columns()
    if not columns: return
    choice=random.choice(columns)
    if difficulty=='medium':
        for symbol in ('O','X'):
            for column in columns:
                row=game.find_available_row(column); game.board[row][column]=symbol
                if game.check_winner(symbol): game.board[row][column]=''; choice=column; game.drop_piece(choice); return
                game.board[row][column]=''
    game.drop_piece(choice)

@app.route('/play/connect4/start')
def connect4_start():
    setup=session.get('setup')
    if not setup: return redirect(url_for('new_match'))
    if setup.get('ruleset_id') not in (GameRuleSet.CLASSIC,GameRuleSet.EARNED_TURN,GameRuleSet.DESTRUCTIVE):
        flash('Forza 4 supporta Classico, Turno conquistato e Distruttivo.','error'); return redirect(url_for('new_match'))
    if setup.get('ruleset_id') in (GameRuleSet.EARNED_TURN,GameRuleSet.DESTRUCTIVE) and setup.get('mode')!=GameMode.DUEL:
        flash('Turno conquistato richiede Coppia.','error'); return redirect(url_for('new_match'))
    game=Connect4Game(setup.get('ruleset_id',GameRuleSet.CLASSIC)); session['active_connect4']=game.export_state(); session['connect4_result_saved']=False
    return redirect(url_for('connect4_play'))

@app.route('/play/connect4/award/<symbol>',methods=['POST'])
def award_connect4_turn(symbol):
    state=session.get('active_connect4')
    if not state:return redirect(url_for('new_match'))
    game=Connect4Game.from_state(state);ok,msg=game.award_turn(symbol.upper())
    if not ok:flash(msg,'error')
    session['active_connect4']=game.export_state();return redirect(url_for('connect4_play'))

@app.route('/play/connect4',methods=['GET','POST'])
def connect4_play():
    setup=session.get('setup'); state=session.get('active_connect4')
    if not setup or not state: return redirect(url_for('new_match'))
    game=Connect4Game.from_state(state); names=pmap(); ids=setup['player_ids']
    player_x=names.get(ids[0],'Giocatore X'); player_o='Computer' if setup['mode']==GameMode.VS_PC else names.get(ids[1],'Giocatore O')
    if request.method=='POST' and game.status=='active':
        action=request.args.get('action','drop')
        try:
            if action=='remove': row,column=[int(x) for x in request.form.get('cell','-1--1').split('-')]
            else: column=int(request.form.get('column','-1')); row=-1
        except (ValueError,TypeError): column=-1; row=-1
        if action=='remove': ok,msg=game.remove_opponent(row,column)
        else: ok,msg=game.drop_piece(column)
        if not ok: flash(msg,'error')
        elif setup['mode']==GameMode.VS_PC and game.status=='active' and game.current_symbol=='O': connect4_pc_move(game,setup.get('difficulty','easy'))
        session['active_connect4']=game.export_state()
        if game.status!='active' and not session.get('connect4_result_saved'):
            winner_id=None
            if game.status=='won': winner_id=ids[0] if game.winner=='X' else (None if setup['mode']==GameMode.VS_PC else ids[1])
            results=load(RESULTS); results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'connect4','ruleset_id':game.ruleset.ruleset_id,
                'mode':setup['mode'],'participant_ids':ids,'winner_id':winner_id,'winner_symbol':game.winner,
                'status':game.status,'moves':game.moves,'completed_at':datetime.now().isoformat(timespec='seconds')})); save(RESULTS,results)
            players_data=load(PLAYERS)
            for player in players_data:
                if player['id'] in ids: player['games']=player.get('games',0)+1
                if winner_id and player['id']==winner_id: player['wins']=player.get('wins',0)+1
            save(PLAYERS,players_data); session['connect4_result_saved']=True
        return redirect(url_for('connect4_play',_anchor='board-area'))
    return render_template('connect4_play.html',game=game,player_x=player_x,player_o=player_o)

@app.route('/play/connect4/rematch',methods=['POST'])
def connect4_rematch():
    return redirect(url_for('connect4_start'))

@app.route('/history')
def history():
    game_filter=request.args.get('game','all'); ruleset_filter=request.args.get('ruleset','all'); player_filter=request.args.get('player','all'); session_filter=request.args.get('session','all')
    items=load(RESULTS)
    if game_filter!='all': items=[r for r in items if r.get('game_id')==game_filter]
    if ruleset_filter!='all': items=[r for r in items if r.get('ruleset_id')==ruleset_filter]
    if player_filter!='all': items=[r for r in items if player_filter in r.get('participant_ids',[])]
    if session_filter!='all': items=[r for r in items if r.get('session_id')==session_filter]
    return render_template('history.html',results=list(reversed(items)),names=pmap(),players=load(PLAYERS),sessions=load(SESSIONS),filters={'game':game_filter,'ruleset':ruleset_filter,'player':player_filter,'session':session_filter})

@app.route('/leaderboard')
def leaderboard(): return render_template('leaderboard.html',leaderboard=leaderboard_data())

@app.route('/player/<player_id>')
def player_profile(player_id):
    player=next((p for p in load(PLAYERS) if p.get('id')==player_id),None)
    if not player: flash('Giocatore non trovato.','error'); return redirect(url_for('players'))
    results=[r for r in load(RESULTS) if player_id in r.get('participant_ids',[])]
    games={};rules={}
    for r in results:
        games[r.get('game_id','unknown')]=games.get(r.get('game_id','unknown'),0)+1
        rules[r.get('ruleset_id','unknown')]=rules.get(r.get('ruleset_id','unknown'),0)+1
    wins=len([r for r in results if r.get('winner_id')==player_id]);draws=len([r for r in results if r.get('status')=='draw']);points=sum(result_points(r,player_id) for r in results)
    return render_template('player_profile.html',player=player,results=list(reversed(results)),wins=wins,draws=draws,points=points,win_rate=(round(100.0*wins/len(results),1) if results else 0),favorite_game=(max(games,key=games.get) if games else None),favorite_ruleset=(max(rules,key=rules.get) if rules else None))

@app.route('/sessions',methods=['GET','POST'])
def game_sessions():
    items=load(SESSIONS)
    if request.method=='POST':
        if request.form.get('mode')=='tournament':
            name=request.form.get('t_name','').strip()
            team_ids=request.form.getlist('team_ids')
            program=request.form.getlist('program_games')
            if not name: flash('Inserisci un nome per il torneo.','error')
            elif len(team_ids)<2: flash('Seleziona almeno due squadre per il torneo.','error')
            elif len(program)<2: flash('Seleziona almeno due giochi per il programma del torneo.','error')
            else:
                item={'id':uuid.uuid4().hex,'name':name,'created_at':datetime.now().isoformat(timespec='seconds'),
                      'status':'active','mode':'tournament','team_ids':team_ids,'program':program,
                      'team_points':{},'completed_games':[]}
                items.append(item); save(SESSIONS,items)
                session['active_event_session_id']=item['id']
                flash('Torneo creato e attivato.','success')
        else:
            name=request.form.get('name','').strip()
            if name:
                item={'id':uuid.uuid4().hex,'name':name,'created_at':datetime.now().isoformat(timespec='seconds'),'status':'active'}
                items.append(item);save(SESSIONS,items);session['active_event_session_id']=item['id']
                flash('Sessione creata e attivata.','success')
        return redirect(url_for('game_sessions'))
    results=load(RESULTS)
    teams_data=load(TEAMS)
    team_name_map={t['id']:t['name'] for t in teams_data}
    game_name_map={g['game_id']:g['name'] for g in get_game_info()}
    for item in items:
        linked=[r for r in results if r.get('session_id')==item['id']];item['matches']=len(linked)
        if item.get('mode')=='tournament':
            item['team_names']=team_name_map
            item['team_standings']=sorted(item.get('team_points',{}).items(),key=lambda x:-x[1])
            completed=item.get('completed_games',[])
            next_gid=None
            for gid in item.get('program',[]):
                if item.get('program',[]).count(gid)>completed.count(gid): next_gid=gid; break
            item['next_game_name']=game_name_map.get(next_gid,next_gid) if next_gid else None
            item['next_game_url']=start_url_for_game(next_gid) if next_gid else None
        else:
            item['leaderboard']=leaderboard_data(linked)[:3]
    return render_template('sessions.html',sessions=list(reversed(items)),active_session_id=active_session_id(),
                            teams_list=teams_data,game_catalog=[g for g in get_game_info() if g['status']=='ready'])

@app.route('/sessions/<session_id>/activate',methods=['POST'])
def activate_session(session_id):
    if any(x.get('id')==session_id for x in load(SESSIONS)):session['active_event_session_id']=session_id;flash('Sessione attivata.','success')
    return redirect(url_for('game_sessions'))

@app.route('/sessions/deactivate',methods=['POST'])
def deactivate_session(): session.pop('active_event_session_id',None);flash('Sessione disattivata.','success');return redirect(url_for('game_sessions'))

@app.route('/achievements')
def achievements():
    items=[];results=load(RESULTS)
    for p in load(PLAYERS):
        for a in unlocked_for(p['id'],results):a['player_name']=p['name'];items.append(a)
    return render_template('achievements.html',achievements=items)
@app.route('/exports')
def exports():return render_template('exports.html')
@app.route('/export/<dataset>.<format>')
def export_data(dataset,format):
    maps={'players':load(PLAYERS),'results':load(RESULTS),'sessions':load(SESSIONS),'leaderboard':leaderboard_data()}
    if dataset not in maps or format not in ('csv','json'):return ('Formato non valido',400)
    rows=maps[dataset]
    if format=='json':data=json_bytes(rows);mime='application/json'
    else:fields=sorted(set(k for row in rows for k in row.keys())) if rows else ['empty'];data=csv_bytes(rows,fields);mime='text/csv'
    return Response(data,mimetype=mime,headers={'Content-Disposition':'attachment; filename='+dataset+'.'+format})
@app.route('/backup')
def backup_platform():
    h,path=tempfile.mkstemp(suffix='.zip');os.close(h);backup_zip(path,{'players':load(PLAYERS),'results':load(RESULTS),'sessions':load(SESSIONS),'teams':load(TEAMS)})
    return send_file(path,as_attachment=True,download_name='FreeTime_backup.zip')

RESTORE_DATASETS={'players.json':PLAYERS,'results.json':RESULTS,'sessions.json':SESSIONS,'teams.json':TEAMS}
@app.route('/restore',methods=['POST'])
def restore_backup():
    file=request.files.get('backup_file')
    if not file or file.filename=='':
        flash('Seleziona un file di backup ZIP.','error'); return redirect(url_for('exports'))
    try:
        zf=zipfile.ZipFile(io.BytesIO(file.read())); names=zf.namelist(); parsed={}
        for fname,target_path in RESTORE_DATASETS.items():
            if fname not in names: continue
            content=json.loads(zf.read(fname).decode('utf-8'))
            if not isinstance(content,list): raise ValueError(fname+' non è nel formato atteso (lista).')
            parsed[target_path]=content
        if not parsed:
            flash('Lo ZIP non contiene dataset riconosciuti (players.json, results.json, sessions.json, teams.json).','error')
            return redirect(url_for('exports'))
    except (zipfile.BadZipFile,ValueError,UnicodeDecodeError,json.JSONDecodeError) as e:
        flash('Backup non valido, nessun dato è stato modificato. Dettaglio: '+str(e),'error'); return redirect(url_for('exports'))

    ensure_data()
    safety_name='pre_restore_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S')
    safety_dir=os.path.join(DATA,safety_name); os.makedirs(safety_dir,exist_ok=True)
    for target_path in RESTORE_DATASETS.values():
        if os.path.isfile(target_path): shutil.copy2(target_path,os.path.join(safety_dir,os.path.basename(target_path)))

    for target_path,content in parsed.items(): save(target_path,content)
    flash('Backup ripristinato ('+str(len(parsed))+' dataset). Copia di sicurezza dei dati precedenti salvata in data/'+safety_name+'.','success')
    return redirect(url_for('exports'))

PHRASE_GAMES={'wheel':'Ruota della fortuna','impiccato':'Impiccato','mimo':'Indovina mimando'}
MAX_QUIZ_OPTIONS=8
MAX_CROSSWORD_ENTRIES=20

EXAMPLE_PACKS={'cultura_generale':'Cultura generale','musica':'Musica','cinema':'Cinema'}

@app.route('/instructor/load-examples/<pack>',methods=['POST'])
def load_examples(pack):
    if pack not in EXAMPLE_PACKS:
        flash('Pacchetto non riconosciuto.','error'); return redirect(url_for('instructor_panel'))
    path=os.path.join(BASE,'examples',pack+'.json')
    try:
        with open(path,'r',encoding='utf-8') as f: items=json.load(f)
    except (OSError,ValueError):
        flash('Impossibile leggere il pacchetto di esempio.','error'); return redirect(url_for('instructor_panel'))
    count=0
    for item in items:
        gid=item.get('game_id')
        if not gid: continue
        payload={k:v for k,v in item.items() if k!='game_id'}
        add_content(CONTENT,gid,payload); count+=1
    flash('Caricati {0} contenuti di esempio ({1}).'.format(count,EXAMPLE_PACKS[pack]),'success')
    return redirect(url_for('instructor_panel'))

@app.route('/instructor',methods=['GET','POST'])
def instructor_panel():
    if request.method=='POST':
        game_id=request.form.get('game_id','wheel')
        if game_id in PHRASE_GAMES:
            category=request.form.get('category','').strip()
            phrase=request.form.get('phrase','').strip()
            if not category:
                flash('Inserisci una categoria: dà un contesto a chi deve indovinare.','error')
            elif not phrase:
                flash('Inserisci una frase o parola da far indovinare.','error')
            elif len(phrase)>60:
                flash('La frase è troppo lunga (massimo 60 caratteri).','error')
            elif not all(ch.isalpha() or ch.isspace() or ch in "'-.,!?" for ch in phrase):
                flash('Usa solo lettere, spazi e punteggiatura di base (niente numeri o simboli).','error')
            else:
                add_content(CONTENT,game_id,{'category':category,'phrase':phrase})
                flash('Aggiunta a '+PHRASE_GAMES[game_id]+'.','success')
        elif game_id=='quiz':
            question=request.form.get('question','').strip()
            raw_options=[request.form.get('option{0}'.format(i),'').strip() for i in range(MAX_QUIZ_OPTIONS)]
            filled=[(i,o) for i,o in enumerate(raw_options) if o]
            try: correct_index_raw=int(request.form.get('correct_index','-1'))
            except (TypeError,ValueError): correct_index_raw=-1
            idx_map={orig:pos for pos,(orig,val) in enumerate(filled)}
            if not question:
                flash('Inserisci il testo della domanda.','error')
            elif len(filled)<2:
                flash('Inserisci almeno due risposte.','error')
            elif correct_index_raw not in idx_map:
                flash('Indica quale risposta è quella corretta.','error')
            else:
                options=[val for orig,val in filled]
                add_content(CONTENT,'quiz',{'question':question,'options':options,'correct_index':idx_map[correct_index_raw]})
                flash('Domanda aggiunta al Quizzone ({0} risposte).'.format(len(options)),'success')
        elif game_id=='crossword':
            title=request.form.get('cw_title','').strip()
            entries=[]
            invalid=False
            for i in range(MAX_CROSSWORD_ENTRIES):
                clue=request.form.get('cw_clue{0}'.format(i),'').strip()
                answer=request.form.get('cw_answer{0}'.format(i),'').strip()
                if clue and answer:
                    if ' ' in answer or not answer.isalpha():
                        flash('La risposta {0} deve essere una singola parola, solo lettere (niente spazi o numeri).'.format(i+1),'error'); invalid=True; break
                    entries.append({'clue':clue,'answer':answer})
            if invalid:
                pass
            elif len(entries)<3:
                flash('Inserisci almeno 3 coppie indizio/risposta per il cruciverba.','error')
            else:
                add_content(CONTENT,'crossword',{'title':title,'entries':entries})
                flash('Cruciverba aggiunto alla coda ({0} parole).'.format(len(entries)),'success')
        else:
            flash('Gioco non supportato dal pannello istruttore.','error')
        return redirect(url_for('instructor_panel'))
    pending={gid:pending_for(CONTENT,gid) for gid in PHRASE_GAMES}
    pending['quiz']=pending_for(CONTENT,'quiz')
    pending['crossword']=pending_for(CONTENT,'crossword')
    return render_template('instructor.html',pending=pending,phrase_games=PHRASE_GAMES,example_packs=EXAMPLE_PACKS)

@app.route('/instructor/<content_id>/delete',methods=['POST'])
def instructor_delete(content_id):
    if delete_content(CONTENT,content_id): flash('Contenuto rimosso dalla coda.','success')
    else: flash('Contenuto non trovato.','error')
    return redirect(url_for('instructor_panel'))

@app.route('/new-match/wheel',methods=['GET','POST'])
def new_match_wheel():
    people=enabled_players(load(PLAYERS))
    pending=next_pending(CONTENT,'wheel')
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        if not ids:
            flash('Seleziona almeno un giocatore.','error')
        elif not pending:
            flash('Nessuna frase in coda. Chiedi a un istruttore di inserirne una dal Pannello istruttore.','error')
        else:
            session['wheel_setup']={'player_ids':ids,'mode':request.form.get('mode','turno_conquistato')}
            return redirect(url_for('wheel_start'))
        return redirect(url_for('new_match_wheel'))
    return render_template('new_match_wheel.html',players=people,pending=pending,tournament_teams=t_teams)

@app.route('/play/wheel/start')
def wheel_start():
    setup=session.get('wheel_setup')
    if not setup: return redirect(url_for('new_match_wheel'))
    content=next_pending(CONTENT,'wheel')
    if not content:
        flash('Nessuna frase disponibile. Torna al Pannello istruttore.','error')
        return redirect(url_for('new_match_wheel'))
    game=WheelGame(); game.setup(content.get('category',''),content.get('phrase',''),setup['player_ids'],setup.get('mode','turno_conquistato'))
    mark_used(CONTENT,content['id'])
    session['active_wheel']=game.export_state()
    session['wheel_result_saved']=False
    return redirect(url_for('wheel_play',_anchor='board-area'))

@app.route('/play/wheel',methods=['GET','POST'])
def wheel_play():
    state=session.get('active_wheel')
    if not state: return redirect(url_for('new_match_wheel'))
    game=WheelGame.from_state(state)
    if request.method=='POST':
        action=request.form.get('action')
        if action=='spin': ok,msg=game.spin()
        elif action=='letter': ok,msg=game.guess_letter(request.form.get('letter',''))
        elif action=='phrase': ok,msg=game.guess_phrase(request.form.get('phrase_guess',''))
        elif action=='attack': ok,msg=game.attack(request.form.get('target',''))
        else: ok,msg=False,'Azione non valida.'
        if not ok: flash(msg,'error')
        session['active_wheel']=game.export_state()
        if game.status=='won' and not session.get('wheel_result_saved'):
            winner_id=max(game.scores,key=lambda k:game.scores[k]) if game.scores else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'wheel','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,'status':'won',
                'moves':len(game.guessed),'completed_at':datetime.now().isoformat(timespec='seconds'),
                'scores':game.scores,'phrase':game.phrase,'category':game.category}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['wheel_result_saved']=True
        return redirect(url_for('wheel_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('wheel_play.html',game=game,names=names,current_id=game.current_player(),sorted_scores=sorted_scores)

@app.route('/play/wheel/spin-ajax',methods=['POST'])
def wheel_spin_ajax():
    state=session.get('active_wheel')
    if not state: return jsonify({'error':'no_state'}),400
    game=WheelGame.from_state(state)
    ok,msg=game.spin()
    session['active_wheel']=game.export_state()
    return jsonify({'ok':ok,'message':msg,'spin_value':game.spin_value,'status':game.status})

@app.route('/play/wheel/rematch',methods=['POST'])
def wheel_rematch():
    session.pop('active_wheel',None); session.pop('wheel_result_saved',None); session.pop('wheel_setup',None)
    return redirect(url_for('new_match_wheel'))

@app.route('/new-match/memory',methods=['GET','POST'])
def new_match_memory():
    people=enabled_players(load(PLAYERS))
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids'); pairs=request.form.get('pairs','8')
        if not ids: flash('Seleziona almeno un giocatore.','error')
        else:
            session['memory_setup']={'player_ids':ids,'pairs':pairs,'mode':request.form.get('mode','turno_conquistato')}
            return redirect(url_for('memory_start'))
        return redirect(url_for('new_match_memory'))
    return render_template('new_match_memory.html',players=people,tournament_teams=t_teams)

@app.route('/play/memory/start')
def memory_start():
    setup=session.get('memory_setup')
    if not setup: return redirect(url_for('new_match_memory'))
    game=MemoryGame(); game.setup(setup.get('pairs',8),setup['player_ids'],setup.get('mode','turno_conquistato'))
    session['active_memory']=game.export_state(); session['memory_result_saved']=False
    return redirect(url_for('memory_play',_anchor='board-area'))

@app.route('/play/memory',methods=['GET','POST'])
def memory_play():
    state=session.get('active_memory')
    if not state: return redirect(url_for('new_match_memory'))
    game=MemoryGame.from_state(state)
    if request.method=='POST':
        action=request.form.get('action')
        if action=='flip':
            try: idx=int(request.form.get('cell',''))
            except (TypeError,ValueError): idx=None
            ok,msg=game.flip(idx)
        elif action=='continue': ok,msg=game.continue_turn()
        else: ok,msg=False,'Azione non valida.'
        if not ok: flash(msg,'error')
        session['active_memory']=game.export_state()
        if game.status=='won' and not session.get('memory_result_saved'):
            top=max(game.scores.values()) if game.scores else 0
            leaders=[pid for pid,s in game.scores.items() if s==top]
            winner_id=leaders[0] if len(leaders)==1 else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'memory','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,
                'status':'draw' if winner_id is None else 'won','moves':len(game.cards),
                'completed_at':datetime.now().isoformat(timespec='seconds'),'scores':game.scores}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['memory_result_saved']=True
        return redirect(url_for('memory_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('memory_play.html',game=game,names=names,current_id=game.current_player(),sorted_scores=sorted_scores)

@app.route('/play/memory/rematch',methods=['POST'])
def memory_rematch():
    session.pop('active_memory',None); session.pop('memory_result_saved',None); session.pop('memory_setup',None)
    return redirect(url_for('new_match_memory'))

@app.route('/new-match/mastermind',methods=['GET','POST'])
def new_match_mastermind():
    people=enabled_players(load(PLAYERS))
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids'); difficulty=request.form.get('difficulty','medium')
        if not ids: flash('Seleziona almeno un giocatore.','error')
        else:
            session['mastermind_setup']={'player_ids':ids,'difficulty':difficulty,'mode':request.form.get('mode','classico')}
            return redirect(url_for('mastermind_start'))
        return redirect(url_for('new_match_mastermind'))
    return render_template('new_match_mastermind.html',players=people,difficulties=MASTERMIND_DIFFICULTIES,tournament_teams=t_teams)

@app.route('/play/mastermind/start')
def mastermind_start():
    setup=session.get('mastermind_setup')
    if not setup: return redirect(url_for('new_match_mastermind'))
    game=MastermindGame(); game.setup(setup.get('difficulty','medium'),setup['player_ids'],setup.get('mode','classico'))
    session['active_mastermind']=game.export_state(); session['mastermind_result_saved']=False
    return redirect(url_for('mastermind_play',_anchor='board-area'))

@app.route('/play/mastermind',methods=['GET','POST'])
def mastermind_play():
    state=session.get('active_mastermind')
    if not state: return redirect(url_for('new_match_mastermind'))
    game=MastermindGame.from_state(state)
    if request.method=='POST':
        colors=[request.form.get('peg{0}'.format(i),'') for i in range(game.length)]
        ok,msg=game.guess(colors)
        if not ok: flash(msg,'error')
        session['active_mastermind']=game.export_state()
        if game.status in ('won','lost') and not session.get('mastermind_result_saved'):
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'mastermind','ruleset_id':game.difficulty,
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':game.winner_id,
                'status':'won' if game.status=='won' else 'draw','moves':len(game.guesses),
                'completed_at':datetime.now().isoformat(timespec='seconds'),'code':game.code}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==game.winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['mastermind_result_saved']=True
        return redirect(url_for('mastermind_play',_anchor='board-area'))
    names=pmap()
    return render_template('mastermind_play.html',game=game,names=names,current_id=game.current_player(),
                            colors=game.palette,color_names=MASTERMIND_COLOR_NAMES)

@app.route('/play/mastermind/rematch',methods=['POST'])
def mastermind_rematch():
    session.pop('active_mastermind',None); session.pop('mastermind_result_saved',None); session.pop('mastermind_setup',None)
    return redirect(url_for('new_match_mastermind'))

@app.route('/new-match/impiccato',methods=['GET','POST'])
def new_match_impiccato():
    people=enabled_players(load(PLAYERS))
    pending=next_pending(CONTENT,'impiccato')
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        if not ids: flash('Seleziona almeno un giocatore.','error')
        elif not pending: flash('Nessuna parola in coda. Chiedi a un istruttore di inserirne una.','error')
        else:
            session['impiccato_setup']={'player_ids':ids,'mode':request.form.get('mode','turno_conquistato')}
            return redirect(url_for('impiccato_start'))
        return redirect(url_for('new_match_impiccato'))
    return render_template('new_match_impiccato.html',players=people,pending=pending,tournament_teams=t_teams)

@app.route('/play/impiccato/start')
def impiccato_start():
    setup=session.get('impiccato_setup')
    if not setup: return redirect(url_for('new_match_impiccato'))
    content=next_pending(CONTENT,'impiccato')
    if not content:
        flash('Nessuna parola disponibile. Torna al Pannello istruttore.','error')
        return redirect(url_for('new_match_impiccato'))
    game=HangmanGame(); game.setup(content.get('category',''),content.get('phrase',''),setup['player_ids'],setup.get('mode','turno_conquistato'))
    mark_used(CONTENT,content['id'])
    session['active_impiccato']=game.export_state(); session['impiccato_result_saved']=False
    return redirect(url_for('impiccato_play',_anchor='board-area'))

@app.route('/play/impiccato',methods=['GET','POST'])
def impiccato_play():
    state=session.get('active_impiccato')
    if not state: return redirect(url_for('new_match_impiccato'))
    game=HangmanGame.from_state(state)
    if request.method=='POST':
        ok,msg=game.guess_letter(request.form.get('letter',''))
        if not ok: flash(msg,'error')
        session['active_impiccato']=game.export_state()
        if game.status in ('won','lost') and not session.get('impiccato_result_saved'):
            winner_id=max(game.scores,key=lambda k:game.scores[k]) if any(game.scores.values()) else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'impiccato','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,
                'status':'won' if game.status=='won' else 'draw','moves':len(game.guessed),
                'completed_at':datetime.now().isoformat(timespec='seconds'),'scores':game.scores,
                'phrase':game.phrase,'category':game.category}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['impiccato_result_saved']=True
        return redirect(url_for('impiccato_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('impiccato_play.html',game=game,names=names,current_id=game.current_player(),
                            sorted_scores=sorted_scores,max_errors=6)

@app.route('/play/impiccato/rematch',methods=['POST'])
def impiccato_rematch():
    session.pop('active_impiccato',None); session.pop('impiccato_result_saved',None); session.pop('impiccato_setup',None)
    return redirect(url_for('new_match_impiccato'))

@app.route('/new-match/mimo',methods=['GET','POST'])
def new_match_mimo():
    people=enabled_players(load(PLAYERS))
    pending=pending_for(CONTENT,'mimo')
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        if len(ids)<2: flash('Servono almeno due giocatori per Indovina mimando.','error')
        elif not pending: flash('Nessuna frase in coda per Indovina mimando. Chiedi a un istruttore di inserirne una.','error')
        else:
            session['mimo_setup']={'player_ids':ids,'mode':request.form.get('mode','classico')}
            return redirect(url_for('mimo_start'))
        return redirect(url_for('new_match_mimo'))
    return render_template('new_match_mimo.html',players=people,pending=pending,tournament_teams=t_teams)

@app.route('/play/mimo/start')
def mimo_start():
    setup=session.get('mimo_setup')
    if not setup: return redirect(url_for('new_match_mimo'))
    game=CharadesGame(); game.setup(setup['player_ids'],setup.get('mode','classico'))
    content=next_pending(CONTENT,'mimo')
    if not content:
        flash('Nessuna frase disponibile.','error'); return redirect(url_for('new_match_mimo'))
    game.load_round(content); mark_used(CONTENT,content['id'])
    session['active_mimo']=game.export_state(); session['mimo_result_saved']=False
    return redirect(url_for('mimo_play',_anchor='board-area'))

@app.route('/play/mimo',methods=['GET','POST'])
def mimo_play():
    state=session.get('active_mimo')
    if not state: return redirect(url_for('new_match_mimo'))
    game=CharadesGame.from_state(state)
    if request.method=='POST':
        action=request.form.get('action')
        if action in ('correct','pass'):
            game.resolve(action=='correct')
            nxt=next_pending(CONTENT,'mimo')
            if nxt: game.load_round(nxt); mark_used(CONTENT,nxt['id'])
            else: game.status='finished'
        session['active_mimo']=game.export_state()
        if game.status=='finished' and not session.get('mimo_result_saved'):
            winner_id=None
            if game.scores:
                top=max(game.scores.values())
                leaders=[pid for pid,s in game.scores.items() if s==top and s>0]
                winner_id=leaders[0] if len(leaders)==1 else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'mimo','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,
                'status':'won' if winner_id else 'draw','moves':game.rounds_played,
                'completed_at':datetime.now().isoformat(timespec='seconds'),'scores':game.scores}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['mimo_result_saved']=True
        return redirect(url_for('mimo_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('mimo_play.html',game=game,names=names,current_id=game.current_player(),sorted_scores=sorted_scores)

@app.route('/play/mimo/rematch',methods=['POST'])
def mimo_rematch():
    session.pop('active_mimo',None); session.pop('mimo_result_saved',None); session.pop('mimo_setup',None)
    return redirect(url_for('new_match_mimo'))

@app.route('/new-match/sequence',methods=['GET','POST'])
def new_match_sequence():
    people=enabled_players(load(PLAYERS))
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        try: grid_size=int(request.form.get('grid_size','16'))
        except (TypeError,ValueError): grid_size=16
        sequence_type=request.form.get('sequence_type','numeri')
        if not ids: flash('Seleziona almeno un giocatore.','error')
        else:
            session['sequence_setup']={'player_ids':ids,'grid_size':grid_size,'sequence_type':sequence_type}
            return redirect(url_for('sequence_start'))
        return redirect(url_for('new_match_sequence'))
    return render_template('new_match_sequence.html',players=people,tournament_teams=t_teams,sequence_types=SEQUENCE_TYPES)

@app.route('/play/sequence/start')
def sequence_start():
    setup=session.get('sequence_setup')
    if not setup: return redirect(url_for('new_match_sequence'))
    game=SequenceGame(); game.setup(setup.get('grid_size',16),setup.get('sequence_type','numeri'),setup['player_ids'])
    session['active_sequence']=game.export_state(); session['sequence_result_saved']=False
    return redirect(url_for('sequence_play',_anchor='board-area'))

@app.route('/play/sequence',methods=['GET','POST'])
def sequence_play():
    state=session.get('active_sequence')
    if not state: return redirect(url_for('new_match_sequence'))
    game=SequenceGame.from_state(state)
    if request.method=='POST':
        action=request.form.get('action')
        if action=='ready': ok,msg=game.start_turn()
        elif action=='tap':
            try: index=int(request.form.get('index',''))
            except (TypeError,ValueError): index=None
            ok,msg=(False,'Selezione non valida.') if index is None else game.tap(index)
        else: ok,msg=False,'Azione non valida.'
        if not ok: flash(msg,'error')
        session['active_sequence']=game.export_state()
        if game.status=='finished' and not session.get('sequence_result_saved'):
            winner_id=min(game.results,key=lambda k:game.results[k]) if game.results else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'sequence','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,'status':'won',
                'moves':game.grid_size,'completed_at':datetime.now().isoformat(timespec='seconds'),
                'times':game.results}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['sequence_result_saved']=True
        return redirect(url_for('sequence_play',_anchor='board-area'))
    names=pmap()
    sorted_times=sorted(game.results.items(),key=lambda x:x[1])
    return render_template('sequence_play.html',game=game,names=names,current_id=game.current_player(),sorted_times=sorted_times)

@app.route('/play/sequence/rematch',methods=['POST'])
def sequence_rematch():
    session.pop('active_sequence',None); session.pop('sequence_result_saved',None); session.pop('sequence_setup',None)
    return redirect(url_for('new_match_sequence'))

@app.route('/new-match/quiz',methods=['GET','POST'])
def new_match_quiz():
    people=enabled_players(load(PLAYERS))
    pending=pending_for(CONTENT,'quiz')
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        if not ids: flash('Seleziona almeno un giocatore.','error')
        elif not pending: flash('Nessuna domanda in coda. Chiedi a un istruttore di inserirne una.','error')
        else:
            session['quiz_setup']={'player_ids':ids,'mode':request.form.get('mode','classico')}
            return redirect(url_for('quiz_start'))
        return redirect(url_for('new_match_quiz'))
    return render_template('new_match_quiz.html',players=people,pending=pending,tournament_teams=t_teams)

@app.route('/play/quiz/start')
def quiz_start():
    setup=session.get('quiz_setup')
    if not setup: return redirect(url_for('new_match_quiz'))
    game=QuizGame(); game.setup(setup['player_ids'],setup.get('mode','classico'))
    content=next_pending(CONTENT,'quiz')
    if not content:
        flash('Nessuna domanda disponibile.','error'); return redirect(url_for('new_match_quiz'))
    game.load_question(content); mark_used(CONTENT,content['id'])
    session['active_quiz']=game.export_state(); session['quiz_result_saved']=False
    return redirect(url_for('quiz_play',_anchor='board-area'))

@app.route('/play/quiz',methods=['GET','POST'])
def quiz_play():
    state=session.get('active_quiz')
    if not state: return redirect(url_for('new_match_quiz'))
    game=QuizGame.from_state(state)
    if request.method=='POST':
        try: idx=int(request.form.get('option',''))
        except (TypeError,ValueError): idx=None
        if idx is None: flash('Scegli una risposta.','error')
        else:
            game.answer(idx)
            nxt=next_pending(CONTENT,'quiz')
            if nxt: game.load_question(nxt); mark_used(CONTENT,nxt['id'])
            else: game.status='finished'
        session['active_quiz']=game.export_state()
        if game.status=='finished' and not session.get('quiz_result_saved'):
            winner_id=None
            if game.scores:
                top=max(game.scores.values())
                leaders=[pid for pid,s in game.scores.items() if s==top and s>0]
                winner_id=leaders[0] if len(leaders)==1 else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'quiz','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,
                'status':'won' if winner_id else 'draw','moves':game.questions_played,
                'completed_at':datetime.now().isoformat(timespec='seconds'),'scores':game.scores}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['quiz_result_saved']=True
        return redirect(url_for('quiz_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('quiz_play.html',game=game,names=names,current_id=game.current_player(),sorted_scores=sorted_scores)

@app.route('/play/quiz/rematch',methods=['POST'])
def quiz_rematch():
    session.pop('active_quiz',None); session.pop('quiz_result_saved',None); session.pop('quiz_setup',None)
    return redirect(url_for('new_match_quiz'))

@app.route('/new-match/crossword',methods=['GET','POST'])
def new_match_crossword():
    people=enabled_players(load(PLAYERS))
    pending=next_pending(CONTENT,'crossword')
    tournament=active_tournament(); t_teams=tournament_teams_info(tournament)
    if request.method=='POST':
        ids=[t['id'] for t in t_teams] if t_teams else request.form.getlist('player_ids')
        if not ids: flash('Seleziona almeno un giocatore o squadra.','error')
        elif not pending: flash('Nessun cruciverba in coda. Chiedi a un istruttore di inserirne uno.','error')
        else:
            session['crossword_setup']={'player_ids':ids}
            return redirect(url_for('crossword_start'))
        return redirect(url_for('new_match_crossword'))
    return render_template('new_match_crossword.html',players=people,pending=pending,tournament_teams=t_teams)

@app.route('/play/crossword/start')
def crossword_start():
    setup=session.get('crossword_setup')
    if not setup: return redirect(url_for('new_match_crossword'))
    content=next_pending(CONTENT,'crossword')
    if not content:
        flash('Nessun cruciverba disponibile.','error'); return redirect(url_for('new_match_crossword'))
    game=CrosswordGame(); game.setup(content.get('title',''),content.get('entries',[]),setup['player_ids'])
    if not game.entries:
        flash('Non è stato possibile generare uno schema collegato da queste parole (nessuna coppia si incrocia).','error')
        return redirect(url_for('new_match_crossword'))
    mark_used(CONTENT,content['id'])
    if game.dropped:
        flash('{0} parola/e escluse perché non si incrociavano con le altre: {1}.'.format(len(game.dropped),', '.join(game.dropped)),'error')
    session['active_crossword']=game.export_state(); session['crossword_result_saved']=False
    return redirect(url_for('crossword_play',_anchor='board-area'))

@app.route('/play/crossword',methods=['GET','POST'])
def crossword_play():
    state=session.get('active_crossword')
    if not state: return redirect(url_for('new_match_crossword'))
    game=CrosswordGame.from_state(state)
    if request.method=='POST':
        action=request.form.get('action','word')
        if action=='word':
            try: idx=int(request.form.get('entry_index',''))
            except (TypeError,ValueError): idx=None
            ok,msg=(False,'Parola non valida.') if idx is None else game.guess_word(idx,request.form.get('word',''))
        elif action=='reveal':
            ok,msg=game.reveal_letter(request.form.get('letter',''))
        elif action=='pass':
            ok,msg=game.pass_turn()
        else:
            ok,msg=False,'Azione non valida.'
        if not ok: flash(msg,'error')
        session['active_crossword']=game.export_state()
        if game.status=='won' and not session.get('crossword_result_saved'):
            winner_id=max(game.scores,key=lambda k:game.scores[k]) if any(game.scores.values()) else None
            results=load(RESULTS)
            results.append(attach_active_session({'id':uuid.uuid4().hex,'game_id':'crossword','ruleset_id':'classic',
                'mode':GameMode.TEAM,'participant_ids':game.participant_ids,'winner_id':winner_id,'status':'won',
                'moves':sum(1 for c in game.cells if c['revealed']),
                'completed_at':datetime.now().isoformat(timespec='seconds'),'scores':game.scores,'title':game.title}))
            save(RESULTS,results)
            players=load(PLAYERS)
            for p in players:
                if p['id'] in game.participant_ids: p['games']=p.get('games',0)+1
                if p['id']==winner_id: p['wins']=p.get('wins',0)+1
            save(PLAYERS,players)
            session['crossword_result_saved']=True
        return redirect(url_for('crossword_play',_anchor='board-area'))
    names=pmap()
    sorted_scores=sorted(game.scores.items(),key=lambda x:-x[1])
    return render_template('crossword_play.html',game=game,names=names,current_id=game.current_player(),sorted_scores=sorted_scores)

@app.route('/play/crossword/rematch',methods=['POST'])
def crossword_rematch():
    session.pop('active_crossword',None); session.pop('crossword_result_saved',None); session.pop('crossword_setup',None)
    return redirect(url_for('new_match_crossword'))

@app.route('/service-worker.js')
def service_worker():
    resp=app.send_static_file('service-worker.js')
    resp.headers['Service-Worker-Allowed']='/'
    resp.headers['Cache-Control']='no-cache'
    return resp

def open_browser(): webbrowser.open_new('http://127.0.0.1:5000/')
if __name__=='__main__': ensure_data(); Timer(1.0,open_browser).start(); app.run(host='127.0.0.1',port=5000,debug=True,use_reloader=False)
