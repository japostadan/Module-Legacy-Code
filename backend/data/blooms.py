import datetime

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data.connection import db_cursor
from data.users import User


@dataclass
class Bloom:
    id: int
    sender: str
    content: str
    sent_timestamp: datetime.datetime
    rebloom_of: Optional[int] = None
    original_sender: Optional[str] = None
    rebloom_count: int = 0


_BLOOM_COLUMNS = """
    b.id,
    u.username          AS sender,
    b.content,
    b.send_timestamp,
    b.rebloom_of,
    orig_u.username     AS original_sender,
    (SELECT COUNT(*) FROM blooms rb WHERE rb.rebloom_of = b.id) AS rebloom_count
"""

_BLOOM_JOINS = """
    INNER JOIN users u          ON u.id = b.sender_id
    LEFT  JOIN blooms orig_b    ON orig_b.id = b.rebloom_of
    LEFT  JOIN users  orig_u    ON orig_u.id = orig_b.sender_id
"""


def _row_to_bloom(row) -> Bloom:
    bloom_id, sender, content, timestamp, rebloom_of, original_sender, rebloom_count = row
    return Bloom(
        id=bloom_id,
        sender=sender,
        content=content,
        sent_timestamp=timestamp,
        rebloom_of=rebloom_of,
        original_sender=original_sender,
        rebloom_count=rebloom_count,
    )


def add_bloom(*, sender: User, content: str) -> None:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def add_rebloom(*, sender: User, bloom_id: int) -> Optional[Bloom]:
    original = get_bloom(bloom_id)
    if original is None:
        return None
    # Reblooming a rebloom is not allowed.
    if original.rebloom_of is not None:
        raise ValueError("Cannot rebloom a rebloom")

    now = datetime.datetime.now(tz=datetime.UTC)
    new_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp, rebloom_of) "
            "VALUES (%(id)s, %(sender_id)s, %(content)s, %(timestamp)s, %(rebloom_of)s)",
            dict(
                id=new_id,
                sender_id=sender.id,
                content=original.content,
                timestamp=now,
                rebloom_of=bloom_id,
            ),
        )
    return get_bloom(new_id)


def get_blooms_for_user(
    username: str, *, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs: Dict[str, Any] = {"sender_username": username}

        before_clause = ""
        if before is not None:
            before_clause = "AND b.send_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before

        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT {_BLOOM_COLUMNS}
            FROM blooms b
            {_BLOOM_JOINS}
            WHERE u.username = %(sender_username)s
              {before_clause}
            ORDER BY b.send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        return [_row_to_bloom(row) for row in cur.fetchall()]


def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT {_BLOOM_COLUMNS}
            FROM blooms b
            {_BLOOM_JOINS}
            WHERE b.id = %(bloom_id)s
            """,
            {"bloom_id": bloom_id},
        )
        row = cur.fetchone()
        return _row_to_bloom(row) if row else None


def get_blooms_with_hashtag(
    hashtag_without_leading_hash: str, *, limit: int = None
) -> List[Bloom]:
    kwargs: Dict[str, Any] = {"hashtag": hashtag_without_leading_hash}
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT {_BLOOM_COLUMNS}
            FROM blooms b
            INNER JOIN hashtags ON b.id = hashtags.bloom_id
            {_BLOOM_JOINS}
            WHERE hashtag = %(hashtag)s
            ORDER BY b.send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        return [_row_to_bloom(row) for row in cur.fetchall()]


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause
