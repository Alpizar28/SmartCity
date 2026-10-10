import io
import zipfile
from types import SimpleNamespace

import pandas as pd
import pytest

from download import Downloader, BudgetExceeded
from integrate import join_coverage, unambiguous, distance_m
from quality import number, profile, temporal, valid_coordinates
from readers import complete_zip_members, madrid_long


class Raw(io.BytesIO):
    def read(self, n=-1, decode_content=False):
        return super().read(n)


class Response:
    def __init__(self,body,status=200):
        self.status_code=status;self.raw=Raw(body);self.url='https://example.test/data'
        self.headers={'Content-Length':str(len(body)),'Content-Type':'text/plain'}
    def __enter__(self):return self
    def __exit__(self,*args):return False


def test_budget_includes_failed_responses_and_restarts(tmp_path,monkeypatch):
    d=Downloader(tmp_path,budget=10)
    monkeypatch.setattr(d.session,'get',lambda *a,**k:Response(b'forbidden',403))
    assert d.fetch('fail','s','https://example.test/data',10) is None
    assert d.used==9
    d=Downloader(tmp_path,budget=10)
    monkeypatch.setattr(d.session,'get',lambda *a,**k:Response(b'12345'))
    with pytest.raises(BudgetExceeded):d.fetch('ok','s','https://example.test/data',5)
    assert (tmp_path/d.records()[-1]['path']).read_bytes()==b'1' and d.used==10
    with pytest.raises(BudgetExceeded):d.fetch('next','s','https://example.test/next',1)


def test_range_ignored_is_capped_not_complete(tmp_path,monkeypatch):
    d=Downloader(tmp_path)
    monkeypatch.setattr(d.session,'get',lambda *a,**k:Response(b'abcdef'))
    p=d.fetch('prefix','s','https://example.test/data',3,range_header='bytes=0-2')
    assert p.read_bytes()==b'abc'
    assert d.records()[0]['complete_response']=='False'


def test_403_no_retry(tmp_path,monkeypatch):
    d=Downloader(tmp_path);calls=[]
    def get(*a,**kw):calls.append(1);return Response(b'no',403)
    monkeypatch.setattr(d.session,'get',get)
    d.fetch('no','s','https://example.test/no',10,retries=2)
    assert len(calls)==1


def test_503_backoff_retry(tmp_path,monkeypatch):
    d=Downloader(tmp_path);responses=iter([Response(b'busy',503),Response(b'ok')]);wait=[]
    monkeypatch.setattr(d.session,'get',lambda *a,**k:next(responses))
    monkeypatch.setattr('download.time.sleep',lambda n:wait.append(n))
    assert d.fetch('retry','s','https://example.test/r',10).read_bytes()==b'ok'
    assert wait==[2] and d.used==6


def test_complete_zip_members_crc_and_truncation(tmp_path):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('a.csv','x,y\n1,2\n')
        z.writestr('b.csv','x,y\n3,4\n')
    b=data.getvalue();second=b.index(b'PK\x03\x04',4)
    p=tmp_path/'prefix';p.write_bytes(b[:second+35])
    result=complete_zip_members(p,tmp_path/'out')
    assert len(result)==1 and (tmp_path/'out/a.csv').read_text()=='x,y\n1,2\n'
    p.write_bytes(b)
    assert len(complete_zip_members(p,tmp_path/'out'))==2


def test_unsafe_zip_path_rejected(tmp_path):
    p=tmp_path/'z'
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('../unsafe.csv','x')
    with pytest.raises(ValueError):complete_zip_members(p,tmp_path/'out')


def test_corrupt_crc_rejected(tmp_path):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('a.csv','x,y\n1,2\n')
    b=bytearray(data.getvalue());b[14:18]=b'\x00'*4
    p=tmp_path/'bad';p.write_bytes(b)
    with pytest.raises(ValueError,match='CRC'):complete_zip_members(p,tmp_path/'out')


def test_transport_failure_counted_and_not_returned_as_valid(tmp_path,monkeypatch):
    from urllib3.exceptions import ReadTimeoutError
    class TimeoutRaw:
        def __init__(self):self.calls=0
        def read(self,n,decode_content=False):
            self.calls+=1
            if self.calls==1:return b'part'
            raise ReadTimeoutError(None,None,'test timeout')
    d=Downloader(tmp_path);r=Response(b'not complete');r.raw=TimeoutRaw()
    monkeypatch.setattr(d.session,'get',lambda *a,**k:r)
    assert d.fetch('timeout','s','https://example.test/data',100,retries=1) is None
    assert d.used==4 and d.records()[0]['error'] and d.records()[0]['complete_response']=='False'


def test_number_nulls_decimal_zero():
    n=number(pd.Series(['1,5','0','Null','-1']))
    assert n.iloc[0]==1.5 and n.iloc[1]==0 and pd.isna(n.iloc[2]) and n.iloc[3]==-1


def test_profile_missing_attributes_duplicates():
    d=pd.DataFrame({'id':['a','a','b'],'value':['0',None,'3']})
    out=profile(d,'s',['id'])
    assert out['duplicate_key_rows']==1
    assert out['attributes'][1]['null_count']==1


def test_madrid_hour24_endpoint_not_previous_day():
    d={'ANO':['2025'],'MES':['1'],'DIA':['31'],'ESTACION':['4'],'MAGNITUD':['8']}
    for h in range(1,25):d[f'H{h:02d}']=['0'];d[f'V{h:02d}']=['V']
    x=madrid_long(pd.DataFrame(d),'MAD-AIR')
    assert len(x)==24 and x['time'].max()==pd.Timestamp('2025-02-01')
    assert x['value'].sum()==0


def test_temporal_gaps_and_duplicates():
    d=pd.DataFrame({'entity':['a']*3,'variable':['x']*3,
        'time':pd.to_datetime(['2023-01-01 00:00','2023-01-01 02:00','2023-01-01 02:00']),
        'quality':['valid']*3,'value':[1,2,2]})
    r=temporal(d,60).iloc[0]
    assert r.duplicate_time_rows==1 and r.missing_slots_between_endpoints==1 and r.max_gap_minutes==120


def test_no_cartesian_join_allowed():
    l=pd.DataFrame({'zone':['x','x'],'v':[1,2]});r=pd.DataFrame({'zone':['x'],'w':[3]})
    with pytest.raises(ValueError):join_coverage(l,r,['zone'],'test')


def test_join_denominator_and_unmatched():
    l=pd.DataFrame({'zone':['a','b'],'v':[1,2]});r=pd.DataFrame({'zone':['b','c'],'w':[3,4]})
    j,c=join_coverage(l,r,['zone'],'test')
    assert len(j)==1 and c['left_match_pct']==50 and c['left_unmatched']==1 and c['right_unmatched']==1


def test_conflicts_not_summed_and_identical_deduplicated():
    d=pd.DataFrame({'entity':['a','a','b','b'],'variable':['x']*4,'time':[pd.Timestamp('2023-01-01')]*4,
                    'value':[1,2,3,3],'quality':['valid']*4})
    x,stats=unambiguous(d)
    assert len(x)==1 and x.iloc[0].entity=='b' and stats['ambiguous_rows_excluded_from_join_not_deleted']==2


def test_coordinates_and_proximity():
    assert distance_m(40,-3,40,-3)==0
    assert valid_coordinates(pd.Series([40,999]),pd.Series([-3,-3])).tolist()==[True,False]


def test_fall_dst_utc_identity_preserved():
    # Same NYC01:00wall clock, two distinct actual UTC observation timestamps.
    utc=pd.to_datetime(['2023-11-05 05:00Z','2023-11-05 06:00Z'],utc=True)
    df=pd.DataFrame({'entity':['site']*2,'variable':['PM25']*2,'time':utc,
                     'value':[18.6,19.5],'quality':['valid']*2})
    selected,stats=unambiguous(df)
    assert len(selected)==2 and stats['ambiguous_rows_excluded_from_join_not_deleted']==0
    assert utc.tz_convert('America/New_York').tz_localize(None).duplicated().sum()==1
