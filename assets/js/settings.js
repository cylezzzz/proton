
// assets/js/settings.js
import {apiGet, apiPost} from "./api.js";

const nsfw = document.getElementById("nsfw");
const provider = document.getElementById("provider");
const outdir = document.getElementById("outdir");
const thumb = document.getElementById("thumb");
const saveBtn = document.getElementById("save");
const statusBox = document.getElementById("statusBox");
const saveStatus = document.getElementById("saveStatus");

async function refresh(){
  const s = await apiGet("/api/status");
  statusBox.textContent = JSON.stringify(s, null, 2);
  nsfw.checked = !!s.settings.nsfw_allowed;
  provider.value = (s.settings.provider_order||[]).join(",");
  outdir.value = s.settings.output_dir || "";
  thumb.value = s.settings.thumb_size || 320;
}
saveBtn.addEventListener("click", async ()=>{
  saveStatus.textContent = "Speichern...";
  const s = {
    nsfw_allowed: nsfw.checked,
    provider_order: provider.value.split(",").map(x=>x.trim()).filter(Boolean),
    output_dir: outdir.value.trim() || undefined,
    thumb_size: parseInt(thumb.value||"320")
  };
  const res = await apiPost("/api/settings", s);
  if(res.status==="ok"){ saveStatus.textContent = "Gespeichert."; refresh(); }
  else { saveStatus.textContent = "Fehler."; }
});

refresh();
