"""解析来源身份及本项目公开资料字段。"""
import json
from pathlib import Path
CONTRACT=json.loads((Path(__file__).resolve().parents[1]/'docs'/'source-contract.json').read_text(encoding='utf-8'))
def decode(raw,receipt):
    doc=json.loads(raw.decode('utf-8'))
    if not all(k in doc for k in ('kind','id','revision')): raise ValueError('资料身份缺失')
    kind=doc['kind']
    if kind not in CONTRACT['roles']: raise ValueError('未知来源类型')
    if any(k not in doc for k in CONTRACT['required_fields'][kind]): raise ValueError('来源业务字段缺失')
    return [{'type':kind,'id':doc['id'],'version':doc['revision'],'payload':{k:v for k,v in doc.items() if k not in ('kind','id','revision')}}]

def map_editions(rows,map_revision):
    """同一 map_revision 的范围页按来源版次分组；其他版次不能填入本组缺页。"""
    editions={}
    for r in rows:
        if r['type']=='area_map' and r['payload'].get('map_revision')==map_revision:
            editions.setdefault(r['version'],[]).append(r)
    return editions

def edition_status(pages):
    """一组范围页的完整性：页码 1..pages_expected 齐备才算完整。

    单份响应上的 pages_received 只说明该响应含几页，不能单独证明整组完整；
    无页码的响应按各响应页数求和估计。
    """
    expected=max((int(r['payload'].get('pages_expected') or 0) for r in pages),default=0)
    numbered=sorted({int(r['payload']['page']) for r in pages if r['payload'].get('page') is not None})
    if numbered:
        received=len(numbered)
        missing=[i for i in range(1,expected+1) if i not in numbered]
    else:
        received=sum(int(r['payload'].get('pages_received') or 0) for r in pages)
        missing=[]
    return {'expected':expected,'received':received,'pages':numbered,'missing':missing,
            'complete':expected>0 and received>=expected and not missing}

def assess(rows):
    """按当前双来源契约核对候选关联；范围图按整组页码判定完整。"""
    left=sorted((r for r in rows if r['type']==CONTRACT['roles'][0]),key=lambda r:r['version'])
    maps=[r for r in rows if r['type']==CONTRACT['roles'][1]]
    editions={}
    for r in maps:
        editions.setdefault((r['payload'].get('county'),r['payload'].get('map_revision'),r['version']),[]).append(r)
    complete=[key for key,pages in editions.items() if edition_status(pages)['complete']]
    pairs=[]
    for first in left:
        a=first['payload']
        for county,map_revision,version in sorted(complete):
            if a.get('county')!=county:continue
            if a.get('map_revision') is not None and a.get('map_revision')!=map_revision:continue
            for second in editions[(county,map_revision,version)]:
                pairs.append({'left_id':first['id'],'left_version':first['version'],
                              'right_id':second['id'],'right_version':second['version'],
                              'left_source':first['source'],'right_source':second['source']})
    return {'publishable':bool(pairs),'reasons':[] if pairs else ['同县公告与范围图可以配对'],
            'received_types':sorted({r['type'] for r in rows}),
            'received_versions':len(rows),'matched_pairs':pairs,
            'candidate_relations':sorted({str(r['payload'].get(CONTRACT['relation_field'])) for r in rows})}
