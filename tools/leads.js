/* GitHub Pages only: an opt-in contact card after a campaign, a Feedback link on the start screen,
   and anonymous visit counting. Added by tools/build_pages.py; the claude.ai artifact never has it. */
(function(){
  var FORM = "__FORM_URL__", es = function(){ try { return typeof LANG!=="undefined" && LANG==="es"; } catch(e){ return false; } };
  function ver(){ try { return typeof VERSION!=="undefined" ? VERSION : ""; } catch(e){ return ""; } }
  function link(src){
    var p = {source:src, lang:es()?"es":"en", version:ver()};
    try { if (typeof S!=="undefined" && S && S.mode){ p.scenario = S.mode.scen||""; p.difficulty = S.mode.diff||""; p.turn = String(S.turn||""); } } catch(e){}
    return FORM + (FORM.indexOf("?")<0?"?":"&") + Object.keys(p).map(function(k){ return k+"="+encodeURIComponent(p[k]); }).join("&");
  }
  function ev(name){ try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({path:"event/"+name, title:name, event:true}); } catch(e){} }
  var css = document.createElement("style");
  css.textContent = ".ldfb{position:fixed;right:14px;bottom:14px;z-index:60;background:#251f19;color:#efe7da;border:1px solid #3a3129;border-radius:16px;padding:6px 12px;font:600 12.5px 'IBM Plex Sans',system-ui,sans-serif;text-decoration:none}"
    + ".ldfb:hover{border-color:#e8a93b;color:#e8a93b}"
    + ".ldcard{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:61;width:min(460px,calc(100% - 24px));background:#1c1814;color:#efe7da;border:1px solid #e8a93b;border-radius:10px;padding:14px 16px;box-shadow:0 10px 30px rgba(0,0,0,.6);font:14px/1.45 'IBM Plex Sans',system-ui,sans-serif}"
    + ".ldcard b{display:block;font:700 20px 'Barlow Condensed','Arial Narrow',sans-serif;letter-spacing:.04em;color:#e8a93b;margin-bottom:4px}"
    + ".ldcard p{margin:0 0 10px;color:#cfc3b2;font-size:13.5px}.ldrow{display:flex;gap:8px;flex-wrap:wrap}"
    + ".ldcard a,.ldcard button{font:600 13.5px 'IBM Plex Sans',system-ui,sans-serif;border-radius:4px;padding:8px 14px;cursor:pointer;text-decoration:none}"
    + ".ldcard a{background:#e8a93b;color:#14110e;border:0}.ldcard button{background:transparent;color:#efe7da;border:1px solid #3a3129}";
  document.head.appendChild(css);
  var fb = null, card = null, shownFor = null;
  function tick(){
    var intro = false, over = null;
    try { intro = typeof UI!=="undefined" && UI && UI.screen==="intro"; over = typeof S!=="undefined" && S && S.over ? S : null; } catch(e){}
    if (intro && !fb){ fb = document.createElement("a"); fb.className = "ldfb"; fb.target = "_blank"; fb.rel = "noopener"; document.body.appendChild(fb); fb.addEventListener("click", function(){ fb.href = link("feedback"); ev("feedback-click"); }); }
    if (fb){ fb.style.display = intro ? "" : "none"; fb.textContent = es() ? "Comentarios" : "Feedback"; fb.href = link("feedback"); }
    var key = over ? String(over.seed0||"") + ":" + over.turn : null;
    if (over && key!==shownFor){
      shownFor = key; ev("campaign-end");
      var seen = false; try { seen = localStorage.getItem("crudo-lead")==="done"; } catch(e){}
      if (!seen && !card){
        card = document.createElement("div"); card.className = "ldcard"; card.setAttribute("role","dialog");
        card.innerHTML = es()
          ? "<b>Gracias por probar CRUDO</b><p>¿Quieres recibir la próxima versión y The Energy Gazette? Deja tus datos (opcional) y cuéntanos qué mejorar.</p><div class='ldrow'><a target='_blank' rel='noopener'>Dejar mis datos</a><button>Ahora no</button></div>"
          : "<b>Thanks for testing CRUDO</b><p>Want the next version and The Energy Gazette? Leave your details (optional) and tell us what to improve.</p><div class='ldrow'><a target='_blank' rel='noopener'>Leave my details</a><button>Not now</button></div>";
        var a = card.querySelector("a"); a.href = link("end-of-campaign");
        a.addEventListener("click", function(){ ev("lead-click"); try { localStorage.setItem("crudo-lead","done"); } catch(e){} card.remove(); card = null; });
        card.querySelector("button").addEventListener("click", function(){ card.remove(); card = null; });
        document.body.appendChild(card);
      }
    }
    if (!over && card){ card.remove(); card = null; }
  }
  setInterval(tick, 1500); tick();
})();
