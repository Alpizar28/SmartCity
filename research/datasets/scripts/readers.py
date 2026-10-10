"""Read source formats in chunks; preserve originals and verify complete ZIP members."""
import io
import struct
import zlib
import hashlib
from pathlib import Path

import pandas as pd

from quality import number


def complete_zip_members(path, output, max_uncompressed=70_000_000):
    """Extract complete deflated local members from a capped ZIP response.

    Does not pretend that a prefix contains a ZIP central directory. Refuses encryption,
    descriptors, unsafe paths, ZIP64 and excessive expansion. CRC+length each member.
    """
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    members=[]
    with Path(path).open('rb') as f:
        while True:
            pos=f.tell();head=f.read(30)
            if len(head)<30 or head[:4]!=b'PK\x03\x04':
                break
            _,version,flags,method,_,_,crc,compressed,size,nlen,xlen=struct.unpack('<IHHHHHIIIHH',head)
            name=f.read(nlen).decode('utf-8');f.read(xlen)
            if flags & 9 or method!=8 or size>max_uncompressed or compressed==0xFFFFFFFF:
                raise ValueError('Unsupported or excessive ZIP member')
            if '..' in Path(name).parts or Path(name).is_absolute():
                raise ValueError('Unsafe ZIP path')
            payload=f.read(compressed)
            if len(payload)!=compressed:
                break  # Last truncated member is not analyzed.
            decoder=zlib.decompressobj(-15)
            data=decoder.decompress(payload,max_uncompressed+1)
            if len(data)!=size or not decoder.eof or zlib.crc32(data)&0xffffffff!=crc:
                raise ValueError('ZIP member length/CRC failed')
            target=output/Path(name).name
            if not target.exists():
                target.write_bytes(data)
            members.append({'name':name,'offset':pos,'compressed_bytes':compressed,'uncompressed_bytes':size,
                            'crc32':crc,'sha256':hashlib.sha256(data).hexdigest(),'path':str(target)})
    return members


def madrid_long(df, source):
    base=df.copy()
    date=pd.to_datetime(dict(year=number(base['ANO']),month=number(base['MES']),day=number(base['DIA'])),errors='coerce')
    result=[]
    units_air={'1':'ug/m3','6':'mg/m3','7':'ug/m3','8':'ug/m3','9':'ug/m3','10':'ug/m3','12':'ug/m3','14':'ug/m3',
               '20':'ug/m3','30':'ug/m3','35':'ug/m3','37':'ug/m3','38':'ug/m3','39':'ug/m3','42':'mg/m3','43':'mg/m3','44':'mg/m3','431':'mg/m3'}
    # Meteo units documented separately in official dictionary, not air code mapping.
    units_meteo={'81':'m/s','82':'degrees','83':'degC','86':'percent','87':'hPa','88':'W/m2','89':'mm'}
    for h in range(1,25):
        x=pd.DataFrame({'entity':base['ESTACION'].astype(str),'variable':base['MAGNITUD'].astype(str),
                        'time':date+pd.Timedelta(hours=h), 'value':number(base[f'H{h:02d}']),
                        'quality':base[f'V{h:02d}'].map({'V':'valid','N':'invalid'}).fillna('unknown'),
                        'zone':'Madrid','lat':float('nan'),'lon':float('nan')})
        x['unit']=x['variable'].map(units_air if source=='MAD-AIR' else units_meteo).fillna('unverified')
        x['source']=source
        x['entity']=source+':'+x['entity']
        result.append(x)
    return pd.concat(result,ignore_index=True)


def empty_geo(df):
    for col in ['lat','lon']:
        if col not in df:
            df[col]=float('nan')
    return df
