"""交易审核清单独立保存已作出的放行建议。"""
import json
from .districts import restrictions

def initialize(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS dispatch_review(
        collection TEXT NOT NULL, batch_no TEXT NOT NULL, recommendation TEXT NOT NULL,
        evidence_json TEXT NOT NULL, PRIMARY KEY(collection,batch_no))""")
    connection.commit()

def refresh(connection,collection):
    initialize(connection)
    with connection:
        for row in restrictions(connection,collection):
            advice={'受限':'暂缓','范围外':'可审核放行','待核':'等待资料','解除':'可审核放行'}[row['state']]
            connection.execute('INSERT INTO dispatch_review VALUES(?,?,?,?) ON CONFLICT(collection,batch_no) '
                               'DO UPDATE SET recommendation=excluded.recommendation,evidence_json=excluded.evidence_json',
                               (collection,row['batch'],advice,json.dumps(row,ensure_ascii=False,sort_keys=True)))
    return queue(connection,collection)

def queue(connection,collection):
    initialize(connection)
    return [dict(batch=r[0],recommendation=r[1],evidence=json.loads(r[2])) for r in connection.execute(
        'SELECT batch_no,recommendation,evidence_json FROM dispatch_review WHERE collection=? ORDER BY batch_no',(collection,))]
