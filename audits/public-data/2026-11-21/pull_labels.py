import pyarrow.parquet as pq, fsspec, json, time, os
fs=fsspec.filesystem("http")
base="https://huggingface.co/datasets/lerobot/droid_1.0.1/resolve/main/"
cols=["episode_index","is_last","is_episode_successful","task_category","building","language_instruction","collector_id","date"]
rows=[]; t0=time.time()
for i in range(156):
    u=f"{base}data/chunk-000/file-{i:03d}.parquet"
    for attempt in range(3):
        try:
            with fs.open(u,"rb") as f:
                t=pq.read_table(f,columns=cols)
            t=t.filter(t.column("is_last").cast("bool"))
            rows.extend(t.to_pylist()); break
        except Exception as e:
            print("retry",i,type(e).__name__,flush=True); time.sleep(3)
    if i%20==0: print(i,len(rows),round(time.time()-t0),flush=True)
with open("droid_episodes.jsonl","w") as f:
    for r in rows: f.write(json.dumps(r,default=str)+"\n")
print("done",len(rows),round(time.time()-t0))
