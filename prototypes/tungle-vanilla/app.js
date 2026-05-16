const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const hours = ["8a", "9a", "10a", "11a", "12p", "1p", "2p", "3p", "4p", "5p", "6p", "7p"];

const initialState = {
  mode: "owner-calendar", // owner-calendar -> compose-invite -> invitee-picks -> confirmed
  currentUser: "Erin Lariviere",
  publicUrl: "tungle.me/erin",
  meeting: {
    title: "Coffee with Brendan",
    duration: 30,
    location: "Phone or Café Olimpico",
    minimumProposedTimes: 5,
    invitees: ["brendan@example.com"],
  },
  availability: {},
  proposed: [],
  inviteePicks: [],
  confirmedSlot: null,
  activity: ["Prototype loaded: evidence-inspired, not production truth."],
};

function key(day, hour) { return `${day}-${hour}`; }
function createState() {
  const s = structuredClone(initialState);
  days.forEach((day, d) => hours.forEach((hour, h) => {
    const k = key(day, hour);
    s.availability[k] = h >= 1 && h <= 8 && d >= 1 && d <= 5 ? "available" : "busy";
  }));
  [key("Tue", "10a"), key("Wed", "2p"), key("Thu", "11a"), key("Fri", "3p"), key("Mon", "4p")].forEach(k => s.proposed.push(k));
  return s;
}

class TungleApp extends HTMLElement {
  constructor() {
    super();
    this.state = createState();
    this.variant = new URLSearchParams(location.search).get("variant") || "classic";
    document.body.dataset.variant = this.variant;
  }

  connectedCallback() { this.render(); }

  transition(event, payload = {}) {
    const s = this.state;
    const log = (msg) => s.activity.unshift(msg);
    switch (event) {
      case "SET_MODE": s.mode = payload.mode; log(`mode → ${payload.mode}`); break;
      case "TOGGLE_AVAILABILITY": {
        const current = s.availability[payload.slot];
        s.availability[payload.slot] = current === "available" ? "busy" : "available";
        s.proposed = s.proposed.filter(x => x !== payload.slot);
        log(`${payload.slot} marked ${s.availability[payload.slot]}`);
        break;
      }
      case "TOGGLE_PROPOSED": {
        if (s.availability[payload.slot] !== "available") return log(`${payload.slot} is busy; cannot propose`);
        s.proposed = s.proposed.includes(payload.slot) ? s.proposed.filter(x => x !== payload.slot) : [...s.proposed, payload.slot];
        log(`${payload.slot} ${s.proposed.includes(payload.slot) ? "proposed" : "unproposed"}`);
        break;
      }
      case "SEND_INVITE": s.mode = "invitee-picks"; log(`invite sent to ${s.meeting.invitees.join(", ")}`); break;
      case "INVITEE_PICK": {
        s.inviteePicks = s.inviteePicks.includes(payload.slot) ? s.inviteePicks.filter(x => x !== payload.slot) : [...s.inviteePicks, payload.slot];
        log(`invitee ${s.inviteePicks.includes(payload.slot) ? "picked" : "removed"} ${payload.slot}`);
        break;
      }
      case "CONFIRM": s.confirmedSlot = payload.slot || s.inviteePicks[0] || s.proposed[0]; s.mode = "confirmed"; log(`confirmed ${s.confirmedSlot}`); break;
      case "RESET": this.state = createState(); break;
    }
    this.render();
  }

  render() {
    this.innerHTML = `
      <main class="shell">
        <header class="topbar">
          <div class="brand"><div class="brand-mark">t</div><div>Tungle<span class="muted">.me</span></div></div>
          <nav class="nav">
            ${this.navButton("owner-calendar", "My calendar")}
            ${this.navButton("compose-invite", "Create invitation")}
            ${this.navButton("invitee-picks", "Invitee view")}
            ${this.navButton("confirmed", "Confirmed")}
            <button data-action="reset">Reset</button>
          </nav>
        </header>
        <section class="workspace">
          <aside class="panel"><div class="panel-body">${this.profile()}</div></aside>
          <section class="panel">
            <div class="panel-head"><div><h2>${this.mainTitle()}</h2><div class="muted small">Orange = available. Green check = proposed. Red = busy.</div></div><div class="pill hot">${this.state.mode}</div></div>
            <div class="panel-body">${this.mainPanel()}</div>
          </section>
          <aside class="panel debug-panel"><div class="panel-head"><h3>State surface</h3></div><div class="panel-body"><div class="state">${this.safe(JSON.stringify(this.state, null, 2))}</div></div></aside>
        </section>
        ${this.variantBar()}
      </main>`;
    this.bind();
  }

  navButton(mode, label) { return `<button class="${this.state.mode === mode ? "active" : ""}" data-mode="${mode}">${label}</button>`; }
  mainTitle() {
    return {"owner-calendar":"Paint availability", "compose-invite":"Compose a meeting invitation", "invitee-picks":"Invitee picks times", "confirmed":"Meeting confirmed"}[this.state.mode];
  }
  profile() {
    return `<div class="profile-card"><div class="avatar">E</div><div><h2>${this.state.currentUser}</h2><div class="muted">Community Manager</div><div class="pill-list"><span class="pill good">${this.state.publicUrl}</span><span class="pill">Eastern Time</span></div></div><div class="actions"><button class="primary" data-mode="compose-invite">schedule a meeting</button><button class="secondary" data-mode="owner-calendar">edit availability</button></div><div class="timeline">${["Connect calendar", "Paint weekly availability", "Propose best times", "Invitee chooses", "Confirm"].map((x,i)=>`<div class="step ${i <= this.stepIndex() ? "active" : ""}"><div class="dot">${i+1}</div><div>${x}</div></div>`).join("")}</div></div>`;
  }
  stepIndex() { return {"owner-calendar":1,"compose-invite":2,"invitee-picks":3,"confirmed":4}[this.state.mode] ?? 0; }
  mainPanel() {
    if (this.state.mode === "compose-invite") return this.inviteComposer();
    if (this.state.mode === "confirmed") return this.confirmed();
    return this.calendar(this.state.mode === "invitee-picks" ? "invitee" : "owner");
  }
  inviteComposer() {
    return `<div class="invite-card"><label class="field">Title<input value="${this.safe(this.state.meeting.title)}" readonly /></label><label class="field">Duration<select><option>${this.state.meeting.duration} minutes</option></select></label><label class="field">Location<input value="${this.safe(this.state.meeting.location)}" readonly /></label><div><strong>Proposed times</strong><div class="pill-list">${this.state.proposed.map(s => `<span class="pill good">${s}</span>`).join("")}</div></div><div class="actions"><button class="primary" data-action="send">Send invitation</button><button class="secondary" data-mode="owner-calendar">Adjust times</button></div></div>`;
  }
  confirmed() {
    return `<div class="invite-card"><h2>You're all set.</h2><p class="muted">${this.state.meeting.title} is confirmed for <strong>${this.state.confirmedSlot || "a proposed time"}</strong>.</p><div class="actions"><button class="primary" data-action="reset">Start over</button></div></div>`;
  }
  calendar(role) {
    return `<div class="calendar">${days.map(day => `<div class="day"><div class="day-head">${day}</div>${hours.map(hour => { const slot = key(day,hour); return `<div class="slot" title="${slot}" data-slot="${slot}" data-role="${role}" data-state="${this.state.availability[slot]}" data-proposed="${this.state.proposed.includes(slot)}"><span class="small muted">${hour}</span></div>`; }).join("")}</div>`).join("")}</div>${role === "invitee" ? `<div class="actions" style="margin-top:14px"><button class="primary" data-action="confirm">Confirm selected time</button></div>` : `<div class="small muted" style="margin-top:12px">Click slots to flip busy/available. Option-click available slots to toggle proposed.</div>`}`;
  }
  variantBar() { return `<div class="variant-bar">${["classic","compact","public"].map(v => `<a class="${this.variant===v?"active":""}" href="?variant=${v}">${v}</a>`).join("")}</div>`; }
  safe(value) { return String(value).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c])); }
  bind() {
    this.querySelectorAll("[data-mode]").forEach(btn => btn.addEventListener("click", () => this.transition("SET_MODE", {mode: btn.dataset.mode})));
    this.querySelectorAll("[data-action='reset']").forEach(btn => btn.addEventListener("click", () => this.transition("RESET")));
    this.querySelectorAll("[data-action='send']").forEach(btn => btn.addEventListener("click", () => this.transition("SEND_INVITE")));
    this.querySelectorAll("[data-action='confirm']").forEach(btn => btn.addEventListener("click", () => this.transition("CONFIRM")));
    this.querySelectorAll("[data-slot]").forEach(slot => slot.addEventListener("click", (event) => {
      const selected = slot.dataset.slot;
      if (slot.dataset.role === "invitee") return this.transition("INVITEE_PICK", {slot: selected});
      this.transition(event.altKey ? "TOGGLE_PROPOSED" : "TOGGLE_AVAILABILITY", {slot: selected});
    }));
  }
}

customElements.define("tungle-app", TungleApp);
