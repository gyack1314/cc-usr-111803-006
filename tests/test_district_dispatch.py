"""完整单图能形成按乡镇区分的独立交易审核清单。"""
from pathlib import Path
import tempfile
import unittest
from capture_service.ledger import connect
from capture_service.collection import collect
from capture_service.districts import restrictions
from capture_service.dispatch import refresh,queue
from capture_service.archive import release,get

ROOT=Path(__file__).resolve().parents[1]
class DistrictDispatch(unittest.TestCase):
    def test_single_map_and_persisted_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'state.db'
            c=connect(path)
            collect(c,'county',ROOT/'data/district-initial.json')
            self.assertEqual({r['batch']:r['state'] for r in restrictions(c,'county')},
                {'T-A':'受限','T-B':'受限','T-C':'范围外','T-D':'受限'})
            initial=refresh(c,'county')
            revision=release(c,'county')
            before=get(c,'county',revision)
            c.close()
            c=connect(path)
            self.assertEqual(queue(c,'county'),initial)
            refresh(c,'county')
            self.assertEqual(queue(c,'county'),initial)
            self.assertEqual(get(c,'county',revision),before)
            c.close()
