// Checks the JavaScript port against Python's reference values in model.json:  node tools/app/check_model.js
const M = require("./model.json");
const R = require("./rncv_model.js");
let bad = 0;
for (const r of M.refs) {
  const f = R.finish(M, r.state), s = R.squeeze(M, r.state);
  const ok = Math.abs(f - r.finish) < 1e-9 && Math.abs(s - r.squeeze) < 1e-9;
  if (!ok) bad++;
  console.log(ok ? "OK " : "BAD", JSON.stringify(r.state), "finish", f.toFixed(4), "vs", r.finish.toFixed(4),
              "squeeze", s.toFixed(4), "vs", r.squeeze.toFixed(4));
}
process.exit(bad ? 1 : 0);
