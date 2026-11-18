"""县级批次归属：按公告引用的整组范围页判定，解除通知按生效日适用。"""
from .ledger import entities
from .domain import map_editions,edition_status

def batches(connection, collection):
    return [dict(row['payload'], source=row['source'])
            for row in entities(connection, collection) if row['type']=='trade_batch']

def _current_notice(rows):
    notices=[r for r in rows if r['type']=='health_notice' and 'map_revision' in r['payload']]
    return max(notices,key=lambda r:r['version']) if notices else None

def _current_edition(rows,map_revision):
    """公告引用 map_revision 的最新一组范围页；缺页时不能用其他版次补齐。"""
    editions=map_editions(rows,map_revision)
    if not editions:return []
    return editions[max(editions)]

def _pending_release_sources(connection,collection):
    """来源目录已列出但正文尚未取得的解除文书；不能据此宣布解除。"""
    if connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collection_sources'").fetchone() is None:
        return []
    return [row[0] for row in connection.execute(
        'SELECT s.source_url FROM collection_sources s WHERE s.collection=? AND s.source_kind=? '
        'AND NOT EXISTS (SELECT 1 FROM collection_progress p '
        'WHERE p.collection=s.collection AND p.source_url=s.source_url) ORDER BY s.source_url',
        (collection,'release_notice'))]

def restrictions(connection, collection):
    rows=entities(connection,collection)
    notice=_current_notice(rows)
    if notice is None:return []
    n=notice['payload']
    edition=_current_edition(rows,n['map_revision'])
    status=edition_status(edition)
    townships=sorted({t for r in edition for t in r['payload'].get('townships',[])})
    releases=[r for r in rows if r['type']=='release_notice' and r['payload'].get('notice_no')==n['notice_no']]
    pending=_pending_release_sources(connection,collection)
    map_pages=[dict(page=r['payload'].get('page'),version=r['version'],source=r['source'])
               for r in sorted(edition,key=lambda r:(r['payload'].get('page') is None,r['payload'].get('page') or 0))]
    result=[]
    for b in batches(connection,collection):
        evidence=dict(batch=b['batch_no'],notice=n['notice_no'],notice_version=notice['version'],
                      map_revision=n['map_revision'],map_complete=status['complete'],
                      pages_expected=status['expected'],map_pages=map_pages,
                      missing_pages=status['missing'])
        sources=[notice['source']]+[p['source'] for p in map_pages]+[b['source']]
        if b['county']!=n['county']:
            state='范围外'
        elif b['township'] in townships:
            if b['ship_on']>=n['effective_from']:
                applied=[r for r in releases
                         if b['township'] in r['payload'].get('townships',[])
                         and b['ship_on']>=r['payload']['released_on']]
                if applied:
                    state='解除'
                    evidence['released_by']=[dict(id=r['id'],version=r['version'],
                                                  released_on=r['payload']['released_on'],source=r['source'])
                                             for r in applied]
                    sources+=[r['source'] for r in applied]
                else:
                    state='受限'
                    if pending:evidence['pending_release_sources']=pending
            else:
                state='范围外'
        elif not status['complete']:
            state='待核'
        else:
            state='范围外'
        evidence['state']=state
        evidence['sources']=list(dict.fromkeys(sources))
        result.append(evidence)
    return result
