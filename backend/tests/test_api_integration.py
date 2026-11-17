"""
Integration Tests for FastAPI Endpoints.
Verifies Auth, Decks, Study Queue, Quiz Game Engine, and APKG Ingestion.
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import engine, Base, AsyncSessionLocal
from backend.app.services.import_service import ImportService


@pytest.mark.asyncio
async def test_full_api_workflow():
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Dev login
        login_res = await client.post(
            "/api/v1/auth/dev-login",
            json={"email": "tester@example.com", "display_name": "Test Scholar"},
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        token = login_data["access_token"]
        user_id = login_data["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Check /auth/me
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "tester@example.com"

        # 4. Ingest sample dataset into user account
        apkg_path = r"D:\HUST_Study\2026.1\Web_va_dich_vu_online\Cong_nghe_Web_va_dich_vu_truc_tuyen\Anki_format_datasets\Tieng_Nhat_Tong_hop_N1_to_N5.apkg"
        if os.path.exists(apkg_path):
            async with AsyncSessionLocal() as db:
                await ImportService.process_apkg_import(
                    file_path=apkg_path,
                    user_id=user_id,
                    job_id="test_job_1",
                    db=db,
                )

            # 5. Fetch Decks Hierarchy
            decks_res = await client.get("/api/v1/decks", headers=headers)
            assert decks_res.status_code == 200
            decks_tree = decks_res.json()
            assert len(decks_tree) > 0
            assert any("Tiếng Nhật Tổng Hợp" in d["name"] for d in decks_tree)

            # 6. Fetch Study Card
            study_res = await client.get("/api/v1/study/queue", headers=headers)
            assert study_res.status_code == 200
            study_data = study_res.json()
            assert study_data["card"] is not None
            card = study_data["card"]
            assert "front_html" in card["rendered"]
            assert "back_html" in card["rendered"]
            assert "again" in card["next_intervals"]

            # 7. Answer Card (Good = 3)
            answer_res = await client.post(
                "/api/v1/study/answer",
                headers=headers,
                json={"card_id": card["id"], "rating": 3, "time_taken_ms": 2500},
            )
            assert answer_res.status_code == 200
            ans_data = answer_res.json()
            assert ans_data["xp_awarded"] > 0
            assert ans_data["rating"] == 3

            # 8. Start Quiz Game
            game_res = await client.post(
                "/api/v1/games/start",
                headers=headers,
                json={"deck_id": card["deck_id"], "total_questions": 5, "srs_sync": True},
            )
            assert game_res.status_code == 200
            game_data = game_res.json()
            session_id = game_data["session_id"]
            assert len(game_data["questions"]) > 0
            q1 = game_data["questions"][0]
            assert len(q1["options"]) == 4

            # 9. Submit Quiz Answer
            sub_res = await client.post(
                "/api/v1/games/answer",
                headers=headers,
                json={
                    "session_id": session_id,
                    "card_id": q1["card_id"],
                    "selected_key": "A",
                    "response_time_ms": 3000,
                },
            )
            assert sub_res.status_code == 200
            sub_data = sub_res.json()
            assert "is_correct" in sub_data
            assert "explanation" in sub_data
            assert sub_data["srs_updated"] is True

            # 10. Finish Quiz Game
            fin_res = await client.post(
                "/api/v1/games/finish",
                headers=headers,
                json={"session_id": session_id},
            )
            assert fin_res.status_code == 200
            fin_data = fin_res.json()
            assert "accuracy_percent" in fin_data
            assert "score" in fin_data

            # 11. Card Browser API verification
            browse_res = await client.get("/api/v1/cards/browse?page=1&page_size=10", headers=headers)
            assert browse_res.status_code == 200
            browse_data = browse_res.json()
            assert browse_data["total"] > 0
            assert len(browse_data["items"]) > 0
            test_card_id = browse_data["items"][0]["id"]

            # 12. Card Detail & Edit API
            card_detail_res = await client.get(f"/api/v1/cards/{test_card_id}", headers=headers)
            assert card_detail_res.status_code == 200
            assert "rendered" in card_detail_res.json()

            patch_res = await client.patch(
                f"/api/v1/cards/{test_card_id}",
                headers=headers,
                json={"is_suspended": True},
            )
            assert patch_res.status_code == 200

            # 13. User Profile Update
            profile_res = await client.put(
                "/api/v1/auth/me",
                headers=headers,
                json={"display_name": "Senior Scholar"},
            )
            assert profile_res.status_code == 200
            assert profile_res.json()["display_name"] == "Senior Scholar"

            # 14. Dev Users List
            dev_users_res = await client.get("/api/v1/auth/dev-users")
            assert dev_users_res.status_code == 200
            assert len(dev_users_res.json()) > 0

            # 15. Stats Overview
            stats_res = await client.get("/api/v1/stats/overview", headers=headers)
            assert stats_res.status_code == 200
            stats_data = stats_res.json()
            assert stats_data["total_cards"] > 0
            assert "retention_rate" in stats_data

            # 16. Comprehensive Deck Stats (Hizashi Equivalent)
            deck_stats_res = await client.get(f"/api/v1/stats/deck/{card['deck_id']}", headers=headers)
            assert deck_stats_res.status_code == 200
            d_stats = deck_stats_res.json()
            assert "overview" in d_stats
            assert d_stats["overview"]["total_cards"] > 0
            assert "distribution" in d_stats
            assert "new" in d_stats["distribution"]
            assert "learned" in d_stats
            assert "tier_counts" in d_stats["learned"]

            # 17. Notetypes List API
            nt_res = await client.get("/api/v1/cards/notetypes/list", headers=headers)
            assert nt_res.status_code == 200
            notetypes = nt_res.json()
            assert len(notetypes) > 0
            test_nt = notetypes[0]
            assert "fields" in test_nt
            assert "templates" in test_nt

            # 18. Card & Note Creation API
            field_payload = {f["name"]: f"Test Value for {f['name']}" for f in test_nt["fields"]}
            create_card_res = await client.post(
                "/api/v1/cards",
                headers=headers,
                json={
                    "deck_id": card["deck_id"],
                    "notetype_id": test_nt["id"],
                    "fields": field_payload,
                    "tags": ["test_tag", "automated"],
                },
            )
            assert create_card_res.status_code == 200
            created_data = create_card_res.json()
            assert created_data["success"] is True
            assert len(created_data["created_cards"]) > 0
            new_card_id = created_data["created_cards"][0]

            # 19. Delete Created Card
            del_card_res = await client.delete(f"/api/v1/cards/{new_card_id}", headers=headers)
            assert del_card_res.status_code == 200
            assert del_card_res.json()["success"] is True

            # 20. Update Deck API (PATCH)
            patch_deck_res = await client.patch(
                f"/api/v1/decks/{card['deck_id']}",
                headers=headers,
                json={"name": "Updated Deck Name Test"},
            )
            assert patch_deck_res.status_code == 200
            assert patch_deck_res.json()["name"] == "Updated Deck Name Test"
