from __future__ import annotations
import json
import random
from datetime import datetime, timezone
from services.formatting import e
from services.rich_text import sanitize_rich_html
from repositories.question_repository import question_editor_data, ensure_legacy_question_bank as _ensure_legacy_question_bank, parent_bank_data

def question_editor_values(conn,set_id,q=None,locked=False):
    q=dict(q) if q else {}
    data=question_editor_data(conn,set_id,q.get('id'))
    rows=data['categories']
    selected=q.get('category_id')
    options=''.join(f'<option value="{x["id"]}" data-key="{e(x["score_key"])}" {"selected" if selected and int(selected)==x["id"] else ""}>{e((x["parent_name"]+" · ") if x["parent_name"] else "")}{e(x["name"])}</option>' for x in rows)
    profiles=data['profiles']
    score_profile_id=data['profile_id']
    scoring_profile_options=''.join(f'<option value="{x["id"]}" {"selected" if score_profile_id==x["id"] else ""}>{e(x["name"])}</option>' for x in profiles)
    banks=data['banks']
    memberships={x['bank_id'] for x in data['memberships']}
    bank_options=''.join(f'<label class="flex items-center gap-2 text-sm"><input type="checkbox" name="add_to_bank_{x["id"]}" value="1" {"checked" if x["id"] in memberships else ""}> {e(x["name"])}</label>' for x in banks) or '<span class="text-sm text-slate-500">Belum ada bank lain untuk tujuan penggunaan ulang.</span>'
    values={'FORM_HEADING':'Edit soal' if q else 'Tambah soal','FORM_ACTION':'/admin/bank-soal/soal/simpan','SET_ID':str(set_id),'SET_TITLE':e(q.get('set_title','')),'QUESTION_ID':str(q.get('id','')),'CATEGORY_OPTIONS':options,'SCORING_PROFILE_OPTIONS':scoring_profile_options,'BANK_MEMBERSHIP_OPTIONS':bank_options,'FORM_ERROR':'<p class="notice">Paket ini memiliki riwayat attempt. Soal dibekukan agar attempt lama tetap utuh.</p>' if locked else '', 'FORM_DISABLED':'disabled' if locked else '', 'POSITION':str(q.get('position',1)),'PROMPT':sanitize_rich_html(q.get('content_html') or q.get('prompt','')),'EXPLANATION':sanitize_rich_html(q.get('explanation','')),'ANSWER':q.get('answer','A')}
    for rank,letter in enumerate('ABCDE'):
        values['OPTION_'+letter]=sanitize_rich_html(q.get('option_'+letter.lower(),''))
        values['ANSWER_'+letter+'_SELECTED']='selected' if q.get('answer','A')==letter else ''
        values['SCORE_'+letter]=str(q.get('score_'+letter.lower(),5-rank))
    if q.get('id') and score_profile_id:
        for row in data['stored_scores']:values['SCORE_'+row['option_key']]=str(row['score_value'])
    return values

def ensure_legacy_question_bank(conn,set_id,parent_bank_id=None):
    return _ensure_legacy_question_bank(conn,set_id,parent_bank_id)

def parent_bank_options(conn,set_id):
    selected,rows=parent_bank_data(conn,set_id)
    return ''.join(f'<option value="{x["id"]}" {"selected" if selected==x["id"] else ""}>{e(x["name"])}</option>' for x in rows)

def build_attempt_snapshot(conn,attempt_id,set_id,profile_id=None):
    source=conn.execute('SELECT duration_min FROM question_sets WHERE id=?',(set_id,)).fetchone()
    blueprint=conn.execute('SELECT * FROM exam_blueprints WHERE key=?',('set-'+str(set_id),)).fetchone()
    ordered=[]
    selected_counts={}
    if blueprint:
        profile_id=blueprint['profile_id']
        bank=conn.execute('SELECT id FROM question_banks WHERE legacy_question_set_id=?',(set_id,)).fetchone()
        rows=conn.execute('SELECT * FROM exam_blueprint_categories WHERE blueprint_id=? ORDER BY position,id',(blueprint['id'],)).fetchall()
        for row in rows:
            selected_counts[row['category_id']]=row['question_count']
            pool=conn.execute('SELECT q.* FROM question_bank_memberships m JOIN questions q ON q.id=m.question_id WHERE m.bank_id=? AND (q.category_id=? OR q.category_id IN (SELECT id FROM question_categories WHERE parent_id=?)) AND q.status=\'active\' ORDER BY m.position,q.position,q.id',(bank['id'] if bank else -1,row['category_id'],row['category_id'])).fetchall()
            if len(pool)<row['question_count']:raise ValueError('Jumlah soal dalam bank berubah; blueprint tidak lagi memenuhi kuota kategori.')
            take=random.sample(pool,row['question_count']) if blueprint['selection_mode']=='random' else pool[:row['question_count']]
            ordered.extend((q,row['category_id'],i+1) for i,q in enumerate(take))
    else:
        pool=conn.execute('SELECT * FROM questions WHERE set_id=? AND status=\'active\' ORDER BY position,id',(set_id,)).fetchall()
        ordered=[(q,q['category_id'],i+1) for i,q in enumerate(pool)]
    if not ordered:raise ValueError('Belum ada soal aktif untuk sesi tryout ini.')
    max_total=0;breakdown={};category_rule_snapshot={}
    for position,(q,category_id,category_position) in enumerate(ordered,1):
        opts={letter:q['option_'+letter.lower()] for letter in 'ABCDE' if q['option_'+letter.lower()]}
        score_row=conn.execute('''SELECT r.* FROM category_scoring_rules r WHERE r.profile_id=? AND r.category_id IN (?,(SELECT parent_id FROM question_categories WHERE id=?)) ORDER BY (r.category_id=?) DESC LIMIT 1''',(profile_id,category_id,category_id,category_id)).fetchone() if profile_id and category_id else None
        scoring={'mode':score_row['scoring_mode'] if score_row else 'correctness','correct_score':score_row['correct_score'] if score_row else 1,'incorrect_score':score_row['incorrect_score'] if score_row else 0,'blank_score':score_row['blank_score'] if score_row else 0,'passing_score':score_row['passing_score'] if score_row else None,'max_score':(score_row['max_score']/max(score_row['item_count'],1)) if score_row else 1,'option_scores':{}}
        if score_row and category_id:
            category_name=conn.execute('SELECT name FROM question_categories WHERE id=?',(category_id,)).fetchone()
            category_rule_snapshot[str(category_id)]={'name':category_name['name'] if category_name else 'Kategori','passing_score':score_row['passing_score'],'item_count':score_row['item_count'],'selected_count':selected_counts.get(category_id,score_row['item_count'])}
        if score_row and score_row['scoring_mode']=='option_points':
            scoring['option_scores']={r['option_key']:r['score_value'] for r in conn.execute('SELECT o.option_key,os.score_value FROM question_options o JOIN question_option_scores os ON os.option_id=o.id WHERE o.question_id=? AND os.profile_id=?',(q['id'],profile_id)).fetchall()}
            if not set(opts).issubset(scoring['option_scores']):
                raise ValueError(f'Bobot TKP belum lengkap untuk profil yang dipilih pada soal #{q["id"]}. Lengkapi bobot opsi soal tersebut sebelum memulai sesi.')
        snap={'prompt':q['content_html'] or q['prompt'],'explanation':q['explanation'],'answer':q['answer']}
        conn.execute('INSERT INTO attempt_questions(attempt_id,question_id,category_id,position,category_position,question_snapshot,options_snapshot,scoring_snapshot,question_version) VALUES (?,?,?,?,?,?,?,?,?)',(attempt_id,q['id'],category_id,position,category_position,json.dumps(snap,ensure_ascii=False),json.dumps(opts,ensure_ascii=False),json.dumps(scoring,ensure_ascii=False),q['version']))
        max_total+=scoring['max_score'];key=str(category_id or 'lainnya');breakdown.setdefault(key,{'count':0,'max_score':0});breakdown[key]['count']+=1;breakdown[key]['max_score']+=scoring['max_score']
    thresholds=[{'key':r['threshold_key'],'label':r['label'],'minimum_score':r['minimum_score'],'category_id':r['category_id']} for r in conn.execute('SELECT threshold_key,label,minimum_score,category_id FROM exam_rule_thresholds WHERE profile_id=? ORDER BY category_id,threshold_key',(profile_id,)).fetchall()] if profile_id else []
    profile_meta=conn.execute('SELECT name,total_questions,max_score FROM exam_rule_profiles WHERE id=?',(profile_id,)).fetchone() if profile_id else None
    profile_snapshot={'name':profile_meta['name'],'total_questions':profile_meta['total_questions'],'max_score':profile_meta['max_score']} if profile_meta else None
    conn.execute('UPDATE attempts SET blueprint_id=?,rule_profile_id=?,rule_snapshot=?,total=? WHERE id=?',(blueprint['id'] if blueprint else None,profile_id,json.dumps({'duration_min':(blueprint['duration_min'] or (source['duration_min'] if source else 0)) if blueprint else (source['duration_min'] if source else 0),'selection_mode':blueprint['selection_mode'] if blueprint else 'manual','profile':profile_snapshot,'categories':category_rule_snapshot,'thresholds':thresholds},ensure_ascii=False),round(max_total),attempt_id))
    return len(ordered)

def attempt_seconds_remaining(conn,attempt):
    rule=json.loads(attempt['rule_snapshot'] or '{}')
    duration=rule.get('duration_min')
    if not duration:
        row=conn.execute('SELECT duration_min FROM question_sets WHERE id=?',(attempt['set_id'],)).fetchone()
        duration=row['duration_min'] if row else 0
    try:started=datetime.strptime(attempt['started_at'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    except (TypeError,ValueError):return max(0,int(duration or 0)*60)
    elapsed=int((datetime.now(timezone.utc)-started).total_seconds())
    return max(0,int(duration or 0)*60-elapsed)
