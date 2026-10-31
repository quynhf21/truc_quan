/* Static GitHub Pages edition: charts recalculate from identifier-free band-level rows. */
const F = { tenure: 0, equipment: 1, web: 2, value: 3, charge: 4, minutes: 5, usage: 6, decile: 7, priority: 8, reason: 9, churn: 10, score: 11 };
const colors = { blue: '#1769aa', teal: '#00a99b', red: '#dc5964', ink: '#12304a', muted: '#64788b' };
let data, page = 'overview';
const $ = id => document.getElementById(id);
const count = n => Number(n).toLocaleString('vi-VN');
const pct = x => `${(x * 100).toLocaleString('vi-VN', {maximumFractionDigits: 1})}%`;
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const label = (key, code) => data.dictionary[data.columns[F[key]]][code];
const total = rows => rows.reduce((n, row) => n + row[F.churn], 0);
const rate = rows => rows.length ? total(rows) / rows.length : 0;
const card = (name, value, note='') => `<div class="kpi"><div class="kpi-label">${esc(name)}</div><div class="kpi-value">${esc(value)}</div><div class="kpi-note">${esc(note)}</div></div>`;
const panel = (name, id, note='') => `<div class="panel"><h3>${esc(name)}</h3><div class="chart" id="${id}"></div>${note ? `<p class="panel-note">${esc(note)}</p>` : ''}</div>`;
const intro = (tag, title, sub) => `<div class="intro"><span class="eyebrow">${esc(tag)}</span><h1>${esc(title)}</h1><p>${esc(sub)}</p></div>`;
const insight = (tag, text) => `<div class="insight"><strong>${esc(tag)}</strong><p>${esc(text)}</p></div>`;
const section = (title, sub='') => `<div class="section"><h2>${esc(title)}</h2>${sub ? `<p>${esc(sub)}</p>` : ''}</div>`;

function filtered() {
  const selected = [[$('tenure').value, F.tenure], [$('web').value, F.web], [$('value').value, F.value], [$('decile').value, F.decile]];
  return data.rows.filter(row => selected.every(([v, col]) => v === 'all' || row[col] === Number(v)));
}

function grouped(rows, key, order=null) {
  const groups = new Map();
  for (const row of rows) {
    const k = label(key, row[F[key]]);
    const item = groups.get(k) || {name:k, n:0, churn:0};
    item.n++; item.churn += row[F.churn]; groups.set(k, item);
  }
  const items = [...groups.values()].map(item => ({...item, rate:item.churn/item.n}));
  if (order) items.sort((a,b) => order.indexOf(a.name) - order.indexOf(b.name));
  return items;
}

function wilson(churn, n) {
  const p = churn/n, z = 1.96, den = 1+z*z/n;
  const center = (p+z*z/(2*n))/den;
  const margin = z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;
  return [center-margin, center+margin];
}

const graphLayout = (title, ytitle, percentage=false) => ({
  title:{text:title,font:{size:15,color:colors.ink}},
  margin:{l:55,r:20,t:55,b:75}, height:330, paper_bgcolor:'#fff', plot_bgcolor:'#fff',
  font:{family:'Inter, Segoe UI, sans-serif',color:colors.ink,size:11},
  xaxis:{gridcolor:'#e8eef3',automargin:true},
  yaxis:{title:ytitle,gridcolor:'#e8eef3',tickformat:percentage?'.0%':undefined,automargin:true},
  showlegend:false
});
const plot = (id, traces, layout) => {
  const target = $(id);
  const caption = document.createElement('div');
  caption.className = 'chart-caption';
  caption.textContent = layout.title?.text || '';
  target.before(caption);
  const horizontal = traces.length === 1 && traces[0].type === 'bar'
    && traces[0].x.some(value => String(value).length > 14);
  if (horizontal) {
    const trace = traces[0];
    [trace.x, trace.y] = [trace.y, trace.x];
    trace.orientation = 'h';
    if (trace.error_y) { trace.error_x = trace.error_y; delete trace.error_y; }
    trace.hovertemplate = trace.hovertemplate?.replace(/%\{x/g, '%{TEMP').replace(/%\{y/g, '%{x').replace(/%\{TEMP/g, '%{y');
    layout.xaxis = {...layout.yaxis, automargin:true};
    layout.yaxis = {automargin:true, autorange:'reversed', tickvals:trace.y,
      ticktext:trace.y.map(value => String(value).replace(/(.{12,18})\s/g, '$1<br>'))};
    if (trace.text) layout.xaxis.range = [0, Math.max(...trace.x) * 1.2];
  }
  layout.title = undefined;
  layout.margin = {l:50,r:45,t:35,b:65};
  layout.legend = {orientation:'h',x:0,y:1.15};
  layout.xaxis = {...layout.xaxis, automargin:true};
  layout.yaxis = {...layout.yaxis, automargin:true};
  return Plotly.newPlot(id,traces,layout,{responsive:true,displaylogo:false});
};

function rateChart(id, rows, key, title, order=null) {
  const g = grouped(rows,key,order), ci = g.map(v=>wilson(v.churn,v.n));
  return plot(id,[{type:'bar',x:g.map(v=>v.name),y:g.map(v=>v.rate),marker:{color:colors.blue},
    error_y:{type:'data',symmetric:false,array:ci.map((v,i)=>v[1]-g[i].rate),arrayminus:ci.map((v,i)=>g[i].rate-v[0])},
    customdata:g.map(v=>[v.n,v.churn]),
    hovertemplate:'%{x}<br>Churn: %{y:.1%}<br>Khách: %{customdata[0]:,}<br>Churner: %{customdata[1]:,}<extra></extra>'}],
    graphLayout(title,'Tỷ lệ churn',true));
}

function volumeChart(id, rows, key, title, order=null, field='n') {
  const g = grouped(rows,key,order);
  return plot(id,[{type:'bar',x:g.map(v=>v.name),y:g.map(v=>v[field]),marker:{color:field==='churn'?colors.red:colors.teal},
    text:g.map(v=>count(v[field])),textposition:'outside',cliponaxis:false,
    hovertemplate:`%{x}<br>${field==='churn'?'Churner':'Khách'}: %{y:,}<extra></extra>`}],
    graphLayout(title,field==='churn'?'Số churner':'Số khách hàng'));
}

function comparison(rows, key, a, b, prefix) {
  const groups=grouped(rows,key), left=groups.find(g=>g.name===a), right=groups.find(g=>g.name===b);
  if (!left || !right) return `${prefix}: bộ lọc hiện tại không đủ hai nhóm để so sánh.`;
  const delta=(left.rate-right.rate)*100;
  return `${prefix}: ${a} có churn ${pct(left.rate)} (n=${count(left.n)}), so với ${pct(right.rate)} (n=${count(right.n)}) ở nhóm ${b}; chênh ${delta>=0?'+':''}${delta.toFixed(1)} điểm %. Đây là liên hệ quan sát.`;
}

function table(head, body) {
  return `<div class="table-wrap"><table><thead><tr>${head.map(v=>`<th>${esc(v)}</th>`).join('')}</tr></thead><tbody>${body.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function overview(rows) {
  const churn=total(rows), top=rows.filter(r=>Number(label('decile',r[F.decile]))>=9);
  $('content').innerHTML = intro('01 / EXECUTIVE VIEW','Churn đang tập trung ở đâu?','Bắt đầu từ quy mô vấn đề, sau đó đi sâu vào tín hiệu và nhóm cần ưu tiên.')+
    `<div class="kpis">${card('Khách trong lát cắt',count(rows.length),'Mẫu số của các KPI')}${card('Khách churn',count(churn),'Churn = Yes')}${card('Tỷ lệ churn',pct(churn/rows.length),`Baseline nguồn: ${pct(data.qa.baseline_churn_rate)}`)}${card('Top 20% risk',count(top.length),'Decile 9–10, score ngoài mẫu')}</div>`+
    insight('ĐỌC NHANH',comparison(rows,'tenure','12–18 tháng','6–11 tháng','Cửa sổ tenure'))+
    section('Quy mô và phân bố','Nhóm rủi ro cao cần có đủ khách hàng để hành động.')+
    `<div class="panels">${panel('Churn theo tenure','tenure-rate','Snapshot theo nhóm thâm niên, không phải đường thời gian.')}${panel('Quy mô tenure','tenure-volume')}${panel('Tín hiệu rà soát','reason-volume','Reason code là rule vận hành sơ bộ.')}<div class="panel"><h3>Chất lượng nguồn</h3><div class="quality"><p><b>${count(data.qa.raw_rows)}</b> dòng raw · ${data.qa.raw_columns} cột</p><p><b>${count(data.qa.missing_any_model_feature_rows)}</b> khách thiếu ít nhất một predictor</p><p><b>${count(data.qa.complete_58_column_rows)}</b> khách complete-case cả 58 cột</p><small>Không dùng complete-case 58 cột làm mẫu số mặc định.</small></div></div></div>`;
  const tenure=['6–11 tháng','12–18 tháng','19–24 tháng','25+ tháng'];
  rateChart('tenure-rate',rows,'tenure','Tỷ lệ churn và CI 95%',tenure);
  volumeChart('tenure-volume',rows,'tenure','Số khách hàng',tenure);
  volumeChart('reason-volume',rows,'reason','Số churner theo reason',null,'churn');
}

function drivers(rows) {
  $('content').innerHTML = intro('02 / DRIVERS','Những tín hiệu nào đi cùng churn?','Đọc tỷ lệ rủi ro cùng quy mô nhóm; snapshot không chứng minh nguyên nhân.')+
    insight('TÍN HIỆU 1',comparison(rows,'equipment','>730 ngày','≤180 ngày','Tuổi thiết bị'))+
    section('Vòng đời & thiết bị')+
    `<div class="panels">${panel('Tenure','d-tenure')}${panel('Tuổi thiết bị','d-equipment')}${panel('Web capability','d-web')}${panel('Quy mô nhóm thiết bị','d-equipment-n')}</div>`+
    insight('TÍN HIỆU 2',comparison(rows,'usage','Giảm mạnh (≤-83)','Tăng nhẹ (0–66)','Thay đổi sử dụng'))+
    section('Giá trị, phí & hành vi','MonthlyRevenue là value proxy; đơn vị PercChangeMinutes chưa được xác minh.')+
    `<div class="panels">${panel('Value tier','d-value')}${panel('Quy mô value tier','d-value-n')}${panel('Phí định kỳ','d-charge')}${panel('Mức sử dụng','d-minutes')}${panel('Thay đổi sử dụng','d-usage')}${panel('Độ phủ tín hiệu','d-usage-n')}</div>`;
  rateChart('d-tenure',rows,'tenure','Churn theo tenure');
  rateChart('d-equipment',rows,'equipment','Churn theo tuổi thiết bị');
  rateChart('d-web',rows,'web','Churn theo web capability');
  volumeChart('d-equipment-n',rows,'equipment','Số khách theo tuổi thiết bị');
  rateChart('d-value',rows,'value','Churn theo doanh thu tháng');
  volumeChart('d-value-n',rows,'value','Số khách theo value tier');
  rateChart('d-charge',rows,'charge','Churn theo recurring charge');
  rateChart('d-minutes',rows,'minutes','Churn theo monthly minutes');
  rateChart('d-usage',rows,'usage','Churn theo thay đổi minutes nguồn');
  volumeChart('d-usage-n',rows,'usage','Số khách theo mức thay đổi');
}

function risk(rows) {
  const sorted=[...rows].sort((a,b)=>b[F.score]-a[F.score]), churn=total(rows);
  const capacities=[5,10,20].map(p=>{const top=sorted.slice(0,Math.max(1,Math.ceil(rows.length*p/100))), c=total(top);return [p,top.length,c,c/top.length,churn?c/churn:0,churn?(c/top.length)/(churn/rows.length):null];});
  const segments=grouped(rows,'priority').sort((a,b)=>Number(a.name.slice(1,2))-Number(b.name.slice(1,2)));
  $('content').innerHTML=intro('03 / RISK & SEGMENTS','Ai nên được ưu tiên?','Score 3-fold ngoài mẫu; các KPI mô hình là kết quả toàn nguồn, bảng capacity theo bộ lọc.')+
    `<div class="kpis">${card('ROC-AUC toàn nguồn',data.model.roc_auc.toFixed(3),'Dự đoán ngoài mẫu')}${card('PR-AUC toàn nguồn',data.model.pr_auc.toFixed(3),'Baseline PR = churn rate')}${card('Log loss toàn nguồn',data.model.log_loss.toFixed(3),'Mô hình 10 feature')}${card('Depth phổ biến',String(data.model.chosen_depth),'Chọn trong train fold')}</div>`+
    insight('Ý NGHĨA VẬN HÀNH',`Top 10% của lát cắt gồm ${count(capacities[1][1])} khách. Gain/recall cho biết số churner quá khứ được tiếp cận, chưa phải hiệu quả chính sách.`)+
    `<div class="panels">${panel('Phân tầng rủi ro','r-decile')}${panel('Cumulative gain','r-gain')}${panel('Calibration','r-cal','Chỉ số từ score ngoài mẫu của lát cắt hiện tại.')}<div class="panel"><h3>Capacity 5 / 10 / 20%</h3>${table(['Capacity','Khách','Churner','Precision','Recall','Lift'],capacities.map(v=>[`${v[0]}%`,count(v[1]),count(v[2]),pct(v[3]),churn?pct(v[4]):'n.a.',v[5]===null?'n.a.':`${v[5].toFixed(2)}×`]))}<p class="panel-note">Churner quá khứ trong top risk không phải số khách được cứu giữ.</p></div><div class="panel wide"><h3>Phân khúc ưu tiên</h3>${table(['Nhóm','Khách','Churner','Churn rate'],segments.map(v=>[v.name,count(v.n),count(v.churn),pct(v.rate)]))}<p class="panel-note">P1–P4 loại trừ nhau; MonthlyRevenue chỉ là value proxy.</p></div></div>`;
  rateChart('r-decile',rows,'decile','Tỷ lệ churn theo risk decile',['1','2','3','4','5','6','7','8','9','10']);
  let cumulative=0, x=[], y=[];
  for(let i=0;i<sorted.length;i++){cumulative+=sorted[i][F.churn]; if(i%Math.max(1,Math.floor(sorted.length/250))===0 || i===sorted.length-1){x.push((i+1)/sorted.length);y.push(churn?cumulative/churn:0);}}
  plot('r-gain',[{type:'scatter',mode:'lines',x,y,name:'Mô hình',line:{color:colors.teal,width:3}},{type:'scatter',mode:'lines',x:[0,1],y:[0,1],name:'Ngẫu nhiên',line:{color:colors.muted,dash:'dash'}}],{...graphLayout('Cumulative gain','Tỷ lệ churner được tiếp cận'),showlegend:true,xaxis:{title:'Tỷ lệ khách được liên hệ',tickformat:'.0%'},yaxis:{title:'Tỷ lệ churner',tickformat:'.0%'}});
  const ascending=[...rows].sort((a,b)=>a[F.score]-b[F.score]), bins=[];
  for(let i=0;i<10;i++){const part=ascending.slice(Math.floor(i*ascending.length/10),Math.floor((i+1)*ascending.length/10)); if(part.length) bins.push({score:part.reduce((s,r)=>s+r[F.score],0)/part.length, observed:rate(part)});}
  plot('r-cal',[{type:'scatter',mode:'lines+markers',x:bins.map(v=>v.score),y:bins.map(v=>v.observed),name:'Quan sát',line:{color:colors.blue,width:3}},{type:'scatter',mode:'lines',x:[0,1],y:[0,1],name:'Lý tưởng',line:{color:colors.muted,dash:'dash'}}],{...graphLayout('Calibration theo 10 nhóm score','Churn quan sát'),showlegend:true,xaxis:{title:'Xác suất dự đoán',tickformat:'.0%',range:[0,.65]},yaxis:{title:'Churn quan sát',tickformat:'.0%',range:[0,.65]}});
}

function strategy(rows) {
  const reasons=grouped(rows,'reason').sort((a,b)=>b.churn-a.churn);
  const priority=rows.filter(r=>!label('priority',r[F.priority]).startsWith('P4'));
  const cards=data.policies.map(policy=>{
    const eligible=rows.filter(r=>label('reason',r[F.reason])===policy.ReasonCode && Number(label('decile',r[F.decile]))>=7);
    return `<div class="policy"><div class="policy-head"><span class="tag">${esc(policy.Status)}</span><h3>${esc(policy.ReasonCode)}</h3></div><p class="muted">${esc(policy['Eligibility hypothesis'])}</p><div class="policy-stat"><b>${count(eligible.length)}</b> khách đủ điều kiện · <b>${eligible.length?pct(rate(eligible)):'n.a.'}</b> churn</div><small>CAN THIỆP ĐỀ XUẤT</small><p>${esc(policy['Treatment hypothesis'])}</p><small>KPI CHÍNH</small><p>${esc(policy['Primary KPI'])}</p><small>GUARDRAIL</small><p>${esc(policy.Guardrail)}</p></div>`;
  }).join('');
  $('content').innerHTML=intro('04 / RETENTION STRATEGY','Can thiệp nào đáng thử?','Reason code là tín hiệu rà soát; mọi treatment cần so với eligible control.')+
    `<div class="kpis three">${card('Nhóm ưu tiên P1–P3',count(priority.length),'Ứng viên liên hệ')}${card('Reason code',String(reasons.length),'Có fallback')}${card('Policy đã thử nghiệm','0','Chưa có treatment/control')}</div>`+
    section('Tín hiệu và quy mô','Mỗi khách có một reason code ưu tiên; tín hiệu nguồn có thể chồng lắp.')+
    `<div class="panel">${table(['Reason code','Khách','Churner','Churn rate'],reasons.map(v=>[v.name,count(v.n),count(v.churn),pct(v.rate)]))}</div>`+
    section('Policy matrix','Ưu tiên device, usage decline và lifecycle trong risk decile ≥7. Plan review cần thêm bằng chứng.')+
    `<div class="policy-grid">${cards}</div><div class="callout"><h3>Thiết kế phép thử tối thiểu</h3><p>Trong từng nhóm đủ điều kiện, chia ngẫu nhiên treatment và business-as-usual control. Khóa outcome window, KPI churn và guardrail trước khi chạy. So sánh theo intent-to-treat trước khi scale.</p><p>CreditRating không dùng đơn lẻ để từ chối hỗ trợ hoặc áp điều kiện bất lợi.</p></div>`;
}

function render() {
  const rows=filtered();
  document.querySelectorAll('.nav').forEach(el=>{
    const active = el.dataset.page === page;
    el.classList.toggle('active', active);
    if (active) el.setAttribute('aria-current', 'page');
    else el.removeAttribute('aria-current');
  });
  if(!rows.length){$('content').innerHTML='<div class="empty"><h2>Không có khách hàng cho bộ lọc này</h2><p>Hãy nới bộ lọc để tiếp tục.</p></div>';return;}
  ({overview,drivers,risk,strategy})[page](rows);
}

function fillSelect(id, key, sorted=false) {
  const entries=data.dictionary[data.columns[F[key]]].map((text,code)=>({text,code}));
  if(sorted) entries.sort((a,b)=>Number(a.text)-Number(b.text));
  if(id==='tenure') { const order=['6–11 tháng','12–18 tháng','19–24 tháng','25+ tháng']; entries.sort((a,b)=>order.indexOf(a.text)-order.indexOf(b.text)); }
  $(id).innerHTML='<option value="all">Tất cả</option>'+entries.map(v=>`<option value="${v.code}">${esc(v.text)}</option>`).join('');
}

async function main() {
  try {
    const response=await fetch('./data.json');
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    data=await response.json();
    if(data.schema!==1 || data.rows.length!==data.qa.raw_rows) throw new Error('Data contract mismatch');
    fillSelect('tenure','tenure'); fillSelect('web','web'); fillSelect('value','value'); fillSelect('decile','decile',true);
    for(const id of ['tenure','web','value','decile']) $(id).addEventListener('change',render);
    $('reset').addEventListener('click',()=>{for(const id of ['tenure','web','value','decile']) $(id).value='all';render();});
    function navigate() {
      const hash = location.hash.slice(1);
      page = ['overview','drivers','risk','strategy'].includes(hash) ? hash : 'overview';
      render();
      const heading = $('content').querySelector('h1,h2');
      if (heading) { heading.tabIndex = -1; heading.focus({preventScroll:true}); }
      window.scrollTo(0,0);
    }
    document.querySelectorAll('.nav').forEach(button=>button.addEventListener('click',()=>{
      if (location.hash === '#' + button.dataset.page) navigate();
      else location.hash = button.dataset.page;
    }));
    window.addEventListener('hashchange', navigate);
    navigate();
  } catch(error) { $('content').innerHTML=`<div class="empty"><h2>Không tải được dashboard</h2><p>${esc(error.message)}</p></div>`; }
}
document.addEventListener('DOMContentLoaded',main);
