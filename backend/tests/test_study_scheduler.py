"""
Tests for the study session core: SM-2 / FSRS schedulers, interval previews,
template renderer and the study queue API.

Run from the repository root:  python -m pytest backend/tests
"""

import itertools
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.anki_core import (
    CardQueue,
    CardState,
    CardType,
    DeckConfigParams,
    FSRSScheduler,
    Rating,
    SM2Scheduler,
    TemplateRenderer,
)
from app.anki_core.scheduler.base import format_due, fuzz_bounds

NOW = 1_800_000_000
TODAY = 20_833


def advance(card: CardState, res) -> CardState:
    """Apply a ScheduleResult to a card state."""
    return CardState(
        card_id=card.card_id,
        card_type=res.card_type,
        queue=res.queue,
        due=res.due,
        interval=res.interval,
        factor=res.factor,
        reps=res.reps,
        lapses=res.lapses,
        left=res.left,
        fsrs_stability=res.fsrs_stability,
        fsrs_difficulty=res.fsrs_difficulty,
    )


def sample_states():
    """A spread of card states covering every card type."""
    yield CardState(card_id=1)
    for left in (1, 2):
        yield CardState(card_id=1, card_type=CardType.LEARNING, queue=CardQueue.LEARNING, due=NOW, left=left)
    yield CardState(card_id=1, card_type=CardType.RELEARNING, queue=CardQueue.LEARNING, due=NOW, interval=3, left=1)
    for ivl, factor in ((1, 2500), (10, 2500), (100, 1300), (400, 3000)):
        yield CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                        due=TODAY, interval=ivl, factor=factor, reps=5)
    yield CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW, due=TODAY,
                    interval=10, factor=2500, fsrs_stability=12.0, fsrs_difficulty=6.0)


SCHEDULERS = [
    SM2Scheduler(DeckConfigParams()),
    SM2Scheduler(DeckConfigParams(relearning_steps=[10.0, 60.0], learning_steps=[1.0, 10.0, 60.0])),
    FSRSScheduler(DeckConfigParams(fsrs_enabled=True)),
    FSRSScheduler(DeckConfigParams(fsrs_enabled=True, desired_retention=0.8, relearning_steps=[])),
]


# ---------------------------------------------------------------------------
# Previews must match reality
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sched", SCHEDULERS, ids=lambda s: type(s).__name__)
def test_preview_matches_schedule(sched):
    for card in sample_states():
        preview = sched.describe_next_intervals(card, NOW, TODAY)
        for rating in Rating:
            res = sched.schedule(card, rating, NOW, TODAY)
            assert preview[rating.name.lower()] == format_due(res, NOW, TODAY), (card, rating)


def test_preview_examples_sm2():
    sched = SM2Scheduler(DeckConfigParams(enable_fuzz=False))
    new = sched.describe_next_intervals(CardState(card_id=1), NOW, TODAY)
    assert new == {"again": "1m", "hard": "6m", "good": "10m", "easy": "4d"}
    relearn = CardState(card_id=1, card_type=CardType.RELEARNING, queue=CardQueue.LEARNING, interval=1, left=1)
    assert sched.describe_next_intervals(relearn, NOW, TODAY)["again"] == "10m"


# ---------------------------------------------------------------------------
# No card loops: a (re)learning card is never immediately due again
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sched", SCHEDULERS, ids=lambda s: type(s).__name__)
def test_answered_card_is_never_due_immediately(sched):
    for card in sample_states():
        for rating in Rating:
            res = sched.schedule(card, rating, NOW, TODAY)
            if res.card_type in (CardType.LEARNING, CardType.RELEARNING):
                assert res.queue in (CardQueue.LEARNING, CardQueue.SUSPENDED)
                assert res.due >= NOW + 60, "learning due must be a future timestamp"
            else:
                assert res.queue in (CardQueue.REVIEW, CardQueue.SUSPENDED)
                assert TODAY + 1 <= res.due < 10**7, "review due must be a future day number"


@pytest.mark.parametrize("sched", SCHEDULERS, ids=lambda s: type(s).__name__)
def test_random_sessions_always_terminate(sched):
    """Any sequence of answers ends in review state after at most a few GOODs."""
    for seq in itertools.product(list(Rating), repeat=4):
        card = CardState(card_id=1)
        now = NOW
        for r in seq:
            card = advance(card, sched.schedule(card, r, now, TODAY))
            now += 3600
        for _ in range(5):
            if card.card_type == CardType.REVIEW:
                break
            card = advance(card, sched.schedule(card, Rating.GOOD, now, TODAY))
        assert card.card_type == CardType.REVIEW


# ---------------------------------------------------------------------------
# SM-2 details
# ---------------------------------------------------------------------------
def test_sm2_review_interval_ordering():
    sched = SM2Scheduler(DeckConfigParams())
    for card in sample_states():
        if card.card_type != CardType.REVIEW:
            continue
        ivls = sched.review_intervals(card)
        assert card.interval < ivls[Rating.HARD] < ivls[Rating.GOOD] < ivls[Rating.EASY]


def test_sm2_overdue_bonus():
    """A card answered 10 days late was remembered longer -> bigger intervals (Anki v2)."""
    sched = SM2Scheduler(DeckConfigParams(enable_fuzz=False))
    on_time = CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                        due=TODAY, interval=10, factor=2500)
    late = on_time.model_copy(update={"due": TODAY - 10})
    assert sched.review_intervals(on_time, TODAY) == {Rating.HARD: 12, Rating.GOOD: 25, Rating.EASY: 32}
    # hard = (10 + 10//4) * 1.2 = 14.4, good = (10 + 5) * 2.5 = 37.5, easy = 20 * 2.5 * 1.3 = 65
    assert sched.review_intervals(late, TODAY) == {Rating.HARD: 14, Rating.GOOD: 38, Rating.EASY: 65}


def test_fuzz_bounds_match_anki():
    assert fuzz_bounds(1) == (1, 1) and fuzz_bounds(2) == (2, 2)
    assert fuzz_bounds(4) == (3, 5)        # delta = 1 + 0.15 * 1.5 = 1.225
    assert fuzz_bounds(25) == (22, 28)     # delta = 1 + 0.675 + 1.3 + 0.25 = 3.225
    lo, hi = fuzz_bounds(365)
    assert lo < 365 < hi and hi - lo < 50


@pytest.mark.parametrize("make", [lambda c: SM2Scheduler(c), lambda c: FSRSScheduler(c.model_copy(update={"fsrs_enabled": True}))])
def test_fuzz_is_deterministic_bounded_and_spreads_cards(make):
    sched = make(DeckConfigParams())
    plain = make(DeckConfigParams(enable_fuzz=False))
    goods = set()
    for cid in range(1, 200):
        card = CardState(card_id=cid, card_type=CardType.REVIEW, queue=CardQueue.REVIEW, due=TODAY,
                         interval=30, factor=2500, reps=7, fsrs_stability=30.0, fsrs_difficulty=5.0)
        a = sched.schedule(card, Rating.GOOD, NOW, TODAY).interval
        assert a == sched.schedule(card, Rating.GOOD, NOW, TODAY).interval  # same input -> same result
        base = plain.schedule(card, Rating.GOOD, NOW, TODAY).interval
        lo, hi = fuzz_bounds(base)
        assert lo <= a <= hi
        ivls = [sched.schedule(card, r, NOW, TODAY).interval for r in (Rating.HARD, Rating.GOOD, Rating.EASY)]
        assert ivls[0] < ivls[1] < ivls[2]
        goods.add(a)
    assert len(goods) >= 5, "fuzz should spread cards over several days"


def test_sm2_relearning_uses_all_steps():
    sched = SM2Scheduler(DeckConfigParams(relearning_steps=[10.0, 60.0]))
    card = CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW, due=TODAY, interval=20)
    lapsed = advance(card, sched.schedule(card, Rating.AGAIN, NOW, TODAY))
    assert lapsed.card_type == CardType.RELEARNING and lapsed.left == 2
    step2 = advance(lapsed, sched.schedule(lapsed, Rating.GOOD, NOW, TODAY))
    assert step2.card_type == CardType.RELEARNING and step2.due == NOW + 3600
    done = sched.schedule(step2, Rating.GOOD, NOW, TODAY)
    assert done.card_type == CardType.REVIEW


def test_leech_threshold_and_half_threshold():
    sched = SM2Scheduler(DeckConfigParams(leech_threshold=8))
    flagged = [n for n in range(1, 20) if sched.is_leech(n)]
    assert flagged == [8, 12, 16]


def test_leech_suspend():
    sched = SM2Scheduler(DeckConfigParams(leech_threshold=1, leech_action="suspend"))
    card = CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW, due=TODAY, interval=5)
    res = sched.schedule(card, Rating.AGAIN, NOW, TODAY)
    assert res.is_leech and res.queue == CardQueue.SUSPENDED


# ---------------------------------------------------------------------------
# FSRS details
# ---------------------------------------------------------------------------
def test_fsrs_initial_difficulty_is_ordered():
    sched = FSRSScheduler(DeckConfigParams(fsrs_enabled=True))
    d = [sched.init_difficulty(r) for r in Rating]
    assert d[0] > d[1] > d[2] > d[3] >= 1.0  # Again hardest ... Easy easiest
    assert all(1.0 <= x <= 10.0 for x in d)


def test_fsrs_interval_matches_retention():
    s = 30.0
    at90 = FSRSScheduler(DeckConfigParams(fsrs_enabled=True, desired_retention=0.90))
    at80 = FSRSScheduler(DeckConfigParams(fsrs_enabled=True, desired_retention=0.80))
    assert at90.next_interval(s) == 30  # by definition R(S) = 90%
    ivl80 = at80.next_interval(s)
    assert ivl80 > 30
    assert abs(at80.retrievability(ivl80, s) - 0.80) < 0.01


def test_fsrs_new_card_uses_learning_steps():
    sched = FSRSScheduler(DeckConfigParams(fsrs_enabled=True))
    res = sched.schedule(CardState(card_id=1), Rating.AGAIN, NOW, TODAY)
    assert res.card_type == CardType.LEARNING
    assert res.due == NOW + 60  # 1 minute, a timestamp (not a day number)


def test_switch_sm2_to_fsrs_keeps_progress():
    """A mature SM-2 card must not be reset when the deck switches to FSRS."""
    card = CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                     due=TODAY, interval=100, factor=2500, reps=10)
    sm2_good = SM2Scheduler(DeckConfigParams()).schedule(card, Rating.GOOD, NOW, TODAY).interval
    fsrs_good = FSRSScheduler(DeckConfigParams(fsrs_enabled=True)).schedule(card, Rating.GOOD, NOW, TODAY)
    assert fsrs_good.interval > 100
    assert 0.3 * sm2_good <= fsrs_good.interval <= 3 * sm2_good
    assert fsrs_good.fsrs_stability > 100


def test_switch_fsrs_to_sm2_keeps_progress():
    fsrs = FSRSScheduler(DeckConfigParams(fsrs_enabled=True))
    card = CardState(card_id=1, card_type=CardType.REVIEW, queue=CardQueue.REVIEW,
                     due=TODAY, interval=60, factor=2500, fsrs_stability=60.0, fsrs_difficulty=5.0)
    assert fsrs.schedule(card, Rating.GOOD, NOW, TODAY).interval > 60
    assert SM2Scheduler(DeckConfigParams(enable_fuzz=False)).schedule(card, Rating.GOOD, NOW, TODAY).interval == 150


# ---------------------------------------------------------------------------
# Template renderer
# ---------------------------------------------------------------------------
R = TemplateRenderer(media_base_url="/media/u1")


def front(qfmt, fields, **kw):
    return R.render_card(qfmt, "", fields, **kw)["front_html"]


def test_field_names_with_spaces_and_nested_sections():
    tpl = "{{#Example Sentence}}<i>{{Example Sentence}}</i>{{#Note}}+{{Note}}{{/Note}}{{/Example Sentence}}"
    assert front(tpl, {"Example Sentence": "x", "Note": "n"}) == "<i>x</i>+n"
    assert front(tpl, {"Example Sentence": "", "Note": "n"}) == ""
    assert front("{{^Note}}none{{/Note}}", {"Note": "<br>"}) == "none"
    assert front("{{#Img}}has{{/Img}}", {"Img": '<img src="a.png">'}) == "has"


def test_field_content_is_not_reparsed_as_template():
    assert front("{{Front}}", {"Front": "a {{Back}} b", "Back": "SECRET"}) == "a {{Back}} b"


def test_japanese_filters():
    f = {"Reading": "漢字[かんじ] を 読[よ]む"}
    assert front("{{furigana:Reading}}", f) == "<ruby><rb>漢字</rb><rt>かんじ</rt></ruby> を<ruby><rb>読</rb><rt>よ</rt></ruby>む"
    assert front("{{kana:Reading}}", f) == "かんじ をよむ"
    assert front("{{kanji:Reading}}", f) == "漢字 を読む"


def test_type_answer_does_not_leak_on_front():
    out = R.render_card("{{Front}} {{type:Back}}", "{{FrontSide}}<hr>{{type:Back}}", {"Front": "Q", "Back": "SECRET"})
    assert "SECRET" not in out["front_html"]
    assert "anki-typeans" in out["front_html"]
    assert "SECRET" in out["back_html"]


def test_type_cloze_answer():
    out = R.render_card("{{cloze:Text}}{{type:cloze:Text}}", "{{cloze:Text}}{{type:cloze:Text}}",
                        {"Text": "{{c1::Hà Nội}} là thủ đô"})
    assert "Hà Nội" not in out["front_html"]
    assert "Hà Nội" in out["back_html"]


def test_special_fields():
    special = {"Tags": "N3 verb", "Deck": "JP::N3", "Subdeck": "N3", "Card": "Card 1", "Type": "Basic"}
    assert front("{{Tags}}|{{Deck}}|{{Subdeck}}|{{Card}}|{{Type}}", {}, special_fields=special) == \
        "N3 verb|JP::N3|N3|Card 1|Basic"


def test_sanitizes_untrusted_field_html():
    evil = '<script>alert(1)</script><img src="x.png" onerror="alert(2)"><a href="javascript:alert(3)">l</a>'
    out = front("{{F}}", {"F": evil})
    assert "<script" not in out and "onerror" not in out and "javascript:" not in out
    assert '<img src="/media/u1/x.png"' in out


def test_sound_filename_is_escaped():
    out = front("{{A}}", {"A": "[sound:a'b\"<x>.mp3]"})
    assert "a'b" not in out.split("data-sound=")[0]
    assert '<x>' not in out
    assert "a%27b%22%3Cx%3E.mp3" in out


def test_hint_ids_are_unique():
    out = front("{{hint:A}}{{hint:B}}", {"A": "1", "B": "2"})
    import re
    ids = re.findall(r'id="(hint_body_\d+)"', out)
    assert len(ids) == 2 and ids[0] != ids[1]


# ---------------------------------------------------------------------------
# Study API: deck options are honoured, quotas, learn-ahead
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_study_queue_uses_deck_config_and_does_not_loop():
    from app.main import app
    from app.db.session import engine, Base, AsyncSessionLocal
    from app.models.deck import Deck
    from app.models.notetype import Notetype, NotetypeField, NotetypeTemplate
    from app.models.card import Card, Note

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"study-{uuid.uuid4().hex[:8]}@example.com"
        login = (await client.post("/api/v1/auth/dev-login", json={"email": email})).json()
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        user_id = login["user"]["id"]

        base_id = uuid.uuid4().int % 10**12
        deck_id, nt_id = base_id, base_id + 1
        async with AsyncSessionLocal() as db:
            db.add(Deck(id=deck_id, user_id=user_id, name="Test Deck"))
            nt = Notetype(id=nt_id, user_id=user_id, name="Basic", css=".card{}")
            nt.fields = [NotetypeField(name="Front", ord=0), NotetypeField(name="Back", ord=1)]
            nt.templates = [NotetypeTemplate(name="Card 1", ord=0, qfmt="{{Front}}",
                                             afmt="{{FrontSide}}<hr id=answer>{{Back}}")]
            db.add(nt)
            await db.flush()
            for i in range(3):
                nid = base_id + 10 + i
                db.add(Note(id=nid, user_id=user_id, notetype_id=nt_id, guid=f"g{nid}", fields=[f"Q{i}", f"A{i}"], tags=[]))
                db.add(Card(id=nid, user_id=user_id, note_id=nid, deck_id=deck_id, due=i))
            await db.commit()

        # Deck options: 1 new card per day, switch to FSRS
        res = await client.put(f"/api/v1/decks/{deck_id}/config", headers=headers,
                               json={"new_per_day": 1, "fsrs_enabled": True})
        assert res.status_code == 200, res.text
        assert res.json()["fsrs_enabled"] is True
        assert (await client.get(f"/api/v1/decks/{deck_id}/config", headers=headers)).json()["new_per_day"] == 1
        bad = await client.put(f"/api/v1/decks/{deck_id}/config", headers=headers, json={"fsrs_params": [1, 2]})
        assert bad.status_code == 422

        q = (await client.get("/api/v1/study/queue", params={"deck_id": deck_id}, headers=headers)).json()
        assert q["remaining_counts"]["new"] == 1
        card = q["card"]
        assert card["next_intervals"]["again"] == "1m"

        # Again 3x on the same new card: must count as ONE new card, and must never be due "now"
        for _ in range(3):
            ans = await client.post("/api/v1/study/answer", headers=headers,
                                    json={"card_id": card["id"], "rating": 1})
            assert ans.status_code == 200
            q = (await client.get("/api/v1/study/queue", params={"deck_id": deck_id}, headers=headers)).json()
            # Only the learning card remains (new quota used up) -> served via learn-ahead, not looping
            assert q["card"]["id"] == card["id"]
            assert q["remaining_counts"]["new"] == 0
            assert q["remaining_counts"]["learning"] == 1

        async with AsyncSessionLocal() as db:
            c = await db.get(Card, card["id"])
            assert c.fsrs_stability is not None, "FSRS from deck options must be used"
            assert c.due > 10**9, "learning due is a timestamp"

        invalid = await client.post("/api/v1/study/answer", headers=headers, json={"card_id": card["id"], "rating": 7})
        assert invalid.status_code == 422


def test_rendered_html_has_no_inline_javascript():
    """Hint links and audio buttons use data-* attributes (frontend sanitizes with DOMPurify)."""
    out = R.render_card("{{hint:A}} [sound:a.mp3] {{B}}", "{{FrontSide}}", {"A": "hint", "B": "x"})
    for html_out in (out["front_html"], out["back_html"]):
        assert "onclick" not in html_out.lower()
    assert 'data-hint-target="hint_body_' in out["front_html"]
    assert 'data-src="/media/u1/a.mp3"' in out["front_html"]
