let chart;
async function refresh(){
  try{
    const r=await fetch("/api/live"); const d=await r.json();
    document.getElementById("n").textContent=d.nitrogen;
    document.getElementById("p").textContent=d.phosphorus;
    document.getElementById("k").textContent=d.potassium;
    document.getElementById("t").textContent=d.temperature;
    document.getElementById("m").textContent=d.moisture;
    document.getElementById("crop1").textContent=d.crop1;
    document.getElementById("crop2").textContent=d.crop2;
    document.getElementById("fert").textContent=d.fertilizer;
    document.getElementById("why").textContent=d.why;
    document.getElementById("updated").textContent=d.updated_at||"-";
  }catch(e){console.log(e)}
}
async function graph(){
  const r=await fetch("/api/chart"); const d=await r.json();
  const ctx=document.getElementById("npkChart");
  if(chart) chart.destroy();
  chart=new Chart(ctx,{type:"line",data:{labels:d.labels,datasets:[
    {label:"Nitrogen",data:d.nitrogen,tension:.25},
    {label:"Phosphorus",data:d.phosphorus,tension:.25},
    {label:"Potassium",data:d.potassium,tension:.25}
  ]},options:{responsive:true,plugins:{legend:{position:"bottom"}},scales:{y:{beginAtZero:true}}}});
}
document.getElementById("saveBtn").onclick=async()=>{
  const d=await (await fetch("/api/live")).json();
  await fetch("/api/save-reading",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});
  alert("Current reading saved to history.");
  graph();
};
refresh(); graph(); setInterval(refresh,3000);
