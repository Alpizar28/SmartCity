"""Budgeted, sequential HTTP acquisition; no private services or credentials."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import html
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from urllib3.exceptions import HTTPError as UrllibError

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['id', 'source', 'level', 'url', 'final_url', 'retrieved_at_utc', 'status',
          'bytes_downloaded', 'sha256', 'path', 'complete_response', 'content_type',
          'content_length', 'content_range', 'etag', 'last_modified', 'period',
          'version', 'attempt', 'error']


class BudgetExceeded(RuntimeError):
    pass


class Downloader:
    def __init__(self, root=ROOT, budget=1_000_000_000):
        self.root = Path(root)
        self.budget = budget
        self.raw = self.root / 'raw'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / '02_download_manifest.csv'
        self.used = sum(int(r['bytes_downloaded']) for r in self.records())
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SmartCityAcademicAudit/2.0',
                                     'Accept-Encoding': 'identity'})

    def records(self):
        if not self.manifest.exists():
            return []
        with self.manifest.open(newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def fetch(self, name, source, url, cap, *, level='A', period='', version='',
              params=None, range_header=None, retries=2, reuse=True):
        prepared = requests.Request('GET', url, params=params).prepare().url
        if reuse:
            for old in reversed(self.records()):
                if old['id'] == name and old['url'] == prepared and old['status'] in ('200', '206') and not old['error'] and (old['complete_response']=='True' or int(old['bytes_downloaded'])==cap):
                    p = self.root / old['path']
                    if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == old['sha256']:
                        return p
        for attempt in range(1, retries + 1):
            if self.used >= self.budget:
                raise BudgetExceeded('1 GB cumulative budget exhausted; authorization required')
            cap_now = min(cap, self.budget - self.used)
            filename = self.raw / f'{name}.record{len(self.records())+1}.bin'
            record = dict.fromkeys(FIELDS, '')
            record.update(id=name, source=source, level=level, url=prepared,
                          retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                          period=period, version=version, attempt=attempt,
                          path=str(filename.relative_to(self.root)))
            read = 0
            digest = hashlib.sha256()
            complete = False
            wait = 2 ** attempt
            status = None
            try:
                headers = {'Range': range_header} if range_header else {}
                with self.session.get(url, params=params, headers=headers,
                                      timeout=(15, 90), stream=True) as r:
                    status = r.status_code
                    record.update(status=status, final_url=r.url,
                                  content_type=r.headers.get('Content-Type', ''),
                                  content_length=r.headers.get('Content-Length', ''),
                                  content_range=r.headers.get('Content-Range', ''),
                                  etag=r.headers.get('ETag', ''),
                                  last_modified=r.headers.get('Last-Modified', ''))
                    # Count entity bytes actually consumed, including failures/retries.
                    # identity encoding avoids unbounded automatic decompression.
                    with filename.open('wb') as out:
                        while read < cap_now:
                            chunk = r.raw.read(min(65536, cap_now-read), decode_content=False)
                            if not chunk:
                                complete = True
                                break
                            out.write(chunk)
                            digest.update(chunk)
                            read += len(chunk)
                        if record['content_length'] and read == int(record['content_length']):
                            complete = True
                    if status >= 400:
                        record['error'] = f'HTTP {status}'
                    if status == 429:
                        try:
                            wait = min(120, max(wait, float(r.headers.get('Retry-After', wait))))
                        except ValueError:
                            wait = 60
            except (requests.RequestException, UrllibError, OSError) as exc:
                record['error'] = str(exc)
            finally:
                self.used += read
                record.update(bytes_downloaded=read, sha256=digest.hexdigest(),
                              complete_response=complete)
                fresh = not self.manifest.exists()
                with self.manifest.open('a', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=FIELDS)
                    if fresh:
                        writer.writeheader()
                    writer.writerow(record)
                logging.info('%s HTTP=%s bytes=%s complete=%s total=%s error=%s',
                             name, status, read, complete, self.used, record['error'])
            if status in (200, 206) and not record['error']:
                if not complete and cap_now < cap:
                    raise BudgetExceeded('Response truncated by cumulative budget; not a valid requested sample')
                return filename
            # 403/401/404 are not retried or worked around.
            if status not in (None, 429, 500, 502, 503, 504) or attempt == retries:
                return None
            time.sleep(wait)
        return None


def phase1_urls():
    with (ROOT / '01_http_evidence.csv').open(encoding='utf-8') as f:
        return {r['probe_id']: r['requested_url'] for r in csv.DictReader(f)}


def initial(d):
    urls = phase1_urls()
    for probe, source, size in [('M07','MAD-AIR',20166384), ('M17','MAD-METEO',15267750),
                               ('M16','MAD-TRAFFIC-META',714026), ('M08','MAD-ENERGY',10055231),
                               ('M18','MAD-CRASH',6595925)]:
        d.fetch(source+'-access', source, urls[probe], 8192, range_header='bytes=0-8191')
        d.fetch(source+'-file', source, urls[probe], size+1024, level='C',
                range_header=f'bytes=0-{size-1}', period='2025' if probe in ('M07','M17') else 'resource as published',
                version=probe)
        time.sleep(1)
    for probe in ('M15','M23','M24','M03','M25','L11','L03','L01','L08','N01','N03','N12'):
        d.fetch(probe+'-refresh', probe, urls[probe], 2_000_000,
                version='phase1 URL revalidated', retries=1)
    d.fetch('EPA-access', 'NYC-AIR', urls['N10'], 8192, range_header='bytes=0-8191')
    # National EPA archive is acquired by verified bounded ranges in a separate stage.
    d.fetch('LCL-access', 'LON-ENERGY', urls['L06'], 4096, range_header='bytes=0-4095')
    # Four complete local ZIP members expected; not an integrity-checked whole archive.
    d.fetch('LCL-prefix', 'LON-ENERGY', urls['L06'], 20_000_000, level='C',
            period='member histories 2011-2014; analyze Jan/Jul2013 and expanded',
            version='partitioned LCL; first complete members, nonrandom household sample')
    for site in ['MY1','BL0','GN0','GR4','HK6']:
        for start,end in [('2013-01-01','2013-02-01'),('2013-07-01','2013-08-01')]:
            url = ('https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/'
                   f'SiteCode={site}/SpeciesCode=NO2/StartDate={start}/EndDate={end}/Json')
            d.fetch(f'LAQN-{site}-{start}', 'LON-AIR', url, 1_000_000, level='B',
                    period=f'{start} <= t < {end}', version='NO2 hourly GMT')
            time.sleep(1)


def nyc(d):
    base = 'https://data.cityofnewyork.us/resource/'
    jobs = [
        ('DOT-global', 'NYC-COUNTS', '7ym2-wayt', {'$select':'count(*) as n,min(yr) as first_year,max(yr) as last_year'}),
        ('DOT-years', 'NYC-COUNTS', '7ym2-wayt', {'$select':'yr,count(*) as n,count(distinct segmentid) as segments', '$group':'yr','$order':'yr','$limit':100}),
        ('DOT-2023-campaigns', 'NYC-COUNTS', '7ym2-wayt', {'$select':'m,d,boro,count(*) as n','$where':'yr=2023','$group':'m,d,boro','$order':'m,d,boro','$limit':3000}),
        ('LL84-granularity', 'NYC-ENERGY', '5zyy-y8am', {'$select':'report_year, count(*) as n', '$group':'report_year','$order':'report_year','$limit':20}),
    ]
    for name,source,ds,params in jobs:
        d.fetch(name,source,base+ds+'.json', 2_000_000,params=params,version='SODA aggregate')
        time.sleep(1)
    # Entire year of DOT is <100k rows in phase1: bounded pages, stable full ordering.
    order='yr,m,d,hh,mm,requestid,segmentid,direction,vol,wktgeom'
    for offset in range(0,100000,10000):
        p=d.fetch(f'DOT-2023-{offset}', 'NYC-COUNTS',base+'7ym2-wayt.json',8_000_000,level='C',
                  params={'$where':'yr=2023','$order':order,'$limit':10000,'$offset':offset},
                  period='2023',version='SODA ordered pages; live table, not transactional snapshot')
        if p is None or len(json.loads(p.read_text())) < 10000:
            break
        time.sleep(1)
    # Two calendar months, projected fields omit precise addresses/narratives.
    fields='unique_key,created_date,closed_date,agency,complaint_type,descriptor,status,borough,latitude,longitude'
    for month,end in [('2023-01-01','2023-02-01'),('2023-07-01','2023-08-01')]:
        where=f"created_date >= '{month}T00:00:00' AND created_date < '{end}T00:00:00'"
        d.fetch('311-count-'+month,'NYC-311',base+'erm2-nwe9.json',1_000_000,
                params={'$select':'count(*) as n,count(distinct unique_key) as unique_ids,min(created_date) as first_date,max(created_date) as last_date','$where':where},period=month,version='SODA aggregate')
        # Systematic one-day-in-seven sample: Jan/Jul1,8,15,22,29 (multiple weekdays vary by month).
        for day in [1,8,15,22,29]:
            start=month[:8]+f'{day:02d}'
            stop=month[:8]+f'{day+1:02d}'
            daywhere=f"created_date >= '{start}T00:00:00' AND created_date < '{stop}T00:00:00'"
            for offset in range(0,20000,5000):
                p=d.fetch(f'311-{start}-{offset}','NYC-311',base+'erm2-nwe9.json',5_000_000,level='B',
                          params={'$select':fields,'$where':daywhere,'$order':'created_date,unique_key','$limit':5000,'$offset':offset},
                          period=start,version='systematic day sample; projected privacy-minimized fields')
                if p is None or len(json.loads(p.read_text())) <5000:
                    break
                time.sleep(1)


def official(d):
    # All identifiers come from the phase1 catalog/search evidence, not guessed endpoints.
    for ds in ['212629-0-estaciones-control-aire','300360-0-meteorologicos-estaciones',
               '300352-0-meteorologicos-horarios','208627-0-transporte-ptomedida-historico']:
        url='https://datos.madrid.es/dataset/'+ds+'/downloads'
        p=d.fetch(ds+'-catalog','MAD-CATALOG',url,3_000_000,version='published download listing')
        if not p:
            continue
        text=p.read_text(errors='replace')
        links=list(dict.fromkeys(html.unescape(x) for x in re.findall(r'href="([^"]+)"',text)))
        for link in links:
            if not any(link.endswith(ext) for ext in ['.csv','.pdf','.zip']):
                continue
            if link.startswith('/'):
                link='https://datos.madrid.es'+link
            if ds.startswith(('212629','300360')) and link.endswith('.csv'):
                d.fetch(ds+'-inventory','MAD-STATION-META',link,5_000_000,level='B',version='current published inventory')
                break
            if ds.startswith('300352') and link.endswith('.pdf'):
                d.fetch('MAD-METEO-dictionary','MAD-METEO-DOC',link,2_000_000,version='official PDF')
                break
        if ds.startswith('208627'):
            # Two alternatives explicitly linked by official current catalog, bounded prefixes only.
            for i,link in enumerate([x for x in links if x.endswith('.zip')][:2]):
                if link.startswith('/'):
                    link='https://datos.madrid.es'+link
                d.fetch(f'MAD-TRAFFIC-official-{i}','MAD-TRAFFIC',link,8192,
                        range_header='bytes=0-8191',version='catalog alternative',retries=1)
    for name,url in [
        ('NYC-terms','https://opendata.cityofnewyork.us/overview/#termsofuse'),
        ('EPA-description','https://aqs.epa.gov/aqsweb/airdata/FileFormats.html'),
        ('EPA-disclaimer','https://www.epa.gov/web-policies-and-procedures/epa-disclaimers'),
        ('NYC-energy-search','https://api.us.socrata.com/api/catalog/v1?search_context=data.cityofnewyork.us&q=hourly%20energy&limit=5'),
        ('DfT2013','https://roadtraffic.dft.gov.uk/api/raw-counts?filter[region_id]=6&filter[year]=2013&page[size]=100'),
    ]:
        d.fetch(name,'OFFICIAL-DOC' if name!='DfT2013' else 'LON-COUNTS',url,2_000_000,
                version='official documentation/catalog or complementary mobility')
    # DOT metadata includes official XLSX attachments; small enough to inspect CRS declaration.
    p=next((d.root/r['path'] for r in reversed(d.records()) if r['id']=='N01-refresh' and r['status']=='200'),None)
    if p:
        for a in json.loads(p.read_text()).get('metadata',{}).get('attachments',[]):
            asset=a.get('assetId')
            if asset:
                url=f'https://data.cityofnewyork.us/api/assets/{asset}?download=true'
                d.fetch('DOT-attachment-'+asset,'NYC-COUNTS-DOC',url,5_000_000,version=a['filename'])


def epa(d):
    url=phase1_urls()['N10'];total=76998372
    records=[r for r in d.records() if r['id']=='EPA-2023' and int(r['bytes_downloaded'])>0]
    start=0;parts=[]
    if records:
        first=records[0];p=d.root/first['path']
        if p.exists() and first['content_range'].startswith('bytes 0-'):
            parts.append(p);start=p.stat().st_size
    for offset in range(start,total,1_048_576):
        end=min(total-1,offset+1_048_575)
        p=d.fetch(f'EPA-range-{offset}','NYC-AIR',url,end-offset+1,level='C',
                  range_header=f'bytes={offset}-{end}',period='2023 national',version='range assembly')
        if p is None or p.stat().st_size!=end-offset+1:
            raise RuntimeError(f'Incomplete EPA range {offset}; no valid archive declared')
        last=[r for r in d.records() if r['path']==str(p.relative_to(d.root))][-1]
        if last['content_range']!=f'bytes {offset}-{end}/{total}':
            raise RuntimeError('Server ignored or changed EPA range; refusing assembly')
        parts.append(p)
    target=d.raw/'EPA-2023-assembled.zip'
    with target.open('wb') as out:
        for p in parts:
            with p.open('rb') as f:
                while block:=f.read(65536):out.write(block)
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (d.root/'results/epa_assembly.json').write_text(json.dumps({'path':str(target.relative_to(d.root)),
        'bytes':target.stat().st_size,'sha256':digest,'parts':[str(p.relative_to(d.root)) for p in parts]},indent=2))


def madrid_traffic(d):
    # Exact January2025 URL discovered in the official catalog, shared with annual air/meteo.
    url=('https://datos.madrid.es/dataset/208627-0-transporte-ptomedida-historico/'
         'resource/208627-73-transporte-ptomedida-historico-zip/download/'
         '208627-73-transporte-ptomedida-historico-zip.zip')
    d.fetch('MAD-TRAFFIC-Jan2025-access','MAD-TRAFFIC',url,8192,
            range_header='bytes=0-8191',period='2025-01',version='official catalog resource73')
    d.fetch('MAD-TRAFFIC-Jan2025','MAD-TRAFFIC',url,120_000_000,level='C',
            period='2025-01',version='official catalog resource73')


def complements(d):
    # Add consecutive January6-12 days around observed DOT campaigns; January8 already acquired.
    base='https://data.cityofnewyork.us/resource/'
    fields='unique_key,created_date,closed_date,agency,complaint_type,descriptor,status,borough,latitude,longitude'
    for day in [6,7,9,10,11,12]:
        start=f'2023-01-{day:02d}';stop=f'2023-01-{day+1:02d}'
        for offset in range(0,20000,5000):
            p=d.fetch(f'311-{start}-{offset}','NYC-311',base+'erm2-nwe9.json',5_000_000,level='B',
                params={'$select':fields,'$where':f"created_date >= '{start}T00:00:00' AND created_date < '{stop}T00:00:00'",'$order':'created_date,unique_key','$limit':5000,'$offset':offset},
                period=start,version='campaign-targeted consecutive weekJan6-12; projected fields')
            if p is None or len(json.loads(p.read_text()))<5000:break
            time.sleep(1)
    d.fetch('LL84-sample','NYC-ENERGY',base+'5zyy-y8am.json',1_000_000,level='B',
        params={'$select':'report_year,property_id,parent_property_id,electricity_use_grid_purchase,electricity_use_grid_purchase_1,direct_ghg_emissions_metric,borough,latitude,longitude',
                '$where':'report_year=2023','$order':'property_id','$limit':200},
        period='report_year2023',version='200ordered properties; annual disclosure not representative of all buildings')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['initial','nyc','official','epa','madrid-traffic','complements'])
    parser.add_argument('--budget',type=int,default=1_000_000_000)
    args=parser.parse_args()
    if args.budget > 1_000_000_000:
        parser.error('Budget above user authorization')
    (ROOT/'results').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(),logging.FileHandler(ROOT/'results/download.log')])
    d=Downloader(budget=args.budget)
    {'initial':initial,'nyc':nyc,'official':official,'epa':epa,'madrid-traffic':madrid_traffic,'complements':complements}[args.stage](d)


if __name__=='__main__':
    main()
