"""
Deck Management and Hierarchy Tree Construction Service.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ..models.deck import Deck, DeckConfig
from ..models.card import Card
from ..schemas.deck import DeckTreeResponse, DeckCountSchema


class DeckService:

    @staticmethod
    async def get_deck_and_child_ids(db: AsyncSession, user_id: str, deck_id: int) -> List[int]:
        """
        Retrieve deck_id and all its descendant subdeck IDs.
        Matches Anki's deck_and_child_ids behavior: any deck whose name starts with 'ParentName::'.
        """
        stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id)
        res = await db.execute(stmt)
        parent_deck = res.scalars().first()
        if not parent_deck:
            return [deck_id]

        prefix = f"{parent_deck.name}::%"
        children_stmt = select(Deck.id).where(
            Deck.user_id == user_id,
            (Deck.id == deck_id) | (Deck.name.like(prefix)),
        )
        children_res = await db.execute(children_stmt)
        return list(children_res.scalars().all())

    @staticmethod
    async def get_user_decks_tree(db: AsyncSession, user_id: str) -> List[DeckTreeResponse]:
        """
        Fetch all user decks and construct an N-level nested hierarchy based on '::' delimiters.
        Rolls up total, new, learning, and due card counts from leaf nodes to root parents.
        """
        # 1. Fetch decks
        stmt = select(Deck).where(Deck.user_id == user_id).order_by(Deck.name)
        result = await db.execute(stmt)
        decks = result.scalars().all()

        if not decks:
            return []

        # 2. Compute direct counts per deck
        now_ts = int(datetime.now(timezone.utc).timestamp())
        today_days = now_ts // 86400

        count_stmt = (
            select(
                Card.deck_id,
                Card.queue,
                Card.due,
                func.count(Card.id).label("cnt"),
            )
            .where(Card.user_id == user_id)
            .group_by(Card.deck_id, Card.queue, Card.due)
        )
        card_res = await db.execute(count_stmt)
        card_rows = card_res.all()

        deck_counts: Dict[int, Dict[str, int]] = {}
        for r in card_rows:
            did, queue, due, cnt = r[0], r[1], r[2], r[3]
            if did not in deck_counts:
                deck_counts[did] = {"new": 0, "learning": 0, "due": 0, "total": 0}
            deck_counts[did]["total"] += cnt
            if queue == 0:
                deck_counts[did]["new"] += cnt
            elif queue in (1, 3):
                deck_counts[did]["learning"] += cnt
            elif queue == 2 and due <= today_days:
                deck_counts[did]["due"] += cnt

        # 3. Create node dictionary indexed by full deck name
        nodes_by_name: Dict[str, DeckTreeResponse] = {}
        for d in decks:
            c = deck_counts.get(d.id, {"new": 0, "learning": 0, "due": 0, "total": 0})
            leaf_name = d.name.rsplit("::", 1)[-1] if "::" in d.name else d.name
            nodes_by_name[d.name] = DeckTreeResponse(
                id=d.id,
                name=leaf_name,
                description=d.description or "",
                is_collapsed=d.is_collapsed,
                total_cards=c["total"],
                counts=DeckCountSchema(new=c["new"], learning=c["learning"], due=c["due"]),
                children=[],
            )

        # 4. Link parents and children
        root_nodes: List[DeckTreeResponse] = []
        for full_name, node in nodes_by_name.items():
            if "::" in full_name:
                parent_name = full_name.rsplit("::", 1)[0]
                if parent_name in nodes_by_name:
                    nodes_by_name[parent_name].children.append(node)
                    continue
            root_nodes.append(node)

        # 5. Post-order traversal to roll up counts recursively to parents and root
        def roll_up_totals(curr: DeckTreeResponse) -> None:
            for child in curr.children:
                roll_up_totals(child)
                curr.total_cards += child.total_cards
                curr.counts.new += child.counts.new
                curr.counts.learning += child.counts.learning
                curr.counts.due += child.counts.due

        for root in root_nodes:
            roll_up_totals(root)

        return root_nodes
