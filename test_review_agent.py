import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, Optional, Dict, Any, Literal

BOOK = json.loads((Path(__file__).parent/'review_agent.ipynb').read_text(encoding='utf-8'))

@pytest.fixture
def ns():
    scope = dict(globals())
    scope.update(llm_analyzer=Mock(),llm_critic=Mock(),llm_supervisor=Mock())
    for i in [47,50,52,54,56,58,60,67,77,62]:
        exec(compile(''.join(BOOK['cells'][i]['source']),f'cell_{i}','exec'),scope)
    return scope

def good():
    return {'items':[{'aspect':'보습','label':1,'evidence':'촉촉해요'}]}

@pytest.mark.parametrize('value',['[]','null','true','0','bad','[1]'])
def test_parser_rejects_non_objects(ns,value):
    assert ns['parse_dict'](value,{}) == {}

@pytest.mark.parametrize('result',[
    None, [], {'items':None}, {'items':[None]}, {'items':[{}]},
    {'items':[{'aspect':None,'label':1,'evidence':'촉촉해요'}]},
    {'items':[{'aspect':'배송','label':1,'evidence':'촉촉해요'}]},
    {'items':[{'aspect':'보습','label':True,'evidence':'촉촉해요'}]},
    {'items':[{'aspect':'보습','label':'1','evidence':'촉촉해요'}]},
    {'items':[{'aspect':'보습','label':1,'evidence':'새로 만든 문구'}]},
    {'items':[{'aspect':'보습','label':1,'evidence':''}]},
    {'items':good()['items']*2},
])
def test_invalid_analysis_routes_to_revision_without_paid_critic(ns,result):
    out=ns['critic_node']({'review':'촉촉해요','analyzer_result':result})
    assert out['critic_result']['verdict']=='Revise'
    ns['llm_critic'].invoke.assert_not_called()

def test_malformed_critic_is_not_index_error(ns):
    ns['llm_critic'].invoke.return_value=SimpleNamespace(content='형식 없는 응답')
    out=ns['critic_node']({'review':'촉촉해요','analyzer_result':good()})
    assert out['critic_result']['reason_code']=='OUTPUT_ERROR'

def test_human_commands_are_atomic(ns):
    original=good(); before=copy.deepcopy(original)
    with pytest.raises(ValueError):
        ns['apply_human_commands'](original,'수정:1:향:0;잘못된명령','촉촉해요')
    assert original==before

@pytest.mark.parametrize('command',['','삭제:1;삭제:1','수정:1:배송:1','추가:향:3:촉촉해요','추가:향:1:없는근거'])
def test_invalid_human_commands_rejected(ns,command):
    with pytest.raises(ValueError):
        ns['apply_human_commands'](good(),command,'촉촉해요')

def test_human_edit_can_correct_evidence(ns):
    out=ns['apply_human_commands'](good(),'수정:1:가격:0:가격이 비싸요','촉촉해요. 가격이 비싸요')
    assert out['items'][0]=={'aspect':'가격','label':0,'evidence':'가격이 비싸요'}

def test_invalid_human_input_not_approved(ns,monkeypatch):
    commands=iter(['잘못된명령','보류'])
    monkeypatch.setattr('builtins.input',lambda _:next(commands))
    out=ns['human_node']({'review':'촉촉해요','analyzer_result':good()})
    assert out['review_status']=='needs_review'
    assert out['human_result'] is None
    assert 'critic_result' not in out

def test_human_explicit_approval(ns,monkeypatch):
    monkeypatch.setattr('builtins.input',lambda _:'승인')
    out=ns['human_node']({'review':'촉촉해요','analyzer_result':good()})
    assert out['review_status']=='human_approved'

def test_graph_normal_flow(ns):
    ns['llm_analyzer'].invoke.return_value=SimpleNamespace(content=json.dumps(good(),ensure_ascii=False))
    ns['llm_critic'].invoke.return_value=SimpleNamespace(content='[VERDICT]\nConformity\n[REASON]\n원문과 일치함')
    out=ns['app'].invoke({'review':'촉촉해요','human_interactive':False})
    assert out['next_agent']=='end' and out['reason_code']=='OK'
    assert ns['llm_analyzer'].invoke.call_count==1
    ns['llm_supervisor'].invoke.assert_not_called()

def test_graph_retry_limit_and_pending_do_not_block_on_input(ns,monkeypatch):
    monkeypatch.setattr('builtins.input',lambda _:pytest.fail('배치에서 입력 호출 금지'))
    ns['llm_analyzer'].invoke.return_value=SimpleNamespace(content='[]')
    out=ns['app'].invoke({'review':'촉촉해요','human_interactive':False,'max_retries':3,'retry_count':0})
    assert out['review_status']=='needs_review'
    assert ns['llm_analyzer'].invoke.call_count==4
    ns['llm_critic'].invoke.assert_not_called()

def test_tail_batch_is_processed(ns,tmp_path):
    path=tmp_path/'data.csv'
    pd.DataFrame({'review':['촉촉해요']*13}).to_csv(path,index=False)
    ns['app']=Mock()
    ns['app'].invoke.return_value={'analyzer_result':good(),'critic_result':{'verdict':'Conformity'}}
    counts=ns['run_batch_analysis'](path,10)
    out=pd.read_csv(path)
    assert counts['completed']==13 and ns['app'].invoke.call_count==13
    assert out['status'].eq('completed').all()
    assert out['evidence'].notna().all() and out['processed_at'].notna().all()
    assert ns['run_batch_analysis'](path,10)['completed']==0

def test_batch_errors_and_pending_not_reported_as_completed(ns,tmp_path):
    path=tmp_path/'data.csv'
    pd.DataFrame({'review':['촉촉해요']*2}).to_csv(path,index=False)
    ns['app']=Mock(); ns['app'].invoke.side_effect=[{'review_status':'needs_review'},RuntimeError('fake failure')]
    counts=ns['run_batch_analysis'](path,10)
    assert counts=={'completed':0,'no_aspects':0,'needs_review':1,'error':1}

@pytest.mark.parametrize('result',[None,[],{'analyzer_result':[]},{'analyzer_result':{'items':[None]}},
    {'analyzer_result':{'items':[{'aspect':1,'label':1,'evidence':'x'}]}},
    {'analyzer_result':{'items':[{'aspect':'보습','label':True,'evidence':'x'}]}}])
def test_format_evaluator_total_function(ns,result):
    assert ns['score_and_reason'](result)[0]==0

def test_format_is_not_sentiment_accuracy(ns):
    result={'analyzer_result':good(),'critic_result':{'verdict':'Revise'}}
    assert ns['score_and_reason'](result)[0]==1

def dashboard_scope():
    code=(Path(__file__).parent/'app.py').read_text(encoding='utf-8')
    parsed=ast.parse(code)
    subset=ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['safe_load_json_list','make_long_df']],type_ignores=[])
    scope={'pd':pd,'json':json,'ALLOWED_ASPECTS':{'보습','가격','향','포장'}}
    exec(compile(subset,'dashboard','exec'),scope)
    return scope

@pytest.mark.parametrize('value',['{}','1','"text"','ERROR_SKIP','NaN'])
def test_dashboard_parser_only_lists(value):
    assert dashboard_scope()['safe_load_json_list'](value)==[]

def test_dashboard_counts_aspects_not_reviews():
    scope=dashboard_scope()
    df=pd.DataFrame([{'review':'촉촉하지만 비싸요','aspect':'["보습","가격"]','label':'[1,0]','processed_at':'실제 저장 시각'},
                     {'review':'미검토','aspect':'["향"]','label':'[1]','status':'needs_review'},
                     {'review':'손상','aspect':'["향","가격"]','label':'[1]'}])
    out=scope['make_long_df'](df)
    assert len(out)==2 and out['review'].nunique()==1
    assert (out['processed_at']=='실제 저장 시각').all()

def test_safe_notebook_and_dashboard_source():
    assert all(not c.get('outputs') for c in BOOK['cells'])
    assert 'df[\'aspect\'] = np.nan' not in ''.join(BOOK['cells'][75]['source'])
    source=(Path(__file__).parent/'app.py').read_text(encoding='utf-8')
    assert 'Timestamp.now()' not in source
    assert 'regex=False' in source and 'hue_order=[1, 0]' in source
    for i,c in enumerate(BOOK['cells']):
        if c['cell_type']=='code':
            text=''.join(c['source'])
            if text.startswith('%%writefile'):
                text=text.split('\n',1)[1]
            if not any(line.lstrip().startswith(('!','%')) for line in text.splitlines()):
                ast.parse(text,filename=f'cell_{i}')
