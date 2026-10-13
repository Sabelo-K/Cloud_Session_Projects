"""Align script sentences to voiceover pauses.
Usage: python3 align_timing.py VOICEOVER.txt voiceover.mp3 timing.json"""
import re,json,subprocess,sys
txt=open(sys.argv[1]).read()
sents=[s.strip() for s in re.split(r'(?<=[.?!:])\s+',txt.replace('\n',' ')) if s.strip()]
out=subprocess.run(['ffmpeg','-hide_banner','-i',sys.argv[2],'-af','silencedetect=noise=-35dB:d=0.25','-f','null','-'],capture_output=True,text=True).stderr
starts=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]
ends=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
pauses=list(zip(starts,ends))
T=float(re.search(r'Duration: (\d+):(\d+):([\d.]+)',out).group(3))+60*int(re.search(r'Duration: (\d+):(\d+)',out).group(2))
speech_start=pauses[0][1] if pauses and pauses[0][0]<0.05 else 0
L=[len(s) for s in sents];tot=sum(L)
cum=0;exp=[]
for l in L[:-1]:
    cum+=l;exp.append(speech_start+(T-speech_start)*cum/tot)
# DP: assign each boundary to a pause, monotonic increasing
n,m=len(exp),len(pauses);INF=1e18
mid=[(a+b)/2 for a,b in pauses]
dp=[[INF]*m for _ in range(n)];bk=[[0]*m for _ in range(n)]
for j in range(m): dp[0][j]=abs(mid[j]-exp[0])
for i in range(1,n):
    best=INF;bj=-1
    for j in range(m):
        if j>0 and dp[i-1][j-1]<best: best=dp[i-1][j-1];bj=j-1
        if best<INF: dp[i][j]=best+abs(mid[j]-exp[i]);bk[i][j]=bj
j=min(range(m),key=lambda j:dp[n-1][j]);path=[j]
for i in range(n-1,0,-1): j=bk[i][j];path.append(j)
path=path[::-1]
res=[];t0=speech_start
for i,s in enumerate(sents):
    if i<n: e=pauses[path[i]][0]; nxt=pauses[path[i]][1]
    else: e=T; nxt=T
    res.append({"i":i,"text":s,"start":round(t0,2),"end":round(e,2)}); t0=nxt
json.dump(res,open(sys.argv[3],'w'),indent=1)
print(len(sents),m); 
for r in res: print(r['start'],r['end'],r['text'][:60])
