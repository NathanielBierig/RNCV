// RNCV finish model v0.8 + defender HP, ported from research/model (state_model.py, model_v07.py).
// Constants come from model.json (export_model.py). Checked against Python by check_model.js.
// A state uses the label codes: choke_arm_position, rnc_style, control, defender_two_on_one,
// choking_hand_tucked, opponent_flattened, chin_tucked ("" = unknown).

(function (root) {
  const b = v => (v === "True" ? 1 : v === "False" ? 0 : 0.5);

  // finish model features (model_v07.encode)
  function encode07(M, st, fat = 0) {
    const arm = { under_chin: 1, over_jaw: 0 }[st.choke_arm_position] ?? 0.5;
    const g = st.rnc_style || "";
    const [f4, other] = g === "figure_four" ? [1, 0] : M.other_locks.includes(g) ? [0, 1]
      : M.open_grips.includes(g) ? [0, 0] : M.unknown_grip;
    const c = st.control || "";
    const [bt, hooks] = c === "body_triangle" ? [1, 0] : c === "two_hooks" ? [0, 1]
      : (c === "one_hook" || c === "none") ? [0, 0] : M.unknown_legs;
    const hand = b(st.choking_hand_tucked);
    const two = b(st.defender_two_on_one) * (1 - (1 - M.deep_keep) * arm * (f4 + other) * hand);
    return { arm, f4, other, bt, hooks, two, chin_tucked: b(st.chin_tucked), flattened: b(st.opponent_flattened),
             def_fatigue: 0, hand_tucked: hand, fatigue: fat };
  }
  const NAMES = { arm: "arm_under", f4: "grip_f4", other: "grip_other", bt: "legs_bt", hooks: "legs_hooks",
                  two: "two_on_one", chin_tucked: "chin_tucked", flattened: "flattened", def_fatigue: "def_fatigue",
                  hand_tucked: "hand_tucked", fatigue: "fatigue" };

  // P(finish | state now), real-world scale (no sampling offset), as sm.predict(beta, x, sample=False)
  function finish(M, st, fat = 0) {
    const x = encode07(M, st, fat);
    let z = M.beta[0];
    M.feats.forEach((f, i) => {
      const key = Object.keys(NAMES).find(k => NAMES[k] === f);
      z += M.beta[2 + i] * x[key];
    });
    return 1 / (1 + Math.exp(-z));
  }

  // squeeze strength 0..1 (state_model.encode + squeeze, v0.6 weights)
  function squeeze(M, st) {
    const p = M.squeeze;
    const arm = { under_chin: 1, over_jaw: 0 }[st.choke_arm_position] ?? 0.5;
    const g = st.rnc_style || "";
    const locked = ["figure_four", "palm_to_palm", "gable", "wrist_pull"];
    const grip = locked.includes(g) ? 1 : M.open_grips.includes(g) ? 0 : 0.5;
    const hand = b(st.choking_hand_tucked);
    let two = b(st.defender_two_on_one) * (1 - (1 - M.deep_keep) * arm * grip * hand);
    two = Math.min(1, two / (1 - (1 - M.deep_keep) * arm * grip * hand));            // undo the finish-model shrink
    const base = arm * (p.w_one_arm + (1 - p.w_one_arm) * grip) + (1 - arm) * p.w_jaw;
    const relief = p.two_relief_open + (p.two_relief_locked - p.two_relief_open) * arm * grip;
    const chin = b(st.chin_tucked);
    const s = base * (1 - relief * two) * (1 - p.chin_relief * chin) * (1 + p.hand_bonus * hand);
    return Math.max(0, Math.min(1, s));
  }

  // HP integrator (state_model.consciousness_trace, with the demo's 2-s ramp-in)
  class HP {
    constructor(M) { this.M = M; this.reset(); }
    reset() { this.B = 0; this.D = 0; this.G = 0; this.el = 0; this.hist = []; }
    step(st, dt, t) {
      const g = this.M.hp;
      const s = squeeze(this.M, st) * Math.min(1, this.el / this.M.landmark);
      const light = s < g.light_below;
      this.B = Math.max(0, this.B + dt * ((1 - g.lingering_share) * s - (light ? this.B / g.blood_recovery_secs : 0)));
      this.D = Math.max(0, this.D + dt * (g.lingering_share * s - (light ? this.D / g.fatigue_recovery_secs : 0)));
      this.G += dt * s; this.el += dt;
      const hp = Math.max(0, 1 - (this.B + this.D) / g.secs_to_out);
      this.hist = this.hist.filter(([tt]) => t - tt <= 1).concat([[t, hp]]);
      return hp;
    }
    get hp() { return Math.max(0, 1 - (this.B + this.D) / this.M.hp.secs_to_out); }
    get fatigue() { return 1 - Math.exp(-this.G / this.M.fatigue_scale); }
    secsLeft() {                                   // HP / drain rate over the last second (estimate)
      const h = this.hist;
      if (this.hp <= 0.01) return 0;
      if (h.length < 4) return null;
      const rate = (h[0][1] - h[h.length - 1][1]) / Math.max(0.2, h[h.length - 1][0] - h[0][0]);
      return rate > 0.01 ? this.hp / rate : null;
    }
  }

  const tier = m => (m >= 3 ? "gold" : m >= 1.5 ? "purple" : m >= 0.8 ? "blue" : "red");
  root.RNCV = { finish, squeeze, encode07, HP, tier };
  if (typeof module !== "undefined") module.exports = root.RNCV;
})(typeof window !== "undefined" ? window : globalThis);
