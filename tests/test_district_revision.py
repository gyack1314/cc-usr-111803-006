"""公告修订、缺页、解除通知与中断恢复下的县级交易审核清单。"""
import tempfile
import unittest
from pathlib import Path
from capture_service.ledger import connect, receive, entities
from capture_service.collection import collect, coverage, progress
from capture_service.transport import Replay
from capture_service.districts import restrictions
from capture_service.dispatch import refresh, queue
from capture_service.archive import release, get

ROOT = Path(__file__).resolve().parents[1]


def states(c):
    return {r['batch']: r['state'] for r in restrictions(c, 'county')}


def advice(c):
    return {r['batch']: r['recommendation'] for r in queue(c, 'county')}


def evidence(c, batch):
    return next(r for r in restrictions(c, 'county') if r['batch'] == batch)


class DistrictRevision(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'state.db'
        self.c = connect(self.path)
        collect(self.c, 'county', ROOT / 'data/district-initial.json')

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def test_incomplete_r2_withdraws_old_approval(self):
        """r2 缺第二页时，未见乡镇不得判作范围外，旧可放行建议须撤回。"""
        initial_revision = release(self.c, 'county')
        collect(self.c, 'county', ROOT / 'data/district-pending.json')
        self.assertEqual(states(self.c),
                         {'T-A': '受限', 'T-B': '待核', 'T-C': '待核', 'T-D': '受限'})
        self.assertEqual(advice(self.c),
                         {'T-A': '暂缓', 'T-B': '等待资料', 'T-C': '等待资料', 'T-D': '暂缓'})
        t_c = evidence(self.c, 'T-C')
        self.assertFalse(t_c['map_complete'])
        self.assertEqual(t_c['missing_pages'], [2])
        self.assertEqual((t_c['notice'], t_c['notice_version'], t_c['map_revision']),
                         ('V-01', 'v2', 'r2'))
        self.assertEqual({p['page'] for p in t_c['map_pages']}, {1})
        # 旧发布仍按当时资料复现：T-C 在初版下为可审核放行
        frozen = get(self.c, 'county', initial_revision)
        self.assertEqual({r['batch']: r['recommendation'] for r in frozen['dispatch_review']},
                         {'T-A': '暂缓', 'T-B': '暂缓', 'T-C': '可审核放行', 'T-D': '暂缓'})

    def test_complete_r2_flips_attribution(self):
        """r2 齐备后：T-B 解除原范围限制，T-C 转为暂缓，T-A 仍受限。"""
        collect(self.c, 'county', ROOT / 'data/district-pending.json')
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        self.assertEqual(states(self.c),
                         {'T-A': '受限', 'T-B': '范围外', 'T-C': '受限', 'T-D': '受限'})
        self.assertEqual(advice(self.c),
                         {'T-A': '暂缓', 'T-B': '可审核放行', 'T-C': '暂缓', 'T-D': '暂缓'})
        t_c = evidence(self.c, 'T-C')
        self.assertTrue(t_c['map_complete'])
        self.assertEqual(t_c['missing_pages'], [])
        self.assertEqual({p['page'] for p in t_c['map_pages']}, {1, 2})

    def test_release_notice_requires_verified_body(self):
        """解除通知正文缺失时不得宣布解除；核实后只对生效日子范围解除。"""
        collect(self.c, 'county', ROOT / 'data/district-pending.json')
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        collect(self.c, 'county', ROOT / 'data/district-release-pending.json')
        self.assertIn('https://county.example.test/REL-01', coverage(self.c, 'county')['missing_required'])
        self.assertEqual(states(self.c)['T-D'], '受限')
        self.assertEqual(advice(self.c)['T-D'], '暂缓')
        self.assertEqual(evidence(self.c, 'T-D')['pending_release_sources'],
                         ['https://county.example.test/REL-01'])
        collect(self.c, 'county', ROOT / 'data/district-release.json')
        self.assertEqual(states(self.c),
                         {'T-A': '受限', 'T-B': '范围外', 'T-C': '受限', 'T-D': '解除'})
        self.assertEqual(advice(self.c),
                         {'T-A': '暂缓', 'T-B': '可审核放行', 'T-C': '暂缓', 'T-D': '可审核放行'})
        released_by = evidence(self.c, 'T-D')['released_by']
        self.assertEqual([(r['id'], r['released_on']) for r in released_by], [('REL-01', '2026-11-16')])
        # 不追溯取消 11 月 15 日的限制，也不解除丙镇
        self.assertNotIn('released_by', evidence(self.c, 'T-A'))
        self.assertNotIn('released_by', evidence(self.c, 'T-C'))

    def test_repeat_fetch_and_moved_address_are_idempotent(self):
        """重复抓取与同原文转址不产生重复资料，审核建议保持不变。"""
        collect(self.c, 'county', ROOT / 'data/district-pending.json')
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        before = queue(self.c, 'county')
        count = len(entities(self.c, 'county'))
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        self.assertEqual(len(entities(self.c, 'county')), count)
        self.assertEqual(queue(self.c, 'county'), before)
        collect(self.c, 'county', ROOT / 'data/district-moved.json')
        self.assertEqual(len(entities(self.c, 'county')), count)
        self.assertEqual(queue(self.c, 'county'), before)
        urls = [p['source_url'] for p in progress(self.c, 'county')]
        self.assertIn('https://county.example.test/moved/V-01-map-page2', urls)
        self.assertEqual(coverage(self.c, 'county')['missing_required'], [])

    def test_interrupted_refresh_recovers_without_stale_advice(self):
        """原文已保存而清单未更新时中断，恢复后建议不领先于依据，旧放行建议被撤回。"""
        # 中断在 v2 公告与 r2 第一页已保存、清单尚未更新时：旧放行建议仍在清单中
        replay = Replay(ROOT / 'data/district-pending.json')
        for step in replay.steps:
            request = step['request']
            raw, receipt = replay.request(request['method'], request['url'])
            receive(self.c, 'county', raw, receipt)
        self.assertEqual(advice(self.c)['T-C'], '可审核放行')
        # 恢复后重新接续：旧放行建议被撤回，未见乡镇不判范围外
        refresh(self.c, 'county')
        self.assertEqual(advice(self.c),
                         {'T-A': '暂缓', 'T-B': '等待资料', 'T-C': '等待资料', 'T-D': '暂缓'})
        # 中断在解除通知正文已保存、清单尚未更新时：建议不抢先放行
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        replay = Replay(ROOT / 'data/district-release.json')
        step = replay.steps[0]['request']
        raw, receipt = replay.request(step['method'], step['url'])
        receive(self.c, 'county', raw, receipt)
        self.assertEqual(advice(self.c)['T-D'], '暂缓')
        refresh(self.c, 'county')
        self.assertEqual(advice(self.c)['T-D'], '可审核放行')

    def test_review_list_survives_restart_and_old_release_is_frozen(self):
        """清单跨重启保持，旧发布按当时资料复现，当前清单反映完整有效资料。"""
        initial_revision = release(self.c, 'county')
        collect(self.c, 'county', ROOT / 'data/district-pending.json')
        collect(self.c, 'county', ROOT / 'data/district-complete.json')
        collect(self.c, 'county', ROOT / 'data/district-release.json')
        current = queue(self.c, 'county')
        self.c.close()
        self.c = connect(self.path)
        self.assertEqual(queue(self.c, 'county'), current)
        self.assertEqual(advice(self.c),
                         {'T-A': '暂缓', 'T-B': '可审核放行', 'T-C': '暂缓', 'T-D': '可审核放行'})
        frozen = get(self.c, 'county', initial_revision)
        self.assertEqual({r['batch']: r['state'] for r in frozen['batch_restrictions']},
                         {'T-A': '受限', 'T-B': '受限', 'T-C': '范围外', 'T-D': '受限'})


if __name__ == '__main__':
    unittest.main()
