"""
Unit Tests for anki_core module.
Tests SM-2 scheduler, FSRS scheduler, Template Renderer, Search Parser,
and APKG Importer on real datasets.
"""

import os
import pytest
from backend.app.anki_core import (
    CardType,
    CardQueue,
    Rating,
    CardState,
    DeckConfigParams,
    SM2Scheduler,
    FSRSScheduler,
    get_scheduler,
    TemplateRenderer,
    SearchQueryParser,
    ApkgImporter,
)


def test_sm2_new_card_lifecycle():
    """Test full SM-2 lifecycle from New -> Learning -> Review."""
    cfg = DeckConfigParams(
        learning_steps=[1.0, 10.0],
        graduating_interval=1,
        easy_interval=4,
    )
    sched = SM2Scheduler(cfg)
    card = CardState(card_id=1, card_type=CardType.NEW, queue=CardQueue.NEW)

    now_ts = 1000000
    today_day = 100

    # 1. First rating: AGAIN -> step 0 (1 minute = 60s)
    res = sched.schedule(card, Rating.AGAIN, now_ts, today_day)
    assert res.card_type == CardType.LEARNING
    assert res.queue == CardQueue.LEARNING
    assert res.due == now_ts + 60
    assert res.left == 2

    # 2. Advance to GOOD -> step 1 (10 minutes = 600s)
    card_learning = CardState(
        card_id=1,
        card_type=res.card_type,
        queue=res.queue,
        due=res.due,
        left=res.left,
        factor=res.factor,
    )
    res2 = sched.schedule(card_learning, Rating.GOOD, now_ts + 60, today_day)
    assert res2.card_type == CardType.LEARNING
    assert res2.due == now_ts + 60 + 600
    assert res2.left == 1

    # 3. Complete step with GOOD -> Graduate to Review (1 day)
    card_graduating = CardState(
        card_id=1,
        card_type=res2.card_type,
        queue=res2.queue,
        due=res2.due,
        left=res2.left,
        factor=res2.factor,
    )
    res3 = sched.schedule(card_graduating, Rating.GOOD, now_ts + 660, today_day)
    assert res3.card_type == CardType.REVIEW
    assert res3.queue == CardQueue.REVIEW
    assert res3.interval == 1
    assert res3.due == today_day + 1


def test_sm2_review_card_and_lapses():
    """Test Review ratings and lapse/leech behavior."""
    cfg = DeckConfigParams(
        starting_ease=2500,
        minimum_ease=1300,
        leech_threshold=3,
    )
    sched = SM2Scheduler(cfg)

    # Review card with interval 10 days
    card = CardState(
        card_id=2,
        card_type=CardType.REVIEW,
        queue=CardQueue.REVIEW,
        interval=10,
        factor=2500,
        due=100,
        lapses=2,
    )

    # GOOD rating: 10 * 2.5 = 25 days
    res_good = sched.schedule(card, Rating.GOOD, 2000000, 100)
    assert res_good.interval == 25
    assert res_good.due == 125
    assert res_good.factor == 2500

    # AGAIN rating: lapse, factor drops by 200, lapse count increases to 3 -> Leech!
    res_again = sched.schedule(card, Rating.AGAIN, 2000000, 100)
    assert res_again.lapses == 3
    assert res_again.is_leech is True
    assert res_again.factor == 2300
    assert res_again.card_type == CardType.RELEARNING


def test_fsrs_scheduling():
    """Test FSRS-5 stability and interval calculation."""
    cfg = DeckConfigParams(fsrs_enabled=True, desired_retention=0.90)
    sched = FSRSScheduler(cfg)

    card = CardState(card_id=3, card_type=CardType.NEW, queue=CardQueue.NEW)

    # First rating EASY graduates directly (GOOD would go through learning steps first)
    res = sched.schedule(card, Rating.EASY, 1000000, 100)
    assert res.fsrs_stability is not None
    assert res.fsrs_difficulty is not None
    assert res.card_type == CardType.REVIEW
    assert res.interval >= 1
    assert res.due == 100 + res.interval

    # Subsequent rating GOOD
    card2 = CardState(
        card_id=3,
        card_type=res.card_type,
        queue=res.queue,
        interval=res.interval,
        due=res.due,
        fsrs_stability=res.fsrs_stability,
        fsrs_difficulty=res.fsrs_difficulty,
    )
    res2 = sched.schedule(card2, Rating.GOOD, 1000000 + 86400 * res.interval, 100 + res.interval)
    assert res2.fsrs_stability > res.fsrs_stability
    assert res2.interval > res.interval


def test_template_rendering():
    """Test mustache replacement, conditionals, cloze, hint, and sound tags."""
    renderer = TemplateRenderer(media_base_url="/media")

    qfmt = '<div class="front">{{Kanji}}<br>{{hint:Reading}}</div>'
    afmt = '{{FrontSide}}\n<hr>\n<div class="back">{{Meaning}}{{#Examples}}<br>{{Examples}}{{/Examples}}</div>'
    css = ".front { color: blue; }"

    fields = {
        "Kanji": "躊躇う",
        "Reading": "ためらう",
        "Meaning": "do dự, chần chừ",
        "Examples": "例: 返事を躊躇う",
    }

    result = renderer.render_card(qfmt, afmt, fields, css)

    # Front contains Kanji and Hint structure
    assert "躊躇う" in result["front_html"]
    assert "Show Reading" in result["front_html"]
    assert "ためらう" in result["front_html"]

    # Back contains FrontSide and Meaning and Examples
    assert "躊躇う" in result["back_html"]
    assert "do dự, chần chừ" in result["back_html"]
    assert "例: 返事を躊躇う" in result["back_html"]
    assert result["css"] == css


def test_cloze_rendering():
    """Test cloze deletion filters."""
    renderer = TemplateRenderer()
    qfmt = "{{cloze:Text}}"
    afmt = "{{cloze:Text}}"
    fields = {"Text": "Canberra is the {{c1::capital::city}} of Australia."}

    # Front for Card 1 (ord 0)
    front_res = renderer.render_card(qfmt, afmt, fields, card_ord=0)
    assert "[city]" in front_res["front_html"]

    # Back for Card 1
    assert '<span class="cloze">capital</span>' in front_res["back_html"]


def test_search_query_parser():
    """Test parsing Anki search syntax."""
    query = 'deck:"Japanese N3" tag:Grammar is:due -is:suspended flag:2 "hesitate"'
    parsed = SearchQueryParser.parse(query)

    assert parsed.deck_names == ["Japanese N3"]
    assert parsed.tags == ["Grammar"]
    assert parsed.is_due is True
    assert parsed.is_suspended is False
    assert parsed.flag == 2
    assert parsed.text_terms == ["hesitate"]


def test_apkg_importer_on_real_dataset():
    """Verify ApkgImporter directly against Tieng_Nhat_Tong_hop_N1_to_N5.apkg."""
    apkg_file = r"D:\HUST_Study\2026.1\Web_va_dich_vu_online\Cong_nghe_Web_va_dich_vu_truc_tuyen\Anki_format_datasets\Tieng_Nhat_Tong_hop_N1_to_N5.apkg"
    if not os.path.exists(apkg_file):
        pytest.skip("Dataset file not found at expected path")

    with ApkgImporter(apkg_file) as importer:
        meta = importer.get_metadata()
        assert len(meta.decks) >= 40
        assert meta.total_notes_count > 50000
        assert meta.total_cards_count > 50000

        # Test first batch of notes
        note_batch = next(importer.iter_notes(batch_size=10))
        assert len(note_batch) == 10
        first_note = note_batch[0]
        assert len(first_note.fields) >= 4

        # Test first batch of cards
        card_batch = next(importer.iter_cards(batch_size=10))
        assert len(card_batch) == 10
        first_card = card_batch[0]
        assert first_card.note_id == first_note.id
