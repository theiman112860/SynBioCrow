from synbiocrow.v24.high_tail_rank_2_4_32 import matrix,tail_labels
def test_tail():
    rows=[{"route_id":f"r{i}","similarity":i/9,"route_length":i%4+1} for i in range(10)]
    X,y,ids=matrix(rows)
    labels,thr=tail_labels(y,0.9)
    assert len(X)==10 and len(labels)==10 and sum(labels)>=1 and ids[0]=="r0"
