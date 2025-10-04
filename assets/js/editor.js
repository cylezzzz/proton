
// assets/js/editor.js
import {apiUpload} from "./api.js";

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
let img = new Image();
let sel = null; // selection rect for crop

function fitCanvasToImage(){
  const maxW = 1000, maxH = 700;
  let {width, height} = img;
  const ratio = Math.min(maxW/width, maxH/height, 1);
  canvas.width = Math.floor(width*ratio);
  canvas.height = Math.floor(height*ratio);
  draw();
}

function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if(img.src){
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
  }
  if(sel){
    ctx.strokeStyle = "#e53e3e";
    ctx.setLineDash([6,4]);
    ctx.strokeRect(sel.x, sel.y, sel.w, sel.h);
    ctx.setLineDash([]);
  }
}

document.getElementById("file").addEventListener("change", (e)=>{
  const file = e.target.files[0];
  if(!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    img = new Image();
    img.onload = ()=>{ fitCanvasToImage(); };
    img.src = ev.target.result;
  };
  reader.readAsDataURL(file);
});

// Mouse selection for crop
let isDown=false, startX=0, startY=0;
canvas.addEventListener("mousedown", (e)=>{
  const rect = canvas.getBoundingClientRect();
  isDown=true; startX=e.clientX-rect.left; startY=e.clientY-rect.top;
  sel = {x:startX,y:startY,w:0,h:0};
  draw();
});
canvas.addEventListener("mousemove", (e)=>{
  if(!isDown || !sel) return;
  const rect = canvas.getBoundingClientRect();
  sel.w = (e.clientX-rect.left) - startX;
  sel.h = (e.clientY-rect.top) - startY;
  draw();
});
canvas.addEventListener("mouseup", ()=>{ isDown=false; });

function currentOps(){
  const ops = {};
  if(document.getElementById("grayscale").checked) ops.grayscale = true;
  const blur = parseFloat(document.getElementById("blur").value||"0"); if(blur>0) ops.blur=blur;
  const rot = parseFloat(document.getElementById("rotate").value||"0"); if(rot) ops.rotate=rot;
  if(document.getElementById("flip_h").checked) ops.flip_h = true;
  if(document.getElementById("flip_v").checked) ops.flip_v = true;
  const px = parseInt(document.getElementById("pixelate").value||"0"); if(px>0) ops.pixelate=px;
  const tv = (document.getElementById("textVal").value||"").trim();
  if(tv){
    ops.text = {
      value: tv,
      x: 20, y: 20,
      size: parseInt(document.getElementById("textSize").value||"28"),
      color: document.getElementById("textColor").value || "#ffffff"
    };
  }
  if(sel && Math.abs(sel.w)>10 && Math.abs(sel.h)>10){
    const scaleX = img.width / canvas.width;
    const scaleY = img.height / canvas.height;
    ops.crop = {
      x: Math.round(Math.min(sel.x, sel.x+sel.w)*scaleX),
      y: Math.round(Math.min(sel.y, sel.y+sel.h)*scaleY),
      w: Math.round(Math.abs(sel.w)*scaleX),
      h: Math.round(Math.abs(sel.h)*scaleY)
    };
  }
  return ops;
}

document.getElementById("btnApply").addEventListener("click", async ()=>{
  if(!img.src){ alert("Bitte zuerst ein Bild laden."); return; }
  const input = document.getElementById("file");
  const file = input.files[0];
  const form = new FormData();
  form.append("image", file);
  form.append("ops", JSON.stringify(currentOps()));
  const res = await apiUpload("/api/images/transform", form);
  if(res.error){ alert(res.error); return; }
  alert("Gespeichert als: "+res.file);
});

// initial canvas size
canvas.width = 800; canvas.height = 500; draw();
