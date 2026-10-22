from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone

from . import __version__
from .analysis import topic_trends, weekly_topic_counts
from .client import APIError, AuthError, PHClient
from .collector import Collector
from .exporters import export
from .store import JsonlStore


def _month_or_day(s: str) -> date:
    return date.fromisoformat(s + "-01" if len(s) == 7 else s)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ph-dataset", description="Build your own Product Hunt dataset.")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--data-dir", default="data", help="where products.jsonl/state.json live (default: data)")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    def collect_opts(sp):
        sp.add_argument("--topic", help="Product Hunt topic slug, e.g. artificial-intelligence")
        sp.add_argument("--with-comments", action="store_true", help="also fetch comments (opt-in)")
        sp.add_argument("--with-makers", action="store_true", help="store maker names (opt-in)")
        sp.add_argument("--max-comments", type=int, default=50)
        sp.add_argument("--featured-only", action="store_true",
                        help="only featured launches (far fewer API calls)")
        sp.add_argument("--max-products", type=int)

    f = sub.add_parser("fetch", help="collect a date range (resumable)")
    f.add_argument("--since", required=True, type=_month_or_day, help="YYYY-MM or YYYY-MM-DD")
    f.add_argument("--until", type=_month_or_day, help="exclusive end date (default: tomorrow UTC)")
    collect_opts(f)

    u = sub.add_parser("update", help="incrementally fetch new days since the last run")
    collect_opts(u)

    e = sub.add_parser("export", help="export deduplicated data")
    e.add_argument("--format", choices=["csv", "json", "parquet"], default="csv")
    e.add_argument("--out", help="output file (default: <data-dir>/products.<format>)")
    e.add_argument("--what", choices=["products", "comments"], default="products")

    t = sub.add_parser("trends", help="top topics by launches and votes")
    t.add_argument("--top", type=int, default=10)
    t.add_argument("--weekly", action="store_true", help="show top topics per ISO week")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if args.cmd in ("fetch", "update"):
        try:
            client = PHClient()
        except AuthError as ex:
            print(f"error: {ex}", file=sys.stderr)
            return 2
        c = Collector(client, args.data_dir, include_makers=args.with_makers,
                      include_comments=args.with_comments, max_comments=args.max_comments, topic=args.topic,
                      featured_only=args.featured_only)
        try:
            if args.cmd == "fetch":
                until = args.until or (datetime.now(timezone.utc).date() + timedelta(days=1))
                n = c.fetch(args.since, until, args.max_products)
            else:
                n = c.update(max_products=args.max_products)
        except (AuthError, APIError) as ex:
            print(f"error: {ex} (progress saved; re-run to resume)", file=sys.stderr)
            return 1
        print(f"Collected {n} products into {args.data_dir}/")
        return 0

    records = JsonlStore(os.path.join(args.data_dir, f"{getattr(args, 'what', 'products')}.jsonl")).load()
    if args.cmd == "export":
        out = args.out or os.path.join(args.data_dir, f"{args.what}.{args.format}")
        export(records, out, args.format)
        print(f"Wrote {len(records)} {args.what} to {out}")
        return 0
    if args.cmd == "trends":
        if not records:
            print("No data yet. Run `ph-dataset fetch` first.")
            return 1
        if args.weekly:
            for wk, cnt in weekly_topic_counts(records, args.top).items():
                print(wk, ", ".join(f"{t} ({n})" for t, n in cnt.most_common()))
        else:
            print(f"{'topic':40} {'launches':>8} {'votes':>8}")
            for t, n, v in topic_trends(records, args.top):
                print(f"{t:40} {n:>8} {v:>8}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
