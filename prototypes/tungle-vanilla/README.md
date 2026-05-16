# Tungle Vanilla Prototype

Throwaway prototype for exploring the rebuilt Tungle interaction model with vanilla HTML/CSS/JS and Web Components.

## Question

Can the old Tungle flow feel coherent as a tiny modern web app: public profile → paint availability → propose times → invitee picks → confirm?

## State machine sketch

```txt
owner-calendar
  TOGGLE_AVAILABILITY
  TOGGLE_PROPOSED
  SET_MODE(compose-invite)

compose-invite
  SEND_INVITE -> invitee-picks

invitee-picks
  INVITEE_PICK
  CONFIRM -> confirmed

confirmed
  RESET -> owner-calendar
```

No persistence. State is rendered live in the right panel.

## Run

From this directory:

```bash
python3 -m http.server 4173
```

Open <http://localhost:4173>.

Variants:

- <http://localhost:4173/?variant=classic>
- <http://localhost:4173/?variant=compact>
- <http://localhost:4173/?variant=public>

## Evidence grounding

Inspired by `notes/ui-evidence-board.md` and `notes/reconstructed-flows.md`. This is not a spec yet. Promote only verified behavior after human screenshot review.
