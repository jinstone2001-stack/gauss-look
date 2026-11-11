import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from gausslook.engine import Engine
from gausslook.fields import isosurface
from test_analysis_v11 import enriched_fchk


def test_surface_cache_reuses_meshes_and_invalidates_changed_checkpoint(tmp_path):
    e = Engine(tmp_path)
    try:
        source = tmp_path / 'source.fchk'
        source.write_text(enriched_fchk())
        cid = e.load(source)['ids'][0]
        calls = []

        def utility(name, args, task):
            calls.append(name)
            Path(args[3]).write_text(
                'mock MO\nmock MO\n2 0 0 0\n4 1 0 0\n4 0 1 0\n4 0 0 1\n1 0 0 0 0\n1 0 0 0 1.4\n'
                + ' '.join(str((i - 1.5) / 4) for i in range(4) for j in range(4) for k in range(4))
            )

        e.utility = utility
        with patch('gausslook.engine.isosurface', wraps=isosurface) as build:
            first = e.orbital_surface(cid, 'alpha', 1, 'coarse', .03, {})
            again = e.orbital_surface(cid, 'alpha', 1, 'coarse', .03, {})
            assert first == again and build.call_count == 2 and len(calls) == 1
            e.orbital_surface(cid, 'alpha', 1, 'coarse', .05, {})
            assert build.call_count == 4 and len(calls) == 1
            source.write_text(source.read_text() + '\n')
            changed = e.orbital_surface(cid, 'alpha', 1, 'coarse', .03, {})
            assert changed['field_id'] != first['field_id']
            assert build.call_count == 6 and len(calls) == 2
        with pytest.raises(ValueError):
            e.orbital_surface(cid, 'alpha', 1, 'coarse', float('nan'), {})
    finally:
        e.close()


def test_cached_mesh_mapping_does_not_leak_and_cache_is_bounded(tmp_path):
    e = Engine(tmp_path)
    try:
        fid = e.demo()['field_id']
        mapped = e.action('mesh', field_id=fid, mapped_field=fid, level=.03)
        plain = e.action('mesh', field_id=fid, level=.03)
        assert 'mapped_values' in mapped and 'mapped_values' not in plain
        for level in np.linspace(.04, .14, 10):
            e.mesh(fid, level=level)
        assert len(e.mesh_cache) == 8
        for params in [{'channel': -1}, {'max_faces': 0}, {'level': float('inf')}]:
            with pytest.raises(ValueError):
                e.mesh(fid, **params)
        p = tmp_path / '한글.glproj'
        p.write_text(json.dumps(e.project(), ensure_ascii=False), encoding='utf-8')
        with patch.object(Path, 'read_text', autospec=True, wraps=Path.read_text) as read:
            # Verify the Windows-sensitive encoding at the file boundary.
            read.return_value = p.read_bytes().decode('utf-8')
            assert e.load(p)['ids']
            assert read.call_args.kwargs['encoding'] == 'utf-8'
    finally:
        e.close()
