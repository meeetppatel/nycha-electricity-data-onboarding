let
    Source    = Clean_Activity,
    Typed     = Table.TransformColumnTypes(Source, {{"period_start", type date}, {"period_end", type date},
                                                    {"quantity", type number}, {"cost", type number}}),
    Valid     = Table.SelectRows(Typed, each [period_end] > [period_start]),
    AddDays   = Table.AddColumn(Valid, "bill_days", each Duration.Days([period_end] - [period_start]), Int64.Type),
    AddMonths = Table.AddColumn(AddDays, "month_start", each
        let s    = Date.StartOfMonth([period_start]),
            last = Date.AddDays([period_end], -1),
            n    = (Date.Year(last) - Date.Year(s)) * 12 + Date.Month(last) - Date.Month(s) + 1
        in List.Transform({0..n-1}, (i) => Date.AddMonths(s, i))),
    Expanded  = Table.ExpandListColumn(AddMonths, "month_start"),
    Typed2    = Table.TransformColumnTypes(Expanded, {{"month_start", type date}}),
    AddOverlap = Table.AddColumn(Typed2, "days_in_month", each
        let ms = [month_start], me = Date.AddMonths(ms, 1),
            a  = List.Max({[period_start], ms}), b = List.Min({[period_end], me})
        in Duration.Days(b - a), Int64.Type),
    AddKwh    = Table.AddColumn(AddOverlap, "kwh_alloc", each [quantity] * [days_in_month] / [bill_days], type number),
    AddCost   = Table.AddColumn(AddKwh, "cost_alloc", each [cost] * [days_in_month] / [bill_days], type number),
    AddEst    = Table.AddColumn(AddCost, "est_kwh_alloc", each if [estimated_flag] = "Y" then [kwh_alloc] else 0, type number),
    InYear    = Table.SelectRows(AddEst, each Date.Year([month_start]) = ReportYear),
    Grouped   = Table.Group(InYear, {"site_id", "site", "site_borough", "month_start"},
                  {{"kwh", each List.Sum([kwh_alloc]), type number},
                   {"cost", each List.Sum([cost_alloc]), type number},
                   {"estimated_kwh", each List.Sum([est_kwh_alloc]), type number}})
in
    Grouped
