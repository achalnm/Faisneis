import itertools
import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def jsonstat_to_frame(ds: dict) -> pd.DataFrame:
    dim_ids: list[str] = ds["id"]
    sizes: list[int] = ds["size"]
    dimensions: dict[str, dict] = ds["dimension"]
    values: list[Any] = ds["value"]

    dim_categories: list[list[str]] = []
    dim_labels: list[list[str]] = []

    for dim_id, size in zip(dim_ids, sizes):
        dim_data = dimensions[dim_id]
        cats = dim_data.get("category", {})
        index = cats.get("index", {})
        labels_map = cats.get("label", {})

        if isinstance(index, list):
            cat_codes = index
        elif isinstance(index, dict):
            cat_codes = [k for k, _ in sorted(index.items(), key=lambda x: x[1])]
        else:
            cat_codes = list(labels_map.keys())[:size]

        cat_codes = cat_codes[:size]
        cat_labels = [labels_map.get(c, c) for c in cat_codes]

        dim_categories.append(cat_codes)
        dim_labels.append(cat_labels)

    time_dim_ids = {d for d in dim_ids if d.startswith("TLIST")}

    rows = []
    for combo_idx, combo_codes in enumerate(itertools.product(*dim_categories)):
        val = values[combo_idx] if combo_idx < len(values) else None
        row: dict[str, Any] = {}
        for i, dim_id in enumerate(dim_ids):
            code = combo_codes[i]
            dim_data = dimensions[dim_id]
            label_map = dim_data.get("category", {}).get("label", {})
            if dim_id in time_dim_ids:
                row[dim_id] = code
            else:
                row[dim_id] = label_map.get(code, code)
        row["value"] = val
        rows.append(row)

    return pd.DataFrame(rows)


def extract_series(
    ds: dict,
    period_start: str | None = None,
    period_end: str | None = None,
    statistic_filter: str | None = None,
) -> dict:
    dim_ids: list[str] = ds.get("id", [])
    dimensions: dict = ds.get("dimension", {})
    ext = ds.get("extension", {})

    title = ds.get("label", "")
    units = ext.get("unit", {})
    matrix = ext.get("matrix", "")

    time_dim = next((d for d in dim_ids if d.startswith("TLIST")), None)
    stat_dim = next((d for d in dim_ids if d.upper() == "STATISTIC"), None)

    df = jsonstat_to_frame(ds)

    if df.empty:
        return {
            "matrix": matrix,
            "title": title,
            "units": "",
            "series": [],
            "source_url": f"https://data.cso.ie/table/{matrix}",
            "last_updated": ext.get("last-updated", ""),
        }

    chosen_stat_label: str | None = None
    chosen_stat_code: str | None = None
    if stat_dim and stat_dim in df.columns:
        stat_cats = dimensions[stat_dim].get("category", {})
        stat_labels = stat_cats.get("label", {})
        stat_index = stat_cats.get("index", {})
        if isinstance(stat_index, list):
            first_code = stat_index[0] if stat_index else None
        elif isinstance(stat_index, dict):
            first_code = next(iter(stat_index), None)
        else:
            first_code = None

        if statistic_filter:
            for code, label in stat_labels.items():
                if statistic_filter.lower() in label.lower():
                    first_code = code
                    break

        if first_code:
            chosen_stat_code = first_code
            chosen_stat_label = stat_labels.get(first_code, first_code)
            df = df[df[stat_dim] == chosen_stat_label]

    unit_str = ""
    if isinstance(units, dict):
        if chosen_stat_code and chosen_stat_code in units:
            unit_str = units[chosen_stat_code].get("label", "")
        elif units:
            unit_str = next(iter(units.values()), {}).get("label", "")
    elif isinstance(units, str):
        unit_str = units

    if not unit_str and chosen_stat_label:
        m = re.search(r"\(([^)]+)\)", chosen_stat_label)
        if m:
            unit_str = m.group(1)
        elif "percentage" in chosen_stat_label.lower() or "% change" in chosen_stat_label.lower():
            unit_str = "%"

    if time_dim and time_dim in df.columns:
        if period_start:
            df = df[df[time_dim] >= period_start]
        if period_end:
            df = df[df[time_dim] <= period_end]

    other_dims = [d for d in dim_ids if d != time_dim and d != stat_dim]
    series = []
    for _, row in df.iterrows():
        if row["value"] is None:
            continue
        point: dict[str, Any] = {"period": row.get(time_dim, ""), "value": row["value"]}
        for d in other_dims:
            if d in row:
                point[d] = row[d]
        series.append(point)

    series.sort(key=lambda x: x.get("period", ""))

    return {
        "matrix": matrix,
        "title": title,
        "units": unit_str,
        "series": series,
        "source_url": f"https://data.cso.ie/table/{matrix}",
        "last_updated": ext.get("last-updated", ""),
    }
