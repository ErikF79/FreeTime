import os,shutil,datetime
B=os.path.dirname(os.path.abspath(__file__));T=r'C:\Python\FreeTime'
if not os.path.isfile(os.path.join(T,'app.py')):raise SystemExit('ERRORE: v0.9 non trovata in '+T)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bk=os.path.join(T,'BACKUP_v09b_'+stamp);os.makedirs(bk)
for rel in ('app.py','templates/base.html','templates/players.html','static/css/style.css'):
 src=os.path.join(T,rel)
 if os.path.isfile(src):dst=os.path.join(bk,rel);os.makedirs(os.path.dirname(dst),exist_ok=True);shutil.copy2(src,dst)
for n in ('player_lifecycle.py','achievement_engine.py','export_engine.py'):shutil.copy2(os.path.join(B,n),os.path.join(T,n))
for src,dst in (('players_v09b.html','players.html'),('exports.html','exports.html'),('achievements.html','achievements.html')):shutil.copy2(os.path.join(B,'templates',src),os.path.join(T,'templates',dst))
p=os.path.join(T,'app.py');s=open(p,encoding='utf-8').read()
s=s.replace('from flask import Flask, flash, redirect, render_template, request, session, url_for','from flask import Flask, flash, redirect, render_template, request, session, url_for, Response, send_file')
s=s.replace('import json, os, random, uuid, webbrowser','import json, os, random, uuid, webbrowser, tempfile')
s=s.replace('from games.connect4 import Connect4Game','from games.connect4 import Connect4Game\nfrom player_lifecycle import migrate_players,find_by_name,enabled_players,toggle_player\nfrom achievement_engine import unlocked_for\nfrom export_engine import csv_bytes,json_bytes,backup_zip')
start=s.index("@app.route('/players',methods=['GET','POST'])");end=s.index("@app.route('/teams')",start)
route="""@app.route('/players',methods=['GET','POST'])
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

"""
s=s[:start]+route+s[end:]
s=s.replace('people=load(PLAYERS)','people=enabled_players(load(PLAYERS))')
marker='def open_browser():'
routes="""@app.route('/achievements')
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
    return send_file(path,as_attachment=True,attachment_filename='FreeTime_backup.zip')

"""
s=s.replace(marker,routes+marker);open(p,'w',encoding='utf-8').write(s)
p=os.path.join(T,'templates','base.html');s=open(p,encoding='utf-8').read().replace("v='0.9'","v='0.9b'").replace('</aside>',"<a href=\"{{ url_for('achievements') }}\">♜<small>Trofei</small></a><a href=\"{{ url_for('exports') }}\">⇩<small>Esporta</small></a></aside>");open(p,'w',encoding='utf-8').write(s)
with open(os.path.join(T,'static','css','style.css'),'a',encoding='utf-8') as f:f.write('\n.player-tabs{display:flex;gap:10px;margin:15px 0}.disabled-profile{opacity:.55}.export-grid,.achievement-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.export-grid article,.achievement-grid article{padding:24px;border-radius:22px;background:var(--panel)}.export-grid a,.player-tabs a,.profiles article button{padding:9px 13px;border-radius:11px;background:#33226b;color:white}.achievement-grid i,.achievement-grid strong,.achievement-grid small,.achievement-grid span{display:block}@media(max-width:760px){.export-grid,.achievement-grid{grid-template-columns:1fr}}\n')
print('AGGIORNAMENTO v0.9b APPLICATO');print('Backup:',bk)
