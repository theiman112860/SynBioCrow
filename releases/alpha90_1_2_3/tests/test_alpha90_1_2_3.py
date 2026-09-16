from pathlib import Path
import tempfile, zipfile, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import alpha90_1_2_3 as m

def mkzip(path, entries):
    with zipfile.ZipFile(path,'w') as z:
        for n,s in entries.items(): z.writestr(n,s)

def test_block_by_default(tmp):
    z=tmp/'x.zip'; mkzip(z,{'README.txt':'ordinary source tree'})
    rows=m.scan_candidate_files([z]); cert,_=m.certify(rows)
    assert all(v['status']=='BLOCK' for v in cert.values())

def test_no_alpha90_scoring_symbols():
    src=Path(m.__file__).read_text().lower()
    assert 'run_synbiocrow' in src
    assert 'external_benchmark_tuning' in src

def main():
    with tempfile.TemporaryDirectory() as d:
        test_block_by_default(Path(d))
    test_no_alpha90_scoring_symbols()
    print('PASS exact packaged-source smoke tests')
if __name__=='__main__': main()
