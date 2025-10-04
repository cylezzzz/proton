
// assets/js/gallery.js
import {apiGet, apiDelete} from "./api.js";

const grid = document.getElementById("grid");

function tileHTML(item){
  const thumb = item.thumb ? `/thumbs/${item.thumb}` : `/outputs/${item.name}`;
  return `<div class="tile">
    <img src="${thumb}" alt="${item.name}">
    <div class="actions">
      <a href="/outputs/${item.name}" download>Download</a>
      <button data-del="${item.name}">Löschen</button>
    </div>
  </div>`;
}

async function load(){
  const items = await apiGet("/api/outputs");
  grid.innerHTML = items.map(tileHTML).join("");
  grid.querySelectorAll("button[data-del]").forEach(btn=>{
    btn.addEventListener("click", async ()=>{
      if(!confirm("Wirklich löschen?")) return;
      const name = btn.getAttribute("data-del");
      const res = await apiDelete("/api/outputs/"+encodeURIComponent(name));
      if(res.status==="deleted"){ load(); }
    });
  });
}

load();
