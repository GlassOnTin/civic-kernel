# The clubhouse demonstration — a half-hour run sheet

*The demonstration offered at the end of
[the invitation](shadow-agm-invitation.md), scripted in the open like everything else.
Audience: a club committee, five to ten people, one laptop, ideally a screen they can
all see. Twenty minutes of showing, ten of questions. Every command below is exercised
by the project's own test suite; the two rigging demos print exactly the failure lines
quoted here.*

## Kit and preparation

**The night before**

- A laptop with Python 3 and a current browser (the verifier needs a 2025-or-later
  Chrome, Firefox or Safari — it says so itself rather than pretending).
- Clone the repo and run the success test once; if it ends `ALL GREEN`, everything the
  demo needs works on this machine:

  ```sh
  git clone https://github.com/GlassOnTin/civic-kernel && cd civic-kernel
  pip install -r requirements.txt
  ./proto/test.sh          # ~a minute; ALL GREEN = the demo will work
  ```

- **If the clubhouse has wifi:** use the live pages
  ([verifier](https://glassontin.github.io/civic-kernel/verifier.html),
  [cast](https://glassontin.github.io/civic-kernel/cast.html)) — then volunteers can
  use their own phones.
- **If it might not:** serve the repo locally and use the laptop for everything:

  ```sh
  python3 -m http.server 8000     # then http://localhost:8000/verifier.html
  ```

  (Phones can't reach a local server without network fiddling — offline, just pass the
  laptop around instead. It demonstrates the same thing.)

**Five minutes before**

- Two browser tabs open: `verifier.html` and `cast.html`.
- One terminal open in the repo directory.
- `rm -rf /tmp/demo-*` if you've rehearsed on this machine.

## The run sheet

### 0–3 min — the frame

**Say:** "Your AGM stays exactly as it is: hands go up, hands are counted, that
decides. What I'm going to show you is the shadow: a sealed ballot that runs alongside
one vote, decides nothing, and can be checked afterwards by anyone — including people
who distrust all of us. I'll run an election, you'll vote in it, and then we'll try to
rig it and watch what happens."

No slides. The demo is the talk.

### 3–9 min — check a finished election

**Do:** verifier tab → **Load the reference election**.

**Expect:** checks turn green section by section; the whole run takes about 15–25
seconds in the browser. Narrate over it, one plain line per section as it lands — each
section heading already carries its own plain-speech line (hover or tap it):

**Say, roughly:** "Sixty members, sealed ballots. It's checking the paperwork is in
the published format… that every event was signed… that the history was never
rewritten — those fingerprints are what your federation would countersign… that every
voter was a real member, without learning which member cast which ballot… that no
device cheated… every sealed envelope, one by one — this is the slow bit, each ballot
proves it came from *some* member on the list… the count, recomputed without opening a
single envelope… and finally that this record matches the copy the world saw — that's
your newsletter's three lines."

**Land on the verdict line and read it aloud:** *"…nobody had to trust the shed."*

### 9–12 min — find one voter's ballot

**Say:** "Derek is one of the sixty. In a real election only Derek would know his
secret. This demo publishes its secrets on purpose — so you can play Derek."

**Do:** in the *Find your own ballot* panel, press **Derek's secret**, then **Look up
my ballot**.

**Expect:** his linking tag, one ballot, **counted**. Point at the box: "The record
says *someone* on the roster cast this, exactly once. It will never say Derek. He can
see his vote counted; he can't prove to anyone else which way he voted — so there's
nothing to sell and nothing a bully can demand afterwards."

(If someone asks: press Nalini's too — she re-voted; her first ballot shows
**superseded**. That's the answer to over-the-shoulder coercion.)

### 12–18 min — a volunteer votes, and the count moves

**Say:** "Now one of you votes as Derek — a re-vote, like Nalini's."

**Do (volunteer, on their phone via the live page, or on the laptop):**

1. cast tab → **Load the reference election** → press **Derek's secret**.
2. The page shows: *Enrolled… you are Derek Wainwright.*
3. Pick **Sandra Okafor** (Derek originally voted Keith — the count will visibly move).
4. **Set the attempt number to 6** — Derek has cast before; a later ballot must carry a
   higher number, and the page says so. *(Forget this and the new ballot is silently
   superseded by his old one — the demo still verifies, but the count won't move.)*
5. **Seal my choice** → the sealed envelope appears. Ask the room: "cast it, or test
   the device first?" If they say test: **Challenge** — the envelope opens, is spoiled
   forever, and you explain a lying phone gets caught exactly here. Seal again.
6. **Cast it** → a ballot file downloads. Get it to the laptop (email works; that's
   the point — the collection channel can be dumb).

**Do (presenter, terminal):**

```sh
python3 proto/clubvote.py collect proto/out /tmp/demo-yourvote ballot-*.json
python3 proto/verify.py /tmp/demo-yourvote
```

**Expect (~15 s):** green to the bottom, the counts now
**Sandra Okafor 9, Keith Bramall 5** (they were 8–6), and the recast line reading
*"17 valid ballots, 14 distinct linking tags counted, 3 silently superseded."*

**Say:** "Your envelope replaced Derek's old one. Nobody watching the box — including
me — can tell which envelope changed, or what either one said. And the total moved by
exactly one."

### 18–24 min — now we rig it, twice

**Say:** "I'm the corrupt committee now. I hold every key the committee holds. First
rig: I take Sandra's sealed ballot and swap it for a forged one — my own envelope,
voting Keith."

**Do:**

```sh
python3 proto/clubvote.py tamper proto/out /tmp/demo-rigged box
```

Drag the `/tmp/demo-rigged` folder onto the verifier page.

**Expect:** red, at the ballot checks:
*"ballot[13] ring signature does not verify (no roster member signed this ballot with
this nullifier)."*

**Say:** "Every hash and signature I could fake, I faked. The one thing I can't make
is a member's proof — I'm not on the list. The page that caught me shares no code with
me; a stranger's copy would catch it too."

**Say:** "Second rig — the subtle one. I don't forge anything. I *erase* your re-vote
from history, re-sign everything honestly, and recount. Every remaining piece is
genuine."

**Do:**

```sh
python3 proto/clubvote.py tamper proto/out /tmp/demo-erased drop
```

Drag `/tmp/demo-erased` onto the verifier.

**Expect:** green all the way down — until the last check:
*"no valid receipt from ['did:web:sheffield-star.example'] matches this log's closing
head — the history under audit is not the history the world saw."*

**Say:** "Everything inside the record agreed, because everything inside the record
was genuine — minus one inconvenient ballot. The only thing that objected is the copy
that lives outside my reach: the newspaper's three lines. *That* is why the invitation
asks your federation to countersign and your newsletter to print a fingerprint. Those
two small favours are what just caught me."

### 24–30 min — the season, and questions

**Say:** "That's the whole machine. For your AGM it looks like: members enrol with
[whoever keeps your register] in the weeks before — five minutes each, name or plot
number, their choice. Two neighbouring societies countersign three times. Three
trustees hold the unsealing keys — any two suffice, none can peek alone. At the
meeting: hands first, as always; then whoever wants casts this shadow ballot. The
newsletter prints three lines. Everyone gets one link to check the lot."

Close with the honest limits, unprompted — they're in
[the invitation](shadow-agm-invitation.md) and they land better said aloud: the record
is public forever; whoever collects the files sees who handed one in; nobody can prove
their own vote and that's deliberate; it's a research prototype and they'd be first;
and if every computer catches fire, the AGM is unaffected.

**Leave behind:** the printed invitation, and the three links written on it — the
verifier, the cast page, the architecture.

## Rough edges to know about (so they don't know about them first)

- The browser verifier needs a current browser for signature checking; on an old one
  it says **CANNOT VERIFY HERE** rather than pretending — if the club laptop is
  ancient, verify in the terminal instead (`python3 proto/verify.py proto/out`).
- The full browser verification is 15–25 seconds of visible progress. That's the
  per-ballot membership proof — narrate it; don't apologise for it. The terminal one
  is similar (~15 s).
- Casting on phones needs the live (https) pages, hence internet. No internet → laptop
  only; the demonstration is unchanged.
- If the volunteer forgets attempt number 6, the verify still passes but the count
  stays 8–6 (their ballot was superseded by Derek's earlier one, seq 5 beats seq 1 —
  last *ballot* counts, not last *timestamp*). Recover in one line: it's a live
  demonstration of the re-vote rule — then cast again at 6.
- Reset between rehearsals: `rm -rf /tmp/demo-*`. Nothing in the demo modifies the
  repo or `proto/out`.
