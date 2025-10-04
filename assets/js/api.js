
// assets/js/api.js
export async function apiGet(url){
  const r = await fetch(url, {credentials:"same-origin"});
  return await r.json();
}
export async function apiPost(url, data){
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
  return await r.json();
}
export async function apiDelete(url){
  const r = await fetch(url, {method:"DELETE"});
  return await r.json();
}
export async function apiUpload(url, formData){
  const r = await fetch(url, {method:"POST", body:formData});
  return await r.json();
}
