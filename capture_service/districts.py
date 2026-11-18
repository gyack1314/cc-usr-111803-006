"""单张已完整范围图下的县级批次归属。"""
from .ledger import entities

def batches(connection, collection):
    return [dict(row['payload'], source=row['source'])
            for row in entities(connection, collection) if row['type']=='trade_batch']

def restrictions(connection, collection):
    rows=entities(connection,collection)
    notices=[r for r in rows if r['type']=='health_notice' and 'map_revision' in r['payload']]
    if not notices:return []
    notice=max(notices,key=lambda r:r['version'])
    n=notice['payload']
    maps=[r for r in rows if r['type']=='area_map' and r['payload'].get('map_revision')==n['map_revision']]
    if not maps:return [dict(batch=b['batch_no'],state='待核',sources=[notice['source']]) for b in batches(connection,collection)]
    area=max(maps,key=lambda r:r['version'])
    a=area['payload']
    complete=a['pages_expected']==a['pages_received']
    result=[]
    for b in batches(connection,collection):
        inside=b['county']==n['county'] and b['township'] in a.get('townships',[])
        state='待核' if not complete else ('受限' if inside and b['ship_on']>=n['effective_from'] else '范围外')
        result.append(dict(batch=b['batch_no'],state=state,notice=n['notice_no'],
                           map_revision=n['map_revision'],sources=[notice['source'],area['source'],b['source']]))
    return result
